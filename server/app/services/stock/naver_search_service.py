"""
네이버 증권 검색 서비스

한글 종목명으로 티커를 검색하는 서비스 (KIS 마스터 파일의 폴백용)
"""
import logging
from typing import Optional, List, Dict
import requests

logger = logging.getLogger(__name__)


class NaverStockSearchService:
    """
    네이버 증권 검색 API를 사용하여 종목명으로 티커를 검색하는 서비스

    KIS 마스터 파일 파싱 실패 시 또는 마스터 파일에 없는 종목 검색 시 사용
    """

    BASE_URL = "https://m.stock.naver.com/api/search/searchList"

    def __init__(self, timeout: int = 5):
        """
        NaverStockSearchService 초기화

        Args:
            timeout: API 요청 타임아웃 (초)
        """
        self.timeout = timeout

    def search_ticker(self, query: str) -> Optional[str]:
        """
        종목명으로 티커 검색

        Args:
            query: 검색어 (종목명 또는 일부)

        Returns:
            Optional[str]: 티커 (예: "005930.KS") 또는 None

        Examples:
            >>> service = NaverStockSearchService()
            >>> service.search_ticker("삼성전자")
            "005930.KS"
            >>> service.search_ticker("카카오")
            "035720.KQ"
        """
        if not query or not query.strip():
            return None

        try:
            logger.info(f"[NaverSearch] 종목 검색: {query}")

            response = requests.get(
                self.BASE_URL,
                params={"keyword": query.strip()},
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            if response.status_code != 200:
                logger.warning(f"[NaverSearch] API 응답 실패: {response.status_code}")
                return None

            data = response.json()

            if not data or len(data) == 0:
                logger.info(f"[NaverSearch] 검색 결과 없음: {query}")
                return None

            # 첫 번째 결과 사용
            item = data[0]
            stock_code = item.get("stockCode")
            stock_name = item.get("stockName")

            # reutersCode 예: "005930.KS", "035720.KQ"
            reuters_code = item.get("reutersCode")

            if reuters_code and "." in reuters_code:
                # reutersCode가 있으면 그대로 사용 (가장 정확)
                logger.info(f"[NaverSearch] 검색 성공: {query} → {reuters_code} ({stock_name})")
                return reuters_code

            # reutersCode가 없으면 stockCode와 marketCode로 조합
            if stock_code:
                # itemCode에서 시장 구분 추출 (예: "KOSPI", "KOSDAQ")
                item_code = item.get("itemCode", "")

                # marketCode 또는 itemCode에서 시장 판별
                if "KOSDAQ" in item_code or item.get("marketCode") == "KOSDAQ":
                    suffix = ".KQ"
                else:  # KOSPI 또는 기타
                    suffix = ".KS"

                ticker = f"{stock_code}{suffix}"
                logger.info(f"[NaverSearch] 검색 성공: {query} → {ticker} ({stock_name})")
                return ticker

            logger.warning(f"[NaverSearch] stockCode 없음: {item}")
            return None

        except requests.Timeout:
            logger.error(f"[NaverSearch] 타임아웃: {query}")
            return None
        except requests.RequestException as e:
            logger.error(f"[NaverSearch] 네트워크 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"[NaverSearch] 검색 실패: {e}", exc_info=True)
            return None

    def search_multiple(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        종목명으로 여러 결과 검색

        Args:
            query: 검색어
            max_results: 최대 결과 수

        Returns:
            List[Dict]: [{"ticker": "005930.KS", "name": "삼성전자"}, ...]
        """
        if not query or not query.strip():
            return []

        try:
            response = requests.get(
                self.BASE_URL,
                params={"keyword": query.strip()},
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            if response.status_code != 200:
                return []

            data = response.json()

            if not data:
                return []

            results = []
            for item in data[:max_results]:
                stock_code = item.get("stockCode")
                stock_name = item.get("stockName")
                reuters_code = item.get("reutersCode")

                if reuters_code and "." in reuters_code:
                    ticker = reuters_code
                elif stock_code:
                    item_code = item.get("itemCode", "")
                    suffix = ".KQ" if "KOSDAQ" in item_code else ".KS"
                    ticker = f"{stock_code}{suffix}"
                else:
                    continue

                results.append({
                    "ticker": ticker,
                    "name": stock_name or ""
                })

            return results

        except Exception as e:
            logger.error(f"[NaverSearch] 다중 검색 실패: {e}")
            return []
