import logging
from typing import Dict, List, Optional

import requests
import yfinance as yf

from .base_provider import BaseStockProvider

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

    def _get_ticker(self, ticker: str):
        """
        yfinance Ticker 객체를 생성합니다.
        Render 등 서버 환경에서의 차단을 막기 위해 User-Agent가 포함된 Session을 주입합니다.
        
        Args:
            ticker: 주식 티커 심볼
            
        Returns:
            yfinance.Ticker: Ticker 객체
        """
        try:
            session = requests.Session()
            # 브라우저인 척 위장하는 헤더 설정
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            return yf.Ticker(ticker, session=session)
        except Exception as e:
            logger.error(f"[YahooStockProvider] Ticker 생성 중 오류: {e}")
            # fallback: 세션 없이 시도
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
        # 1순위: trailingEps 또는 forwardEps 직접 접근
        eps = info.get("trailingEps") or info.get("forwardEps")
        if eps is not None:
            try:
                eps_float = float(eps)
                if eps_float > 0:
                    logger.info(f"[YahooStockProvider] EPS 1순위 성공: trailingEps/forwardEps = {eps_float}")
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
                if shares_float > 0 and net_income_float > 0:
                    eps = net_income_float / shares_float
                    logger.info(
                        f"[YahooStockProvider] EPS 2순위 성공: netIncomeToCommon({net_income_float}) / "
                        f"sharesOutstanding({shares_float}) = {eps}"
                    )
                    return eps
            except (ValueError, TypeError) as e:
                logger.debug(f"[YahooStockProvider] EPS 2순위 계산 실패: {e}")
        
        # 3순위: epsCurrentYear
        eps_current_year = info.get("epsCurrentYear")
        if eps_current_year is not None:
            try:
                eps_float = float(eps_current_year)
                if eps_float > 0:
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
        Yahoo Finance API를 통해 주식 정보를 가져와 표준화된 딕셔너리로 반환합니다.
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS", "AAPL")
            
        Returns:
            Dict: 표준화된 주식 정보 딕셔너리
        """
        stock = self._get_ticker(ticker)
        info = self._get_info(stock)
        
        current_price = self._calculate_current_price(info, stock)
        
        # 표준화된 딕셔너리 생성
        is_korean = ticker.upper().endswith((".KS", ".KQ"))
        currency = "KRW" if is_korean else "USD"
        
        # EPS 계산
        eps = self._calculate_eps(info, current_price)
        
        # ROE 변환 (% 단위로)
        roe = info.get("returnOnEquity")
        roe_percent = None
        if roe is not None:
            try:
                roe_percent = float(roe) * 100
            except (ValueError, TypeError):
                pass
        
        # 배당수익률 계산 (% 단위로)
        dividend_yield = None
        raw_dividend_yield = info.get("dividendYield")
        if raw_dividend_yield is not None:
            try:
                dividend_yield = float(raw_dividend_yield)
                if dividend_yield < 1.0:
                    dividend_yield = dividend_yield * 100
            except (ValueError, TypeError):
                pass
        
        # 배당률(dividendRate)과 현재가로 계산
        if dividend_yield is None:
            dividend_rate = info.get("dividendRate")
            if dividend_rate is not None and current_price and current_price > 0:
                try:
                    dividend_yield = (float(dividend_rate) / current_price) * 100
                except (ValueError, TypeError):
                    pass
        
        return {
            "name": info.get("shortName") or info.get("longName") or ticker,
            "symbol": ticker,
            "current_price": current_price,
            "previous_close": info.get("previousClose"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "eps": eps,
            "dividend_yield": dividend_yield,
            "roe": roe_percent,
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "target_mean_price": info.get("targetMeanPrice"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "summary": info.get("longBusinessSummary"),
            "currency": currency,
        }

    def get_news(self, ticker: str) -> List[str]:
        """
        Yahoo Finance API를 통해 주식 관련 뉴스 제목 리스트를 반환합니다.
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS", "AAPL")
            
        Returns:
            List[str]: 뉴스 제목 리스트 (최대 3개)
        """
        titles = []
        try:
            stock = self._get_ticker(ticker)
            news = stock.news
            if news:
                for n in news[:3]:
                    if isinstance(n, dict) and "title" in n:
                        titles.append(n["title"])
        except Exception as e:
            logger.warning(f"[YahooStockProvider] 뉴스 조회 실패: {e}")
        return titles
