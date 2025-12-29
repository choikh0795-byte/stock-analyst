"""
KIS와 Yahoo Finance 데이터를 병합하는 클래스

성능 최적화를 위해 KIS 데이터를 우선으로 하고,
부족한 부분만 Yahoo 데이터로 보완합니다.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DataMerger:
    """
    KIS API와 Yahoo Finance 데이터를 병합하는 클래스

    병합 전략:
    - KIS 데이터 우선 (현재가, PER, PBR, ROE, EPS 등)
    - Yahoo 데이터로 보완 (부채비율, 목표가)
    - KIS 데이터가 없으면 Yahoo 전체 데이터 사용 (Fallback)
    """

    def __init__(self, calculator):
        """
        Args:
            calculator: StockCalculator 인스턴스 (부채비율 계산용)
        """
        self.calculator = calculator

    def merge_with_financial(
        self,
        kis_data: Dict,
        yahoo_financial: Dict
    ) -> Dict:
        """
        KIS 데이터와 Yahoo 재무제표 데이터를 병합합니다.

        Args:
            kis_data: KIS Provider가 반환한 표준화된 딕셔너리
            yahoo_financial: Yahoo Provider의 get_financial_data_only() 결과

        Returns:
            Dict: 병합된 표준화된 딕셔너리
        """
        # KIS 데이터가 비어있으면 빈 딕셔너리 반환
        if not kis_data:
            logger.warning("[DataMerger] KIS 데이터 없음 → 병합 스킵")
            return kis_data

        # Yahoo 재무제표 데이터가 없으면 KIS 데이터만 반환
        if not yahoo_financial:
            logger.info("[DataMerger] Yahoo 재무제표 없음 → KIS 데이터만 사용")
            return kis_data

        logger.info("[DataMerger] KIS + Yahoo 재무제표 병합 시작")

        # 부채비율 보완
        debt_ratio = self._enrich_debt_ratio(kis_data, yahoo_financial)
        if debt_ratio is not None:
            kis_data["debt_ratio"] = debt_ratio
            logger.info(f"[DataMerger] 부채비율 보완 성공: {debt_ratio:.2f}%")

        # 목표가 보완 (KIS에서 이미 있으면 스킵)
        if kis_data.get("target_mean_price") is None:
            target_price = yahoo_financial.get("target_mean_price")
            if target_price:
                kis_data["target_mean_price"] = target_price
                logger.info(f"[DataMerger] 목표가 보완 성공: {target_price}")

        logger.info("[DataMerger] 병합 완료")
        return kis_data

    def _enrich_debt_ratio(
        self,
        kis_data: Dict,
        yahoo_financial: Dict
    ) -> Optional[float]:
        """
        Yahoo 재무제표 데이터에서 부채비율을 계산합니다.

        Args:
            kis_data: KIS 데이터
            yahoo_financial: Yahoo 재무제표 데이터

        Returns:
            Optional[float]: 부채비율 (%) 또는 None
        """
        # KIS에서 이미 부채비율이 있으면 스킵
        if kis_data.get("debt_ratio") is not None:
            logger.debug("[DataMerger] 부채비율 이미 존재 → 스킵")
            return kis_data.get("debt_ratio")

        # Yahoo 데이터에서 부채비율 계산
        raw_info = yahoo_financial.get("_raw_info", {})
        if not raw_info:
            logger.warning("[DataMerger] Yahoo info 없음 → 부채비율 계산 불가")
            return None

        # Calculator 사용하여 부채비율 계산
        debt_ratio = self.calculator.calculate_debt_ratio(raw_info)

        if debt_ratio is not None:
            logger.info(f"[DataMerger] Yahoo에서 부채비율 계산 성공: {debt_ratio:.2f}%")
        else:
            logger.warning("[DataMerger] Yahoo에서도 부채비율 계산 실패")

        return debt_ratio
