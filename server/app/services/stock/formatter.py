from typing import Optional, Literal
from datetime import datetime


class StockFormatter:
    """Formatting helpers to convert numeric values into display-ready strings."""

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
        return f"{roe:.1f}%"

    @staticmethod
    def format_eps(eps: Optional[float], is_korean: bool) -> str:
        """
        EPS 포맷팅
        
        - None이면 "N/A"
        - 한국 주식: 소수점 버리고 천 단위 콤마 + "원" (예: 5,400원)
        - 미국 주식: 소수점 2자리 + "$" (예: $5.40)
        """
        if eps is None:
            return "N/A"
        
        if is_korean:
            return f"{int(eps):,}원"
        
        return f"${eps:.2f}"

    @staticmethod
    def format_pe_ratio(pe_ratio: Optional[float], is_korean: bool) -> str:
        """
        PER 포맷팅
        
        - None이면 "N/A"
        - 한국 주식: 소수점 1자리 + "배" (예: 12.5배)
        - 미국 주식: 소수점 1자리 + "배" (예: 12.5배)
        """
        if pe_ratio is None:
            return "N/A"
        return f"{pe_ratio:.1f}배"

    @staticmethod
    def format_pb_ratio(pb_ratio: Optional[float], is_korean: bool) -> str:
        """
        PBR 포맷팅
        
        - None이면 "N/A"
        - 소수점 1자리 + "배" (예: 1.5배)
        """
        if pb_ratio is None:
            return "N/A"
        return f"{pb_ratio:.1f}배"

    @staticmethod
    def format_beta(beta: Optional[float]) -> str:
        """
        Beta 포맷팅
        
        - None이면 "N/A"
        - 소수점 2자리 (예: 1.25)
        """
        if beta is None:
            return "N/A"
        return f"{beta:.2f}"

    @staticmethod
    def format_percentage(value: Optional[float], decimals: int = 2) -> str:
        """
        퍼센트 포맷팅
        
        - None이면 "N/A"
        - 소수점 지정 가능 (기본 2자리)
        - "+" 기호는 포함하지 않음 (부호는 별도 필드로 처리)
        """
        if value is None:
            return "N/A"
        return f"{value:.{decimals}f}%"

    @staticmethod
    def format_change_percentage(value: Optional[float], decimals: int = 2) -> str:
        """
        등락률 포맷팅 (부호 포함)
        
        - None이면 "N/A"
        - 양수면 "+" 기호 포함 (예: +2.50%)
        - 음수면 "-" 기호 포함 (예: -1.25%)
        """
        if value is None:
            return "N/A"
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.{decimals}f}%"

    @staticmethod
    def format_change_value(value: Optional[float], is_korean: bool) -> str:
        """
        등락액 포맷팅
        
        - None이면 "N/A"
        - 한국: 정수 처리 + 3자리 쉼표 + '원' (예: +1,200원)
        - 미국: 달러 기호 + 소수점 2자리 + 3자리 쉼표 (예: +$1.25)
        """
        if value is None:
            return "N/A"
        
        sign = "+" if value >= 0 else ""
        
        if is_korean:
            return f"{sign}{int(value):,}원"
        
        return f"{sign}${value:,.2f}"

    @staticmethod
    def format_target_upside(upside: Optional[float]) -> str:
        """
        목표가 괴리율 포맷팅
        
        - None이면 "N/A"
        - 양수면 "+" 기호 포함 (예: +15.5%)
        - 음수면 "-" 기호 포함 (예: -5.2%)
        """
        if upside is None:
            return "N/A"
        sign = "+" if upside >= 0 else ""
        return f"{sign}{upside:.1f}%"

    @staticmethod
    def format_date(date_str: Optional[str], format_type: Literal["short", "long"] = "short") -> str:
        """
        날짜 포맷팅
        
        - None이면 "N/A"
        - short: "2024-01-15"
        - long: "2024년 1월 15일"
        """
        if not date_str:
            return "N/A"
        
        try:
            # ISO 형식 또는 일반 날짜 형식 파싱 시도
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            
            if format_type == "long":
                return dt.strftime("%Y년 %m월 %d일")
            else:
                return dt.strftime("%Y-%m-%d")
        except Exception:
            return date_str  # 파싱 실패 시 원본 반환

    @staticmethod
    def get_change_status(current_price: float, previous_close: float) -> Literal["RISING", "FALLING", "NEUTRAL"]:
        """
        가격 변동 상태 판단
        
        - RISING: 상승 (current_price > previous_close)
        - FALLING: 하락 (current_price < previous_close)
        - NEUTRAL: 동일 (current_price == previous_close)
        """
        if current_price > previous_close:
            return "RISING"
        elif current_price < previous_close:
            return "FALLING"
        else:
            return "NEUTRAL"

