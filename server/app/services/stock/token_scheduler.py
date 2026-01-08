"""
KIS API 토큰 자동 갱신 스케줄러

하루 1회(06:00) 토큰을 갱신하여 첫 사용자 요청 시 토큰 발급 지연을 방지합니다.
서버 재시작 시에는 토큰을 재발급하지 않으며, 파일에 저장된 유효한 토큰을 재사용합니다.
"""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .token_manager import AccessTokenManager

logger = logging.getLogger(__name__)


class TokenScheduler:
    """
    KIS API Access Token 자동 갱신 스케줄러

    역할:
    - 매일 06:00에 토큰 만료 여부 확인
    - 토큰이 곧 만료될 경우에만 갱신 (will_expire_soon 체크)
    - 서버 재시작 시 토큰 재발급 방지 (파일 기반 토큰 재사용)

    설계 원칙:
    - OOP 구조 유지 (Class 기반)
    - TokenManager와 협력하여 토큰 관리
    - 스케줄러 오류 시 서버 크래시 방지
    """

    def __init__(self, token_manager: Optional[AccessTokenManager] = None) -> None:
        """
        TokenScheduler 초기화

        Args:
            token_manager: AccessTokenManager 인스턴스 (None인 경우 새로 생성)
        """
        self._token_manager = token_manager or AccessTokenManager()
        self._scheduler: Optional[AsyncIOScheduler] = None

        logger.info("[TokenScheduler] 초기화 완료")

    def start(self) -> None:
        """
        스케줄러 시작

        매일 06:00에 토큰 갱신 작업 실행
        서버 startup 시 호출되며, 토큰을 즉시 발급하지 않음
        """
        if self._scheduler is not None:
            logger.warning("[TokenScheduler] 이미 실행 중인 스케줄러가 있습니다")
            return

        try:
            self._scheduler = AsyncIOScheduler()

            # 매일 06:00에 실행 (KST 기준)
            # 주의: 서버가 UTC 기준이면 hour를 21(UTC 21:00 = KST 06:00)로 설정 필요
            # 현재는 서버 로컬 시간 기준 06:00으로 설정
            trigger = CronTrigger(hour=6, minute=0)

            self._scheduler.add_job(
                func=self._refresh_token_if_needed,
                trigger=trigger,
                id="kis_token_refresh",
                name="KIS API Token Refresh (Daily 06:00)",
                replace_existing=True,
                misfire_grace_time=3600  # 1시간 이내 실행 실패 시 재시도
            )

            self._scheduler.start()
            logger.info("[TokenScheduler] 스케줄러 시작 완료 (매일 06:00 실행)")

        except Exception as e:
            logger.error(f"[TokenScheduler] 스케줄러 시작 실패: {e}", exc_info=True)
            # 스케줄러 오류로 인한 서버 크래시 방지 - 로그만 남기고 계속 진행

    def stop(self) -> None:
        """
        스케줄러 중지

        서버 shutdown 시 호출
        """
        if self._scheduler is None:
            logger.debug("[TokenScheduler] 중지할 스케줄러가 없습니다")
            return

        try:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("[TokenScheduler] 스케줄러 중지 완료")

        except Exception as e:
            logger.error(f"[TokenScheduler] 스케줄러 중지 실패: {e}", exc_info=True)

    def _refresh_token_if_needed(self) -> None:
        """
        토큰이 곧 만료될 경우에만 갱신

        스케줄러 작업 함수 (매일 06:00 실행)
        will_expire_soon() 체크 후 필요한 경우에만 토큰 재발급
        """
        try:
            logger.info("[TokenScheduler] 토큰 갱신 작업 시작 (스케줄러)")

            # 토큰이 30분 이내에 만료될지 확인
            if self._token_manager.will_expire_soon(threshold_minutes=30):
                logger.info("[TokenScheduler] 토큰이 곧 만료됨 - 갱신 시작")

                # KisApiClient를 통해 토큰 재발급
                # 직접 토큰 발급 API를 호출하는 대신, KisApiClient를 재사용
                from .kis_api_client import KisApiClient

                api_client = KisApiClient()
                # get_access_token()은 내부적으로 유효한 토큰이 있으면 재사용하고,
                # 없으면 새로 발급함
                new_token = api_client.get_access_token()

                if new_token:
                    logger.info("[TokenScheduler] ✅ 토큰 갱신 성공")
                else:
                    logger.warning("[TokenScheduler] ⚠️ 토큰 갱신 실패 (None 반환)")

            else:
                logger.info("[TokenScheduler] 토큰이 아직 유효함 - 갱신 건너뜀")

        except Exception as e:
            # 스케줄러 작업 실패 시 로그만 남기고 서버 크래시 방지
            logger.error(
                f"[TokenScheduler] 토큰 갱신 작업 중 오류 발생: {e}",
                exc_info=True
            )
            logger.warning(
                "[TokenScheduler] 토큰 갱신 실패 - 다음 스케줄 또는 사용자 요청 시 재시도됩니다"
            )
