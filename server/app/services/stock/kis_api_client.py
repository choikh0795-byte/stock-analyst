"""
KIS API 통신 전담 클래스

인증(Token), Rate Limit 제어, 실제 HTTP 요청만 전담하는 하위 클래스.
Single Responsibility Principle (SRP)을 적용하여 API 통신 로직만 관리합니다.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Optional

import requests

from app.core.config import settings
from .token_manager import AccessTokenManager

logger = logging.getLogger(__name__)


class KisApiClient:
    """
    KIS API 통신을 전담하는 클래스

    역할:
    - Access Token 관리 (발급, 갱신, 저장)
    - Rate Limit 제어 (API 호출 간 딜레이)
    - HTTP 요청 (GET, POST)
    - KIS API 응답 검증
    """

    def __init__(self) -> None:
        """KisApiClient 초기화"""
        # AccessTokenManager를 사용하여 토큰을 파일에 저장하고 관리
        self._token_manager = AccessTokenManager()

        # Strip whitespace from credentials to prevent authentication issues
        self._app_key = settings.KIS_APP_KEY.strip() if settings.KIS_APP_KEY else ""
        self._app_secret = settings.KIS_APP_SECRET.strip() if settings.KIS_APP_SECRET else ""
        self._base_url = settings.KIS_BASE_URL

        # Rate Limit 관리를 위한 마지막 API 호출 시간 추적
        self._last_api_call_time: Optional[datetime] = None
        # API 호출 간 최소 딜레이 (초) - Rate Limit 방지
        self._min_api_call_delay = 0.1  # 100ms

    def get_access_token(self) -> str:
        """
        Access Token을 발급받거나 갱신합니다.
        파일에 저장된 토큰이 유효한 경우 재사용하고, 만료된 경우에만 새로 발급받습니다.

        Returns:
            str: Access Token

        Raises:
            ValueError: 토큰 발급 실패 시
            requests.exceptions.HTTPError: HTTP 오류 발생 시
        """
        # 1. 파일 또는 메모리에서 유효한 토큰 확인
        existing_token = self._token_manager.get_token()
        if existing_token:
            logger.debug("[KisApiClient] 유효한 토큰 재사용 (파일/메모리에서)")
            return existing_token

        # 2. 토큰이 없거나 만료된 경우 새로 발급
        logger.info("[KisApiClient] 새 Access Token 발급 요청")

        try:
            # Access Token 발급 요청
            url = f"{self._base_url}/oauth2/tokenP"

            # Ensure credentials are stripped (already done in __init__, but double-check)
            app_key = self._app_key.strip()
            app_secret = self._app_secret.strip()

            headers = {
                "content-type": "application/json"
            }

            # JSON payload with exact key names as required by KIS API
            data = {
                "grant_type": "client_credentials",
                "appkey": app_key,
                "appsecret": app_secret
            }

            logger.debug(f"[KisApiClient] Token request - URL: {url}")
            logger.debug(f"[KisApiClient] Token request - Headers (keys only): {list(headers.keys())}")
            logger.debug(f"[KisApiClient] Token request - Payload keys: {list(data.keys())}")

            response = requests.post(url, headers=headers, json=data)

            # Check response status before raising
            if response.status_code != 200:
                # CRITICAL: Log the response body to see the exact error from KIS
                logger.error("=" * 80)
                logger.error("[KIS API ERROR] Access Token 발급 실패")
                logger.error("=" * 80)
                logger.error(f"Status Code: {response.status_code}")
                logger.error(f"Response Headers: {dict(response.headers)}")

                # Try to get response as JSON first, fallback to text
                try:
                    error_body = response.json()
                    logger.error(f"Response Body (JSON): {error_body}")
                except Exception:
                    error_body = response.text
                    logger.error(f"Response Body (Text): {error_body}")

                logger.error(f"Request URL: {url}")
                logger.error(f"Request Headers (keys only): {list(headers.keys())}")
                logger.error(f"Request Payload keys: {list(data.keys())}")
                logger.error("=" * 80)

                response.raise_for_status()

            result = response.json()
            access_token = result.get("access_token")

            if not access_token:
                raise ValueError("API 응답에 access_token이 없습니다")

            # 토큰 만료 시간 계산 (일반적으로 24시간)
            expires_in = result.get("expires_in", 86400)  # 기본값 24시간

            # AccessTokenManager에 토큰 저장 (파일 및 메모리)
            self._token_manager.save_token(access_token, expires_in)

            logger.info(f"[KisApiClient] Access Token 발급 및 저장 성공 (만료: {expires_in}초 후)")
            return access_token

        except requests.exceptions.HTTPError as e:
            # Additional logging for HTTP errors
            logger.error("=" * 80)
            logger.error("[KIS API ERROR] HTTP Exception during Access Token 발급")
            logger.error("=" * 80)
            if hasattr(e.response, 'text'):
                try:
                    error_body = e.response.json()
                    logger.error(f"Response Body (JSON): {error_body}")
                except Exception:
                    logger.error(f"Response Body (Text): {e.response.text}")
            logger.error(f"Exception: {e}")
            logger.error("=" * 80)
            raise
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"[KisApiClient] Access Token 발급 실패: {e}")
            logger.error("=" * 80)
            raise

    def rate_limit_delay(self) -> None:
        """
        Rate Limit을 고려하여 API 호출 간 딜레이를 추가합니다.
        """
        if self._last_api_call_time:
            elapsed = (datetime.now() - self._last_api_call_time).total_seconds()
            if elapsed < self._min_api_call_delay:
                sleep_time = self._min_api_call_delay - elapsed
                time.sleep(sleep_time)
        self._last_api_call_time = datetime.now()

    def _get_common_headers(self, tr_id: str) -> Dict[str, str]:
        """
        KIS API 요청에 필요한 공통 헤더를 생성합니다.

        Args:
            tr_id: 거래 ID (Transaction ID)

        Returns:
            Dict[str, str]: 헤더 딕셔너리
        """
        access_token = self.get_access_token()

        return {
            "authorization": f"Bearer {access_token}",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
            "tr_id": tr_id
        }

    def get_stock_price_info(self, stock_code: str) -> Dict:
        """
        KIS API를 통해 주식 현재가 정보를 가져옵니다.

        Args:
            stock_code: 종목코드 (6자리, 예: "005930")

        Returns:
            Dict: KIS API 응답 딕셔너리 (output 필드)

        Raises:
            Exception: API 호출 실패 시
        """
        # Rate Limit 적용
        self.rate_limit_delay()

        try:
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

            headers = self._get_common_headers("FHKST01010100")

            params = {
                "fid_cond_mrkt_div_code": "J",  # 주식시장 구분 (J: 주식, Q: 코스닥)
                "fid_input_iscd": stock_code
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            result = response.json()

            logger.debug(f"[KisApiClient] 주식 정보 응답: {result}")

            # 응답 구조: {"output": {...}, "rt_cd": "0", ...}
            if result.get("rt_cd") == "0":
                return result.get("output", {})
            else:
                error_msg = result.get("msg1", "알 수 없는 오류")
                logger.error(f"[KisApiClient] 주식 정보 조회 실패: {error_msg}")
                raise Exception(f"KIS API 오류: {error_msg}")

        except Exception as e:
            logger.error(f"[KisApiClient] 주식 정보 조회 중 오류: {e}")
            raise

    def get_stock_fundamental_info(self, stock_code: str) -> Dict:
        """
        KIS API를 통해 주식 재무정보를 가져옵니다.
        (PER, PBR, EPS 등)

        Args:
            stock_code: 종목코드 (6자리, 예: "005930")

        Returns:
            Dict: 재무정보 딕셔너리
        """
        # Rate Limit 적용
        self.rate_limit_delay()

        try:
            # 재무정보 조회 API (예시, 실제 API 경로는 KIS 문서 참조)
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

            headers = self._get_common_headers("FHKST01010100")  # 실제 재무정보 조회 tr_id로 변경 필요

            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": stock_code
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            result = response.json()

            if result.get("rt_cd") == "0":
                return result.get("output", {})
            else:
                logger.warning(f"[KisApiClient] 재무정보 조회 실패: {result.get('msg1', '알 수 없는 오류')}")
                return {}

        except Exception as e:
            logger.warning(f"[KisApiClient] 재무정보 조회 중 오류: {e}")
            return {}

    def get_financial_statement(self, stock_code: str) -> Dict:
        """
        KIS API를 통해 재무제표 정보를 가져옵니다.
        (당기순이익, 자본총계 등 ROE 계산에 필요한 데이터)

        주의: 실제 KIS API 문서를 확인하여 정확한 tr_id와 엔드포인트를 사용해야 합니다.
        현재 코드는 일반적인 구조를 기반으로 작성되었으며, 실제 API 응답 구조에 맞게 조정이 필요할 수 있습니다.

        Args:
            stock_code: 종목코드 (6자리, 예: "005930")

        Returns:
            Dict: 재무제표 정보 딕셔너리
        """
        # Rate Limit 고려
        self.rate_limit_delay()

        try:
            # 재무제표 조회 API
            # TODO: 실제 KIS API 문서를 확인하여 정확한 엔드포인트와 tr_id로 변경 필요
            url = f"{self._base_url}/uapi/domestic-stock/v1/finance/financial-statement"

            headers = self._get_common_headers("FHKST01010300")  # TODO: 실제 재무제표 조회 tr_id로 변경 필요

            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": stock_code,
                "fid_org_cls_code": "0",  # 0: 전체, 1: 연결, 2: 별도
                "fid_rgst_cls_code": "0",  # 0: 전체, 1: 정기, 2: 비정기
                "fid_period_cls_code": "0"  # 0: 전체, 1: 연간, 2: 분기
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            result = response.json()

            if result.get("rt_cd") == "0":
                output = result.get("output", {})
                # KIS API 응답이 배열 형태일 수 있으므로 처리
                if isinstance(output, list) and len(output) > 0:
                    # 최신 데이터(첫 번째 또는 마지막) 사용
                    logger.debug(f"[KisApiClient] 재무제표 응답 (배열): {len(output)}개 항목")
                    return output[0] if isinstance(output[0], dict) else {}
                elif isinstance(output, dict):
                    logger.debug(f"[KisApiClient] 재무제표 응답 (딕셔너리): 키 개수 = {len(output)}")
                    # 디버깅을 위해 주요 필드 로깅
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"[KisApiClient] 재무제표 응답 필드: {list(output.keys())[:10]}")
                    return output
                else:
                    logger.warning(f"[KisApiClient] 재무제표 응답 형식 예상 외: {type(output)}")
                    return {}
            else:
                error_msg = result.get("msg1", "알 수 없는 오류")
                logger.debug(f"[KisApiClient] 재무제표 조회 실패: {error_msg} (rt_cd: {result.get('rt_cd')})")
                return {}

        except Exception as e:
            logger.debug(f"[KisApiClient] 재무제표 조회 중 오류: {e}")
            return {}

    def get_dividend_info(self, stock_code: str) -> Dict:
        """
        KIS API를 통해 배당 정보를 가져옵니다.
        (주당배당금 DPS 등)

        주의: 실제 KIS API 문서를 확인하여 정확한 tr_id와 엔드포인트를 사용해야 합니다.
        주식기본조회 API에서 배당 정보를 함께 제공하는 경우 별도 API 호출이 필요 없을 수 있습니다.

        Args:
            stock_code: 종목코드 (6자리, 예: "005930")

        Returns:
            Dict: 배당 정보 딕셔너리
        """
        # Rate Limit 고려
        self.rate_limit_delay()

        try:
            # 배당 정보 조회 API
            # TODO: 실제 KIS API 문서를 확인하여 정확한 엔드포인트와 tr_id로 변경 필요
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

            headers = self._get_common_headers("FHKST01010100")  # TODO: 배당 정보 조회 전용 tr_id가 있다면 변경 필요

            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": stock_code
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            result = response.json()

            logger.debug(f"[KisApiClient] 배당 정보 응답: {result}")

            if result.get("rt_cd") == "0":
                return result.get("output", {})
            else:
                logger.debug(f"[KisApiClient] 배당 정보 조회 실패: {result.get('msg1', '알 수 없는 오류')}")
                return {}

        except Exception as e:
            logger.debug(f"[KisApiClient] 배당 정보 조회 중 오류: {e}")
            return {}

    def get_target_price_info(self, stock_code: str) -> Dict:
        """
        KIS API를 통해 목표가/컨센서스 정보를 가져옵니다.

        주의: 실제 KIS API 문서를 확인하여 정확한 tr_id와 엔드포인트를 사용해야 합니다.
        주식기본조회 API에서 목표가 정보를 함께 제공하는 경우 별도 API 호출이 필요 없을 수 있습니다.

        Args:
            stock_code: 종목코드 (6자리, 예: "005930")

        Returns:
            Dict: 목표가 정보 딕셔너리
        """
        # Rate Limit 고려
        self.rate_limit_delay()

        try:
            # 목표가/컨센서스 조회 API
            # TODO: 실제 KIS API 문서를 확인하여 정확한 엔드포인트와 tr_id로 변경 필요
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

            headers = self._get_common_headers("FHKST01010100")  # TODO: 목표가/컨센서스 조회 전용 tr_id가 있다면 변경 필요

            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": stock_code
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            result = response.json()

            if result.get("rt_cd") == "0":
                return result.get("output", {})
            else:
                logger.debug(f"[KisApiClient] 목표가 정보 조회 실패: {result.get('msg1', '알 수 없는 오류')}")
                return {}

        except Exception as e:
            logger.debug(f"[KisApiClient] 목표가 정보 조회 중 오류: {e}")
            return {}
