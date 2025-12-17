import logging
import re
from typing import Dict, List, Optional

from .kis_master_service import KisMasterService
from .kis_provider import KisStockProvider
from .yahoo_provider import YahooStockProvider

logger = logging.getLogger(__name__)


class StockProvider:
    """
    주식 데이터 제공자 라우터 (Router/Context)
    
    전략 패턴의 Context 역할을 수행하며, ticker에 따라 적절한 Provider를 선택합니다.
    - 한국 주식 (.KS, .KQ): KisStockProvider 사용
    - 기타 주식: YahooStockProvider 사용
    - Fallback: KIS 실패 시 자동으로 Yahoo로 재시도
    """

    def __init__(self) -> None:
        # 전략 패턴: Concrete Strategy 인스턴스화
        self._yahoo_provider = YahooStockProvider()
        self._kis_provider = KisStockProvider()
        
        # KIS 마스터 서비스 초기화 및 데이터 로드
        try:
            self._kis_master = KisMasterService()
            # 비동기 로드 (앱 시작 시 백그라운드에서 로드)
            # 실패해도 앱이 죽지 않도록 try-except 처리
            load_success = self._kis_master.load_master_data()
            if load_success:
                logger.info("[StockProvider] KIS 마스터 데이터 로드 성공")
            else:
                logger.warning("[StockProvider] KIS 마스터 데이터 로드 실패, yfinance 검색만 사용")
        except Exception as e:
            logger.error(f"[StockProvider] KIS 마스터 서비스 초기화 실패: {e}, yfinance 검색만 사용")
            self._kis_master = None


    @staticmethod
    def _is_ticker_format(query: str) -> bool:
        ticker_pattern = re.compile(r"^[A-Z0-9]{1,10}(\.KS|\.KQ)?$")
        return bool(ticker_pattern.match(query.upper().strip()))

    def search_ticker(self, query: str) -> str:
        """
        종목명 또는 티커로 검색하여 티커를 반환합니다.
        
        검색 순서:
        1. 티커 형식인지 확인 (예: "005930.KS")
        2. KIS 마스터 서비스에서 종목명으로 검색 (한국 주식)
        3. yfinance 검색 (Fallback)
        
        Args:
            query: 검색어 (종목명 또는 티커)
            
        Returns:
            str: 티커 심볼
            
        Raises:
            ValueError: 검색 실패 시
        """
        query = query.strip()
        if not query:
            raise ValueError("검색어를 입력해주세요.")
        
        query_upper = query.upper()
        
        # 1. 티커 형식인지 확인
        if StockProvider._is_ticker_format(query_upper):
            return query_upper

        # 2. KIS 마스터 서비스에서 종목명으로 검색 (한국 주식)
        if self._kis_master:
            try:
                ticker = self._kis_master.get_ticker_by_name(query)
                if ticker:
                    logger.info(f"[StockProvider] KIS 마스터에서 검색 성공: {query} -> {ticker}")
                    return ticker
            except Exception as e:
                logger.warning(f"[StockProvider] KIS 마스터 검색 중 오류: {e}, yfinance로 Fallback")

        # 3. yfinance 검색 (Fallback)
        return self._search_with_yfinance(query)

    def _search_with_yfinance(self, query: str) -> str:
        """
        yfinance를 사용하여 종목 검색을 수행합니다.
        
        Args:
            query: 검색어 (종목명, 기업명 등)
            
        Returns:
            str: 티커 심볼
            
        Raises:
            ValueError: 검색 실패 시
        """
        try:
            from yfinance import Search

            logger.info(f"[StockProvider] yfinance 검색 시작: {query}")
            search = Search(query, max_results=5, enable_fuzzy_query=True)
            
            if not search.quotes or len(search.quotes) == 0:
                logger.warning(f"[StockProvider] yfinance 검색 결과 없음: {query}")
                raise ValueError(f"'{query}'에 대한 검색 결과를 찾을 수 없습니다.")
            
            # 첫 번째 결과 반환
            ticker = search.quotes[0]["symbol"]
            logger.info(f"[StockProvider] yfinance 검색 성공: {query} -> {ticker}")
            return ticker
            
        except ValueError:
            # ValueError는 그대로 전파
            raise
        except ImportError as e:
            logger.error(f"[StockProvider] yfinance import 실패: {e}")
            raise ValueError(f"검색 기능을 사용할 수 없습니다: {e}")
        except Exception as e:
            logger.error(f"[StockProvider] yfinance 검색 중 예상치 못한 오류: {e}")
            raise ValueError(f"검색 중 오류가 발생했습니다: {str(e)}")

    def get_stock_info(self, ticker: str) -> Dict:
        """
        주식 정보를 가져오는 라우터 메서드.
        
        Ticker에 따라 적절한 Provider를 선택하고, 실패 시 Fallback을 수행합니다.
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS", "AAPL")
            
        Returns:
            Dict: 표준화된 주식 정보 딕셔너리
        """
        ticker_upper = ticker.upper()
        is_korean = ticker_upper.endswith((".KS", ".KQ"))
        
        # 한국 주식인 경우 KIS Provider 사용
        if is_korean:
            logger.info(f"[StockProvider] 한국 주식 감지: {ticker} -> KIS Provider 사용")
            try:
                info = self._kis_provider.get_stock_info(ticker)
                logger.info(f"[StockProvider] KIS Provider 성공: {ticker}")
                return info
            except Exception as e:
                logger.warning(f"[StockProvider] KIS Provider 실패: {ticker}, 오류: {e}")
                logger.info(f"[StockProvider] Fallback: Yahoo Provider로 재시도: {ticker}")
                # Fallback: Yahoo Provider로 재시도
                try:
                    info = self._yahoo_provider.get_stock_info(ticker)
                    logger.info(f"[StockProvider] Yahoo Provider Fallback 성공: {ticker}")
                    return info
                except Exception as fallback_error:
                    logger.error(f"[StockProvider] Yahoo Provider Fallback도 실패: {ticker}, 오류: {fallback_error}")
                    raise
        else:
            # 미국 주식 등 기타 주식은 Yahoo Provider 사용
            logger.info(f"[StockProvider] 미국/기타 주식 감지: {ticker} -> Yahoo Provider 사용")
            try:
                info = self._yahoo_provider.get_stock_info(ticker)
                logger.info(f"[StockProvider] Yahoo Provider 성공: {ticker}")
                return info
            except Exception as e:
                logger.error(f"[StockProvider] Yahoo Provider 실패: {ticker}, 오류: {e}")
                raise

    def get_news(self, ticker: str) -> List[str]:
        """
        주식 관련 뉴스 제목 리스트를 반환합니다.
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS", "AAPL")
            
        Returns:
            List[str]: 뉴스 제목 리스트 (최대 3개)
        """
        ticker_upper = ticker.upper()
        is_korean = ticker_upper.endswith((".KS", ".KQ"))
        
        # 한국 주식인 경우 KIS Provider 사용 (뉴스가 없을 수 있음)
        if is_korean:
            try:
                news = self._kis_provider.get_news(ticker)
                # KIS Provider가 뉴스를 제공하지 않는 경우 Yahoo로 Fallback
                if not news:
                    logger.info(f"[StockProvider] KIS Provider 뉴스 없음, Yahoo Provider로 Fallback: {ticker}")
                    news = self._yahoo_provider.get_news(ticker)
                return news
            except Exception as e:
                logger.warning(f"[StockProvider] KIS Provider 뉴스 조회 실패, Yahoo Provider로 Fallback: {ticker}, 오류: {e}")
                return self._yahoo_provider.get_news(ticker)
        else:
            # 미국 주식 등 기타 주식은 Yahoo Provider 사용
            return self._yahoo_provider.get_news(ticker)
