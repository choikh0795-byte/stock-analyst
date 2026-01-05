"""
자산 검색 인덱스 배치 생성 서비스
"""

from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.asset_search_index import AssetSearchIndex, AssetType
from app.utils.hangul import extract_initial_consonants
from app.utils.search_tokens import build_prefix_tokens


@dataclass
class AssetSourceItem:
    """
    검색 인덱스 생성을 위한 자산 원본 데이터

    Attributes:
        ticker: 종목 티커 코드
        name_kr: 한글 이름
        name_en: 영문 이름
        asset_type: 자산 유형
        exchange: 거래소 코드
    """
    ticker: str
    name_kr: Optional[str]
    name_en: Optional[str]
    asset_type: AssetType
    exchange: str


class AssetSearchIndexBuilder:
    """
    자산 검색 인덱스 배치 생성 서비스

    주어진 자산 목록에 대해 검색 인덱스를 생성하거나 업데이트합니다.
    """

    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy 데이터베이스 세션
        """
        self.db = db

    def build(self, items: list[AssetSourceItem]) -> None:
        """
        자산 검색 인덱스를 생성하거나 업데이트합니다.

        Args:
            items: 인덱스를 생성할 자산 목록
        """
        for item in items:
            initial_kr = self._extract_initial(item.name_kr)
            search_tokens = self._build_search_tokens(
                item.name_kr,
                item.name_en,
                item.ticker
            )

            self._upsert_index(
                ticker=item.ticker,
                asset_type=item.asset_type,
                name_kr=item.name_kr,
                name_en=item.name_en,
                initial_kr=initial_kr,
                search_tokens=search_tokens,
                exchange=item.exchange
            )

        self.db.commit()

    def _extract_initial(self, name_kr: Optional[str]) -> Optional[str]:
        """
        한글 이름에서 초성을 추출합니다.

        Args:
            name_kr: 한글 이름

        Returns:
            초성 문자열 (한글이 없거나 None이면 None)
        """
        if not name_kr:
            return None

        initial = extract_initial_consonants(name_kr)
        return initial if initial else None

    def _build_search_tokens(
        self,
        name_kr: Optional[str],
        name_en: Optional[str],
        ticker: str
    ) -> Optional[list[str]]:
        """
        검색 토큰을 생성합니다.

        Args:
            name_kr: 한글 이름
            name_en: 영문 이름
            ticker: 티커 코드

        Returns:
            중복 제거된 검색 토큰 리스트 (토큰이 없으면 None)
        """
        tokens = set()

        tokens.update(build_prefix_tokens(name_kr))
        tokens.update(build_prefix_tokens(name_en))
        tokens.update(build_prefix_tokens(ticker))

        return list(tokens) if tokens else None

    def _upsert_index(
        self,
        ticker: str,
        asset_type: AssetType,
        name_kr: Optional[str],
        name_en: Optional[str],
        initial_kr: Optional[str],
        search_tokens: Optional[list[str]],
        exchange: str
    ) -> None:
        """
        검색 인덱스를 생성하거나 업데이트합니다.

        Args:
            ticker: 티커 코드
            asset_type: 자산 유형
            name_kr: 한글 이름
            name_en: 영문 이름
            initial_kr: 초성
            search_tokens: 검색 토큰
            exchange: 거래소 코드
        """
        stmt = select(AssetSearchIndex).where(
            AssetSearchIndex.ticker == ticker
        )
        result = self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.asset_type = asset_type
            existing.name_kr = name_kr
            existing.name_en = name_en
            existing.initial_kr = initial_kr
            existing.search_tokens = search_tokens
            existing.exchange = exchange
            existing.is_active = True
        else:
            new_index = AssetSearchIndex(
                ticker=ticker,
                asset_type=asset_type,
                name_kr=name_kr,
                name_en=name_en,
                initial_kr=initial_kr,
                search_tokens=search_tokens,
                exchange=exchange,
                is_active=True
            )
            self.db.add(new_index)
