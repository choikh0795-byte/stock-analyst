"""
KIS API 데이터 파싱 전담 클래스

KIS 특유의 필드명(stck_prpr, hts_avls 등)을 표준 포맷으로 매핑하고
업종 코드를 변환하는 로직 전담.
"""

import logging
from typing import Dict, Optional, Tuple

from .kis_sector_mapping import (
    SECTOR_CODE_MAPPING,
    SECTOR_FIELD_CANDIDATES,
    INDUSTRY_FIELD_CANDIDATES,
    SECTOR_CODE_FIELD_CANDIDATES,
)

logger = logging.getLogger(__name__)


class KisDataParser:
    """
    KIS API 응답 데이터를 표준 형식으로 변환하는 클래스

    역할:
    - KIS 필드명 → 표준 필드명 매핑
    - 업종 코드 → 업종명 변환
    - 섹터/산업 정보 추출
    - 티커 변환 (Yahoo Finance 형식 ↔ KIS 형식)
    """

    @staticmethod
    def convert_ticker_to_stock_code(ticker: str) -> str:
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

    @staticmethod
    def map_sector_code_to_name(code: str) -> Optional[str]:
        """
        업종 코드를 사람이 읽을 수 있는 업종명으로 매핑합니다.

        Args:
            code: 업종 코드

        Returns:
            Optional[str]: 업종명 또는 None
        """
        # 코드의 앞 2자리만 사용 (대분류)
        if len(code) >= 2:
            major_code = code[:2]
            return SECTOR_CODE_MAPPING.get(major_code)

        return None

    @staticmethod
    def extract_sector_info(kis_data: Dict, stock_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        KIS API 응답에서 섹터/업종 정보를 추출합니다.

        Args:
            kis_data: KIS API 응답 데이터
            stock_code: 종목코드

        Returns:
            Tuple[Optional[str], Optional[str]]: (sector, industry) 튜플
        """
        sector = None
        industry = None

        # 섹터 정보 추출
        for field in SECTOR_FIELD_CANDIDATES:
            if field in kis_data:
                try:
                    sector_value = kis_data[field]
                    if sector_value and str(sector_value).strip():
                        sector = str(sector_value).strip()
                        logger.debug(f"[KisDataParser] 섹터 정보 발견: {sector} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue

        # 산업 정보 추출
        for field in INDUSTRY_FIELD_CANDIDATES:
            if field in kis_data:
                try:
                    industry_value = kis_data[field]
                    if industry_value and str(industry_value).strip():
                        industry = str(industry_value).strip()
                        logger.debug(f"[KisDataParser] 산업 정보 발견: {industry} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue

        # 업종 코드를 사람이 읽을 수 있는 문자열로 매핑
        # KIS API에서 업종 코드를 제공하는 경우 매핑 테이블 사용
        if not sector:
            # 업종 코드 필드 확인
            for field in SECTOR_CODE_FIELD_CANDIDATES:
                if field in kis_data:
                    try:
                        code = str(kis_data[field]).strip()
                        sector = KisDataParser.map_sector_code_to_name(code)
                        if sector:
                            logger.info(f"[KisDataParser] 업종 코드 매핑 성공: {code} -> {sector}")
                            break
                    except (ValueError, TypeError):
                        continue

        # 섹터 정보가 없으면 기본값 설정 (ETF/Index가 아닌 "정보없음")
        if not sector:
            sector = "정보없음"
            logger.debug(f"[KisDataParser] 섹터 정보 없음 (종목코드: {stock_code})")

        if not industry:
            industry = "정보없음"
            logger.debug(f"[KisDataParser] 산업 정보 없음 (종목코드: {stock_code})")

        return sector, industry

    @staticmethod
    def parse_kis_price_fields(kis_data: Dict) -> Dict[str, Optional[float]]:
        """
        KIS API 응답에서 가격 관련 필드를 추출합니다.

        Args:
            kis_data: KIS API 응답 데이터

        Returns:
            Dict[str, Optional[float]]: 가격 정보 딕셔너리
        """
        price_info = {}

        # 현재가
        if "stck_prpr" in kis_data:
            try:
                price_info["current_price"] = float(kis_data["stck_prpr"])
            except (ValueError, TypeError):
                price_info["current_price"] = None
        else:
            price_info["current_price"] = None

        # 전일 종가 (KIS API: stck_sdpr = Standard Price)
        if "stck_sdpr" in kis_data:
            try:
                price_info["previous_close"] = float(kis_data["stck_sdpr"])
            except (ValueError, TypeError):
                price_info["previous_close"] = None
        else:
            price_info["previous_close"] = None

        # 52주 최고가 (w52_hgpr 또는 d250_hgpr 사용, stck_hgpr는 당일 최고가임)
        fifty_two_week_high = None
        for field in ["w52_hgpr", "d250_hgpr", "stck_dryy_hgpr"]:
            if field in kis_data:
                try:
                    fifty_two_week_high = float(kis_data[field])
                    if fifty_two_week_high > 0:
                        logger.debug(f"[KisDataParser] 52주 최고가 발견: {fifty_two_week_high} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue
        price_info["fifty_two_week_high"] = fifty_two_week_high

        # 52주 최저가 (w52_lwpr 또는 d250_lwpr 사용, stck_lwpr는 당일 최저가임)
        fifty_two_week_low = None
        for field in ["w52_lwpr", "d250_lwpr", "stck_dryy_lwpr"]:
            if field in kis_data:
                try:
                    fifty_two_week_low = float(kis_data[field])
                    if fifty_two_week_low > 0:
                        logger.debug(f"[KisDataParser] 52주 최저가 발견: {fifty_two_week_low} (필드: {field})")
                        break
                except (ValueError, TypeError):
                    continue
        price_info["fifty_two_week_low"] = fifty_two_week_low

        return price_info

    @staticmethod
    def parse_kis_fundamental_fields(kis_data: Dict) -> Dict[str, Optional[float]]:
        """
        KIS API 응답에서 재무 지표 필드를 추출합니다.

        Args:
            kis_data: KIS API 응답 데이터

        Returns:
            Dict[str, Optional[float]]: 재무 지표 딕셔너리
        """
        fundamental_info = {}

        # 시가총액
        if "hts_avls" in kis_data:
            try:
                fundamental_info["market_cap"] = float(kis_data["hts_avls"])
            except (ValueError, TypeError):
                fundamental_info["market_cap"] = None
        else:
            fundamental_info["market_cap"] = None

        # PER (주가수익비율)
        if "per" in kis_data:
            try:
                fundamental_info["pe_ratio"] = float(kis_data["per"])
            except (ValueError, TypeError):
                fundamental_info["pe_ratio"] = None
        else:
            fundamental_info["pe_ratio"] = None

        # PBR (주가순자산비율)
        if "pbr" in kis_data:
            try:
                fundamental_info["pb_ratio"] = float(kis_data["pbr"])
            except (ValueError, TypeError):
                fundamental_info["pb_ratio"] = None
        else:
            fundamental_info["pb_ratio"] = None

        # EPS (주당순이익)
        if "eps" in kis_data:
            try:
                fundamental_info["eps"] = float(kis_data["eps"])
            except (ValueError, TypeError):
                fundamental_info["eps"] = None
        else:
            fundamental_info["eps"] = None

        return fundamental_info

    @staticmethod
    def convert_kis_response_to_standard_format(
        kis_data: Dict,
        stock_code: str,
        ticker: str,
        roe: Optional[float] = None,
        target_mean_price: Optional[float] = None
    ) -> Dict:
        """
        KIS API 응답을 표준화된 딕셔너리 형식으로 변환합니다.

        Args:
            kis_data: KIS API 응답 딕셔너리
            stock_code: 종목코드
            ticker: 원본 티커 심볼
            roe: ROE (방어 로직을 통해 계산된 값)
            target_mean_price: 목표가 (방어 로직을 통해 계산된 값)

        Returns:
            Dict: 표준화된 주식 정보 딕셔너리
        """
        # 가격 정보 파싱
        price_info = KisDataParser.parse_kis_price_fields(kis_data)

        # 재무 지표 파싱
        fundamental_info = KisDataParser.parse_kis_fundamental_fields(kis_data)

        # 종목명 (hts_kor_isnm 필드 사용)
        name = kis_data.get("hts_kor_isnm") or stock_code

        # 한글종목명 (hts_kor_isnm 필드 사용)
        korean_name = kis_data.get("hts_kor_isnm") or name

        # 섹터/업종 정보 추출
        sector, industry = KisDataParser.extract_sector_info(kis_data, stock_code)

        return {
            "name": name,
            "korean_name": korean_name,  # 한글종목명 추가
            "symbol": ticker,
            "current_price": price_info["current_price"],
            "previous_close": price_info["previous_close"],
            "market_cap": fundamental_info["market_cap"],
            "pe_ratio": fundamental_info["pe_ratio"],
            "pb_ratio": fundamental_info["pb_ratio"],
            "eps": fundamental_info["eps"],
            "roe": roe,  # 방어 로직으로 채워짐
            "fifty_two_week_low": price_info["fifty_two_week_low"],
            "fifty_two_week_high": price_info["fifty_two_week_high"],
            "target_mean_price": target_mean_price,  # 방어 로직으로 채워짐
            "sector": sector,  # 업종 정보 추출
            "industry": industry,  # 산업 정보 추출
            "summary": None,  # KIS API에서 회사 개요를 제공하지 않는 경우
            "currency": "KRW",  # KIS는 한국 주식만 지원
        }
