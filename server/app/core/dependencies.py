from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.ai_service import AIService
from app.services.stock import StockService
from app.services.update_log_service import UpdateLogService


@lru_cache()
def get_stock_service() -> StockService:
    """
    StockService 인스턴스를 생성하고 반환합니다.
    Dependency Injection을 위한 함수입니다.
    """
    return StockService()


@lru_cache()
def get_ai_service() -> AIService:
    """
    AIService 인스턴스를 생성하고 반환합니다.
    Dependency Injection을 위한 함수입니다.
    """
    return AIService(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)


def get_update_log_service(db: Session = Depends(get_db)) -> UpdateLogService:
    """
    UpdateLogService 인스턴스를 생성하고 반환합니다.
    매 요청마다 DB 세션을 주입받도록 설계합니다.
    """
    return UpdateLogService(db=db)

