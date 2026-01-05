from sqlalchemy import String, DateTime, Boolean, BigInteger, Index, Text
from sqlalchemy import Enum as SQLEnum, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum
from typing import Optional, List
from datetime import datetime


class AssetType(str, Enum):
    """
    자산 유형 Enum

    Attributes:
        STOCK_KR: 한국 주식
        STOCK_US: 미국 주식
        ETF: 상장지수펀드
    """
    STOCK_KR = "STOCK_KR"
    STOCK_US = "STOCK_US"
    ETF = "ETF"


class AssetSearchIndex(Base):
    """
    자산 검색 인덱스 모델

    효율적인 자산 검색을 위한 검색 토큰 및 메타데이터를 저장합니다.

    Attributes:
        id: 고유 식별자
        ticker: 종목 티커 코드
        asset_type: 자산 유형 (한국 주식/미국 주식/ETF)
        name_kr: 한글 이름
        name_en: 영문 이름
        initial_kr: 한글 초성
        search_tokens: 검색용 토큰 배열
        exchange: 거래소 코드
        is_active: 활성화 여부
        created_at: 생성 시간
        updated_at: 업데이트 시간
    """
    __tablename__ = "asset_search_index"

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Basic Information
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(
        SQLEnum(AssetType, name="asset_type_enum", create_constraint=True),
        nullable=False
    )

    # Names
    name_kr: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name_en: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # Search Fields
    initial_kr: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    search_tokens: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text),
        nullable=True
    )

    # Exchange Information
    exchange: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        # GIN index for search_tokens array
        Index(
            "idx_asset_search_tokens_gin",
            "search_tokens",
            postgresql_using="gin"
        ),
        # Composite index for filtering by type and status
        Index(
            "idx_asset_type_active",
            "asset_type",
            "is_active"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AssetSearchIndex("
            f"id={self.id}, "
            f"ticker={self.ticker}, "
            f"asset_type={self.asset_type.value}, "
            f"name_kr={self.name_kr}, "
            f"is_active={self.is_active}"
            f")>"
        )
