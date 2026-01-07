"""
자산 검색 서비스

자동완성 검색 기능을 제공하는 서비스 레이어입니다.
메모리 인덱스 기반으로 동작하여 DB 쿼리 없이 빠른 검색을 제공합니다.
"""

from typing import List, Dict
import logging

from app.services.search.memory_index import AssetSearchMemoryIndex
from app.models.asset_search_index import AssetType
from app.utils.hangul import INITIAL_CONSONANTS, HANGUL_SYLLABLE_START, HANGUL_SYLLABLE_END

logger = logging.getLogger(__name__)


class AssetSearchService:
    """
    자산 검색 서비스 클래스 (메모리 기반)

    메모리 인덱스를 사용하여 자동완성 검색 기능을 제공하며,
    한글 초성, 한글 음절, 영문/숫자 검색을 지원합니다.

    Attributes:
        memory_index: 메모리에 로드된 자산 검색 인덱스
    """

    def __init__(self, memory_index: AssetSearchMemoryIndex):
        """
        AssetSearchService 생성자

        Args:
            memory_index: 메모리에 로드된 자산 검색 인덱스
        """
        self.memory_index = memory_index

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        자산을 검색합니다.

        검색 로직:
        - 초성만 있으면: initial_kr prefix 검색
        - 한글 + 초성 혼합: name_kr prefix 또는 initial_kr prefix 검색
        - 영문/숫자: ticker/name_en prefix 우선, search_tokens 검색

        Args:
            query: 검색 쿼리 문자열
            limit: 반환할 최대 결과 개수 (기본값: 10)

        Returns:
            검색 결과 리스트 (dict 형태)
            각 dict는 ticker, name_kr, name_en, asset_type, exchange 포함
        """
        try:
            # Query 전처리
            query_trimmed = query.strip()
            query_lower = query_trimmed.lower()

            if not query_trimmed:
                logger.debug("[AssetSearchService] Empty query, returning empty results")
                return []

            logger.info(f"[AssetSearchService] Searching for: '{query_trimmed}'")

            # 메모리 인덱스 초기화 확인
            if not self.memory_index.is_initialized():
                logger.warning("[AssetSearchService] Memory index not initialized")
                return []

            # 검색 타입 결정
            search_type = self._determine_search_type(query_trimmed)
            logger.debug(f"[AssetSearchService] Search type: {search_type}")

            # 초성 1자 입력 시 limit을 5로 조정
            effective_limit = limit
            if search_type == "initial_only" and len(query_trimmed) == 1:
                effective_limit = min(5, limit)
                logger.debug(f"[AssetSearchService] Single initial consonant detected, limiting to {effective_limit}")

            # 검색 타입별 검색 수행
            if search_type == "alphanumeric":
                # 영문/숫자: ticker/name_en prefix 우선 검색
                results = self._search_with_alphanumeric(query_trimmed, query_lower, effective_limit)
            else:
                # 한글/초성: 기존 로직 사용
                results = self._search_with_korean(query_trimmed, query_lower, search_type, effective_limit)

            # 결과가 없으면 빈 배열 반환
            if not results:
                logger.debug(f"[AssetSearchService] No results found for '{query_trimmed}'")
                return []

            logger.debug(f"[AssetSearchService] Found {len(results)} results")
            return results

        except Exception as e:
            # 모든 예외를 로그에 기록하고 빈 배열 반환
            logger.exception(f"[AssetSearchService] Search failed for query='{query}': {e}")
            return []

    def _determine_search_type(self, query: str) -> str:
        """
        검색 쿼리의 타입을 결정합니다.

        Args:
            query: 검색 쿼리 문자열

        Returns:
            "initial_only": 초성만 포함
            "mixed": 한글 음절 + 초성 혼합
            "alphanumeric": 영문/숫자
        """
        has_initial = False
        has_hangul_syllable = False
        has_alphanumeric = False

        for char in query:
            code_point = ord(char)

            # 한글 음절 (가-힣)
            if HANGUL_SYLLABLE_START <= code_point <= HANGUL_SYLLABLE_END:
                has_hangul_syllable = True
            # 초성
            elif char in INITIAL_CONSONANTS:
                has_initial = True
            # 영문/숫자/기타
            else:
                has_alphanumeric = True

        # 타입 결정
        if has_hangul_syllable or has_initial:
            if has_hangul_syllable and has_initial:
                return "mixed"
            elif has_initial:
                return "initial_only"
            else:
                # 한글 음절만 있어도 mixed로 처리 (name_kr 검색)
                return "mixed"
        else:
            return "alphanumeric"

    def _split_hangul_and_initial(self, query: str) -> tuple[str, str]:
        """
        쿼리를 한글 음절 부분과 초성 부분으로 분리합니다.

        Args:
            query: 검색 쿼리 문자열

        Returns:
            (한글 음절 부분, 초성 부분) 튜플
        """
        hangul_chars = []
        initial_chars = []

        for char in query:
            code_point = ord(char)

            # 한글 음절
            if HANGUL_SYLLABLE_START <= code_point <= HANGUL_SYLLABLE_END:
                hangul_chars.append(char)
            # 초성
            elif char in INITIAL_CONSONANTS:
                initial_chars.append(char)

        return "".join(hangul_chars), "".join(initial_chars)

    def _search_with_korean(
        self,
        query_trimmed: str,
        query_lower: str,
        search_type: str,
        limit: int
    ) -> List[Dict]:
        """
        한글/초성 검색을 수행합니다 (메모리 기반).

        Args:
            query_trimmed: 정제된 검색 쿼리
            query_lower: 소문자 변환된 검색 쿼리
            search_type: 검색 타입 (initial_only, mixed)
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        results = []
        seen_tickers = set()

        if search_type == "initial_only":
            # 초성만 있는 경우: initial_kr prefix 검색
            results = self._search_by_initial_kr(query_trimmed, limit)
            seen_tickers = {r["ticker"] for r in results}

        elif search_type == "mixed":
            # 한글 + 초성 혼합
            hangul_part, initial_part = self._split_hangul_and_initial(query_trimmed)

            # 1. 한글 음절로 name_kr prefix 검색
            if hangul_part:
                name_results = self._search_by_name_kr(hangul_part, limit)
                for r in name_results:
                    if r["ticker"] not in seen_tickers and len(results) < limit:
                        results.append(r)
                        seen_tickers.add(r["ticker"])

            # 2. 초성으로 initial_kr prefix 검색
            if initial_part and len(results) < limit:
                initial_results = self._search_by_initial_kr(initial_part, limit - len(results))
                for r in initial_results:
                    if r["ticker"] not in seen_tickers and len(results) < limit:
                        results.append(r)
                        seen_tickers.add(r["ticker"])

        return results

    def _search_with_alphanumeric(
        self,
        query_trimmed: str,
        query_lower: str,
        limit: int
    ) -> List[Dict]:
        """
        영문/숫자 검색을 수행합니다 (메모리 기반).

        우선순위:
        1. ticker prefix 일치
        2. name_en prefix 일치
        3. search_tokens 포함

        Args:
            query_trimmed: 정제된 검색 쿼리
            query_lower: 소문자 변환된 검색 쿼리
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        results = []
        seen_tickers = set()

        # 1. ticker prefix 검색
        ticker_results = self._search_by_ticker(query_lower, limit)
        for r in ticker_results:
            if len(results) >= limit:
                break
            results.append(r)
            seen_tickers.add(r["ticker"])

        # 2. name_en prefix 검색
        if len(results) < limit:
            name_en_results = self._search_by_name_en(query_lower, limit - len(results))
            for r in name_en_results:
                if r["ticker"] not in seen_tickers and len(results) < limit:
                    results.append(r)
                    seen_tickers.add(r["ticker"])

        # 3. search_tokens 검색
        if len(results) < limit:
            token_results = self._search_by_tokens(query_lower, limit - len(results))
            for r in token_results:
                if r["ticker"] not in seen_tickers and len(results) < limit:
                    results.append(r)
                    seen_tickers.add(r["ticker"])

        return results

    def _search_by_ticker(self, query: str, limit: int) -> List[Dict]:
        """
        Ticker prefix 검색 (메모리 기반)

        Args:
            query: 검색 쿼리 (소문자)
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        results = []
        all_assets = self.memory_index.get_all_assets()

        for asset in all_assets:
            if len(results) >= limit:
                break

            ticker_lower = asset["ticker"].lower()
            if ticker_lower.startswith(query):
                results.append(self._convert_to_response_format(asset))

        return results

    def _search_by_name_kr(self, query: str, limit: int) -> List[Dict]:
        """
        한글 이름 prefix 검색 (메모리 기반)

        Args:
            query: 검색 쿼리
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        results = []
        all_assets = self.memory_index.get_all_assets()
        query_lower = query.lower()

        for asset in all_assets:
            if len(results) >= limit:
                break

            name_kr = asset.get("name_kr")
            if name_kr and name_kr.lower().startswith(query_lower):
                results.append(self._convert_to_response_format(asset))

        return results

    def _search_by_initial_kr(self, query: str, limit: int) -> List[Dict]:
        """
        초성 prefix 검색 (메모리 기반)

        Args:
            query: 검색 쿼리 (초성)
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        results = []
        all_assets = self.memory_index.get_all_assets()

        for asset in all_assets:
            if len(results) >= limit:
                break

            initial_kr = asset.get("initial_kr")
            if initial_kr and initial_kr.startswith(query):
                results.append(self._convert_to_response_format(asset))

        return results

    def _search_by_name_en(self, query: str, limit: int) -> List[Dict]:
        """
        영문 이름 prefix 검색 (메모리 기반)

        Args:
            query: 검색 쿼리 (소문자)
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        results = []
        all_assets = self.memory_index.get_all_assets()

        for asset in all_assets:
            if len(results) >= limit:
                break

            name_en = asset.get("name_en")
            if name_en and name_en.lower().startswith(query):
                results.append(self._convert_to_response_format(asset))

        return results

    def _search_by_tokens(self, query: str, limit: int) -> List[Dict]:
        """
        search_tokens 검색 (메모리 기반)

        Args:
            query: 검색 쿼리 (소문자)
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        results = []
        all_assets = self.memory_index.get_all_assets()

        for asset in all_assets:
            if len(results) >= limit:
                break

            search_tokens = asset.get("search_tokens", [])
            if search_tokens and query in search_tokens:
                results.append(self._convert_to_response_format(asset))

        return results

    def _convert_to_response_format(self, asset: Dict) -> Dict:
        """
        메모리 asset을 API 응답 형식으로 변환합니다.

        Args:
            asset: 메모리에 저장된 asset dict

        Returns:
            API 응답 형식의 dict
        """
        # asset_type이 문자열이면 AssetType enum으로 변환
        asset_type = asset["asset_type"]
        if isinstance(asset_type, str):
            asset_type_enum = AssetType(asset_type)
        else:
            asset_type_enum = asset_type

        return {
            "id": asset["id"],
            "ticker": asset["ticker"],
            "name_kr": asset["name_kr"],
            "name_en": asset["name_en"],
            "asset_type": asset_type_enum.value if hasattr(asset_type_enum, 'value') else asset_type,
            "exchange": asset["exchange"],
            "country": self._get_country_from_asset_type(asset_type_enum),
            "currency": self._get_currency_from_asset_type(asset_type_enum),
        }

    def _get_country_from_asset_type(self, asset_type: AssetType) -> str:
        """
        자산 유형에서 국가 코드를 추론합니다.

        Args:
            asset_type: AssetType Enum

        Returns:
            국가 코드 (KR 또는 US)
        """
        if asset_type == AssetType.STOCK_KR or asset_type == AssetType.ETF:
            return "KR"
        elif asset_type == AssetType.STOCK_US:
            return "US"
        else:
            return "KR"

    def _get_currency_from_asset_type(self, asset_type: AssetType) -> str:
        """
        자산 유형에서 통화 코드를 추론합니다.

        Args:
            asset_type: AssetType Enum

        Returns:
            통화 코드 (KRW 또는 USD)
        """
        if asset_type == AssetType.STOCK_KR or asset_type == AssetType.ETF:
            return "KRW"
        elif asset_type == AssetType.STOCK_US:
            return "USD"
        else:
            return "KRW"
