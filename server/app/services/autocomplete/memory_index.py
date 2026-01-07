"""
자동완성 메모리 인덱스 (DB 접근 없음)

**중요**: 이 클래스는 서버 startup 시에만 DB에 접근하며,
요청 처리 시점에는 절대로 DB에 접근하지 않습니다.

**사용 흐름**:
1. 서버 startup: main.py에서 load_from_db() 호출 (DB 접근)
2. 요청 처리: AutocompleteService가 get_all_assets() 호출 (메모리만)

**DB 접근 시점**:
- ✅ 서버 startup (main.py lifespan)
- ❌ API 요청 처리 중 (절대 금지)
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
import logging

from app.models.asset_search_index import AssetSearchIndex

logger = logging.getLogger(__name__)


class AutocompleteMemoryIndex:
    """
    자동완성 메모리 인덱스 클래스 (Singleton)

    서버 기동 시 asset_search_index 테이블 데이터를 메모리에 로드하여
    자동완성 검색 성능을 개선합니다.

    **Singleton 패턴**: 애플리케이션 전체에서 단일 인스턴스만 존재
    **DB 접근 정책**:
    - load_from_db(): 서버 startup 시에만 호출 (DB 접근)
    - get_all_assets(), is_initialized(): 요청 처리 중 호출 (메모리만)

    Attributes:
        _assets: 메모리에 저장된 자산 정보 리스트
        _initialized: 초기화 완료 여부
    """

    _instance: Optional["AutocompleteMemoryIndex"] = None
    _initialized: bool = False

    def __new__(cls) -> "AutocompleteMemoryIndex":
        """
        Singleton 패턴 구현

        Returns:
            AutocompleteMemoryIndex: 단일 인스턴스
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._assets = []
            cls._instance._initialized = False
            logger.info("[AutocompleteMemoryIndex] Singleton instance created")
        return cls._instance

    def load_from_db(self, db: Session) -> None:
        """
        데이터베이스에서 자산 검색 인덱스를 메모리에 로드합니다.

        **DB 접근**: 이 메서드만 DB에 접근합니다 (서버 startup 시에만 호출).

        is_active = True인 자산만 로드하며, 다음 필드를 저장합니다:
        - ticker: 종목 티커 코드
        - name_kr: 한글 이름
        - name_en: 영문 이름
        - initial_kr: 한글 초성
        - asset_type: 자산 유형 (STOCK_KR, STOCK_US, ETF)
        - exchange: 거래소 코드

        Args:
            db: SQLAlchemy 데이터베이스 세션

        Raises:
            Exception: 데이터 로딩 중 오류 발생 시
        """
        if self._initialized:
            logger.warning("[AutocompleteMemoryIndex] Already initialized. Skipping reload.")
            return

        try:
            logger.info("[AutocompleteMemoryIndex] Starting to load data from database...")

            # is_active = True인 자산만 조회
            stmt = select(AssetSearchIndex).where(AssetSearchIndex.is_active == True)
            results = db.execute(stmt).scalars().all()

            # 메모리 구조로 변환
            self._assets = []
            for asset in results:
                self._assets.append({
                    "id": asset.id,
                    "ticker": asset.ticker,
                    "name_kr": asset.name_kr,
                    "name_en": asset.name_en,
                    "initial_kr": asset.initial_kr,
                    "asset_type": asset.asset_type.value,
                    "exchange": asset.exchange,
                    "search_tokens": asset.search_tokens if asset.search_tokens else []
                })

            self._initialized = True

            logger.info(
                f"[AutocompleteMemoryIndex] ✅ Successfully loaded {len(self._assets)} assets into memory"
            )

        except Exception as e:
            logger.exception(f"[AutocompleteMemoryIndex] ❌ Failed to load data from database: {e}")
            # 초기화 실패 시 빈 리스트로 유지
            self._assets = []
            self._initialized = False
            raise

    def get_all_assets(self) -> List[Dict]:
        """
        메모리에 저장된 모든 자산 정보를 반환합니다.

        **DB 접근**: 없음 (메모리만 사용)

        Returns:
            List[Dict]: 자산 정보 리스트
        """
        return self._assets

    def is_initialized(self) -> bool:
        """
        메모리 인덱스 초기화 완료 여부를 반환합니다.

        **DB 접근**: 없음

        Returns:
            bool: 초기화 완료 시 True, 그렇지 않으면 False
        """
        return self._initialized

    def get_asset_count(self) -> int:
        """
        메모리에 저장된 자산 개수를 반환합니다.

        **DB 접근**: 없음

        Returns:
            int: 자산 개수
        """
        return len(self._assets)

    def clear(self) -> None:
        """
        메모리 인덱스를 초기화합니다.

        **DB 접근**: 없음

        주로 테스트 용도로 사용됩니다.
        """
        self._assets = []
        self._initialized = False
        logger.info("[AutocompleteMemoryIndex] Memory index cleared")
