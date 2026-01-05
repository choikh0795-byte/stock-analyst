from pydantic import BaseModel
from typing import Optional, List, Dict


class StockInfo(BaseModel):
    """자산(주식/ETF) 기본 정보 스키마"""
    name: str
    symbol: str
    asset_type: Optional[str] = "STOCK"  # "STOCK" or "ETF"
    current_price: float
    previous_close: Optional[float] = None
    market_cap: Optional[str] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    # ROE/EPS/부채비율 (백엔드 계산 결과, 주식 전용)
    roe: Optional[float] = None
    roe_str: Optional[str] = None
    eps: Optional[float] = None
    eps_str: Optional[str] = None
    debt_ratio: Optional[float] = None
    debt_ratio_str: Optional[str] = None
    # 구버전 호환 필드
    return_on_equity: Optional[float] = None
    sector: str
    industry: Optional[str] = None  # AI 분석을 위한 산업/테마 정보
    summary: str
    # 6가지 핵심 지표
    fifty_two_week_low: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    target_mean_price: Optional[float] = None
    number_of_analyst_opinions: Optional[int] = None
    peg_ratio: Optional[float] = None
    beta: Optional[float] = None
    # 백엔드에서 포맷팅된 가격 문자열 (한국: "58,800원", 미국: "$145.20")
    current_price_str: Optional[str] = None
    previous_close_str: Optional[str] = None
    fifty_two_week_low_str: Optional[str] = None
    fifty_two_week_high_str: Optional[str] = None
    target_mean_price_str: Optional[str] = None
    market_cap_str: Optional[str] = None
    # 포맷팅된 지표 문자열
    pe_ratio_str: Optional[str] = None
    pb_ratio_str: Optional[str] = None
    beta_str: Optional[str] = None
    # 가격 변동 관련 (계산 및 포맷팅)
    change_value: Optional[float] = None
    change_value_str: Optional[str] = None
    change_percentage: Optional[float] = None
    change_percentage_str: Optional[str] = None
    change_status: Optional[str] = None  # "RISING", "FALLING", "NEUTRAL"
    # 목표가 괴리율
    target_upside: Optional[float] = None
    target_upside_str: Optional[str] = None
    currency: Optional[str] = None
    # ETF 전용 필드 (6개)
    total_assets: Optional[float] = None  # 순자산 (AUM)
    total_assets_str: Optional[str] = None
    dividend_yield: Optional[float] = None  # 배당수익률 (%)
    dividend_yield_str: Optional[str] = None
    premium_discount: Optional[float] = None  # 괴리율 (%)
    premium_discount_str: Optional[str] = None
    inception_date: Optional[str] = None  # 설정일
    inception_date_str: Optional[str] = None
    average_volume: Optional[float] = None  # 평균 거래량 (유동성 지표)
    average_volume_str: Optional[str] = None
    change_52week: Optional[float] = None  # 52주 수익률 (%)
    change_52week_str: Optional[str] = None
    top_holdings: Optional[List[str]] = None  # 구성종목 Top3

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Apple Inc.",
                "symbol": "AAPL",
                "current_price": 175.50,
                "previous_close": 174.50,
                "market_cap": "2800000000000",
                "pe_ratio": 30.5,
                "pb_ratio": 1.5,
                "roe": 18.5,
                "roe_str": "18.5%",
                "eps": 5.40,
                "eps_str": "$5.40",
                "return_on_equity": 0.25,
                "sector": "Technology",
                "summary": "Apple Inc. designs, manufactures...",
                "fifty_two_week_low": 150.00,
                "fifty_two_week_high": 200.00,
                "target_mean_price": 190.00,
                "number_of_analyst_opinions": 45,
                "peg_ratio": 1.2,
                "beta": 1.3
            }
        }


class StockAnalysisRequest(BaseModel):
    """주식 분석 요청 스키마"""
    ticker: str

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL"
            }
        }


class StockAnalysisResponse(BaseModel):
    """주식 분석 응답 스키마"""
    stock_data: StockInfo
    ai_analysis: Optional[dict] = None


class AIAnalysisResponse(BaseModel):
    """AI 분석 결과 스키마 - 최적화된 구조"""
    score: float
    signal: str
    one_line: str
    summary: List[str]
    risk: str

    class Config:
        json_schema_extra = {
            "example": {
                "score": 78.4,
                "signal": "매수",
                "one_line": "강력한 성장세와 안정적인 재무구조를 보유한 우량주",
                "summary": [
                    "높은 시장 점유율과 브랜드 가치",
                    "지속적인 혁신과 R&D 투자",
                    "건전한 재무 지표"
                ],
                "risk": "시장 변동성과 경쟁 심화"
            }
        }


class TickerSearchRequest(BaseModel):
    """티커 검색 요청 스키마"""
    query: str

    class Config:
        json_schema_extra = {
            "example": {
                "query": "엔비디아"
            }
        }


class TickerSearchResponse(BaseModel):
    """티커 검색 응답 스키마"""
    ticker: str
    name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "NVDA",
                "name": "NVIDIA Corporation"
            }
        }
