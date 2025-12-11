from typing import Tuple, List, Dict
import yfinance as yf
import logging
import time  # [추가] 재시도 딜레이용

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
        """
        try:
            logger.info(f"[StockService] 검색 시작: {ticker}")

            # [수정] 세션 직접 주입 금지! 
            # requirements.txt에 curl_cffi가 있으면 yfinance가 알아서 사용합니다.
            stock = yf.Ticker(ticker)
            
            info = None
            
            # [추가] 429 에러 방지를 위한 3회 재시도 로직
            # Render 서버 등에서는 첫 요청이 튀는 경우가 많아 재시도가 필수입니다.
            for attempt in range(3):
                try:
                    # 데이터 가져오기 시도
                    temp_info = stock.info
                    
                    # 데이터가 유효한지 체크
                    if temp_info and isinstance(temp_info, dict) and len(temp_info) > 0:
                        info = temp_info
                        break  # 성공하면 반복문 탈출
                except Exception as e:
                    logger.warning(f"[Attempt {attempt+1}/3] 데이터 가져오기 실패 ({ticker}): {e}")
                    time.sleep(1)  # 1초 쉬고 다시 시도
            
            # 3번 다 실패했거나 데이터가 비어있으면 에러 처리
            if not info:
                logger.error(f"[StockService] 429 차단 또는 데이터 없음: {ticker}")
                raise ValueError(f"'{ticker}' 정보를 가져올 수 없습니다. (서버 차단 또는 티커 오류)")

            # --- 이하 로직은 기존과 동일 ---

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
            
            # 데이터 추출
            pe_ratio = info.get("trailingPE")
            pb_ratio = info.get("priceToBook")
            return_on_equity = info.get("returnOnEquity")
            fifty_two_week_low = info.get("fiftyTwoWeekLow")
            fifty_two_week_high = info.get("fiftyTwoWeekHigh")
            target_mean_price = info.get("targetMeanPrice")
            number_of_analyst_opinions = info.get("numberOfAnalystOpinions")
            peg_ratio = info.get("pegRatio")
            beta = info.get("beta")
            dividend_yield = info.get("dividendYield")
            
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
                "fifty_two_week_low": fifty_two_week_low,
                "fifty_two_week_high": fifty_two_week_high,
                "target_mean_price": target_mean_price,
                "number_of_analyst_opinions": number_of_analyst_opinions,
                "peg_ratio": peg_ratio,
                "beta": beta,
                "dividend_yield": dividend_yield,
            }

            # 가격이 0원(데이터 오류)이면 history로 재시도
            if data['current_price'] == 0:
                try:
                    hist = stock.history(period="5d")
                    if not hist.empty and len(hist) > 0:
                        latest_price = hist['Close'].iloc[-1]
                        if latest_price and latest_price > 0:
                            data['current_price'] = float(latest_price)
                            if len(hist) > 1:
                                data['previous_close'] = float(hist['Close'].iloc[-2])
                            else:
                                data['previous_close'] = float(latest_price)
                            logger.info(f"[StockService] history에서 가격 데이터 복구: ${data['current_price']}")
                        else:
                            raise ValueError(f"'{ticker}'의 가격 데이터를 찾을 수 없습니다.")
                    else:
                        raise ValueError(f"'{ticker}'의 가격 데이터를 찾을 수 없습니다.")
                except Exception as hist_error:
                    logger.warning(f"[StockService] history 데이터 가져오기 실패: {hist_error}")
                    raise ValueError(f"'{ticker}'의 가격 데이터를 찾을 수 없습니다.")

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
        """주식 관련 뉴스 헤드라인을 가져옵니다."""
        news_titles = []
        try:
            # 뉴스도 차단될 수 있으므로 예외처리 강화
            raw_news = stock.news
            if raw_news:
                for n in raw_news[:limit]:
                    if isinstance(n, dict) and 'title' in n:
                        news_titles.append(n['title'])
        except Exception:
            # 뉴스는 없어도 서비스에 지장 없으므로 조용히 넘어감
            pass 
        
        return news_titles