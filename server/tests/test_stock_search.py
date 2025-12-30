"""
주식 검색 서비스 테스트

NaverStockSearchService 및 KisMasterService의 하이브리드 검색 기능 테스트
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.stock.naver_search_service import NaverStockSearchService
from app.services.stock.kis_master_service import KisMasterService


class TestNaverStockSearchService:
    """네이버 주식 검색 서비스 테스트"""

    def test_init(self):
        """초기화 테스트"""
        service = NaverStockSearchService(timeout=10)
        assert service.timeout == 10

    @patch('app.services.stock.naver_search_service.requests.get')
    def test_search_ticker_success_with_reuters_code(self, mock_get):
        """티커 검색 성공 (reutersCode 있는 경우)"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "stockCode": "005930",
                "stockName": "삼성전자",
                "reutersCode": "005930.KS",
                "itemCode": "KOSPI"
            }
        ]
        mock_get.return_value = mock_response

        service = NaverStockSearchService()
        ticker = service.search_ticker("삼성전자")

        assert ticker == "005930.KS"
        mock_get.assert_called_once()

    @patch('app.services.stock.naver_search_service.requests.get')
    def test_search_ticker_success_without_reuters_code_kospi(self, mock_get):
        """티커 검색 성공 (reutersCode 없는 경우 - KOSPI)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "stockCode": "005930",
                "stockName": "삼성전자",
                "itemCode": "KOSPI"
            }
        ]
        mock_get.return_value = mock_response

        service = NaverStockSearchService()
        ticker = service.search_ticker("삼성전자")

        assert ticker == "005930.KS"

    @patch('app.services.stock.naver_search_service.requests.get')
    def test_search_ticker_success_kosdaq(self, mock_get):
        """티커 검색 성공 (KOSDAQ)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "stockCode": "035720",
                "stockName": "카카오",
                "reutersCode": "035720.KQ",
                "itemCode": "KOSDAQ"
            }
        ]
        mock_get.return_value = mock_response

        service = NaverStockSearchService()
        ticker = service.search_ticker("카카오")

        assert ticker == "035720.KQ"

    @patch('app.services.stock.naver_search_service.requests.get')
    def test_search_ticker_empty_result(self, mock_get):
        """검색 결과 없음"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        service = NaverStockSearchService()
        ticker = service.search_ticker("존재하지않는종목")

        assert ticker is None

    @patch('app.services.stock.naver_search_service.requests.get')
    def test_search_ticker_api_error(self, mock_get):
        """API 오류"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        service = NaverStockSearchService()
        ticker = service.search_ticker("삼성전자")

        assert ticker is None

    @patch('app.services.stock.naver_search_service.requests.get')
    def test_search_ticker_timeout(self, mock_get):
        """타임아웃"""
        mock_get.side_effect = Exception("Timeout")

        service = NaverStockSearchService()
        ticker = service.search_ticker("삼성전자")

        assert ticker is None

    def test_search_ticker_empty_query(self):
        """빈 검색어"""
        service = NaverStockSearchService()
        assert service.search_ticker("") is None
        assert service.search_ticker("  ") is None
        assert service.search_ticker(None) is None

    @patch('app.services.stock.naver_search_service.requests.get')
    def test_search_multiple(self, mock_get):
        """다중 검색"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "stockCode": "005930",
                "stockName": "삼성전자",
                "reutersCode": "005930.KS"
            },
            {
                "stockCode": "000660",
                "stockName": "SK하이닉스",
                "reutersCode": "000660.KS"
            }
        ]
        mock_get.return_value = mock_response

        service = NaverStockSearchService()
        results = service.search_multiple("삼성", max_results=2)

        assert len(results) == 2
        assert results[0]["ticker"] == "005930.KS"
        assert results[0]["name"] == "삼성전자"
        assert results[1]["ticker"] == "000660.KS"


class TestKisMasterServiceHybrid:
    """KIS 마스터 서비스 하이브리드 검색 테스트"""

    def test_init_with_naver_fallback(self):
        """네이버 폴백 활성화 초기화"""
        service = KisMasterService(enable_naver_fallback=True)
        assert service._enable_naver_fallback is True
        assert service._naver_search is not None

    def test_init_without_naver_fallback(self):
        """네이버 폴백 비활성화 초기화"""
        service = KisMasterService(enable_naver_fallback=False)
        assert service._enable_naver_fallback is False
        assert service._naver_search is None

    @patch.object(NaverStockSearchService, 'search_ticker')
    def test_get_ticker_by_name_naver_fallback(self, mock_naver_search):
        """네이버 폴백 동작 테스트 (마스터 파일 미로드)"""
        mock_naver_search.return_value = "035720.KQ"

        service = KisMasterService(enable_naver_fallback=True)
        # 마스터 데이터를 로드하지 않음 (_loaded = False)

        ticker = service.get_ticker_by_name("카카오")

        # 네이버 API가 호출되어야 함
        mock_naver_search.assert_called_once_with("카카오")
        assert ticker == "035720.KQ"

        # 캐시에 추가되었는지 확인
        assert service._name_to_code.get("카카오") == "035720.KQ"

    def test_get_ticker_by_name_master_priority(self):
        """마스터 파일 우선 검색 (캐시 히트)"""
        service = KisMasterService(enable_naver_fallback=True)

        # 마스터 캐시에 직접 추가 (마스터 파일 로드 시뮬레이션)
        service._loaded = True
        service._name_to_code["삼성전자"] = "005930.KS"

        ticker = service.get_ticker_by_name("삼성전자")

        # 마스터에서 바로 찾아야 하므로 네이버 API 호출 없음
        assert ticker == "005930.KS"

    @patch.object(NaverStockSearchService, 'search_ticker')
    def test_get_ticker_by_name_master_miss_then_naver(self, mock_naver_search):
        """마스터 파일 미스 → 네이버 폴백"""
        mock_naver_search.return_value = "035720.KQ"

        service = KisMasterService(enable_naver_fallback=True)
        service._loaded = True  # 마스터 로드됨
        service._name_to_code["삼성전자"] = "005930.KS"  # 다른 종목만 있음

        # 카카오는 마스터에 없으므로 네이버로 폴백
        ticker = service.get_ticker_by_name("카카오")

        mock_naver_search.assert_called_once_with("카카오")
        assert ticker == "035720.KQ"

    @patch.object(NaverStockSearchService, 'search_ticker')
    def test_get_ticker_by_name_naver_failure(self, mock_naver_search):
        """네이버 폴백 실패"""
        mock_naver_search.return_value = None

        service = KisMasterService(enable_naver_fallback=True)
        # 마스터 미로드

        ticker = service.get_ticker_by_name("존재하지않는종목")

        assert ticker is None

    def test_get_ticker_by_name_no_fallback(self):
        """네이버 폴백 비활성화 시"""
        service = KisMasterService(enable_naver_fallback=False)
        # 마스터 미로드

        ticker = service.get_ticker_by_name("삼성전자")

        # 마스터도 없고 네이버도 비활성화이므로 None
        assert ticker is None


class TestKisMasterServiceCaching:
    """KIS 마스터 서비스 캐싱 테스트"""

    @patch.object(NaverStockSearchService, 'search_ticker')
    def test_naver_result_cached(self, mock_naver_search):
        """네이버 검색 결과가 캐시되는지 확인"""
        mock_naver_search.return_value = "035720.KQ"

        service = KisMasterService(enable_naver_fallback=True)

        # 첫 번째 검색 (네이버 API 호출)
        ticker1 = service.get_ticker_by_name("카카오")
        assert ticker1 == "035720.KQ"
        assert mock_naver_search.call_count == 1

        # 두 번째 검색 (캐시 히트, 네이버 API 호출 없음)
        service._loaded = True  # 캐시가 있으므로 loaded로 간주
        ticker2 = service.get_ticker_by_name("카카오")
        assert ticker2 == "035720.KQ"
        assert mock_naver_search.call_count == 1  # 여전히 1회만


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
