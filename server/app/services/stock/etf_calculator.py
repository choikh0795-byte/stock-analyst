"""
ETF 전용 지표 계산 클래스

주식과 다른 ETF 특화 지표를 추출/계산합니다.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ETFCalculator:
    """
    ETF 전용 지표 계산 및 추출

    주요 지표:
    - 운용보수 (Expense Ratio)
    - 순자산 (AUM - Assets Under Management)
    - 배당수익률 (Dividend Yield)
    - 괴리율 (Premium/Discount to NAV)
    - 설정일 (Inception Date)
    - 구성종목 Top3 (Holdings)
    """

    def extract_expense_ratio(self, ticker_obj, info: Dict) -> Optional[float]:
        """
        운용보수 (Expense Ratio) 추출

        Yahoo Finance 필드 우선순위:
        1. ticker.funds_data.fund_operations (신규 API, 2024년 9월 추가)
        2. annualReportExpenseRatio (레거시 필드, 많은 ETF에서 null 반환)

        Args:
            ticker_obj: yfinance Ticker 객체
            info: yfinance info 딕셔너리

        Returns:
            Optional[float]: 운용보수 (%, 예: 0.03 = 0.03%)
        """
        # 1순위: funds_data.fund_operations (신규 API)
        # yfinance 0.2.40+ 에서 추가된 새로운 API
        # GitHub Issue #2040에서 제안된 해결책
        try:
            if hasattr(ticker_obj, 'funds_data'):
                funds_data = ticker_obj.funds_data
                if funds_data is not None and hasattr(funds_data, 'fund_operations'):
                    fund_ops = funds_data.fund_operations
                    # fund_operations는 DataFrame 또는 dict 형태
                    if fund_ops is not None:
                        # DataFrame인 경우
                        if hasattr(fund_ops, 'to_dict'):
                            fund_ops_dict = fund_ops.to_dict('records')
                            if fund_ops_dict and len(fund_ops_dict) > 0:
                                expense_ratio = fund_ops_dict[0].get('Annual Report Expense Ratio')
                                if expense_ratio is not None:
                                    try:
                                        # funds_data는 이미 % 단위로 제공될 수 있음 (확인 필요)
                                        ratio = float(expense_ratio)
                                        # 0.0009 형식이면 * 100, 0.09 형식이면 그대로
                                        if ratio < 1.0:  # 0.0009 형식 (0.09%)
                                            ratio = ratio * 100
                                        logger.info(f"[ETFCalculator] 운용보수 추출 (funds_data): {ratio:.2f}%")
                                        return round(ratio, 2)
                                    except (ValueError, TypeError) as e:
                                        logger.debug(f"[ETFCalculator] funds_data 파싱 실패: {e}")
                        # dict인 경우
                        elif isinstance(fund_ops, dict):
                            expense_ratio = fund_ops.get('Annual Report Expense Ratio')
                            if expense_ratio is not None:
                                try:
                                    ratio = float(expense_ratio)
                                    if ratio < 1.0:
                                        ratio = ratio * 100
                                    logger.info(f"[ETFCalculator] 운용보수 추출 (funds_data): {ratio:.2f}%")
                                    return round(ratio, 2)
                                except (ValueError, TypeError) as e:
                                    logger.debug(f"[ETFCalculator] funds_data 파싱 실패: {e}")
        except Exception as e:
            logger.debug(f"[ETFCalculator] funds_data 접근 실패 (신규 API): {e}")

        # 2순위: annualReportExpenseRatio (레거시)
        expense_ratio = info.get("annualReportExpenseRatio")
        if expense_ratio is not None:
            try:
                ratio = float(expense_ratio) * 100  # 0.0003 → 0.03%
                logger.info(f"[ETFCalculator] 운용보수 추출 (레거시): {ratio:.2f}%")
                return round(ratio, 2)
            except (ValueError, TypeError):
                pass

        # 모든 방법 실패
        logger.warning("[ETFCalculator] 운용보수 추출 실패: 모든 필드 시도했으나 데이터 없음")
        return None

    def extract_total_assets(self, info: Dict) -> Optional[float]:
        """
        순자산 (AUM - Assets Under Management) 추출

        Yahoo Finance 필드:
        - totalAssets

        Args:
            info: yfinance info 딕셔너리

        Returns:
            Optional[float]: 순자산 (달러/원화, 예: 5000000000 = 50억)
        """
        total_assets = info.get("totalAssets")
        if total_assets is not None:
            try:
                assets = float(total_assets)
                logger.info(f"[ETFCalculator] 순자산 추출: {assets:,.0f}")
                return assets
            except (ValueError, TypeError):
                pass

        logger.warning("[ETFCalculator] 순자산 추출 실패: totalAssets 없음")
        return None

    def extract_dividend_yield(self, info: Dict) -> Optional[float]:
        """
        배당수익률 추출

        Yahoo Finance 필드:
        - yield (우선)
        - dividendYield (대안)
        - trailingAnnualDividendYield

        Args:
            info: yfinance info 딕셔너리

        Returns:
            Optional[float]: 배당수익률 (%, 예: 2.5 = 2.5%)
        """
        # 1순위: yield
        dividend_yield = info.get("yield") or info.get("dividendYield") or info.get("trailingAnnualDividendYield")

        if dividend_yield is not None:
            try:
                # Yahoo는 보통 0.025 형식으로 제공 → 2.5%로 변환
                yield_pct = float(dividend_yield) * 100
                logger.info(f"[ETFCalculator] 배당수익률 추출: {yield_pct:.2f}%")
                return round(yield_pct, 2)
            except (ValueError, TypeError):
                pass

        logger.warning("[ETFCalculator] 배당수익률 추출 실패")
        return None

    def calculate_premium_discount(
        self,
        current_price: float,
        nav_price: Optional[float]
    ) -> Optional[float]:
        """
        괴리율 계산 (Premium/Discount to NAV)

        공식:
        괴리율 = ((시장가 - NAV) / NAV) * 100

        Args:
            current_price: 현재 시장가
            nav_price: NAV (Net Asset Value)

        Returns:
            Optional[float]: 괴리율 (%, 양수=프리미엄, 음수=디스카운트)
        """
        if nav_price is None or nav_price <= 0:
            logger.warning("[ETFCalculator] NAV 값이 없어 괴리율 계산 불가")
            return None

        try:
            premium_discount = ((current_price - nav_price) / nav_price) * 100
            logger.info(f"[ETFCalculator] 괴리율 계산: {premium_discount:.2f}% (시장가={current_price}, NAV={nav_price})")
            return round(premium_discount, 2)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"[ETFCalculator] 괴리율 계산 실패: {e}")
            return None

    def extract_nav_price(self, info: Dict) -> Optional[float]:
        """
        NAV (Net Asset Value) 추출

        Yahoo Finance 필드:
        - navPrice (ETF 전용 필드, 있을 경우)

        Args:
            info: yfinance info 딕셔너리

        Returns:
            Optional[float]: NAV 가격
        """
        nav_price = info.get("navPrice")
        if nav_price is not None:
            try:
                nav = float(nav_price)
                logger.info(f"[ETFCalculator] NAV 추출: {nav}")
                return nav
            except (ValueError, TypeError):
                pass

        # NAV가 없으면 None 반환 (괴리율 계산 불가)
        return None

    def extract_inception_date(self, info: Dict) -> Optional[str]:
        """
        설정일 (Inception Date) 추출

        Yahoo Finance 필드:
        - fundInceptionDate

        Args:
            info: yfinance info 딕셔너리

        Returns:
            Optional[str]: 설정일 (문자열, 예: "2010-01-15")
        """
        inception_date = info.get("fundInceptionDate")
        if inception_date is not None:
            # Unix timestamp를 날짜 문자열로 변환
            try:
                from datetime import datetime
                if isinstance(inception_date, (int, float)):
                    date_obj = datetime.fromtimestamp(inception_date)
                    date_str = date_obj.strftime("%Y-%m-%d")
                    logger.info(f"[ETFCalculator] 설정일 추출: {date_str}")
                    return date_str
                elif isinstance(inception_date, str):
                    return inception_date
            except Exception as e:
                logger.warning(f"[ETFCalculator] 설정일 변환 실패: {e}")

        return None

    def extract_top_holdings(self, info: Dict, limit: int = 3) -> List[str]:
        """
        구성종목 Top N 추출

        Yahoo Finance 필드:
        - holdings (딕셔너리 형태일 경우)

        Note: Yahoo Finance API는 holdings 정보를 제공하지 않을 수 있음
        이 경우 빈 리스트 반환

        Args:
            info: yfinance info 딕셔너리
            limit: 상위 N개 추출

        Returns:
            List[str]: 구성종목 리스트 (최대 limit개)
        """
        # Yahoo Finance는 holdings 정보를 info에서 직접 제공하지 않음
        # 별도 API 호출 필요 (ticker.get_holdings() 등)
        # 일단 빈 리스트 반환 (향후 확장 가능)
        logger.warning("[ETFCalculator] 구성종목 정보는 Yahoo Finance info에서 제공하지 않음 (향후 확장 필요)")
        return []

    def calculate_tracking_error(
        self,
        etf_returns: List[float],
        benchmark_returns: List[float]
    ) -> Optional[float]:
        """
        추적오차 계산 (Tracking Error)

        공식:
        추적오차 = std(ETF 수익률 - 벤치마크 수익률)

        Note: 벤치마크 데이터가 필요하므로 현재 단계에서는 구현 보류
        향후 벤치마크 티커 정보가 있을 경우 구현

        Args:
            etf_returns: ETF 일일 수익률 리스트
            benchmark_returns: 벤치마크 일일 수익률 리스트

        Returns:
            Optional[float]: 추적오차 (%, 연율화)
        """
        # 추적오차 계산은 벤치마크 데이터가 필요하므로 보류
        logger.info("[ETFCalculator] 추적오차 계산은 향후 구현 예정 (벤치마크 데이터 필요)")
        return None
