import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests

from app.core.config import settings
from .base_provider import BaseStockProvider
from .token_manager import AccessTokenManager

logger = logging.getLogger(__name__)


class KisStockProvider(BaseStockProvider):
    """
    한국투자증권(KIS) Open API를 사용하는 주식 데이터 제공자
    
    KIS API를 사용하여 한국 주식 정보를 가져오고,
    Yahoo Provider와 동일한 구조의 표준화된 딕셔너리를 반환합니다.
    """

    def __init__(self) -> None:
        """KisStockProvider 초기화"""
        super().__init__()
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

    def _get_access_token(self) -> str:
        """
        Access Token을 발급받거나 갱신합니다.
        파일에 저장된 토큰이 유효한 경우 재사용하고, 만료된 경우에만 새로 발급받습니다.
        
        Returns:
            str: Access Token
        """
        # 1. 파일 또는 메모리에서 유효한 토큰 확인
        existing_token = self._token_manager.get_token()
        if existing_token:
            logger.debug("[KisStockProvider] 유효한 토큰 재사용 (파일/메모리에서)")
            return existing_token
        
        # 2. 토큰이 없거나 만료된 경우 새로 발급
        logger.info("[KisStockProvider] 새 Access Token 발급 요청")
        
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
            
            logger.debug(f"[KisStockProvider] Token request - URL: {url}")
            logger.debug(f"[KisStockProvider] Token request - Headers (keys only): {list(headers.keys())}")
            logger.debug(f"[KisStockProvider] Token request - Payload keys: {list(data.keys())}")
            
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
            
            logger.info(f"[KisStockProvider] Access Token 발급 및 저장 성공 (만료: {expires_in}초 후)")
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
            logger.error(f"[KisStockProvider] Access Token 발급 실패: {e}")
            logger.error("=" * 80)
            raise

    def _convert_ticker_to_stock_code(self, ticker: str) -> str:
        """
        Yahoo Finance 티커 형식을 KIS API 종목코드로 변환합니다.
        
        Args:
            ticker: Yahoo Finance 티커 (예: "005930.KS")
            
        Returns:
            str: KIS 종목코드 (예: "005930")
        """
        # ".KS" 또는 ".KQ" 제거
        if ticker.endswith(".KS") or ticker.endswith(".KQ"):
            return ticker[:-3]
        return ticker

    def _get_stock_price_info(self, stock_code: str) -> Dict:
        """
        KIS API를 통해 주식 현재가 정보를 가져옵니다.
        
        Args:
            stock_code: 종목코드 (6자리, 예: "005930")
            
        Returns:
            Dict: KIS API 응답 딕셔너리
        """
        access_token = self._get_access_token()
        
        try:
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = {
                "authorization": f"Bearer {access_token}",
                "appkey": self._app_key,
                "appsecret": self._app_secret,
                "tr_id": "FHKST01010100"
            }
            
            params = {
                "fid_cond_mrkt_div_code": "J",  # 주식시장 구분 (J: 주식, Q: 코스닥)
                "fid_input_iscd": stock_code
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()

            logger.debug(f"[KisStockProvider] 주식 정보 응답: {result}")
            
            # 응답 구조: {"output": {...}, "rt_cd": "0", ...}
            if result.get("rt_cd") == "0":
                return result.get("output", {})
            else:
                error_msg = result.get("msg1", "알 수 없는 오류")
                logger.error(f"[KisStockProvider] 주식 정보 조회 실패: {error_msg}")
                raise Exception(f"KIS API 오류: {error_msg}")
                
        except Exception as e:
            logger.error(f"[KisStockProvider] 주식 정보 조회 중 오류: {e}")
            raise

    def _get_stock_fundamental_info(self, stock_code: str) -> Dict:
        """
        KIS API를 통해 주식 재무정보를 가져옵니다.
        (PER, PBR, EPS 등)
        
        Args:
            stock_code: 종목코드 (6자리, 예: "005930")
            
        Returns:
            Dict: 재무정보 딕셔너리
        """
        access_token = self._get_access_token()
        
        try:
            # 재무정보 조회 API (예시, 실제 API 경로는 KIS 문서 참조)
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = {
                "authorization": f"Bearer {access_token}",
                "appkey": self._app_key,
                "appsecret": self._app_secret,
                "tr_id": "FHKST01010100"  # 실제 재무정보 조회 tr_id로 변경 필요
            }
            
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
                logger.warning(f"[KisStockProvider] 재무정보 조회 실패: {result.get('msg1', '알 수 없는 오류')}")
                return {}
                
        except Exception as e:
            logger.warning(f"[KisStockProvider] 재무정보 조회 중 오류: {e}")
            return {}

    def _rate_limit_delay(self) -> None:
        """
        Rate Limit을 고려하여 API 호출 간 딜레이를 추가합니다.
        """
        if self._last_api_call_time:
            elapsed = (datetime.now() - self._last_api_call_time).total_seconds()
            if elapsed < self._min_api_call_delay:
                sleep_time = self._min_api_call_delay - elapsed
                time.sleep(sleep_time)
        self._last_api_call_time = datetime.now()

    def _get_financial_statement(self, stock_code: str) -> Dict:
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
        self._rate_limit_delay()
        
        access_token = self._get_access_token()
        
        try:
            # 재무제표 조회 API
            # TODO: 실제 KIS API 문서를 확인하여 정확한 엔드포인트와 tr_id로 변경 필요
            # 일반적으로 사용되는 엔드포인트 예시:
            # - /uapi/domestic-stock/v1/finance/financial-statement
            # - /uapi/domestic-stock/v1/quotations/inquire-price (재무 정보 포함)
            url = f"{self._base_url}/uapi/domestic-stock/v1/finance/financial-statement"
            
            headers = {
                "authorization": f"Bearer {access_token}",
                "appkey": self._app_key,
                "appsecret": self._app_secret,
                "tr_id": "FHKST01010300"  # TODO: 실제 재무제표 조회 tr_id로 변경 필요 (KIS API 문서 참조)
            }
            
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
                    logger.debug(f"[KisStockProvider] 재무제표 응답 (배열): {len(output)}개 항목")
                    return output[0] if isinstance(output[0], dict) else {}
                elif isinstance(output, dict):
                    logger.debug(f"[KisStockProvider] 재무제표 응답 (딕셔너리): 키 개수 = {len(output)}")
                    # 디버깅을 위해 주요 필드 로깅
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"[KisStockProvider] 재무제표 응답 필드: {list(output.keys())[:10]}")
                    return output
                else:
                    logger.warning(f"[KisStockProvider] 재무제표 응답 형식 예상 외: {type(output)}")
                    return {}
            else:
                error_msg = result.get("msg1", "알 수 없는 오류")
                logger.debug(f"[KisStockProvider] 재무제표 조회 실패: {error_msg} (rt_cd: {result.get('rt_cd')})")
                return {}
                
        except Exception as e:
            logger.debug(f"[KisStockProvider] 재무제표 조회 중 오류: {e}")
            return {}

    def _get_dividend_info(self, stock_code: str) -> Dict:
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
        self._rate_limit_delay()
        
        access_token = self._get_access_token()
        
        try:
            # 배당 정보 조회 API
            # TODO: 실제 KIS API 문서를 확인하여 정확한 엔드포인트와 tr_id로 변경 필요
            # 주식기본조회 API에서 배당 정보를 함께 제공하는 경우 별도 호출 불필요
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = {
                "authorization": f"Bearer {access_token}",
                "appkey": self._app_key,
                "appsecret": self._app_secret,
                "tr_id": "FHKST01010100"  # TODO: 배당 정보 조회 전용 tr_id가 있다면 변경 필요
            }
            
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": stock_code
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()

            logger.debug(f"[KisStockProvider] 배당 정보 응답: {result}")
            
            if result.get("rt_cd") == "0":
                return result.get("output", {})
            else:
                logger.debug(f"[KisStockProvider] 배당 정보 조회 실패: {result.get('msg1', '알 수 없는 오류')}")
                return {}
                
        except Exception as e:
            logger.debug(f"[KisStockProvider] 배당 정보 조회 중 오류: {e}")
            return {}

    def _get_target_price_info(self, stock_code: str) -> Dict:
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
        self._rate_limit_delay()
        
        access_token = self._get_access_token()
        
        try:
            # 목표가/컨센서스 조회 API
            # TODO: 실제 KIS API 문서를 확인하여 정확한 엔드포인트와 tr_id로 변경 필요
            # 주식기본조회 API에서 목표가 정보를 함께 제공하는 경우 별도 호출 불필요
            url = f"{self._base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = {
                "authorization": f"Bearer {access_token}",
                "appkey": self._app_key,
                "appsecret": self._app_secret,
                "tr_id": "FHKST01010100"  # TODO: 목표가/컨센서스 조회 전용 tr_id가 있다면 변경 필요
            }
            
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
                logger.debug(f"[KisStockProvider] 목표가 정보 조회 실패: {result.get('msg1', '알 수 없는 오류')}")
                return {}
                
        except Exception as e:
            logger.debug(f"[KisStockProvider] 목표가 정보 조회 중 오류: {e}")
            return {}

    def _get_roe_with_defense(self, stock_code: str, kis_data: Dict, current_price: Optional[float]) -> Optional[float]:
        """
        ROE를 4단계 방어 로직으로 가져옵니다.
        
        1차 방어: 기본 조회 API에서 직접 확인
        2차 방어: PBR과 PER을 이용한 파생 계산 (PBR / PER) * 100
        3차 방어: EPS, PBR, 현재가를 이용한 파생 계산 EPS / (Current_Price / PBR) * 100
        4차 방어: 재무제표 API를 통해 계산 (당기순이익 / 자본총계) * 100
        
        Args:
            stock_code: 종목코드
            kis_data: 기본 조회 API 응답 데이터
            current_price: 현재가 (계산에 필요할 수 있음)
            
        Returns:
            Optional[float]: ROE 값 (% 단위) 또는 None
        """
        # 1차 방어: 기본 조회 API에서 직접 확인
        roe_fields = ["roe", "ROE", "rtn_on_equity", "rtn_on_eqty", "return_on_equity"]
        for field in roe_fields:
            if field in kis_data:
                try:
                    roe_value = float(kis_data[field])
                    if roe_value and roe_value != 0:
                        logger.info(f"[KisStockProvider] 1차 방어 성공: ROE = {roe_value}% (필드: {field})")
                        return roe_value
                except (ValueError, TypeError):
                    continue
        
        # 2차 방어: PBR과 PER을 이용한 파생 계산 (우선순위 1)
        # 공식: ROE = (PBR / PER) * 100
        pb_ratio = None
        pe_ratio = None
        
        if "pbr" in kis_data:
            try:
                pb_ratio = float(kis_data["pbr"])
            except (ValueError, TypeError):
                pass
        
        if "per" in kis_data:
            try:
                pe_ratio = float(kis_data["per"])
            except (ValueError, TypeError):
                pass
        
        if pb_ratio and pb_ratio > 0 and pe_ratio and pe_ratio > 0:
            roe = (pb_ratio / pe_ratio) * 100
            logger.info(f"[KisStockProvider] 2차 방어 성공: ROE 파생 계산 = {roe:.2f}% (PBR: {pb_ratio}, PER: {pe_ratio})")
            return round(roe, 2)
        
        # 3차 방어: EPS, PBR, 현재가를 이용한 파생 계산 (우선순위 2)
        # 공식: ROE = EPS / (Current_Price / PBR) * 100
        eps = None
        if "eps" in kis_data:
            try:
                eps = float(kis_data["eps"])
            except (ValueError, TypeError):
                pass
        
        if eps and eps > 0 and pb_ratio and pb_ratio > 0 and current_price and current_price > 0:
            # BPS = Current_Price / PBR
            bps = current_price / pb_ratio
            if bps > 0:
                roe = (eps / bps) * 100
                logger.info(f"[KisStockProvider] 3차 방어 성공: ROE 파생 계산 = {roe:.2f}% (EPS: {eps}, PBR: {pb_ratio}, 현재가: {current_price}, BPS: {bps})")
                return round(roe, 2)
        
        # 4차 방어: 재무제표 API를 통해 계산
        logger.info(f"[KisStockProvider] 4차 방어 시작: 재무제표 API 호출 (종목코드: {stock_code})")
        financial_data = self._get_financial_statement(stock_code)
        
        if financial_data:
            # 디버깅: 재무제표 데이터의 모든 키 로깅
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[KisStockProvider] 재무제표 데이터 키: {list(financial_data.keys())}")
            # 당기순이익과 자본총계 필드명은 KIS API 응답 구조에 따라 다를 수 있음
            # 일반적인 필드명들을 시도
            net_income_fields = ["net_income", "netIncome", "당기순이익", "thstrm_ntin", "thstrm_ntin_amt", "frm_trm_ntin", "frm_trm_ntin_amt"]
            equity_fields = ["total_equity", "totalEquity", "자본총계", "eqty_tot", "eqty_tot_amt", "eqty", "eqty_amt"]
            
            net_income = None
            total_equity = None
            
            # 필드명으로 직접 접근 시도
            for field in net_income_fields:
                if field in financial_data:
                    try:
                        value = financial_data[field]
                        # 배열인 경우 최근 4분기 합산 또는 최신 값 사용
                        if isinstance(value, list) and len(value) > 0:
                            # 숫자 배열인 경우 합산
                            try:
                                net_income = sum(float(x) for x in value if x is not None and x != 0)
                            except (ValueError, TypeError):
                                # 첫 번째 값 사용
                                net_income = float(value[0]) if value[0] else None
                        else:
                            net_income = float(value)
                        
                        if net_income and net_income != 0:
                            logger.debug(f"[KisStockProvider] 당기순이익 발견: {net_income} (필드: {field})")
                            break
                    except (ValueError, TypeError):
                        continue
            
            for field in equity_fields:
                if field in financial_data:
                    try:
                        value = financial_data[field]
                        # 배열인 경우 최신 값 사용
                        if isinstance(value, list) and len(value) > 0:
                            total_equity = float(value[0]) if value[0] else None
                        else:
                            total_equity = float(value)
                        
                        if total_equity and total_equity != 0:
                            logger.debug(f"[KisStockProvider] 자본총계 발견: {total_equity} (필드: {field})")
                            break
                    except (ValueError, TypeError):
                        continue
            
            if net_income and total_equity and total_equity > 0:
                roe = (net_income / total_equity) * 100
                logger.info(f"[KisStockProvider] 4차 방어 성공: ROE 계산 = {roe:.2f}% (당기순이익: {net_income}, 자본총계: {total_equity})")
                return round(roe, 2)
            else:
                logger.warning(f"[KisStockProvider] 4차 방어 실패: 재무 데이터 불완전 (당기순이익: {net_income}, 자본총계: {total_equity})")
        
        # 모든 방어 로직 실패
        logger.warning(f"[KisStockProvider] 모든 방어 로직 실패: ROE 데이터를 가져올 수 없음 (종목코드: {stock_code})")
        return None

    def _get_dividend_yield_with_defense(self, stock_code: str, kis_data: Dict, current_price: Optional[float]) -> Optional[float]:
        """
        배당수익률을 3단계 방어 로직으로 가져옵니다.
        
        1차 방어: 기본 조회 API에서 직접 확인
        2차 방어: 배당 정보 API를 통해 계산 (DPS / 현재가) * 100
        3차 방어: 예외 처리 및 로깅
        
        Args:
            stock_code: 종목코드
            kis_data: 기본 조회 API 응답 데이터
            current_price: 현재가
            
        Returns:
            Optional[float]: 배당수익률 (% 단위) 또는 None
        """
        # 1차 방어: 기본 조회 API에서 직접 확인
        dividend_yield_fields = ["dvyd", "dividend_yield", "dividendYield", "배당수익률", "배당률"]
        for field in dividend_yield_fields:
            if field in kis_data:
                try:
                    div_yield = float(kis_data[field])
                    if div_yield and div_yield != 0:
                        logger.info(f"[KisStockProvider] 1차 방어 성공: 배당수익률 = {div_yield}% (필드: {field})")
                        return div_yield
                except (ValueError, TypeError):
                    continue
        
        # 2차 방어: 배당 정보 API를 통해 계산
        if current_price and current_price > 0:
            logger.info(f"[KisStockProvider] 2차 방어 시작: 배당 정보 API 호출 (종목코드: {stock_code})")
            dividend_data = self._get_dividend_info(stock_code)
            
            if dividend_data:
                # 주당배당금(DPS) 필드명은 KIS API 응답 구조에 따라 다를 수 있음
                dps_fields = ["dps", "DPS", "dividend_per_share", "주당배당금", "stck_dvdn_amt", "stck_dvdn"]
                
                dps = None
                for field in dps_fields:
                    if field in dividend_data:
                        try:
                            dps = float(dividend_data[field])
                            if dps and dps > 0:
                                break
                        except (ValueError, TypeError):
                            continue
                
                if dps and dps > 0:
                    dividend_yield = (dps / current_price) * 100
                    logger.info(f"[KisStockProvider] 2차 방어 성공: 배당수익률 계산 = {dividend_yield:.2f}% (DPS: {dps}, 현재가: {current_price})")
                    return round(dividend_yield, 2)
                else:
                    logger.warning(f"[KisStockProvider] 2차 방어 실패: DPS 데이터 없음 (종목코드: {stock_code})")
            else:
                logger.warning(f"[KisStockProvider] 2차 방어 실패: 배당 정보 API 응답 없음 (종목코드: {stock_code})")
        else:
            logger.warning(f"[KisStockProvider] 2차 방어 실패: 현재가 정보 없음 (종목코드: {stock_code})")
        
        # 3차 방어: 예외 처리 및 로깅
        logger.warning(f"[KisStockProvider] 배당 데이터 확인 불가: 배당수익률을 가져올 수 없음 (종목코드: {stock_code}). 0.0으로 설정합니다.")
        return 0.0

    def _get_target_price_with_defense(self, stock_code: str, kis_data: Dict) -> Optional[float]:
        """
        목표가를 3단계 방어 로직으로 가져옵니다.
        
        1차 방어: 기본 조회 API에서 직접 확인
        2차 방어: 목표가/컨센서스 API를 통해 조회
        3차 방어: 예외 처리 및 로깅
        
        Args:
            stock_code: 종목코드
            kis_data: 기본 조회 API 응답 데이터
            
        Returns:
            Optional[float]: 목표가 평균 또는 None
        """
        # 1차 방어: 기본 조회 API에서 직접 확인
        target_price_fields = ["target_price", "targetPrice", "목표가", "tgt_prc", "tgt_prc_amt", "analyst_target_price"]
        for field in target_price_fields:
            if field in kis_data:
                try:
                    target_price = float(kis_data[field])
                    if target_price and target_price != 0:
                        logger.info(f"[KisStockProvider] 1차 방어 성공: 목표가 = {target_price} (필드: {field})")
                        return target_price
                except (ValueError, TypeError):
                    continue
        
        # 2차 방어: 목표가/컨센서스 API를 통해 조회
        logger.info(f"[KisStockProvider] 2차 방어 시작: 목표가/컨센서스 API 호출 (종목코드: {stock_code})")
        target_data = self._get_target_price_info(stock_code)
        
        if target_data:
            # 목표가 평균 필드명은 KIS API 응답 구조에 따라 다를 수 있음
            target_fields = ["target_price", "targetPrice", "목표가", "tgt_prc", "tgt_prc_amt", "analyst_target_price", "mean_target_price"]
            
            for field in target_fields:
                if field in target_data:
                    try:
                        target_price = float(target_data[field])
                        if target_price and target_price != 0:
                            logger.info(f"[KisStockProvider] 2차 방어 성공: 목표가 = {target_price} (필드: {field})")
                            return target_price
                    except (ValueError, TypeError):
                        continue
            
            logger.warning(f"[KisStockProvider] 2차 방어 실패: 목표가 필드 없음 (종목코드: {stock_code})")
        else:
            logger.warning(f"[KisStockProvider] 2차 방어 실패: 목표가 정보 API 응답 없음 (종목코드: {stock_code})")
        
        # 3차 방어: 예외 처리 및 로깅
        logger.warning(f"[KisStockProvider] 3차 방어: 목표가 데이터를 가져올 수 없음 (종목코드: {stock_code})")
        return None

    def _extract_sector_info(self, kis_data: Dict, stock_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        KIS API 응답에서 섹터/업종 정보를 추출합니다.
        
        Args:
            kis_data: KIS API 응답 데이터
            stock_code: 종목코드
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (sector, industry) 튜플
        """
        # KIS API에서 업종 정보를 제공하는 필드명들 (일반적인 필드명 시도)
        sector_fields = [
            "bstp_nm",  # 업종명
            "bstp_kor_nm",  # 업종 한글명
            "itms_mrkt_cls_code",  # 시장 구분 코드
            "sector",  # 섹터
            "sector_name",  # 섹터명
            "업종명",
            "업종",
        ]
        
        industry_fields = [
            "induty_nm",  # 산업명
            "induty_kor_nm",  # 산업 한글명
            "industry",  # 산업
            "industry_name",  # 산업명
            "산업명",
            "산업",
        ]
        
        sector = None
        industry = None
        
        # 섹터 정보 추출
        for field in sector_fields:
            if field in kis_data:
                try:
                    sector_value = kis_data[field]
                    if sector_value and str(sector_value).strip():
                        sector = str(sector_value).strip()
                        logger.debug(f"[KisStockProvider] 섹터 정보 발견: {sector} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue
        
        # 산업 정보 추출
        for field in industry_fields:
            if field in kis_data:
                try:
                    industry_value = kis_data[field]
                    if industry_value and str(industry_value).strip():
                        industry = str(industry_value).strip()
                        logger.debug(f"[KisStockProvider] 산업 정보 발견: {industry} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue
        
        # 업종 코드를 사람이 읽을 수 있는 문자열로 매핑
        # KIS API에서 업종 코드를 제공하는 경우 매핑 테이블 사용
        if not sector:
            # 업종 코드 필드 확인
            sector_code_fields = ["bstp_cd", "sector_code", "업종코드"]
            for field in sector_code_fields:
                if field in kis_data:
                    try:
                        code = str(kis_data[field]).strip()
                        sector = self._map_sector_code_to_name(code)
                        if sector:
                            logger.info(f"[KisStockProvider] 업종 코드 매핑 성공: {code} -> {sector}")
                            break
                    except (ValueError, TypeError):
                        continue
        
        # 섹터 정보가 없으면 기본값 설정 (ETF/Index가 아닌 "정보없음")
        if not sector:
            sector = "정보없음"
            logger.debug(f"[KisStockProvider] 섹터 정보 없음 (종목코드: {stock_code})")
        
        if not industry:
            industry = "정보없음"
            logger.debug(f"[KisStockProvider] 산업 정보 없음 (종목코드: {stock_code})")
        
        return sector, industry

    def _map_sector_code_to_name(self, code: str) -> Optional[str]:
        """
        업종 코드를 사람이 읽을 수 있는 업종명으로 매핑합니다.
        
        Args:
            code: 업종 코드
            
        Returns:
            Optional[str]: 업종명 또는 None
        """
        # 한국 주식 시장의 주요 업종 코드 매핑 (예시)
        # 실제 KIS API 문서를 참조하여 정확한 매핑 테이블을 작성해야 합니다.
        sector_mapping = {
            # 제조업 관련
            "10": "제조업",
            "11": "제조업",
            "12": "제조업",
            "13": "제조업",
            "14": "제조업",
            "15": "제조업",
            "16": "제조업",
            "17": "제조업",
            "18": "제조업",
            "19": "제조업",
            "20": "제조업",
            "21": "제조업",
            "22": "제조업",
            "23": "제조업",
            "24": "제조업",
            "25": "제조업",
            "26": "제조업",
            "27": "제조업",
            "28": "제조업",
            "29": "제조업",
            "30": "제조업",
            "31": "제조업",
            "32": "제조업",
            "33": "제조업",
            # 운수장비 (기아 등)
            "35": "운수장비",
            # 기타 제조업
            "36": "제조업",
            "37": "제조업",
            "38": "제조업",
            "39": "제조업",
            # 건설업
            "40": "건설업",
            "41": "건설업",
            "42": "건설업",
            # 도매 및 소매업
            "45": "도매 및 소매업",
            "46": "도매 및 소매업",
            "47": "도매 및 소매업",
            # 운수 및 창고업
            "49": "운수 및 창고업",
            "50": "운수 및 창고업",
            "51": "운수 및 창고업",
            "52": "운수 및 창고업",
            # 정보통신업
            "58": "정보통신업",
            "59": "정보통신업",
            "60": "정보통신업",
            "61": "정보통신업",
            "62": "정보통신업",
            "63": "정보통신업",
            # 금융 및 보험업
            "64": "금융 및 보험업",
            "65": "금융 및 보험업",
            "66": "금융 및 보험업",
            # 부동산업
            "68": "부동산업",
            # 전문, 과학 및 기술 서비스업
            "69": "전문, 과학 및 기술 서비스업",
            "70": "전문, 과학 및 기술 서비스업",
            "71": "전문, 과학 및 기술 서비스업",
            "72": "전문, 과학 및 기술 서비스업",
            "73": "전문, 과학 및 기술 서비스업",
            "74": "전문, 과학 및 기술 서비스업",
            "75": "전문, 과학 및 기술 서비스업",
            # 사업시설 관리 및 사업 지원 서비스업
            "76": "사업시설 관리 및 사업 지원 서비스업",
            "77": "사업시설 관리 및 사업 지원 서비스업",
            "78": "사업시설 관리 및 사업 지원 서비스업",
            "79": "사업시설 관리 및 사업 지원 서비스업",
            # 교육 서비스업
            "85": "교육 서비스업",
            # 보건업 및 사회복지 서비스업
            "86": "보건업 및 사회복지 서비스업",
            "87": "보건업 및 사회복지 서비스업",
            # 예술, 스포츠 및 여가관련 서비스업
            "90": "예술, 스포츠 및 여가관련 서비스업",
            # 기타 서비스업
            "91": "기타 서비스업",
            "92": "기타 서비스업",
            "93": "기타 서비스업",
            "94": "기타 서비스업",
            "95": "기타 서비스업",
            "96": "기타 서비스업",
        }
        
        # 코드의 앞 2자리만 사용 (대분류)
        if len(code) >= 2:
            major_code = code[:2]
            return sector_mapping.get(major_code)
        
        return None

    def _convert_kis_response_to_standard_format(self, kis_data: Dict, stock_code: str, ticker: str) -> Dict:
        """
        KIS API 응답을 표준화된 딕셔너리 형식으로 변환합니다.
        3단계 방어 로직을 통해 ROE, 배당수익률, 목표가를 채웁니다.
        
        Args:
            kis_data: KIS API 응답 딕셔너리
            stock_code: 종목코드
            ticker: 원본 티커 심볼
            
        Returns:
            Dict: 표준화된 주식 정보 딕셔너리
        """
        # KIS API 응답 필드 매핑
        # stck_prpr: 현재가
        # hts_avls: 시가총액
        # prdy_clpr: 전일 종가
        # stck_hgpr: 52주 최고가
        # stck_lwpr: 52주 최저가
        # per: PER (주가수익비율)
        # pbr: PBR (주가순자산비율)
        # eps: EPS (주당순이익)
        # dvyd: 배당수익률
        
        current_price = None
        if "stck_prpr" in kis_data:
            try:
                current_price = float(kis_data["stck_prpr"])
            except (ValueError, TypeError):
                pass
        
        market_cap = None
        if "hts_avls" in kis_data:
            try:
                market_cap = float(kis_data["hts_avls"])
            except (ValueError, TypeError):
                pass
        
        previous_close = None
        if "prdy_clpr" in kis_data:
            try:
                previous_close = float(kis_data["prdy_clpr"])
            except (ValueError, TypeError):
                pass
        
        fifty_two_week_high = None
        if "stck_hgpr" in kis_data:
            try:
                fifty_two_week_high = float(kis_data["stck_hgpr"])
            except (ValueError, TypeError):
                pass
        
        fifty_two_week_low = None
        if "stck_lwpr" in kis_data:
            try:
                fifty_two_week_low = float(kis_data["stck_lwpr"])
            except (ValueError, TypeError):
                pass
        
        pe_ratio = None
        if "per" in kis_data:
            try:
                pe_ratio = float(kis_data["per"])
            except (ValueError, TypeError):
                pass
        
        pb_ratio = None
        if "pbr" in kis_data:
            try:
                pb_ratio = float(kis_data["pbr"])
            except (ValueError, TypeError):
                pass
        
        eps = None
        if "eps" in kis_data:
            try:
                eps = float(kis_data["eps"])
            except (ValueError, TypeError):
                pass
        
        # 배당수익률: 1차 방어 (기본 조회에서 확인)
        dividend_yield = None
        if "dvyd" in kis_data:
            try:
                dividend_yield = float(kis_data["dvyd"])
                if dividend_yield == 0:
                    dividend_yield = None  # 0인 경우 2차 방어로 진행
            except (ValueError, TypeError):
                pass
        
        # 3단계 방어 로직 적용
        # ROE: 3단계 방어 로직으로 가져오기
        roe = self._get_roe_with_defense(stock_code, kis_data, current_price)
        
        # 배당수익률: 1차에서 없거나 0인 경우 2차 방어로 진행
        if not dividend_yield:
            dividend_yield = self._get_dividend_yield_with_defense(stock_code, kis_data, current_price)
        
        # 목표가: 3단계 방어 로직으로 가져오기
        target_mean_price = self._get_target_price_with_defense(stock_code, kis_data)
        
        # 종목명 (hts_kor_isnm 필드 사용)
        name = kis_data.get("hts_kor_isnm") or stock_code
        
        # 한글종목명 (hts_kor_isnm 필드 사용)
        korean_name = kis_data.get("hts_kor_isnm") or name
        
        # 섹터/업종 정보 추출
        sector, industry = self._extract_sector_info(kis_data, stock_code)

        
        return {
            "name": name,
            "korean_name": korean_stock_name,  # 한글종목명 추가
            "symbol": ticker,
            "current_price": current_price,
            "previous_close": previous_close,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "eps": eps,
            "dividend_yield": dividend_yield,
            "roe": roe,  # 4단계 방어 로직으로 채워짐
            "fifty_two_week_low": fifty_two_week_low,
            "fifty_two_week_high": fifty_two_week_high,
            "target_mean_price": target_mean_price,  # 3단계 방어 로직으로 채워짐
            "sector": sector,  # 업종 정보 추출
            "industry": industry,  # 산업 정보 추출
            "summary": None,  # KIS API에서 회사 개요를 제공하지 않는 경우
            "currency": "KRW",  # KIS는 한국 주식만 지원
        }

    def get_stock_info(self, ticker: str) -> Dict:
        """
        KIS API를 통해 주식 정보를 가져와 표준화된 딕셔너리로 반환합니다.
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS")
            
        Returns:
            Dict: 표준화된 주식 정보 딕셔너리
        """
        # KIS API는 한국 주식만 지원하므로 .KS 또는 .KQ로 끝나는 티커만 처리
        if not ticker.upper().endswith((".KS", ".KQ")):
            raise ValueError(f"KIS API는 한국 주식만 지원합니다. 티커: {ticker}")
        
        # 티커를 종목코드로 변환
        stock_code = self._convert_ticker_to_stock_code(ticker)
        
        # 주식 현재가 정보 조회
        kis_data = self._get_stock_price_info(stock_code)
        
        # 재무정보 조회 시도 (선택적)
        fundamental_data = self._get_stock_fundamental_info(stock_code)
        
        # 재무정보를 주가 정보에 병합
        if fundamental_data:
            kis_data.update(fundamental_data)

        # 표준화된 딕셔너리로 변환
        return self._convert_kis_response_to_standard_format(kis_data, stock_code, ticker)

    def get_news(self, ticker: str) -> List[str]:
        """
        KIS API를 통해 주식 관련 뉴스 제목 리스트를 반환합니다.
        
        Note: KIS API에서 뉴스 정보를 제공하지 않는 경우 빈 리스트를 반환합니다.
        대신 Yahoo Provider를 사용하거나 별도의 뉴스 API를 연동해야 합니다.
        
        Args:
            ticker: 주식 티커 심볼 (예: "005930.KS")
            
        Returns:
            List[str]: 뉴스 제목 리스트 (현재는 빈 리스트)
        """
        # KIS API는 뉴스 정보를 직접 제공하지 않음
        # 필요시 별도의 뉴스 API를 연동하거나 Yahoo Provider의 get_news를 사용
        logger.warning(f"[KisStockProvider] KIS API는 뉴스 정보를 제공하지 않습니다. 티커: {ticker}")
        return []