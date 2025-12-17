from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, List
from app.schemas.stock import (
    StockInfo,
    StockAnalysisRequest,
    StockAnalysisResponse,
    AIAnalysisResponse,
    TickerSearchRequest,
    TickerSearchResponse,
)
from app.services.stock.service import StockService
from app.services.ai_service import AIService
from app.core.dependencies import get_stock_service, get_ai_service
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=TickerSearchResponse)
async def search_ticker(
    request: TickerSearchRequest,
    stock_service: StockService = Depends(get_stock_service)
) -> TickerSearchResponse:
    """
    종목명이나 기업명을 티커로 변환합니다.
    
    Args:
        request: 검색 요청 데이터 (한글 종목명, 기업명, 티커 모두 가능)
        stock_service: 주입받은 StockService 인스턴스
        
    Returns:
        TickerSearchResponse: 변환된 티커와 종목명
    """
    try:
        ticker = stock_service.search_ticker(request.query)
        return TickerSearchResponse(ticker=ticker)
    except ValueError as e:
        error_message = str(e)
        logger.warning(f"[Stocks Router] Ticker search failed for '{request.query}': {error_message}")
        # 검색 실패는 404가 아니라 400 (Bad Request) 또는 422 (Unprocessable Entity)가 더 적절
        # 하지만 클라이언트 호환성을 위해 404 유지하되, 더 명확한 메시지 제공
        raise HTTPException(
            status_code=404, 
            detail=f"'{request.query}'에 대한 종목을 찾을 수 없습니다. 티커 심볼(예: 005930.KS, AAPL)을 직접 입력해주세요."
        )
    except Exception as e:
        logger.error(f"[Stocks Router] Unexpected error during ticker search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"종목 검색 중 서버 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{ticker}")
async def get_stock(
    ticker: str,
    stock_service: StockService = Depends(get_stock_service),
    db: Session = Depends(get_db)
) -> Dict:
    """
    티커로 주식 정보를 가져옵니다.
    
    Args:
        ticker: 주식 티커 심볼
        stock_service: 주입받은 StockService 인스턴스
        db: 데이터베이스 세션
        
    Returns:
        Dict: 주식 정보와 뉴스
    """
    try:
        stock_data, news = stock_service.get_stock_info(ticker.upper(), db)
        return {
            "stock_data": stock_data,
            "news": news
        }
    except ValueError as e:
        logger.error(f"[Stocks Router] ValueError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[Stocks Router] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")


@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock(
    request: StockAnalysisRequest,
    stock_service: StockService = Depends(get_stock_service),
    ai_service: AIService = Depends(get_ai_service),
    db: Session = Depends(get_db)
) -> StockAnalysisResponse:
    """
    주식 정보를 가져오고 AI 분석을 수행합니다.
    
    Args:
        request: 주식 분석 요청 데이터
        stock_service: 주입받은 StockService 인스턴스
        ai_service: 주입받은 AIService 인스턴스
        db: 데이터베이스 세션
        
    Returns:
        StockAnalysisResponse: 주식 정보, 뉴스, AI 분석 결과
    """
    try:
        ticker = request.ticker.upper()
        
        # 주식 정보 가져오기
        stock_data, news = stock_service.get_stock_info(ticker, db)
        
        # market_cap 타입 검증 및 강제 변환 (스키마 호환성)
        if 'market_cap' in stock_data and stock_data['market_cap'] is not None:
            if not isinstance(stock_data['market_cap'], str):
                try:
                    stock_data['market_cap'] = str(int(float(stock_data['market_cap'])))
                    logger.info(f"[Stocks Router] market_cap 타입 변환 완료: {stock_data['market_cap']}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"[Stocks Router] market_cap 변환 실패: {e}, None으로 설정")
                    stock_data['market_cap'] = None
        
        # AI 분석 수행
        ai_analysis = ai_service.analyze_stock(stock_data, news)
        
        # AI 분석 결과에서 metric_insights를 stock_data에 추가
        if ai_analysis and 'metric_insights' in ai_analysis:
            stock_data['metric_insights'] = ai_analysis.get('metric_insights')
        
        return StockAnalysisResponse(
            stock_data=StockInfo(**stock_data),
            news=news,
            ai_analysis=ai_analysis
        )
    except ValueError as e:
        logger.error(f"[Stocks Router] ValueError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[Stocks Router] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")


@router.post("/analyze-ai", response_model=AIAnalysisResponse)
async def analyze_stock_ai_only(
    request: StockAnalysisRequest,
    stock_service: StockService = Depends(get_stock_service),
    ai_service: AIService = Depends(get_ai_service),
    db: Session = Depends(get_db)
) -> AIAnalysisResponse:
    """
    주식 정보를 가져온 후 AI 분석만 수행합니다.
    
    Args:
        request: 주식 분석 요청 데이터
        stock_service: 주입받은 StockService 인스턴스
        ai_service: 주입받은 AIService 인스턴스
        db: 데이터베이스 세션
        
    Returns:
        AIAnalysisResponse: AI 분석 결과만
    """  
    try:
        ticker = request.ticker.upper()
        
        # 주식 정보 가져오기
        stock_data, news = stock_service.get_stock_info(ticker, db)
        
        # AI 분석 수행
        ai_analysis = ai_service.analyze_stock(stock_data, news)
        
        if ai_analysis:
            return AIAnalysisResponse(**ai_analysis)
        else:
            raise HTTPException(
                status_code=500, 
                detail="AI 분석에 실패했습니다."
            )
    except ValueError as e:
        logger.error(f"[Stocks Router] ValueError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Stocks Router] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

