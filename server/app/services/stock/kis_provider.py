"""
한국투자증권(KIS) Open API 주식 데이터 제공자

리팩토링 후:
- KisApiClient: API 통신 전담
- KisDataParser: 데이터 파싱 및 매핑 전담
- KisDefenseEngine: n차 방어 로직 전담
- KisStockProvider: Facade 패턴으로 위 컴포넌트들을 조합
"""

import logging
from typing import Dict

from .base_provider import BaseStockProvider
from .kis_api_client import KisApiClient
from .kis_data_parser import KisDataParser
from .kis_defense_engine import KisDefenseEngine

logger = logging.getLogger(__name__)


class KisStockProvider(BaseStockProvider):
    """
    한국투자증권(KIS) Open API를 사용하는 주식 데이터 제공자

    Facade Pattern을 적용하여 여러 컴포넌트를 조합:
    - KisApiClient: API 통신 (인증, Rate Limit, HTTP 요청)
    - KisDataParser: 데이터 파싱 (필드 매핑, 업종 코드 변환)
    - KisDefenseEngine: 방어 로직 (ROE, 배당수익률, 목표가 n차 방어)

    KIS API를 사용하여 한국 주식 정보를 가져오고,
    Yahoo Provider와 동일한 구조의 표준화된 딕셔너리를 반환합니다.
    """

    def __init__(self) -> None:
        """KisStockProvider 초기화"""
        super().__init__()

        # 컴포넌트 초기화 (Dependency Injection)
        self._api_client = KisApiClient()
        self._data_parser = KisDataParser()
        self._defense_engine = KisDefenseEngine(self._api_client)

        logger.info("[KisStockProvider] 초기화 완료 (모듈식 아키텍처)")

    def get_stock_info(self, ticker: str) -> Dict:
        """
        KIS API를 통해 주식 정보를 가져와 표준화된 딕셔너리로 반환합니다.

        성능 최적화 (v2):
        - 방어 로직 완전 제거 (ROE, 목표가는 Yahoo에서 가져옴)
        - KIS API 1회만 호출 (현재가 정보)
        - 불필요한 계산 제거

        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS")

        Returns:
            Dict: 표준화된 주식 정보 딕셔너리

        Raises:
            ValueError: KIS API가 지원하지 않는 티커인 경우
        """
        # KIS API는 한국 주식만 지원하므로 .KS 또는 .KQ로 끝나는 티커만 처리
        if not ticker.upper().endswith((".KS", ".KQ")):
            raise ValueError(f"KIS API는 한국 주식만 지원합니다. 티커: {ticker}")

        logger.info(f"[KisStockProvider] 주식 정보 조회 시작: {ticker}")

        # 1. 티커를 종목코드로 변환
        stock_code = self._data_parser.convert_ticker_to_stock_code(ticker)
        logger.debug(f"[KisStockProvider] 티커 변환: {ticker} -> {stock_code}")

        # 2. 주식 현재가 정보 조회 (1회만 호출)
        # FHKST01010100 API: 현재가, PER, PBR, EPS 등 기본 지표 포함
        kis_data = self._api_client.get_stock_price_info(stock_code)
        logger.info(f"[KisStockProvider] KIS API 조회 완료 (1회 호출)")

        # 3. 표준화된 딕셔너리로 변환
        # ROE, 목표가는 None으로 전달 (Yahoo에서 병합 시 채워짐)
        result = self._data_parser.convert_kis_response_to_standard_format(
            kis_data=kis_data,
            stock_code=stock_code,
            ticker=ticker,
            roe=None,  # Yahoo에서 가져올 것
            target_mean_price=None  # Yahoo에서 가져올 것
        )

        logger.info(f"[KisStockProvider] 주식 정보 조회 완료: {ticker}")
        return result
