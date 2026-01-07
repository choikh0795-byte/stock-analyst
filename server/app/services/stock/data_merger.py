"""
KIS와 Yahoo Finance 데이터를 병합하는 클래스

성능 최적화 (v3):
- KIS 데이터를 우선으로 하고, Yahoo 데이터로 보완
- Yahoo raw 데이터를 Calculator로 계산하여 병합
- 음수 값 허용 (적자 기업 지원)
"""

import logging
from typing import Dict
from .calculator import StockCalculator

logger = logging.getLogger(__name__)


class DataMerger:
    """
    KIS API와 Yahoo Finance 데이터를 병합하는 클래스

    병합 전략 (v3):
    - KIS 데이터 우선 (현재가, PER, PBR, EPS 등)
    - Yahoo 데이터로 보완 (ROE, 부채비율, 목표가)
    - Calculator를 사용하여 Yahoo raw 데이터 계산
    """

    def __init__(self):
        """DataMerger 초기화"""
        self._calculator = StockCalculator()

    def merge_with_financial(
        self,
        kis_data: Dict,
        yahoo_financial: Dict
    ) -> Dict:
        """
        KIS 데이터와 Yahoo 재무제표 데이터를 병합합니다.

        개선 사항 (v3):
        - Yahoo raw 데이터를 Calculator로 계산하여 병합
        - 음수 값 허용 (적자 기업 지원)
        - ROE, 부채비율, 목표가 계산 추가

        Args:
            kis_data: KIS Provider가 반환한 표준화된 딕셔너리
            yahoo_financial: Yahoo Provider의 get_financial_data_only() 결과 (raw 데이터)

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

        # ✅ ROE 보완 (KIS에 없으면 Yahoo raw 데이터로 계산)
        if kis_data.get("roe") is None:
            return_on_equity = yahoo_financial.get("returnOnEquity")
            if return_on_equity is not None:
                try:
                    # returnOnEquity는 0.14094 형태 (14.094%)
                    roe = round(float(return_on_equity) * 100, 2)
                    kis_data["roe"] = roe
                    logger.info(f"[DataMerger] ROE 보완 성공: {roe:.2f}%")
                except (ValueError, TypeError) as e:
                    logger.warning(f"[DataMerger] ROE 계산 실패: {e}")

        # ✅ 부채비율 보완 (KIS에 없으면 Yahoo raw 데이터로 계산)
        if kis_data.get("debt_ratio") is None:
            debt_ratio = self._calculator.calculate_debt_ratio(yahoo_financial)
            if debt_ratio is not None:
                kis_data["debt_ratio"] = debt_ratio
                logger.info(f"[DataMerger] 부채비율 보완 성공: {debt_ratio:.2f}%")

        # ✅ 목표가 보완 (KIS에 없으면 Yahoo 값 사용)
        if kis_data.get("target_mean_price") is None:
            target_mean_price = yahoo_financial.get("targetMeanPrice")
            if target_mean_price is not None:
                try:
                    kis_data["target_mean_price"] = float(target_mean_price)
                    logger.info(f"[DataMerger] 목표가 보완 성공: {target_mean_price}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"[DataMerger] 목표가 변환 실패: {e}")

        logger.info("[DataMerger] 병합 완료")
        return kis_data
