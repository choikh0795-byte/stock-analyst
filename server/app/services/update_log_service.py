import logging
from typing import List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.update_log import UpdateLog

logger = logging.getLogger(__name__)


class UpdateLogService:
    """
    업데이트 로그 조회 비즈니스 로직을 담당하는 서비스.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all_logs(self) -> List[UpdateLog]:
        """
        업데이트 로그 전체를 최신순으로 반환합니다.
        """
        try:
            return (
                self.db.query(UpdateLog)
                .order_by(UpdateLog.created_at.desc())
                .all()
            )
        except SQLAlchemyError as exc:
            logger.error(f"[UpdateLogService] 로그 조회 중 오류: {exc}")
            raise

