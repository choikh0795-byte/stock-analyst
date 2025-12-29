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

        # 1. 티커를 종목코드로 변환 (데이터 파싱 컴포넌트 사용)
        stock_code = self._data_parser.convert_ticker_to_stock_code(ticker)
        logger.debug(f"[KisStockProvider] 티커 변환: {ticker} -> {stock_code}")

        # 2. 주식 현재가 정보 조회 (API 클라이언트 사용)
        # FHKST01010100 API는 현재가, 재무정보(PER, PBR, EPS, DPS 등)를 모두 포함하므로 한 번만 호출
        kis_data = self._api_client.get_stock_price_info(stock_code)
        logger.debug(f"[KisStockProvider] 주식 현재가 및 재무정보 조회 완료")

        # 3. 현재가 추출 (방어 로직에서 필요)
        current_price = None
        if "stck_prpr" in kis_data:
            try:
                current_price = float(kis_data["stck_prpr"])
            except (ValueError, TypeError):
                pass

        # 4. n차 방어 로직 실행 (방어 엔진 사용)
        logger.info(f"[KisStockProvider] 방어 로직 시작: {stock_code}")

        # ROE 방어 로직 (4단계)
        roe = self._defense_engine.get_roe_with_defense(stock_code, kis_data, current_price)

        # 목표가 방어 로직 (2단계)
        target_mean_price = self._defense_engine.get_target_price_with_defense(stock_code, kis_data)

        # 방어 로직 Summary 출력
        summary = self._defense_engine.get_defense_summary()
        logger.info(f"[KisStockProvider] 방어 로직 완료: {summary}")

        # 5. 표준화된 딕셔너리로 변환 (데이터 파싱 컴포넌트 사용)
        result = self._data_parser.convert_kis_response_to_standard_format(
            kis_data=kis_data,
            stock_code=stock_code,
            ticker=ticker,
            roe=roe,
            target_mean_price=target_mean_price
        )

        logger.info(f"[KisStockProvider] 주식 정보 조회 완료: {ticker}")
        return result
