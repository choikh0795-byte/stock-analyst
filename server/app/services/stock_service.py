from typing import Tuple, List, Dict
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class StockService:
    """
    주식 정보를 가져오는 비즈니스 로직을 처리하는 서비스 클래스
    """
    
    def __init__(self):
        """StockService 초기화"""
        pass
    
    def get_stock_info(self, ticker: str) -> Tuple[Dict, List[str]]:
        """
        yfinance를 사용하여 주식 정보를 가져옵니다.
        
        Args:
            ticker: 주식 티커 심볼
            
        Returns:
            Tuple[Dict, List[str]]: (주식 정보 딕셔너리, 뉴스 헤드라인 리스트)
            
        Raises:
            ValueError: 주식 정보를 가져올 수 없을 때
        """
        try:
            logger.info(f"[StockService] 검색 시작: {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # info가 None이거나 빈 딕셔너리인지 확인
            if not info or (isinstance(info, dict) and len(info) == 0):
                raise ValueError(f"'{ticker}' 정보를 가져올 수 없습니다. 티커 심볼을 확인해주세요.")

            # 가격을 찾는 순서 (더 많은 필드 시도)
            current_price = (
                info.get("currentPrice") 
                or info.get("regularMarketPrice")
                or info.get("regularMarketPreviousClose")
                or info.get("previousClose")
                or info.get("ask")
                or info.get("bid")
                or info.get("open")
                or 0
            )
            
            # 디버깅을 위한 로깅
            if current_price == 0:
                logger.warning(f"[StockService] 가격 필드 확인: currentPrice={info.get('currentPrice')}, "
                              f"regularMarketPrice={info.get('regularMarketPrice')}, "
                              f"previousClose={info.get('previousClose')}")
            
            # PER 같은 지표가 ETF엔 없을 수 있음 (None 체크 강화)
            pe_ratio = info.get("trailingPE")
            
            # PBR (Price-to-Book Ratio)
            pb_ratio = info.get("priceToBook")
            
            # ROE (Return on Equity)
            return_on_equity = info.get("returnOnEquity")
            
            # 5가지 핵심 지표 안전하게 가져오기
            # 1. 52주 최저/최고가
            fifty_two_week_low = info.get("fiftyTwoWeekLow")
            fifty_two_week_high = info.get("fiftyTwoWeekHigh")
            
            # 2. 목표가
            target_mean_price = info.get("targetMeanPrice")
            number_of_analyst_opinions = info.get("numberOfAnalystOpinions")
            
            # 3. PEG 지수
            peg_ratio = info.get("pegRatio")
            
            # 4. Beta
            beta = info.get("beta")
            
            # 5. 배당 수익률
            dividend_yield = info.get("dividendYield")
            
            # 데이터 매핑
            data = {
                "name": info.get("shortName", info.get("longName", ticker)),
                "symbol": info.get("symbol", ticker),
                "current_price": current_price,
                "previous_close": info.get("previousClose", current_price),
                "market_cap": (
                    str(info.get("marketCap", "N/A")) 
                    if info.get("marketCap") 
                    else "N/A"
                ),
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "return_on_equity": return_on_equity,
                "sector": info.get("sector", "ETF/Index"),
                "summary": (info.get("longBusinessSummary", "정보 없음")[:500]),
                # 6가지 핵심 지표 추가
                "fifty_two_week_low": fifty_two_week_low,
                "fifty_two_week_high": fifty_two_week_high,
                "target_mean_price": target_mean_price,
                "number_of_analyst_opinions": number_of_analyst_opinions,
                "peg_ratio": peg_ratio,
                "beta": beta,
                "dividend_yield": dividend_yield,
            }

            # 가격이 0원(데이터 오류)이면 에러
            if data['current_price'] == 0:
                # 추가로 history 데이터에서 가격을 시도
                try:
                    hist = stock.history(period="5d")  # 최근 5일 데이터 가져오기
                    if not hist.empty and len(hist) > 0:
                        latest_price = hist['Close'].iloc[-1]
                        if latest_price and latest_price > 0:
                            data['current_price'] = float(latest_price)
                            # 이전 종가 설정 (데이터가 2개 이상이면 이전 날짜, 아니면 같은 값)
                            if len(hist) > 1:
                                data['previous_close'] = float(hist['Close'].iloc[-2])
                            else:
                                data['previous_close'] = float(latest_price)
                            logger.info(f"[StockService] history에서 가격 데이터 복구: ${data['current_price']}")
                        else:
                            raise ValueError(f"'{ticker}'의 가격 데이터를 찾을 수 없습니다. 티커 심볼이 올바른지 확인해주세요.")
                    else:
                        raise ValueError(f"'{ticker}'의 가격 데이터를 찾을 수 없습니다. 티커 심볼이 올바른지 확인해주세요.")
                except Exception as hist_error:
                    logger.warning(f"[StockService] history 데이터 가져오기 실패: {hist_error}")
                    raise ValueError(f"'{ticker}'의 가격 데이터를 찾을 수 없습니다. 티커 심볼이 올바른지 확인해주세요.")

            logger.info(
                f"[StockService] 데이터 확보 성공: {data['name']} / ${data['current_price']}"
            )

            # 뉴스 가져오기
            news_titles = self._get_news_titles(stock)
            
            return data, news_titles

        except Exception as e:
            logger.error(f"[StockService] 치명적 에러: {e}")
            raise
    
    def _get_news_titles(self, stock: yf.Ticker, limit: int = 3) -> List[str]:
        """
        주식 관련 뉴스 헤드라인을 가져옵니다.
        
        Args:
            stock: yfinance Ticker 객체
            limit: 가져올 뉴스 개수 (기본값: 3)
            
        Returns:
            List[str]: 뉴스 헤드라인 리스트
        """
        news_titles = []
        try:
            raw_news = stock.news
            if raw_news:
                for n in raw_news[:limit]:
                    if isinstance(n, dict) and 'title' in n:
                        news_titles.append(n['title'])
        except Exception as e:
            logger.warning(f"[StockService] 뉴스 가져오기 실패: {e}")
        
        return news_titles

