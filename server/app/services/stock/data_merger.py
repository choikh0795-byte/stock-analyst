"""
KIS와 Yahoo Finance 데이터를 병합하는 클래스

성능 최적화 (v2):
- KIS 데이터를 우선으로 하고, Yahoo 데이터로 보완
- 계산 로직 제거 (Yahoo가 이미 계산한 값 사용)
- 단순 병합만 수행 (유지보수성 향상)
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DataMerger:
    """
    KIS API와 Yahoo Finance 데이터를 병합하는 클래스

    병합 전략 (v2):
    - KIS 데이터 우선 (현재가, PER, PBR, EPS 등)
    - Yahoo 데이터로 보완 (ROE, 부채비율, 목표가)
    - 계산 없음, 단순 병합만 (성능 최적화)
    """

    def merge_with_financial(
        self,
        kis_data: Dict,
        yahoo_financial: Dict
    ) -> Dict:
        """
        KIS 데이터와 Yahoo 재무제표 데이터를 병합합니다.

        성능 최적화:
        - Yahoo에서 이미 계산된 값(ROE, 부채비율, 목표가)을 직접 사용
        - 계산 로직 없음 (Calculator 호출 제거)
        - 단순 병합만 수행

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

        logger.info("[DataMerger] KIS + Yahoo 병합 시작")

        # ✅ ROE 보완 (KIS에 없으면 Yahoo 값 사용)
        if kis_data.get("roe") is None and yahoo_financial.get("roe") is not None:
            kis_data["roe"] = yahoo_financial["roe"]
            logger.info(f"[DataMerger] ROE 보완: {yahoo_financial['roe']:.2f}%")

        # ✅ 부채비율 보완 (KIS에 없으면 Yahoo 값 사용)
        if kis_data.get("debt_ratio") is None and yahoo_financial.get("debt_ratio") is not None:
            kis_data["debt_ratio"] = yahoo_financial["debt_ratio"]
            logger.info(f"[DataMerger] 부채비율 보완: {yahoo_financial['debt_ratio']:.2f}%")

        # ✅ 목표가 보완 (KIS에 없으면 Yahoo 값 사용)
        if kis_data.get("target_mean_price") is None and yahoo_financial.get("target_mean_price") is not None:
            kis_data["target_mean_price"] = yahoo_financial["target_mean_price"]
            logger.info(f"[DataMerger] 목표가 보완: {yahoo_financial['target_mean_price']}")

        logger.info("[DataMerger] 병합 완료")
        return kis_data
