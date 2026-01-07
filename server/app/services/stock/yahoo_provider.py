import logging
from typing import Dict, List, Optional

import yfinance as yf

from .base_provider import BaseStockProvider
from .asset_type import AssetType, AssetTypeDetector
from .etf_calculator import ETFCalculator

logger = logging.getLogger(__name__)


class YahooStockProvider(BaseStockProvider):
    """
    Yahoo Finance API를 사용하는 주식 데이터 제공자
    
    yfinance 라이브러리를 사용하여 주식 정보를 가져오고,
    fast_info와 info를 조합하여 완성된 표준화된 딕셔너리를 반환합니다.
    """

    def __init__(self) -> None:
        """YahooStockProvider 초기화"""
        super().__init__()
        self._etf_calculator = ETFCalculator()

    def _get_ticker(self, ticker: str):
        """
        yfinance Ticker 객체를 생성합니다.

        Args:
            ticker: 주식 티커 심볼

        Returns:
            yfinance.Ticker: Ticker 객체
        """
        return yf.Ticker(ticker)

    def _get_info(self, stock) -> Dict:
        """
        stock.info 데이터를 가져오되, 실패하거나 비어있을 경우 fast_info로 보완합니다.
        
        Args:
            stock: yfinance Ticker 객체
            
        Returns:
            Dict: 보완된 info 딕셔너리
        """
        info = {}
        
        # 1. 기본 info 가져오기 시도 (느리거나 차단될 수 있음)
        try:
            info = stock.info
        except Exception as e:
            logger.warning(f"[YahooStockProvider] info fetch warning (1차 시도): {e}")
        
        # info가 None이거나 비어있을 경우 딕셔너리 초기화
        if info is None:
            info = {}

        # 2. fast_info를 사용하여 핵심 데이터 강제 주입 (방어 로직)
        # fast_info는 Yahoo Finance API를 직접 찌르므로 차단 확률이 낮고 속도가 빠름
        try:
            fast_info = stock.fast_info
            
            # (1) 시가총액 (Market Cap)
            if 'marketCap' not in info or not info['marketCap']:
                val = fast_info.market_cap
                if val:
                    info['marketCap'] = val
                    logger.info(f"[YahooStockProvider] fast_info로 marketCap 복구: {val}")

            # (2) 현재가 (Current Price)
            # last_price가 가장 최신 가격임
            if 'currentPrice' not in info or not info['currentPrice']:
                val = fast_info.last_price
                if val:
                    info['currentPrice'] = val
                    info['regularMarketPrice'] = val  # 호환성을 위해 추가
                    logger.info(f"[YahooStockProvider] fast_info로 currentPrice 복구: {val}")

            # (3) 전일 종가 (Previous Close)
            if 'previousClose' not in info or not info['previousClose']:
                val = fast_info.previous_close
                if val:
                    info['previousClose'] = val

            # (4) 52주 최고/최저
            if 'fiftyTwoWeekHigh' not in info or not info['fiftyTwoWeekHigh']:
                val = fast_info.year_high
                if val:
                    info['fiftyTwoWeekHigh'] = val
            
            if 'fiftyTwoWeekLow' not in info or not info['fiftyTwoWeekLow']:
                val = fast_info.year_low
                if val:
                    info['fiftyTwoWeekLow'] = val

        except Exception as e:
            logger.warning(f"[YahooStockProvider] fast_info fetch failed (2차 방어 실패): {e}")

        return info

    def _calculate_current_price(self, info: Dict, stock) -> float:
        """
        현재가를 계산합니다.
        
        Args:
            info: yfinance info 딕셔너리
            stock: yfinance Ticker 객체
            
        Returns:
            float: 현재가
        """
        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or info.get("open")
            or 0
        )

        if current_price == 0:
            try:
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
            except Exception:
                pass

        return current_price

    def get_stock_info(self, ticker: str) -> Dict:
        """
        Yahoo Finance API를 통해 자산(주식/ETF) 정보를 가져와 표준화된 딕셔너리로 반환합니다.

        자산 타입별 처리:
        - STOCK: 기존 주식 지표 (PER, PBR, ROE, EPS, 부채비율, 목표가)
        - ETF: ETF 전용 지표 (운용보수, 순자산, 괴리율, 배당수익률, 설정일)

        Args:
            ticker: 자산 티커 심볼 (예: "005930.KS", "AAPL", "SPY")

        Returns:
            Dict: 표준화된 자산 정보 딕셔너리 (asset_type 필드 포함)
        """
        stock = self._get_ticker(ticker)
        info = self._get_info(stock)

        current_price = self._calculate_current_price(info, stock)

        # 자산 타입 판별
        asset_type = AssetTypeDetector.detect_from_info(info)

        # 표준화된 딕셔너리 생성
        is_korean = ticker.upper().endswith((".KS", ".KQ"))
        currency = "KRW" if is_korean else "USD"

        # 기본 정보 (공통)
        result = {
            "name": info.get("shortName") or info.get("longName") or ticker,
            "symbol": ticker,
            "asset_type": asset_type.value,  # "STOCK" or "ETF"
            "current_price": current_price,
            "previous_close": info.get("previousClose"),
            "market_cap": info.get("marketCap"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "summary": info.get("longBusinessSummary"),
            "currency": currency,
        }

        # 자산 타입별 지표 추가
        if asset_type == AssetType.ETF:
            # ETF 전용 지표
            logger.info(f"[YahooStockProvider] ETF 감지: {ticker}, ETF 지표 추출 시작")

            # 순자산 (AUM)
            total_assets = self._etf_calculator.extract_total_assets(info)
            result["total_assets"] = total_assets

            # 배당수익률
            dividend_yield = self._etf_calculator.extract_dividend_yield(info)
            result["dividend_yield"] = dividend_yield

            # 괴리율 계산 (NAV vs 시장가)
            nav_price = self._etf_calculator.extract_nav_price(info)
            premium_discount = self._etf_calculator.calculate_premium_discount(current_price, nav_price)
            result["nav_price"] = nav_price
            result["premium_discount"] = premium_discount

            # 설정일
            inception_date = self._etf_calculator.extract_inception_date(info)
            result["inception_date"] = inception_date

            # 평균 거래량 (유동성 지표)
            average_volume = self._etf_calculator.extract_average_volume(info)
            result["average_volume"] = average_volume

            # 52주 수익률 (수익률 지표)
            # ticker_obj를 전달하여 history 기반 정확한 계산 가능
            change_52week = self._etf_calculator.extract_52week_change(info, ticker_obj=stock)
            result["change_52week"] = change_52week

            # 구성종목 Top3 (현재 Yahoo에서 제공하지 않으므로 빈 리스트)
            top_holdings = self._etf_calculator.extract_top_holdings(info, limit=3)
            result["top_holdings"] = top_holdings

            # ETF는 PER, PBR, EPS, ROE, 부채비율, 목표가가 없으므로 None 처리
            result["pe_ratio"] = None
            result["pb_ratio"] = None
            result["eps"] = None
            result["roe"] = None
            result["debt_ratio"] = None
            result["target_mean_price"] = None

            logger.info(f"[YahooStockProvider] ETF 지표 추출 완료: {ticker}")

        else:
            # 주식 지표 (raw 데이터만 추출, 계산은 Calculator에서)
            logger.info(f"[YahooStockProvider] 주식 감지: {ticker}, 주식 지표 추출 시작")

            # Raw 데이터만 추출 (계산하지 않음)
            result["eps"] = None  # Calculator에서 계산
            result["roe"] = None  # Calculator에서 계산
            result["debt_ratio"] = None  # Calculator에서 계산

            # 주식 전용 지표 (raw 데이터)
            result["pe_ratio"] = info.get("trailingPE") or info.get("forwardPE")
            result["pb_ratio"] = info.get("priceToBook")
            result["target_mean_price"] = info.get("targetMeanPrice")

            # ETF 필드는 None 처리
            result["total_assets"] = None
            result["dividend_yield"] = None
            result["nav_price"] = None
            result["premium_discount"] = None
            result["inception_date"] = None
            result["average_volume"] = None
            result["change_52week"] = None
            result["top_holdings"] = []

        # 원본 info 딕셔너리 포함 (Service/Calculator에서 사용)
        # Service의 _convert_to_calculator_format과 Calculator에서 필요한 raw 데이터 제공
        result["_info"] = info

        return result

    def get_financial_data_only(self, ticker: str) -> Dict:
        """
        Yahoo Finance에서 재무제표 raw 데이터만 경량으로 조회합니다.

        성능 최적화 (v3 - 리팩토링):
        - Raw 데이터만 추출 (계산은 Calculator에서)
        - ROE, 부채비율은 Service/Calculator에서 처리
        - KIS와 병합 후 Calculator에서 계산

        Args:
            ticker: 주식 티커 심볼

        Returns:
            Dict: 재무제표 raw 데이터 (returnOnEquity, totalDebt, totalAssets, targetMeanPrice 등)
        """
        try:
            stock = self._get_ticker(ticker)
            info = stock.info

            if info is None:
                logger.warning(f"[YahooStockProvider] info 조회 실패: {ticker}")
                return {}

            # Raw 데이터만 추출 (계산 없음)
            return_on_equity = info.get("returnOnEquity")  # 0.14094 형태 (raw)
            total_debt = info.get("totalDebt") or info.get("totalLiabilities")
            total_assets = info.get("totalAssets")
            target_mean_price = info.get("targetMeanPrice")

            logger.info(
                f"[YahooStockProvider] 재무제표 raw 데이터 추출: "
                f"returnOnEquity={return_on_equity}, totalDebt={total_debt}, "
                f"totalAssets={total_assets}, targetMeanPrice={target_mean_price}"
            )

            return {
                "returnOnEquity": return_on_equity,  # raw 값 (0.14094)
                "totalDebt": total_debt,  # raw 값
                "totalAssets": total_assets,  # raw 값
                "netIncomeToCommon": info.get("netIncomeToCommon"),  # 부채비율 계산용
                "returnOnAssets": info.get("returnOnAssets"),  # 부채비율 계산용
                "debtToEquity": info.get("debtToEquity"),  # 부채비율 계산용
                "targetMeanPrice": target_mean_price,  # raw 값
            }

        except Exception as e:
            logger.error(f"[YahooStockProvider] 재무제표 조회 실패: {ticker}, 오류: {e}")
            return {}

