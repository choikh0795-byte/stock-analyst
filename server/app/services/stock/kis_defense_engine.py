"""
KIS API 데이터 방어 로직 전담 클래스

ROE, 배당수익률, 목표가 등 실패 가능성이 높은 데이터를 'n차 단계'에 걸쳐 가져오는 로직을 관리.
Strategy Pattern을 적용하여 각 방어 단계를 독립적인 전략으로 분리하고 실행 상태를 가시화합니다.
"""

import logging
from typing import Callable, Dict, List, Optional, Tuple

from .kis_sector_mapping import (
    ROE_FIELD_CANDIDATES,
    DIVIDEND_YIELD_FIELD_CANDIDATES,
    TARGET_PRICE_FIELD_CANDIDATES,
    NET_INCOME_FIELD_CANDIDATES,
    EQUITY_FIELD_CANDIDATES,
    DPS_FIELD_CANDIDATES,
)

logger = logging.getLogger(__name__)


class DefenseStrategy:
    """
    방어 전략 기본 클래스

    각 방어 단계를 나타내는 전략 객체의 베이스 클래스입니다.
    """

    def __init__(self, step_number: int, step_name: str):
        """
        Args:
            step_number: 방어 단계 번호 (1, 2, 3, ...)
            step_name: 방어 단계 설명 (예: "Field Check", "PBR/PER Calculation")
        """
        self.step_number = step_number
        self.step_name = step_name

    def execute(self, *args, **kwargs) -> Optional[float]:
        """
        방어 로직 실행

        Returns:
            Optional[float]: 성공 시 값, 실패 시 None
        """
        raise NotImplementedError("Subclasses must implement execute()")


class KisDefenseEngine:
    """
    KIS API 데이터 방어 로직 엔진

    역할:
    - ROE, 배당수익률, 목표가 등 n차 방어 로직 관리
    - Strategy Pattern으로 각 단계를 독립적으로 실행
    - 실행 상태를 [Defense][Metric] Step N -> Result 형식으로 로깅
    - 최종 Summary 정보 제공
    """

    def __init__(self, api_client):
        """
        Args:
            api_client: KisApiClient 인스턴스 (API 호출용)
        """
        self.api_client = api_client
        # 방어 로직 실행 결과 Summary 저장
        self.defense_summary: Dict[str, str] = {}

    def _execute_defense_strategies(
        self,
        metric_name: str,
        strategies: List[Tuple[str, Callable[[], Optional[float]]]],
        allow_zero: bool = False,
    ) -> Optional[float]:
        """
        방어 전략들을 순차적으로 실행하고 결과를 로깅합니다.

        Args:
            metric_name: 지표 이름 (예: "ROE", "Dividend Yield", "Target Price")
            strategies: (step_name, strategy_func) 튜플 리스트
            allow_zero: True이면 0.0도 유효한 값으로 처리 (배당수익률 등)

        Returns:
            Optional[float]: 성공한 첫 번째 값 또는 None
        """
        for step_num, (step_name, strategy_func) in enumerate(strategies, start=1):
            try:
                result = strategy_func()
                # allow_zero=True이면 0.0도 성공으로 처리 (배당수익률 등)
                # allow_zero=False이면 0이 아닌 값만 성공으로 처리 (ROE, 목표가 등)
                is_valid = result is not None and (allow_zero or result != 0)

                if is_valid:
                    logger.info(f"[Defense][{metric_name}] Step {step_num} ({step_name}) -> Success (Value: {result})")
                    self.defense_summary[metric_name] = f"Step {step_num} ({step_name})"
                    return result
                else:
                    if result is None:
                        logger.info(f"[Defense][{metric_name}] Step {step_num} ({step_name}) -> Failed (result=None)")
                    else:
                        logger.info(f"[Defense][{metric_name}] Step {step_num} ({step_name}) -> Failed (result={result}, allow_zero={allow_zero})")
            except Exception as e:
                logger.warning(f"[Defense][{metric_name}] Step {step_num} ({step_name}) -> Failed (Error: {e})")

        # 모든 전략 실패
        logger.warning(f"[Defense][{metric_name}] All steps failed")
        self.defense_summary[metric_name] = "Failed"
        return None

    def get_roe_with_defense(
        self,
        stock_code: str,
        kis_data: Dict,
        current_price: Optional[float]
    ) -> Optional[float]:
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
        # 방어 전략 정의
        strategies = [
            ("Field Check", lambda: self._roe_step1_field_check(kis_data)),
            ("PBR/PER Calculation", lambda: self._roe_step2_pbr_per_calc(kis_data)),
            ("EPS/PBR/Price Calculation", lambda: self._roe_step3_eps_calc(kis_data, current_price)),
            ("Financial Statement API", lambda: self._roe_step4_financial_api(stock_code)),
        ]

        return self._execute_defense_strategies("ROE", strategies)

    def _roe_step1_field_check(self, kis_data: Dict) -> Optional[float]:
        """
        1차 방어: 기본 조회 API에서 ROE 필드 직접 확인
        """
        for field in ROE_FIELD_CANDIDATES:
            if field in kis_data:
                try:
                    roe_value = float(kis_data[field])
                    if roe_value and roe_value != 0:
                        logger.debug(f"[Defense][ROE][Step1] ROE 필드 발견: {roe_value}% (필드: {field})")
                        return roe_value
                except (ValueError, TypeError):
                    continue
        return None

    def _roe_step2_pbr_per_calc(self, kis_data: Dict) -> Optional[float]:
        """
        2차 방어: PBR과 PER을 이용한 파생 계산
        공식: ROE = (PBR / PER) * 100
        """
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
            logger.debug(f"[Defense][ROE][Step2] PBR: {pb_ratio}, PER: {pe_ratio} -> ROE: {roe:.2f}%")
            return round(roe, 2)

        return None

    def _roe_step3_eps_calc(self, kis_data: Dict, current_price: Optional[float]) -> Optional[float]:
        """
        3차 방어: EPS, PBR, 현재가를 이용한 파생 계산
        공식: ROE = EPS / (Current_Price / PBR) * 100
        """
        eps = None
        pb_ratio = None

        if "eps" in kis_data:
            try:
                eps = float(kis_data["eps"])
            except (ValueError, TypeError):
                pass

        if "pbr" in kis_data:
            try:
                pb_ratio = float(kis_data["pbr"])
            except (ValueError, TypeError):
                pass

        if eps and eps > 0 and pb_ratio and pb_ratio > 0 and current_price and current_price > 0:
            # BPS = Current_Price / PBR
            bps = current_price / pb_ratio
            if bps > 0:
                roe = (eps / bps) * 100
                logger.debug(f"[Defense][ROE][Step3] EPS: {eps}, PBR: {pb_ratio}, 현재가: {current_price}, BPS: {bps} -> ROE: {roe:.2f}%")
                return round(roe, 2)

        return None

    def _roe_step4_financial_api(self, stock_code: str) -> Optional[float]:
        """
        4차 방어: 재무제표 API를 통해 계산
        공식: ROE = (당기순이익 / 자본총계) * 100
        """
        logger.debug(f"[Defense][ROE][Step4] 재무제표 API 호출 (종목코드: {stock_code})")
        financial_data = self.api_client.get_financial_statement(stock_code)

        if not financial_data:
            return None

        # 디버깅: 재무제표 데이터의 모든 키 로깅
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[Defense][ROE][Step4] 재무제표 데이터 키: {list(financial_data.keys())}")

        net_income = None
        total_equity = None

        # 당기순이익 추출
        for field in NET_INCOME_FIELD_CANDIDATES:
            if field in financial_data:
                try:
                    value = financial_data[field]
                    # 배열인 경우 최근 4분기 합산 또는 최신 값 사용
                    if isinstance(value, list) and len(value) > 0:
                        try:
                            net_income = sum(float(x) for x in value if x is not None and x != 0)
                        except (ValueError, TypeError):
                            net_income = float(value[0]) if value[0] else None
                    else:
                        net_income = float(value)

                    if net_income and net_income != 0:
                        logger.debug(f"[Defense][ROE][Step4] 당기순이익 발견: {net_income} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue

        # 자본총계 추출
        for field in EQUITY_FIELD_CANDIDATES:
            if field in financial_data:
                try:
                    value = financial_data[field]
                    # 배열인 경우 최신 값 사용
                    if isinstance(value, list) and len(value) > 0:
                        total_equity = float(value[0]) if value[0] else None
                    else:
                        total_equity = float(value)

                    if total_equity and total_equity != 0:
                        logger.debug(f"[Defense][ROE][Step4] 자본총계 발견: {total_equity} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue

        if net_income and total_equity and total_equity > 0:
            roe = (net_income / total_equity) * 100
            logger.debug(f"[Defense][ROE][Step4] 당기순이익: {net_income}, 자본총계: {total_equity} -> ROE: {roe:.2f}%")
            return round(roe, 2)

        logger.debug(f"[Defense][ROE][Step4] 재무 데이터 불완전 (당기순이익: {net_income}, 자본총계: {total_equity})")
        return None

    def get_dividend_yield_with_defense(
        self,
        stock_code: str,
        kis_data: Dict,
        current_price: Optional[float]
    ) -> Optional[float]:
        """
        배당수익률을 4단계 방어 로직으로 가져옵니다.

        1차 방어: 기본 조회 API에서 배당수익률 필드 직접 확인 (pdy, dvyd 등)
        2차 방어: 기본 조회 API에서 DPS 추출하여 계산 (dps / 현재가) * 100 (추가 API 호출 없음)
        3차 방어: 배당 정보 API를 통해 계산 (DPS / 현재가) * 100 (별도 API 호출)
        4차 방어: 배당 없음으로 간주 (0.0 반환)

        Args:
            stock_code: 종목코드
            kis_data: 기본 조회 API 응답 데이터
            current_price: 현재가

        Returns:
            Optional[float]: 배당수익률 (% 단위) 또는 0.0
        """
        logger.info(f"[Dividend-Process] 배당수익률 계산 시작: {stock_code}, 현재가={current_price}")

        # 방어 전략 정의
        strategies = [
            ("Field Check", lambda: self._dividend_step1_field_check(kis_data)),
            ("DPS Calculation (kis_data)", lambda: self._dividend_step2_dps_from_kis_data(kis_data, current_price)),
            ("Dividend API Calculation", lambda: self._dividend_step3_api_calc(stock_code, current_price)),
            ("Default Zero", lambda: self._dividend_step4_default()),
        ]

        # allow_zero=True: 배당수익률 0.0도 유효한 값으로 처리
        result = self._execute_defense_strategies("Dividend Yield", strategies, allow_zero=True)
        # 배당수익률은 최소 0.0 반환 (None 대신)
        final_result = result if result is not None else 0.0
        logger.info(f"[Dividend-Process] 배당수익률 계산 완료: {stock_code} -> {final_result}%")
        return final_result

    def _dividend_step1_field_check(self, kis_data: Dict) -> Optional[float]:
        """
        1차 방어: 기본 조회 API에서 배당수익률 필드 직접 확인 (pdy, dvyd 등)
        """
        logger.debug(f"[Dividend-Calc][Step1] kis_data 필드 목록: {list(kis_data.keys())[:20]}")

        for field in DIVIDEND_YIELD_FIELD_CANDIDATES:
            if field in kis_data:
                try:
                    raw_value = kis_data[field]
                    logger.debug(f"[Dividend-Calc][Step1] 필드 '{field}' 발견: 원본값={raw_value}, 타입={type(raw_value)}")
                    div_yield = float(raw_value)
                    if div_yield is not None:  # 0.0도 허용
                        logger.info(f"[Dividend-Calc][Step1] Success: Raw {field}={raw_value} -> {div_yield}%")
                        return div_yield
                except (ValueError, TypeError) as e:
                    logger.debug(f"[Dividend-Calc][Step1] 필드 '{field}' 변환 실패: {e}")
                    continue

        logger.debug(f"[Dividend-Calc][Step1] 배당수익률 필드 없음. 검색 대상: {DIVIDEND_YIELD_FIELD_CANDIDATES}")
        return None

    def _dividend_step2_dps_from_kis_data(self, kis_data: Dict, current_price: Optional[float]) -> Optional[float]:
        """
        2차 방어: 기본 조회 API 응답(kis_data)에서 DPS 추출하여 계산 (추가 API 호출 없음)
        공식: 배당수익률 = (DPS / 현재가) * 100
        """
        if not current_price or current_price <= 0:
            logger.debug(f"[Dividend-Calc][Step2] 현재가 없음: {current_price}")
            return None

        logger.debug(f"[Dividend-Calc][Step2] DPS 필드 검색 시작. 현재가={current_price}")

        dps = None
        found_field = None
        for field in DPS_FIELD_CANDIDATES:
            if field in kis_data:
                try:
                    raw_value = kis_data[field]
                    logger.debug(f"[Dividend-Calc][Step2] 필드 '{field}' 발견: 원본값={raw_value}, 타입={type(raw_value)}")
                    dps = float(raw_value)
                    if dps and dps > 0:
                        found_field = field
                        logger.debug(f"[Dividend-Calc][Step2] DPS 추출 성공: {field}={dps}")
                        break
                except (ValueError, TypeError) as e:
                    logger.debug(f"[Dividend-Calc][Step2] 필드 '{field}' 변환 실패: {e}")
                    continue

        if dps and dps > 0:
            dividend_yield = (dps / current_price) * 100
            logger.info(f"[Dividend-Calc][Step2] Success: DPS={dps} (필드={found_field}), Price={current_price} -> Calc Yield: {dividend_yield:.2f}%")
            return round(dividend_yield, 2)

        logger.debug(f"[Dividend-Calc][Step2] DPS 필드 없음. 검색 대상: {DPS_FIELD_CANDIDATES}")
        return None

    def _dividend_step3_api_calc(self, stock_code: str, current_price: Optional[float]) -> Optional[float]:
        """
        3차 방어: 배당 정보 API를 통해 계산 (별도 API 호출)

        NOTE: 현재 KIS API에서 get_dividend_info는 get_stock_price_info와 동일한 엔드포인트(FHKST01010100)를 사용하므로,
        이 단계는 실제로 중복 호출입니다. Step 1, 2에서 이미 모든 배당 데이터를 확인했으므로,
        성능 최적화를 위해 이 단계를 스킵합니다.
        """
        logger.debug(f"[Dividend-Calc][Step3] 스킵됨 (중복 API 호출 방지, 성능 최적화)")
        return None

    def _dividend_step4_default(self) -> float:
        """
        4차 방어: 배당 없음으로 간주 (0.0 반환)
        """
        logger.info("[Dividend-Calc][Step4] 모든 데이터 소스 실패 -> 기본값 0.0 반환 (배당 없음)")
        return 0.0

    def get_target_price_with_defense(
        self,
        stock_code: str,
        kis_data: Dict
    ) -> Optional[float]:
        """
        목표가를 3단계 방어 로직으로 가져옵니다.

        1차 방어: 기본 조회 API에서 직접 확인
        2차 방어: 목표가/컨센서스 API를 통해 조회
        3차 방어: None 반환

        Args:
            stock_code: 종목코드
            kis_data: 기본 조회 API 응답 데이터

        Returns:
            Optional[float]: 목표가 평균 또는 None
        """
        # 방어 전략 정의
        strategies = [
            ("Field Check", lambda: self._target_step1_field_check(kis_data)),
            ("Target Price API", lambda: self._target_step2_api_call(stock_code)),
        ]

        return self._execute_defense_strategies("Target Price", strategies)

    def _target_step1_field_check(self, kis_data: Dict) -> Optional[float]:
        """
        1차 방어: 기본 조회 API에서 목표가 필드 직접 확인
        """
        for field in TARGET_PRICE_FIELD_CANDIDATES:
            if field in kis_data:
                try:
                    target_price = float(kis_data[field])
                    if target_price and target_price != 0:
                        logger.debug(f"[Defense][Target][Step1] 목표가 필드 발견: {target_price} (필드: {field})")
                        return target_price
                except (ValueError, TypeError):
                    continue
        return None

    def _target_step2_api_call(self, stock_code: str) -> Optional[float]:
        """
        2차 방어: 목표가/컨센서스 API를 통해 조회

        NOTE: 현재 KIS API에서 get_target_price_info는 get_stock_price_info와 동일한 엔드포인트(FHKST01010100)를 사용하므로,
        이 단계는 실제로 중복 호출입니다. Step 1에서 이미 모든 목표가 데이터를 확인했으므로,
        성능 최적화를 위해 이 단계를 스킵합니다.
        """
        logger.debug(f"[Defense][Target][Step2] 스킵됨 (중복 API 호출 방지, 성능 최적화)")
        return None

    def get_defense_summary(self) -> str:
        """
        방어 로직 실행 결과 Summary를 문자열로 반환합니다.

        Returns:
            str: Summary 문자열 (예: "ROE: Step 2 (PBR/PER), Dividend: Step 1 (Field Check), Target: Failed")
        """
        summary_parts = []
        for metric, result in self.defense_summary.items():
            summary_parts.append(f"{metric}: {result}")

        if summary_parts:
            summary = ", ".join(summary_parts)
            logger.info(f"[Defense Summary] {summary}")
            return summary
        else:
            return "No defense logic executed"
