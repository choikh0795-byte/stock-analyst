from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.ai_service import AIService
from app.services.stock import StockService
from app.services.update_log_service import UpdateLogService
from app.services.autocomplete import AutocompleteService, AutocompleteMemoryIndex


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


@lru_cache()
def get_autocomplete_service() -> AutocompleteService:
    """
    AutocompleteService 인스턴스를 생성하고 반환합니다 (자동완성 전용).

    **중요**: 이 Service는 요청 처리 시 DB에 절대 접근하지 않습니다.
    메모리 인덱스(Singleton)만 주입받아 빠른 자동완성 검색을 제공합니다.

    **DB 접근 정책**:
    - ✅ 서버 startup 시: 메모리 인덱스 로딩 (main.py lifespan)
    - ❌ API 요청 처리 중: DB 접근 절대 금지

    **사용 사례**:
    - 검색창 자동완성
    - Prefix 검색 (제한된 결과 개수)

    **NOT for**:
    - 일반 검색 (→ StockService.search_ticker() 사용)
    """
    memory_index = AutocompleteMemoryIndex()
    return AutocompleteService(memory_index=memory_index)

