"""
자산 검색 인덱스 배치 생성 서비스
"""

from dataclasses import dataclass
from typing import Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.asset_search_index import AssetSearchIndex, AssetType
from app.utils.hangul import extract_initial_consonants
from app.utils.search_tokens import build_prefix_tokens

logger = logging.getLogger(__name__)


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

    대량 데이터 처리를 위해 bulk upsert를 사용합니다.
    """

    BATCH_SIZE = 1000  # Bulk insert 배치 크기

    def __init__(self, db: Session):
        """
        Args:
            db: SQLAlchemy 데이터베이스 세션
        """
        self.db = db

    def build(self, items: list[AssetSourceItem]) -> int:
        """
        자산 검색 인덱스를 생성하거나 업데이트합니다.

        대량 데이터 처리를 위해 1,000개 단위로 bulk upsert를 수행합니다.

        Args:
            items: 인덱스를 생성할 자산 목록

        Returns:
            int: 생성/업데이트된 레코드 수
        """
        if not items:
            logger.warning("[AssetSearchIndexBuilder] 인덱싱할 항목이 없습니다.")
            return 0

        logger.info(f"[AssetSearchIndexBuilder] 인덱싱 시작: {len(items)}개 항목")

        # 배치 데이터 준비
        batch_data = []
        for item in items:
            initial_kr = self._extract_initial(item.name_kr)
            search_tokens = self._build_search_tokens(
                item.name_kr,
                item.name_en,
                item.ticker
            )

            batch_data.append({
                "ticker": item.ticker,
                "asset_type": item.asset_type,
                "name_kr": item.name_kr,
                "name_en": item.name_en,
                "initial_kr": initial_kr,
                "search_tokens": search_tokens,
                "exchange": item.exchange,
                "is_active": True,
            })

        # Bulk upsert 수행 (BATCH_SIZE 단위)
        total_upserted = 0
        for i in range(0, len(batch_data), self.BATCH_SIZE):
            batch = batch_data[i:i + self.BATCH_SIZE]
            count = self._bulk_upsert(batch)
            total_upserted += count
            logger.info(
                f"[AssetSearchIndexBuilder] 배치 처리 완료: "
                f"{i + count}/{len(batch_data)} ({count}개)"
            )

        self.db.commit()
        logger.info(f"[AssetSearchIndexBuilder] 인덱싱 완료: {total_upserted}개 항목")
        return total_upserted

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

        우선순위:
        1. 한글 이름 접두사 (한국 주식)
        2. 영문 이름 접두사 (미국 주식)
        3. 티커 접두사 (모든 주식)

        Args:
            name_kr: 한글 이름
            name_en: 영문 이름
            ticker: 티커 코드

        Returns:
            중복 제거된 검색 토큰 리스트 (우선순위 순서) (토큰이 없으면 None)
        """
        # 우선순위 보장을 위해 리스트 사용 (set 대신)
        tokens_ordered = []

        # 1. 한글 이름 토큰 (한국 주식 우선순위)
        if name_kr and name_kr.strip():
            kr_tokens = build_prefix_tokens(name_kr)
            tokens_ordered.extend(kr_tokens)

        # 2. 영문 이름 토큰 (미국 주식 우선순위)
        # name_kr과 동일한 경우 중복 방지
        if name_en and name_en.strip() and name_en != name_kr:
            en_tokens = build_prefix_tokens(name_en)
            tokens_ordered.extend(en_tokens)

        # 3. 티커 토큰 (모든 주식)
        if ticker and ticker.strip():
            ticker_tokens = build_prefix_tokens(ticker)
            tokens_ordered.extend(ticker_tokens)

        # 중복 제거 (순서 유지)
        seen = set()
        unique_tokens = []
        for token in tokens_ordered:
            if token and token not in seen:
                seen.add(token)
                unique_tokens.append(token)

        return unique_tokens if unique_tokens else None

    def _bulk_upsert(self, batch_data: list[dict]) -> int:
        """
        배치 데이터를 bulk upsert합니다.

        PostgreSQL의 INSERT ... ON CONFLICT DO UPDATE를 사용하여
        ticker와 asset_type이 중복될 경우 업데이트합니다.

        Args:
            batch_data: 삽입/업데이트할 데이터 리스트

        Returns:
            int: 처리된 레코드 수
        """
        if not batch_data:
            return 0

        try:
            # PostgreSQL INSERT ... ON CONFLICT DO UPDATE
            stmt = insert(AssetSearchIndex).values(batch_data)

            # ticker와 asset_type이 중복될 경우 업데이트
            # NOTE: unique constraint가 필요함 (ticker, asset_type)
            stmt = stmt.on_conflict_do_update(
                index_elements=['ticker', 'asset_type'],
                set_={
                    'name_kr': stmt.excluded.name_kr,
                    'name_en': stmt.excluded.name_en,
                    'initial_kr': stmt.excluded.initial_kr,
                    'search_tokens': stmt.excluded.search_tokens,
                    'exchange': stmt.excluded.exchange,
                    'is_active': stmt.excluded.is_active,
                }
            )

            # 실행
            self.db.execute(stmt)
            return len(batch_data)

        except Exception as e:
            logger.error(f"[AssetSearchIndexBuilder] Bulk upsert 실패: {e}")
            # 롤백하고 재시도 (fallback to one-by-one)
            self.db.rollback()
            return self._fallback_upsert(batch_data)

    def _fallback_upsert(self, batch_data: list[dict]) -> int:
        """
        Bulk upsert 실패 시 fallback으로 하나씩 upsert합니다.

        Args:
            batch_data: 삽입/업데이트할 데이터 리스트

        Returns:
            int: 처리된 레코드 수
        """
        count = 0
        for data in batch_data:
            try:
                stmt = select(AssetSearchIndex).where(
                    AssetSearchIndex.ticker == data['ticker'],
                    AssetSearchIndex.asset_type == data['asset_type']
                )
                result = self.db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # 업데이트
                    existing.name_kr = data['name_kr']
                    existing.name_en = data['name_en']
                    existing.initial_kr = data['initial_kr']
                    existing.search_tokens = data['search_tokens']
                    existing.exchange = data['exchange']
                    existing.is_active = data['is_active']
                else:
                    # 삽입
                    new_index = AssetSearchIndex(**data)
                    self.db.add(new_index)

                count += 1

            except Exception as e:
                logger.error(f"[AssetSearchIndexBuilder] 개별 upsert 실패: {e}")
                continue

        return count
