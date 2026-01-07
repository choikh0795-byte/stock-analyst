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

    def _calculate_eps(self, info: Dict, current_price: float) -> Optional[float]:
        """
        EPS(주당순이익)를 다단계 방어 로직으로 계산
        
        우선순위:
        1. trailingEps 또는 forwardEps (직접 접근)
        2. netIncomeToCommon / sharesOutstanding (기본 계산)
        3. epsCurrentYear (기존 필드)
        4. currentPrice / trailingPE (밸류에이션 역산)
        
        Args:
            info: yfinance API 응답 데이터 딕셔너리
            current_price: 현재 주가
            
        Returns:
            계산된 EPS 값 (float) 또는 None
        """

        # logger.warning(
        #     f"[YahooStockProvider][DEBUG] JOBX info dump keys: {list(info.keys())}"
        # )
        # logger.warning(
        #     f"[YahooStockProvider][DEBUG] JOBX EPS related fields: "
        #     f"trailingEps={info.get('trailingEps')}, "
        #     f"forwardEps={info.get('forwardEps')}, "
        #     f"netIncomeToCommon={info.get('netIncomeToCommon')}, "
        #     f"sharesOutstanding={info.get('sharesOutstanding')}, "
        #     f"epsCurrentYear={info.get('epsCurrentYear')}, "
        #     f"trailingPE={info.get('trailingPE')}"
        # )

        # 1순위: trailingEps 또는 forwardEps 직접 접근
        eps = info.get("trailingEps") or info.get("forwardEps")
        if eps is not None:
            try:
                eps_float = float(eps)
                if eps_float != 0:
                    logger.info(
                        f"[YahooStockProvider] EPS 1순위 성공: trailingEps/forwardEps = {eps_float}"
                    )
                    return eps_float
            except (ValueError, TypeError):
                pass
        
        # 2순위: netIncomeToCommon / sharesOutstanding
        net_income = info.get("netIncomeToCommon")
        shares_outstanding = info.get("sharesOutstanding")
        if net_income is not None and shares_outstanding is not None:
            try:
                net_income_float = float(net_income)
                shares_float = float(shares_outstanding)
                if shares_float > 0:
                    eps = net_income_float / shares_float
                    if eps != 0:
                        logger.info(
                            f"[YahooStockProvider] EPS 2순위 성공: netIncomeToCommon / sharesOutstanding = {eps}"
                        )
                        return eps

            except (ValueError, TypeError) as e:
                logger.debug(f"[YahooStockProvider] EPS 2순위 계산 실패: {e}")
        
        # 3순위: epsCurrentYear
        eps_current_year = info.get("epsCurrentYear")
        if eps_current_year is not None:
            try:
                eps_float = float(eps_current_year)
                if eps_float != 0:
                    logger.info(f"[YahooStockProvider] EPS 3순위 성공: epsCurrentYear = {eps_float}")
                    return eps_float
            except (ValueError, TypeError):
                pass
        
        # 4순위: currentPrice / trailingPE (밸류에이션 역산)
        trailing_pe = info.get("trailingPE")
        if current_price and current_price > 0 and trailing_pe is not None:
            try:
                trailing_pe_float = float(trailing_pe)
                if trailing_pe_float > 0:
                    eps = current_price / trailing_pe_float
                    logger.info(
                        f"[YahooStockProvider] EPS 4순위 성공: currentPrice({current_price}) / "
                        f"trailingPE({trailing_pe_float}) = {eps}"
                    )
                    return eps
            except (ValueError, TypeError) as e:
                logger.debug(f"[YahooStockProvider] EPS 4순위 계산 실패: {e}")
        
        # 모든 단계 실패
        logger.warning("[YahooStockProvider] EPS 계산 실패: 모든 단계 실패")
        return None

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
            # 주식 지표 (기존 로직)
            logger.info(f"[YahooStockProvider] 주식 감지: {ticker}, 주식 지표 추출 시작")

            # EPS 계산
            eps = self._calculate_eps(info, current_price)
            result["eps"] = eps

            # ROE 변환 (% 단위로)
            roe = info.get("returnOnEquity")
            roe_percent = None
            if roe is not None:
                try:
                    roe_percent = float(roe) * 100
                except (ValueError, TypeError):
                    pass
            result["roe"] = roe_percent

            # 부채비율 계산 (Debt Ratio = Total Debt / Total Assets * 100)
            debt_ratio = None
            total_debt = info.get("totalDebt")

            # totalDebt가 없으면 totalLiabilities 사용
            if not total_debt or total_debt <= 0:
                total_debt = info.get("totalLiabilities")

            if total_debt and total_debt > 0:
                # 1순위: totalAssets 직접 사용
                total_assets = info.get("totalAssets")
                if total_assets is not None and total_assets > 0:
                    try:
                        debt_ratio = (float(total_debt) / float(total_assets)) * 100
                        logger.info(f"[YahooStockProvider] 부채비율 1차 계산: {debt_ratio:.2f}% (부채={total_debt:,}, 자산={total_assets:,})")
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

                # 2순위: ROA 역산
                if debt_ratio is None:
                    return_on_assets = info.get("returnOnAssets")
                    net_income = info.get("netIncomeToCommon")

                    if return_on_assets is not None and return_on_assets > 0 and net_income is not None:
                        try:
                            total_assets_calc = float(net_income) / float(return_on_assets)
                            debt_ratio = (float(total_debt) / total_assets_calc) * 100
                            logger.info(
                                f"[YahooStockProvider] 부채비율 2차 계산 (ROA 역산): {debt_ratio:.2f}% "
                                f"(부채={total_debt:,}, 자산={total_assets_calc:,.0f})"
                            )
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass

                # 3순위: debtToEquity 공식 사용
                if debt_ratio is None:
                    debt_to_equity = info.get("debtToEquity")
                    if debt_to_equity is not None:
                        try:
                            debt_to_equity_float = float(debt_to_equity)
                            if debt_to_equity_float >= 0:
                                # debtToEquity가 100 이상이면 이미 % 단위
                                if debt_to_equity_float >= 100:
                                    debt_to_equity_ratio = debt_to_equity_float / 100
                                else:
                                    debt_to_equity_ratio = debt_to_equity_float

                                debt_ratio = (debt_to_equity_ratio / (1 + debt_to_equity_ratio)) * 100
                                logger.info(f"[YahooStockProvider] 부채비율 3차 계산 (debtToEquity 공식): {debt_ratio:.2f}%")
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass

            result["debt_ratio"] = debt_ratio

            # 주식 전용 지표
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

        return result

    def get_financial_data_only(self, ticker: str) -> Dict:
        """
        Yahoo Finance에서 재무제표 데이터만 경량으로 조회합니다.

        성능 최적화 (v2):
        - ROE, 부채비율, 목표가를 이미 계산된 값으로 직접 추출
        - 불필요한 계산 로직 제거 (Calculator 호출 불필요)
        - KIS와 병합 시 즉시 사용 가능

        Args:
            ticker: 주식 티커 심볼

        Returns:
            Dict: 재무제표 데이터 (ROE, 부채비율, 목표가)
        """
        try:
            stock = self._get_ticker(ticker)
            info = stock.info

            if info is None:
                logger.warning(f"[YahooStockProvider] info 조회 실패: {ticker}")
                return {}

            # ✅ ROE 직접 추출 (Yahoo가 이미 계산한 값)
            roe = info.get("returnOnEquity")
            roe_percent = None
            if roe is not None:
                try:
                    roe_percent = float(roe) * 100  # 0.14094 → 14.094%
                    logger.info(f"[YahooStockProvider] ROE 추출: {roe_percent:.2f}%")
                except (ValueError, TypeError):
                    pass

            # ✅ 부채비율 계산 (debtToEquity가 아닌 Debt/Assets 비율 계산)
            # ⚠️ 주의: debtToEquity는 부채/자본 비율이므로 부채/자산 비율과 다릅니다!
            debt_ratio = None
            total_debt = info.get("totalDebt")

            # totalDebt가 없으면 totalLiabilities 사용
            if not total_debt or total_debt <= 0:
                total_debt = info.get("totalLiabilities")

            if total_debt and total_debt > 0:
                # 1순위: totalAssets 직접 사용
                total_assets = info.get("totalAssets")
                if total_assets is not None and total_assets > 0:
                    try:
                        debt_ratio = (float(total_debt) / float(total_assets)) * 100
                        logger.info(f"[YahooStockProvider] 부채비율 1차 계산: {debt_ratio:.2f}% (부채={total_debt:,}, 자산={total_assets:,})")
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

                # 2순위: ROA 역산
                if debt_ratio is None:
                    return_on_assets = info.get("returnOnAssets")
                    net_income = info.get("netIncomeToCommon")

                    if return_on_assets is not None and return_on_assets > 0 and net_income is not None:
                        try:
                            total_assets_calc = float(net_income) / float(return_on_assets)
                            debt_ratio = (float(total_debt) / total_assets_calc) * 100
                            logger.info(
                                f"[YahooStockProvider] 부채비율 2차 계산 (ROA 역산): {debt_ratio:.2f}% "
                                f"(부채={total_debt:,}, 자산={total_assets_calc:,.0f})"
                            )
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass

                # 3순위: debtToEquity 공식 사용
                if debt_ratio is None:
                    debt_to_equity = info.get("debtToEquity")
                    if debt_to_equity is not None:
                        try:
                            debt_to_equity_float = float(debt_to_equity)
                            if debt_to_equity_float >= 0:
                                # debtToEquity가 100 이상이면 이미 % 단위
                                if debt_to_equity_float >= 100:
                                    debt_to_equity_ratio = debt_to_equity_float / 100
                                else:
                                    debt_to_equity_ratio = debt_to_equity_float

                                debt_ratio = (debt_to_equity_ratio / (1 + debt_to_equity_ratio)) * 100
                                logger.info(f"[YahooStockProvider] 부채비율 3차 계산 (debtToEquity 공식): {debt_ratio:.2f}%")
                        except (ValueError, TypeError, ZeroDivisionError):
                            pass

            # ✅ 목표가 직접 추출
            target_mean_price = info.get("targetMeanPrice")
            if target_mean_price is not None:
                logger.info(f"[YahooStockProvider] 목표가 추출: {target_mean_price}")

            return {
                "roe": roe_percent,  # % 단위 (예: 14.09)
                "debt_ratio": debt_ratio,  # % 단위 (예: 6.38)
                "target_mean_price": target_mean_price,  # 원화 또는 달러 (예: 146689.66)
            }

        except Exception as e:
            logger.error(f"[YahooStockProvider] 재무제표 조회 실패: {ticker}, 오류: {e}")
            return {}

