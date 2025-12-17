from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseStockProvider(ABC):
    """
    주식 데이터 제공자를 위한 추상 베이스 클래스 (Strategy Pattern)
    
    모든 Provider는 이 인터페이스를 구현하여 동일한 구조의 데이터를 반환해야 합니다.
    내부 동작은 다르지만, 반환값은 완벽히 동일한 구조의 Dictionary여야 합니다.
    """

    @abstractmethod
    def get_stock_info(self, ticker: str) -> Dict:
        """
        주식 정보를 표준화된 딕셔너리로 반환합니다.
        
        반환되는 딕셔너리는 다음 키들을 포함해야 합니다:
        - name: 종목명 (str)
        - symbol: 티커 심볼 (str)
        - current_price: 현재가 (float)
        - previous_close: 전일 종가 (Optional[float])
        - market_cap: 시가총액 (Optional[float])
        - pe_ratio: PER (Price-to-Earnings Ratio) (Optional[float])
        - pb_ratio: PBR (Price-to-Book Ratio) (Optional[float])
        - eps: EPS (Earnings Per Share) (Optional[float])
        - dividend_yield: 배당수익률 (Optional[float], % 단위)
        - roe: ROE (Return on Equity) (Optional[float], % 단위)
        - fifty_two_week_low: 52주 최저가 (Optional[float])
        - fifty_two_week_high: 52주 최고가 (Optional[float])
        - target_mean_price: 목표가 평균 (Optional[float])
        - sector: 섹터 (Optional[str])
        - industry: 산업 (Optional[str])
        - summary: 회사 개요 (Optional[str])
        - currency: 통화 (str, 예: "KRW" 또는 "USD")
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS", "AAPL")
            
        Returns:
            Dict: 표준화된 주식 정보 딕셔너리
        """
        pass

    @abstractmethod
    def get_news(self, ticker: str) -> List[str]:
        """
        주식 관련 뉴스 제목 리스트를 반환합니다.
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS", "AAPL")
            
        Returns:
            List[str]: 뉴스 제목 리스트 (최대 3개 권장)
        """
        pass
