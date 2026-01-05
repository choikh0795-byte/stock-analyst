"""
자산 검색 서비스

자동완성 검색 기능을 제공하는 서비스 레이어입니다.
"""

from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

from sqlalchemy import select, or_, func
from app.models.asset_search_index import AssetSearchIndex
from app.utils.hangul import INITIAL_CONSONANTS, HANGUL_SYLLABLE_START, HANGUL_SYLLABLE_END
import logging

logger = logging.getLogger(__name__)


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
        - 영문/숫자: search_tokens @> ARRAY[query]

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
        else:
            # 영문/숫자 (search_tokens 사용)
            stmt = stmt.where(
            cast(AssetSearchIndex.search_tokens, ARRAY(TEXT)).op("@>")(
                cast([query_lower], ARRAY(TEXT))
            )
        )


        # 정렬: name_kr 우선, 그 다음 ticker
        stmt = stmt.order_by(
            AssetSearchIndex.name_kr.asc().nulls_last(),
            AssetSearchIndex.ticker.asc()
        )

        # Limit 적용
        stmt = stmt.limit(limit)

        # 쿼리 실행
        results = self.db.execute(stmt).scalars().all()

        # Dict 형태로 변환
        return [
            {
                "ticker": result.ticker,
                "name_kr": result.name_kr,
                "name_en": result.name_en,
                "asset_type": result.asset_type.value,
                "exchange": result.exchange,
            }
            for result in results
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
