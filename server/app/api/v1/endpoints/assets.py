"""
자산 검색 API 엔드포인트

자동완성 검색 기능을 제공하는 API 라우터입니다.
"""

from fastapi import APIRouter, Depends, Query
from app.services.search import AssetSearchService
from app.core.dependencies import get_asset_search_service
from app.schemas.asset import AssetSearchResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=AssetSearchResponse)
async def search_assets(
    q: str = Query(..., description="검색 쿼리 (종목명, 티커, 초성 등)"),
    limit: int = Query(10, ge=1, le=100, description="최대 결과 개수"),
    asset_search_service: AssetSearchService = Depends(get_asset_search_service)
) -> AssetSearchResponse:
    """
    자산을 검색합니다 (자동완성).

    검색 타입:
    - 초성만: "ㅅㅅㅈㅈ" -> 삼성전자
    - 한글: "삼성" -> 삼성전자, 삼성물산, ...
    - 영문/숫자: "aapl" -> AAPL

    Args:
        q: 검색 쿼리 문자열
        limit: 반환할 최대 결과 개수 (기본값: 10, 최대: 100)
        asset_search_service: 주입받은 AssetSearchService 인스턴스

    Returns:
        AssetSearchResponse: 검색 결과 객체
            - results: 검색 결과 리스트 (각 항목은 ticker, name_kr, name_en, asset_type, exchange 포함)
            - total: 총 결과 개수
    """
    logger.info(f"[Assets Router] Search request: q='{q}', limit={limit}")

    try:
        results = asset_search_service.search(query=q, limit=limit)
        logger.info(f"[Assets Router] Found {len(results)} results")
        return AssetSearchResponse(results=results, total=len(results))

    except Exception as e:
        # 모든 예외를 로그에 기록하고 빈 결과 반환 (500 에러 방지)
        logger.exception(f"[Assets Router] Search failed for q='{q}': {e}")
        return AssetSearchResponse(results=[], total=0)
