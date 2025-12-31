"""
Asset Type 분류 시스템

주식과 ETF를 구분하고, 향후 펀드/채권 등 확장 가능한 구조
"""

from enum import Enum
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    """
    자산 타입 분류

    - STOCK: 주식 (국내/해외)
    - ETF: 상장지수펀드
    - UNKNOWN: 판별 불가

    향후 확장:
    - FUND: 펀드
    - BOND: 채권
    - CRYPTO: 암호화폐
    """
    STOCK = "STOCK"
    ETF = "ETF"
    UNKNOWN = "UNKNOWN"


class AssetTypeDetector:
    """
    자산 타입 판별 클래스

    Yahoo Finance info 데이터의 quoteType 필드를 기반으로
    자산 유형을 판별합니다.
    """

    @staticmethod
    def detect_from_info(info: Dict) -> AssetType:
        """
        Yahoo Finance info 딕셔너리로부터 자산 타입을 판별합니다.

        판별 로직:
        1. quoteType 필드 확인
           - 'ETF' → AssetType.ETF
           - 'EQUITY' → AssetType.STOCK
           - 'MUTUALFUND' → (향후) AssetType.FUND
        2. quoteType이 없으면 UNKNOWN

        Args:
            info: yfinance Ticker.info 딕셔너리

        Returns:
            AssetType: 판별된 자산 타입
        """
        if not info:
            logger.warning("[AssetTypeDetector] info 딕셔너리가 비어있음 → UNKNOWN")
            return AssetType.UNKNOWN

        quote_type = info.get("quoteType")

        if quote_type == "ETF":
            logger.info(f"[AssetTypeDetector] 자산 타입: ETF")
            return AssetType.ETF
        elif quote_type == "EQUITY":
            logger.info(f"[AssetTypeDetector] 자산 타입: STOCK")
            return AssetType.STOCK
        else:
            logger.warning(f"[AssetTypeDetector] 알 수 없는 quoteType: {quote_type} → UNKNOWN")
            return AssetType.UNKNOWN

    @staticmethod
    def is_etf(info: Dict) -> bool:
        """
        해당 자산이 ETF인지 여부를 반환합니다.

        Args:
            info: yfinance Ticker.info 딕셔너리

        Returns:
            bool: ETF이면 True, 아니면 False
        """
        return AssetTypeDetector.detect_from_info(info) == AssetType.ETF

    @staticmethod
    def is_stock(info: Dict) -> bool:
        """
        해당 자산이 주식인지 여부를 반환합니다.

        Args:
            info: yfinance Ticker.info 딕셔너리

        Returns:
            bool: 주식이면 True, 아니면 False
        """
        return AssetTypeDetector.detect_from_info(info) == AssetType.STOCK
