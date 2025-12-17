import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AccessTokenManager:
    """
    KIS API Access Token을 파일에 저장하고 관리하는 클래스
    
    토큰은 24시간 유효하며, 파일에 저장하여 프로그램 재시작 후에도 재사용합니다.
    만료 1시간 전에 자동으로 갱신합니다.
    """
    
    def __init__(self, token_file_path: Optional[str] = None):
        """
        AccessTokenManager 초기화
        
        Args:
            token_file_path: 토큰 파일 경로. None인 경우 기본 경로 사용
        """
        if token_file_path is None:
            # server 디렉토리를 기준으로 token.json 파일 경로 설정
            # 현재 파일 위치: server/app/services/stock/token_manager.py
            # 목표 위치: server/token.json
            current_file = Path(__file__)
            server_dir = current_file.parent.parent.parent.parent  # server 디렉토리
            token_file_path = str(server_dir / "token.json")
        
        self.token_file_path = Path(token_file_path)
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    def _load_token_from_file(self) -> tuple[Optional[str], Optional[datetime]]:
        """
        파일에서 토큰과 만료 시간을 로드합니다.
        
        Returns:
            tuple: (access_token, expires_at) 또는 (None, None) if 파일이 없거나 유효하지 않음
        """
        if not self.token_file_path.exists():
            logger.debug(f"[AccessTokenManager] 토큰 파일이 존재하지 않음: {self.token_file_path}")
            return None, None
        
        try:
            with open(self.token_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            access_token = data.get("access_token")
            timestamp_str = data.get("timestamp")
            
            if not access_token or not timestamp_str:
                logger.warning(f"[AccessTokenManager] 토큰 파일에 필수 필드가 없음: {self.token_file_path}")
                return None, None
            
            # ISO 형식의 timestamp를 datetime으로 변환
            try:
                expires_at = datetime.fromisoformat(timestamp_str)
            except (ValueError, TypeError) as e:
                logger.warning(f"[AccessTokenManager] 타임스탬프 파싱 실패: {e}")
                return None, None
            
            logger.info(f"[AccessTokenManager] 토큰 파일에서 로드 성공 (만료: {expires_at})")
            return access_token, expires_at
            
        except json.JSONDecodeError as e:
            logger.warning(f"[AccessTokenManager] 토큰 파일 JSON 파싱 실패: {e}")
            return None, None
        except Exception as e:
            logger.error(f"[AccessTokenManager] 토큰 파일 로드 중 오류: {e}")
            return None, None
    
    def _save_token_to_file(self, access_token: str, expires_in: int = 86400) -> None:
        """
        토큰과 만료 시간을 파일에 저장합니다.
        
        Args:
            access_token: 저장할 Access Token
            expires_in: 토큰 유효기간 (초). 기본값 86400 (24시간)
        """
        try:
            # 만료 시간 계산 (24시간 - 1시간 여유 = 23시간)
            # 실제로는 API에서 받은 expires_in 값을 사용하되, 안전을 위해 1시간 여유를 둠
            expires_at = datetime.now() + timedelta(seconds=expires_in - 3600)  # 1시간 여유
            
            data = {
                "access_token": access_token,
                "timestamp": expires_at.isoformat(),
                "expires_in": expires_in,
                "saved_at": datetime.now().isoformat()
            }
            
            # 디렉토리가 없으면 생성
            self.token_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.token_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[AccessTokenManager] 토큰 파일에 저장 성공: {self.token_file_path} (만료: {expires_at})")
            
        except Exception as e:
            logger.error(f"[AccessTokenManager] 토큰 파일 저장 중 오류: {e}")
            raise
    
    def is_token_valid(self, access_token: Optional[str] = None, expires_at: Optional[datetime] = None) -> bool:
        """
        토큰이 유효한지 확인합니다.
        
        Args:
            access_token: 확인할 토큰 (None인 경우 내부 저장된 토큰 사용)
            expires_at: 만료 시간 (None인 경우 내부 저장된 만료 시간 사용)
        
        Returns:
            bool: 토큰이 유효하면 True, 그렇지 않으면 False
        """
        token = access_token or self._access_token
        expires = expires_at or self._token_expires_at
        
        if not token or not expires:
            return False
        
        # 현재 시간이 만료 시간보다 1시간 이상 여유가 있으면 유효
        # (1시간 여유를 두어 만료 직전에 갱신)
        now = datetime.now()
        time_until_expiry = (expires - now).total_seconds()
        
        return time_until_expiry > 3600  # 1시간 이상 남았으면 유효
    
    def get_token(self) -> Optional[str]:
        """
        유효한 토큰을 반환합니다. 파일에서 로드하거나 메모리에서 반환합니다.
        
        Returns:
            Optional[str]: 유효한 토큰이 있으면 반환, 없으면 None
        """
        # 먼저 메모리에 저장된 토큰이 유효한지 확인
        if self.is_token_valid():
            logger.debug("[AccessTokenManager] 메모리에서 유효한 토큰 반환")
            return self._access_token
        
        # 파일에서 토큰 로드 시도
        access_token, expires_at = self._load_token_from_file()
        
        if access_token and expires_at:
            self._access_token = access_token
            self._token_expires_at = expires_at
            
            # 로드한 토큰이 유효한지 확인
            if self.is_token_valid():
                logger.info("[AccessTokenManager] 파일에서 유효한 토큰 로드 및 반환")
                return self._access_token
            else:
                logger.info("[AccessTokenManager] 파일에서 로드한 토큰이 만료됨")
                self._access_token = None
                self._token_expires_at = None
        
        return None
    
    def save_token(self, access_token: str, expires_in: int = 86400) -> None:
        """
        새 토큰을 저장합니다 (파일 및 메모리).
        
        Args:
            access_token: 저장할 Access Token
            expires_in: 토큰 유효기간 (초). 기본값 86400 (24시간)
        """
        self._access_token = access_token
        # 만료 시간 계산 (24시간 - 1시간 여유 = 23시간)
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 3600)
        
        # 파일에 저장
        self._save_token_to_file(access_token, expires_in)
        
        logger.info(f"[AccessTokenManager] 새 토큰 저장 완료 (만료: {self._token_expires_at})")
    
    def clear_token(self) -> None:
        """
        저장된 토큰을 삭제합니다 (파일 및 메모리).
        """
        self._access_token = None
        self._token_expires_at = None
        
        if self.token_file_path.exists():
            try:
                self.token_file_path.unlink()
                logger.info(f"[AccessTokenManager] 토큰 파일 삭제: {self.token_file_path}")
            except Exception as e:
                logger.warning(f"[AccessTokenManager] 토큰 파일 삭제 실패: {e}")
