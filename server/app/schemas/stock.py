from pydantic import BaseModel
from typing import Optional, List, Dict


class StockInfo(BaseModel):
    """주식 기본 정보 스키마"""
    name: str
    symbol: str
    current_price: float
    previous_close: float
    market_cap: Optional[str] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    return_on_equity: Optional[float] = None
    sector: str
    summary: str
    # 6가지 핵심 지표
    fifty_two_week_low: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    target_mean_price: Optional[float] = None
    number_of_analyst_opinions: Optional[int] = None
    peg_ratio: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    # 지표별 AI 인사이트 (각 지표에 대한 한 문장 평가)
    metric_insights: Optional[Dict[str, str]] = None

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
                "return_on_equity": 0.25,
                "sector": "Technology",
                "summary": "Apple Inc. designs, manufactures...",
                "fifty_two_week_low": 150.00,
                "fifty_two_week_high": 200.00,
                "target_mean_price": 190.00,
                "number_of_analyst_opinions": 45,
                "peg_ratio": 1.2,
                "beta": 1.3,
                "dividend_yield": 0.005
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
    news: List[str]
    ai_analysis: Optional[dict] = None


class AIAnalysisResponse(BaseModel):
    """AI 분석 결과 스키마"""
    score: int
    signal: str
    one_line: str
    summary: List[str]
    risk: str
    metric_insights: Optional[Dict[str, str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "score": 75,
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

