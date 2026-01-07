"""
자산 자동완성 API 엔드포인트 (메모리 기반 - DB 접근 절대 금지)

**중요**: 이 엔드포인트는 자동완성 전용이며, 요청 처리 시 DB에 절대 접근하지 않습니다.
모든 데이터는 서버 startup 시 메모리에 로드되며, API 요청은 메모리만 사용합니다.

**DB 접근 정책**:
- ✅ 서버 startup: main.py에서 메모리 인덱스 로딩 (DB 접근)
- ❌ API 요청 처리: DB 접근 절대 금지 (메모리만 사용)

**일반 검색은 여기 아님**:
정확한 종목명→티커 변환이 필요하면 POST /api/v1/stock/search를 사용하세요.
"""

from fastapi import APIRouter, Depends, Query
from app.services.autocomplete import AutocompleteService
from app.core.dependencies import get_autocomplete_service
from app.schemas.asset import AssetSearchResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=AssetSearchResponse)
async def autocomplete_assets(
    q: str = Query(..., description="검색 쿼리 (종목명, 티커, 초성 등)"),
    limit: int = Query(10, ge=1, le=100, description="최대 결과 개수"),
    autocomplete_service: AutocompleteService = Depends(get_autocomplete_service)
) -> AssetSearchResponse:
    """
    자산을 자동완성 검색합니다 (메모리 기반).

    **DB 접근**: 이 엔드포인트는 DB에 절대 접근하지 않습니다 (메모리만 사용).

    **검색 타입**:
    - 초성만: "ㅅㅅㅈㅈ" -> 삼성전자
    - 한글: "삼성" -> 삼성전자, 삼성물산, ...
    - 영문/숫자: "aapl" -> AAPL

    **사용 사례**:
    - 검색창 실시간 자동완성
    - Prefix 기반 빠른 검색

    **NOT for**:
    - 정확한 종목명→티커 변환 (→ POST /api/v1/stock/search 사용)

    Args:
        q: 검색 쿼리 문자열
        limit: 반환할 최대 결과 개수 (기본값: 10, 최대: 100)
        autocomplete_service: 주입받은 AutocompleteService 인스턴스

    Returns:
        AssetSearchResponse: 검색 결과 객체
            - results: 검색 결과 리스트 (각 항목은 ticker, name_kr, name_en, asset_type, exchange 포함)
            - total: 총 결과 개수
    """
    logger.info(f"[Autocomplete Router] Autocomplete request: q='{q}', limit={limit}")

    try:
        # 메모리 기반 검색 (DB 접근 없음)
        results = autocomplete_service.search(query=q, limit=limit)
        logger.info(f"[Autocomplete Router] Found {len(results)} results (메모리 기반)")
        return AssetSearchResponse(results=results, total=len(results))

    except Exception as e:
        # 모든 예외를 로그에 기록하고 빈 결과 반환 (500 에러 방지)
        logger.exception(f"[Autocomplete Router] Search failed for q='{q}': {e}")
        return AssetSearchResponse(results=[], total=0)
