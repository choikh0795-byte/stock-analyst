from functools import lru_cache
from app.services.stock import StockService
from app.services.ai_service import AIService
from app.core.config import settings


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

