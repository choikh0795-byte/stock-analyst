from typing import Optional


class StockFormatter:
    """Formatting helpers to convert numeric values into display-friendly strings."""

    @staticmethod
    def format_currency(value: Optional[float], is_korean: bool) -> str:
        """
        가격 데이터를 통화 형식으로 포맷팅

        - 한국: 정수 처리 + 3자리 쉼표 + '원'
        - 미국: 달러 기호 + 소수점 2자리 + 3자리 쉼표
        """
        if value is None or value == 0:
            return "-"

        if is_korean:
            return f"{int(value):,}원"

        return f"${value:,.2f}"

    @staticmethod
    def format_dividend(dividend_yield: Optional[float], is_korean: bool) -> str:
        """
        배당률 스마트 포맷팅

        - 0 또는 None이면 "N/A"
        - 한국 종목만 소수 표기(<0.5)일 때 100을 곱해 퍼센트로 변환
        - 그 외에는 주어진 값을 퍼센트로 가정
        """
        if dividend_yield in (None, 0):
            return "N/A"

        try:
            value = float(dividend_yield)
        except Exception:
            return "N/A"

        if is_korean and value < 0.5:
            value = value * 100

        return f"{value:.2f}%"

    @staticmethod
    def format_market_cap(market_cap: Optional[float]) -> str:
        if market_cap is None or market_cap == 0:
            return "N/A"
        return f"{int(market_cap):,}"

    @staticmethod
    def format_roe(roe: Optional[float]) -> str:
        if roe is None:
            return "N/A"
        return f"{roe}%"

    @staticmethod
    def format_volatility(volatility: Optional[float], volatility_type: Optional[str]) -> str:
        if volatility is None:
            return "N/A"

        if volatility_type == "beta":
            return f"{volatility} (Beta)"

        return f"{volatility}% (1년)"

