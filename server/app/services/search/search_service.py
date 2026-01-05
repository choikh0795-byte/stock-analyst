"""
자산 검색 서비스

자동완성 검색 기능을 제공하는 서비스 레이어입니다.
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from enum import IntEnum

from sqlalchemy import select, or_, func
from app.models.asset_search_index import AssetSearchIndex
from app.utils.hangul import INITIAL_CONSONANTS, HANGUL_SYLLABLE_START, HANGUL_SYLLABLE_END
import logging

logger = logging.getLogger(__name__)


class MatchType(IntEnum):
    """
    검색 매칭 타입 (우선순위 순서)

    값이 작을수록 우선순위가 높습니다.
    """
    EXACT = 0    # 완전일치
    PREFIX = 1   # 접두사 일치
    TOKEN = 2    # 토큰 일치


class AssetSearchService:
    """
    자산 검색 서비스 클래스

    자동완성 검색 기능을 제공하며, 한글 초성, 한글 음절, 영문/숫자 검색을 지원합니다.

    Attributes:
        db: SQLAlchemy 데이터베이스 세션
    """

    def __init__(self, db: Session):
        """
        AssetSearchService 생성자

        Args:
            db: SQLAlchemy 데이터베이스 세션
        """
        self.db = db

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        자산을 검색합니다.

        검색 로직:
        - 초성만 있으면: initial_kr LIKE '{query}%'
        - 한글 + 초성 혼합: name_kr ILIKE '{한글부분}%' OR initial_kr LIKE '{초성}%'
        - 영문/숫자: ticker/name_en prefix 우선, search_tokens 검색

        우선순위 정렬:
        - 완전일치 > prefix 일치 > token 일치
        - 같은 우선순위 내에서는 name_kr, ticker 순

        Args:
            query: 검색 쿼리 문자열
            limit: 반환할 최대 결과 개수 (기본값: 10)

        Returns:
            검색 결과 리스트 (dict 형태)
            각 dict는 ticker, name_kr, name_en, asset_type, exchange 포함
        """
        # Query 전처리
        query_trimmed = query.strip()
        query_lower = query_trimmed.lower()

        if not query_trimmed:
            return []

        logger.info(f"[AssetSearchService] Searching for: '{query_trimmed}'")

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

        # 우선순위 정렬 및 매칭 타입 추가
        results_with_priority = []
        for result in results:
            match_type = self._calculate_match_type(result, query_trimmed, query_lower, search_type)
            results_with_priority.append({
                "result": result,
                "match_type": match_type
            })

        # 우선순위 정렬: match_type (낮을수록 우선) > name_kr > ticker
        results_with_priority.sort(
            key=lambda x: (
                x["match_type"],
                x["result"].name_kr if x["result"].name_kr else "",
                x["result"].ticker
            )
        )

        # Dict 형태로 변환 (match_type 제거)
        return [
            {
                "ticker": item["result"].ticker,
                "name_kr": item["result"].name_kr,
                "name_en": item["result"].name_en,
                "asset_type": item["result"].asset_type.value,
                "exchange": item["result"].exchange,
            }
            for item in results_with_priority[:effective_limit]
        ]

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
    ) -> List[AssetSearchIndex]:
        """
        한글/초성 검색을 수행합니다.

        Args:
            query_trimmed: 정제된 검색 쿼리
            query_lower: 소문자 변환된 검색 쿼리
            search_type: 검색 타입 (initial_only, mixed)
            limit: 최대 결과 개수

        Returns:
            검색 결과 리스트
        """
        # 기본 쿼리 (is_active = True 필터)
        stmt = select(AssetSearchIndex).where(AssetSearchIndex.is_active == True)

        # 검색 타입별 조건 추가
        if search_type == "initial_only":
            # 초성만 있는 경우
            stmt = stmt.where(
                AssetSearchIndex.initial_kr.like(f"{query_trimmed}%")
            )
        elif search_type == "mixed":
            # 한글 + 초성 혼합
            hangul_part, initial_part = self._split_hangul_and_initial(query_trimmed)
            conditions = []

            if hangul_part:
                conditions.append(
                    func.lower(AssetSearchIndex.name_kr).like(f"{hangul_part.lower()}%")
                )

            if initial_part:
                conditions.append(
                    AssetSearchIndex.initial_kr.like(f"{initial_part}%")
                )

            if conditions:
                stmt = stmt.where(or_(*conditions))

        # 넉넉하게 가져온 후 정렬 (limit * 3)
        stmt = stmt.limit(limit * 3)

        # 쿼리 실행
        return self.db.execute(stmt).scalars().all()

    def _search_with_alphanumeric(
        self,
        query_trimmed: str,
        query_lower: str,
        limit: int
    ) -> List[AssetSearchIndex]:
        """
        영문/숫자 검색을 수행합니다.

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
        # 기본 쿼리 (is_active = True 필터)
        base_where = AssetSearchIndex.is_active == True

        # 1. ticker prefix 검색
        ticker_stmt = select(AssetSearchIndex).where(
            base_where,
            func.lower(AssetSearchIndex.ticker).like(f"{query_lower}%")
        ).limit(limit * 3)
        ticker_results = self.db.execute(ticker_stmt).scalars().all()

        # 2. name_en prefix 검색
        name_en_stmt = select(AssetSearchIndex).where(
            base_where,
            func.lower(AssetSearchIndex.name_en).like(f"{query_lower}%")
        ).limit(limit * 3)
        name_en_results = self.db.execute(name_en_stmt).scalars().all()

        # 3. search_tokens 검색
        tokens_stmt = select(AssetSearchIndex).where(
            base_where,
            cast(AssetSearchIndex.search_tokens, ARRAY(TEXT)).op("@>")(
                cast([query_lower], ARRAY(TEXT))
            )
        ).limit(limit * 3)
        tokens_results = self.db.execute(tokens_stmt).scalars().all()

        # 중복 제거하면서 결합 (ticker를 key로 사용)
        seen_tickers = set()
        combined_results = []

        for result in ticker_results + name_en_results + tokens_results:
            if result.ticker not in seen_tickers:
                seen_tickers.add(result.ticker)
                combined_results.append(result)

        return combined_results

    def _calculate_match_type(
        self,
        result: AssetSearchIndex,
        query_trimmed: str,
        query_lower: str,
        search_type: str
    ) -> MatchType:
        """
        검색 결과의 매칭 타입을 계산합니다.

        Args:
            result: 검색 결과 객체
            query_trimmed: 정제된 검색 쿼리
            query_lower: 소문자 변환된 검색 쿼리
            search_type: 검색 타입

        Returns:
            MatchType (EXACT, PREFIX, TOKEN)
        """
        # 완전일치 확인
        if search_type == "alphanumeric":
            # 영문/숫자: ticker, name_en 완전일치 확인
            if result.ticker.lower() == query_lower:
                return MatchType.EXACT
            if result.name_en and result.name_en.lower() == query_lower:
                return MatchType.EXACT

            # Prefix 확인
            if result.ticker.lower().startswith(query_lower):
                return MatchType.PREFIX
            if result.name_en and result.name_en.lower().startswith(query_lower):
                return MatchType.PREFIX

            # 나머지는 TOKEN
            return MatchType.TOKEN

        elif search_type == "initial_only":
            # 초성 검색: initial_kr 완전일치 확인
            if result.initial_kr and result.initial_kr == query_trimmed:
                return MatchType.EXACT

            # Prefix
            if result.initial_kr and result.initial_kr.startswith(query_trimmed):
                return MatchType.PREFIX

            return MatchType.TOKEN

        elif search_type == "mixed":
            # 한글 검색: name_kr 완전일치 확인
            if result.name_kr and result.name_kr.lower() == query_lower:
                return MatchType.EXACT

            # Prefix 확인
            hangul_part, initial_part = self._split_hangul_and_initial(query_trimmed)

            if hangul_part and result.name_kr:
                if result.name_kr.lower().startswith(hangul_part.lower()):
                    return MatchType.PREFIX

            if initial_part and result.initial_kr:
                if result.initial_kr.startswith(initial_part):
                    return MatchType.PREFIX

            return MatchType.TOKEN

        # 기본값
        return MatchType.TOKEN
