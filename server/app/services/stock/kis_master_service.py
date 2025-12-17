import logging
import os
import ssl
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class KisMasterService:
    """
    KIS(한국투자증권) 마스터 파일을 다운로드하고 파싱하여
    종목명 ↔ 티커 매핑 및 티커 → 기본 정보를 제공하는 서비스
    
    마스터 파일은 고정 길이(Fixed-width) 텍스트 형식이며,
    cp949 인코딩을 사용합니다.
    """

    # 마스터 파일 다운로드 URL (KIS 공식 다운로드 서버)
    # 참고: 실제 URL은 KIS API 문서를 확인하여 업데이트가 필요할 수 있습니다.
    KOSPI_MASTER_URLS = [
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
    ]
    
    KOSDAQ_MASTER_URLS = [
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
    ]

    # Part2 필드 구조 (고정 폭) - 코스피
    # 샘플 코드의 field_specs에 맞춘 구조
    PART2_FIELD_SPECS_KOSPI = [
        2, 1, 4, 4, 4,  # 그룹코드, 시가총액규모, 지수업종대분류, 지수업종중분류, 지수업종소분류
        1, 1, 1, 1, 1,  # 제조업, 저유동성, 지배구조지수종목, KOSPI200섹터업종, KOSPI100
        1, 1, 1, 1, 1,  # KOSPI50, KRX, ETP, ELW발행, KRX100
        1, 1, 1, 1, 1,  # KRX자동차, KRX반도체, KRX바이오, KRX은행, SPAC
        1, 1, 1, 1, 1,  # KRX에너지화학, KRX철강, 단기과열, KRX미디어통신, KRX건설
        1, 1, 1, 1, 1,  # Non1, KRX증권, KRX선박, KRX섹터_보험, KRX섹터_운송
        1, 9, 5, 5, 1,  # SRI, 기준가, 매매수량단위, 시간외수량단위, 거래정지
        1, 1, 1, 1, 1,  # 정리매매, 관리종목, 시장경고, 경고예고, 불성실공시
        1, 1, 1, 2, 1,  # 우회상장, 락구분, 액면변경, 증자구분, 증거금비율
        1, 1, 1, 9, 5,  # 신용가능, 신용기간, 전일거래량, 액면가, 상장일자
        9, 9, 9, 5, 9,  # 상장주수, 자본금, 결산월, 공모가, 우선주
        8, 9, 3, 1, 1,  # 공매도과열, 이상급등, KRX300, KOSPI, 매출액
        1, 1, 1, 9, 9,  # 영업이익, 경상이익, 당기순이익, ROE, 기준년월
        9, 9, 9, 5, 9,  # 시가총액, 그룹사코드, 회사신용한도초과, 담보대출가능, 대주가능
    ]
    
    PART2_COLUMNS_KOSPI = [
        '그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류',
        '제조업', '저유동성', '지배구조지수종목', 'KOSPI200섹터업종', 'KOSPI100',
        'KOSPI50', 'KRX', 'ETP', 'ELW발행', 'KRX100',
        'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행', 'SPAC',
        'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설',
        'Non1', 'KRX증권', 'KRX선박', 'KRX섹터_보험', 'KRX섹터_운송',
        'SRI', '기준가', '매매수량단위', '시간외수량단위', '거래정지',
        '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시',
        '우회상장', '락구분', '액면변경', '증자구분', '증거금비율',
        '신용가능', '신용기간', '전일거래량', '액면가', '상장일자',
        '상장주수', '자본금', '결산월', '공모가', '우선주',
        '공매도과열', '이상급등', 'KRX300', 'KOSPI', '매출액',
        '영업이익', '경상이익', '당기순이익', 'ROE', '기준년월',
        '시가총액', '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능'
    ]
    
    # Part2 필드 구조 (고정 폭) - 코스닥
    # 샘플 코드의 field_specs에 맞춘 구조
    PART2_FIELD_SPECS_KOSDAQ = [
        2, 1,  # 증권그룹구분코드, 시가총액 규모 구분 코드 유가
        4, 4, 4, 1, 1,  # 지수업종 대분류 코드, 지수 업종 중분류 코드, 지수업종 소분류 코드, 벤처기업 여부 (Y/N), 저유동성종목 여부
        1, 1, 1, 1, 1,  # KRX 종목 여부, ETP 상품구분코드, KRX100 종목 여부 (Y/N), KRX 자동차 여부, KRX 반도체 여부
        1, 1, 1, 1, 1,  # KRX 바이오 여부, KRX 은행 여부, 기업인수목적회사여부, KRX 에너지 화학 여부, KRX 철강 여부
        1, 1, 1, 1,  # 단기과열종목구분코드, KRX 미디어 통신 여부, KRX 건설 여부, (코스닥)투자주의환기종목여부
        1, 1, 1, 1, 1,  # KRX 증권 구분, KRX 선박 구분, KRX섹터지수 보험여부, KRX섹터지수 운송여부, KOSDAQ150지수여부 (Y,N)
        9, 5, 5, 1, 1,  # 주식 기준가, 정규 시장 매매 수량 단위, 시간외 시장 매매 수량 단위, 거래정지 여부, 정리매매 여부
        1, 2, 1, 1, 1,  # 관리 종목 여부, 시장 경고 구분 코드, 시장 경고위험 예고 여부, 불성실 공시 여부, 우회 상장 여부
        2, 2, 2, 3, 1,  # 락구분 코드, 액면가 변경 구분 코드, 증자 구분 코드, 증거금 비율, 신용주문 가능 여부
        3, 12, 12, 8, 15,  # 신용기간, 전일 거래량, 주식 액면가, 주식 상장 일자, 상장 주수(천)
        21, 2, 7, 1, 1,  # 자본금, 결산 월, 공모 가격, 우선주 구분 코드, 공매도과열종목여부
        1, 1, 9, 9, 9,  # 이상급등종목여부, KRX300 종목 여부 (Y/N), 매출액, 영업이익, 경상이익
        5, 9, 8, 9, 3,  # 단기순이익, ROE(자기자본이익률), 기준년월, 전일기준 시가총액 (억), 그룹사 코드
        1, 1, 1, 1, 1  # 회사신용한도초과여부, 담보대출가능여부, 대주가능여부
    ]
    
    PART2_COLUMNS_KOSDAQ = [
        '증권그룹구분코드', '시가총액 규모 구분 코드 유가',
        '지수업종 대분류 코드', '지수 업종 중분류 코드', '지수업종 소분류 코드', '벤처기업 여부 (Y/N)',
        '저유동성종목 여부', 'KRX 종목 여부', 'ETP 상품구분코드', 'KRX100 종목 여부 (Y/N)',
        'KRX 자동차 여부', 'KRX 반도체 여부', 'KRX 바이오 여부', 'KRX 은행 여부', '기업인수목적회사여부',
        'KRX 에너지 화학 여부', 'KRX 철강 여부', '단기과열종목구분코드', 'KRX 미디어 통신 여부',
        'KRX 건설 여부', '(코스닥)투자주의환기종목여부', 'KRX 증권 구분', 'KRX 선박 구분',
        'KRX섹터지수 보험여부', 'KRX섹터지수 운송여부', 'KOSDAQ150지수여부 (Y,N)', '주식 기준가',
        '정규 시장 매매 수량 단위', '시간외 시장 매매 수량 단위', '거래정지 여부', '정리매매 여부',
        '관리 종목 여부', '시장 경고 구분 코드', '시장 경고위험 예고 여부', '불성실 공시 여부',
        '우회 상장 여부', '락구분 코드', '액면가 변경 구분 코드', '증자 구분 코드', '증거금 비율',
        '신용주문 가능 여부', '신용기간', '전일 거래량', '주식 액면가', '주식 상장 일자', '상장 주수(천)',
        '자본금', '결산 월', '공모 가격', '우선주 구분 코드', '공매도과열종목여부', '이상급등종목여부',
        'KRX300 종목 여부 (Y/N)', '매출액', '영업이익', '경상이익', '단기순이익', 'ROE(자기자본이익률)',
        '기준년월', '전일기준 시가총액 (억)', '그룹사 코드', '회사신용한도초과여부', '담보대출가능여부', '대주가능여부'
    ]

    def __init__(self, cache_dir: Optional[str] = None):
        """
        KisMasterService 초기화
        
        Args:
            cache_dir: 마스터 파일을 캐시할 디렉토리 경로 (None이면 임시 디렉토리 사용)
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Windows와 Unix 모두 지원
            import tempfile
            temp_base = Path(tempfile.gettempdir())
            self.cache_dir = temp_base / "kis_master"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 메모리 캐시
        self._name_to_code: Dict[str, str] = {}  # {"삼성전자": "005930.KS", ...}
        self._code_to_detail: Dict[str, Dict] = {}  # {"005930.KS": {"name": "삼성전자", "sector_code": "...", "market": "KOSPI"}, ...}
        
        # 데이터 로드 여부 플래그
        self._loaded = False

    def _download_and_extract_master_file(self, urls: List[str], zip_filename: str, extracted_filename: str) -> Optional[Path]:
        """
        마스터 파일을 다운로드하고 압축을 해제합니다.
        
        Args:
            urls: 다운로드 시도할 URL 리스트
            zip_filename: 다운로드할 압축 파일명
            extracted_filename: 압축 해제 후 파일명
            
        Returns:
            Path: 압축 해제된 파일 경로 또는 None (실패 시)
        """
        extracted_file_path = self.cache_dir / extracted_filename
        
        # 이미 압축 해제된 파일이 있으면 재사용
        if extracted_file_path.exists():
            logger.info(f"[KisMasterService] 기존 마스터 파일 사용: {extracted_file_path}")
            return extracted_file_path
        
        zip_file_path = self.cache_dir / zip_filename
        
        # 압축 파일이 없으면 다운로드
        if not zip_file_path.exists():
            # SSL 컨텍스트 설정 (인증서 검증 비활성화)
            ssl._create_default_https_context = ssl._create_unverified_context
            
            # 여러 URL 시도
            for url in urls:
                try:
                    logger.info(f"[KisMasterService] 마스터 파일 다운로드 시도: {url}")
                    urllib.request.urlretrieve(url, str(zip_file_path))
                    
                    # 파일 크기 체크 (최소 1KB 이상이어야 함)
                    if zip_file_path.stat().st_size < 1024:
                        logger.warning(f"[KisMasterService] 다운로드된 파일이 너무 작음: {zip_file_path.stat().st_size} bytes")
                        zip_file_path.unlink(missing_ok=True)
                        continue
                    
                    logger.info(f"[KisMasterService] 마스터 파일 다운로드 성공: {zip_file_path} ({zip_file_path.stat().st_size} bytes)")
                    break
                    
                except Exception as e:
                    logger.warning(f"[KisMasterService] URL 다운로드 실패 ({url}): {e}")
                    zip_file_path.unlink(missing_ok=True)
                    continue
            else:
                # 모든 URL 실패
                logger.error(f"[KisMasterService] 모든 URL에서 마스터 파일 다운로드 실패: {zip_filename}")
                return None
        
        # 압축 해제
        try:
            logger.info(f"[KisMasterService] 압축 파일 해제 중: {zip_file_path}")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.cache_dir)
            
            # 압축 파일 삭제 (선택사항)
            if zip_file_path.exists():
                zip_file_path.unlink()
            
            logger.info(f"[KisMasterService] 압축 해제 완료: {extracted_file_path}")
            return extracted_file_path
            
        except zipfile.BadZipFile:
            logger.error(f"[KisMasterService] 잘못된 압축 파일: {zip_file_path}")
            zip_file_path.unlink(missing_ok=True)
            return None
        except Exception as e:
            logger.error(f"[KisMasterService] 압축 해제 중 오류: {e}")
            return None

    def _parse_master_file(self, file_path: Path, market: str) -> int:
        """
        마스터 파일을 파싱하여 메모리 캐시에 저장합니다.
        샘플 코드 방식을 사용하여 파일을 part1과 part2로 나누어 파싱합니다.
        
        Args:
            file_path: 마스터 파일 경로
            market: 시장 구분 ("KOSPI" 또는 "KOSDAQ")
            
        Returns:
            int: 파싱된 종목 수
        """
        if not file_path.exists():
            logger.error(f"[KisMasterService] 마스터 파일이 존재하지 않음: {file_path}")
            return 0
        
        ticker_suffix = ".KS" if market == "KOSPI" else ".KQ"
        
        # 시장에 따라 다른 필드 구조 사용
        if market == "KOSPI":
            part2_suffix = 228  # 코스피는 뒷부분 228자리
            part1_columns = ['단축코드', '표준코드', '한글명']
            field_specs = self.PART2_FIELD_SPECS_KOSPI
            part2_columns = self.PART2_COLUMNS_KOSPI
            base_price_col = '기준가'
            margin_rate_col = '증거금비율'
            listing_date_col = '상장일자'
            roe_col = 'ROE'
            sector_col = '지수업종대분류'
        else:  # KOSDAQ
            part2_suffix = 222  # 코스닥은 뒷부분 222자리
            part1_columns = ['단축코드', '표준코드', '한글종목명']
            field_specs = self.PART2_FIELD_SPECS_KOSDAQ
            part2_columns = self.PART2_COLUMNS_KOSDAQ
            base_price_col = '주식 기준가'
            margin_rate_col = '증거금 비율'
            listing_date_col = '주식 상장 일자'
            roe_col = 'ROE(자기자본이익률)'
            sector_col = '지수업종 대분류 코드'
        
        try:
            # 임시 파일 경로
            tmp_file1 = self.cache_dir / f"{market}_part1.tmp"
            tmp_file2 = self.cache_dir / f"{market}_part2.tmp"
            
            # 파일을 part1과 part2로 분리
            logger.info(f"[KisMasterService] {market} 마스터 파일 파싱 시작: {file_path}")
            
            with open(file_path, "r", encoding="cp949") as f:
                wf1 = open(tmp_file1, "w", encoding="utf-8")
                wf2 = open(tmp_file2, "w", encoding="utf-8")
                
                for row in f:
                    # part1: 앞부분 (단축코드, 표준코드, 한글명)
                    rf1 = row[0:len(row) - part2_suffix]
                    rf1_1 = rf1[0:9].rstrip()
                    rf1_2 = rf1[9:21].rstrip()
                    rf1_3 = rf1[21:].strip()
                    wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')
                    
                    # part2: 뒷부분 (나머지 필드들)
                    rf2 = row[-part2_suffix:]
                    wf2.write(rf2)
                
                wf1.close()
                wf2.close()
            
            # Part1을 CSV로 읽기
            df1 = pd.read_csv(tmp_file1, header=None, names=part1_columns, encoding='utf-8')
            
            # Part2를 고정 폭으로 읽기
            df2 = pd.read_fwf(tmp_file2, widths=field_specs, names=part2_columns, encoding='utf-8')
            
            # 두 데이터프레임 병합
            df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)
            
            # 임시 파일 삭제
            tmp_file1.unlink(missing_ok=True)
            tmp_file2.unlink(missing_ok=True)
            
            # 데이터프레임을 순회하며 메모리 캐시에 저장
            count = 0
            for _, row in df.iterrows():
                try:
                    # 단축코드에서 종목코드 추출 (6자리)
                    short_code = str(row['단축코드']).strip()
                    if not short_code or len(short_code) < 6:
                        continue
                    
                    stock_code = short_code[:6]
                    if not stock_code.isdigit():
                        continue
                    
                    # 티커 생성
                    ticker = f"{stock_code}{ticker_suffix}"
                    
                    # 종목명 추출 (코스피는 '한글명', 코스닥은 '한글종목명')
                    name_col = '한글명' if market == "KOSPI" else '한글종목명'
                    name = str(row[name_col]).strip()
                    if not name or name == 'nan':
                        continue
                    
                    # 상세 정보 구성
                    detail = {
                        "name": name,
                        "sector_code": str(row.get(sector_col, '')).strip(),
                        "market": market,
                        "stock_code": stock_code,
                        "short_code": short_code,
                        "standard_code": str(row.get('표준코드', '')).strip(),
                        "base_price": str(row.get(base_price_col, '')).strip(),
                        "margin_rate": str(row.get(margin_rate_col, '')).strip(),
                        "listing_date": str(row.get(listing_date_col, '')).strip(),
                        "roe": str(row.get(roe_col, '')).strip(),
                    }
                    
                    # 매핑 저장
                    self._name_to_code[name] = ticker
                    self._code_to_detail[ticker] = detail
                    
                    count += 1
                    
                except Exception as e:
                    logger.warning(f"[KisMasterService] 행 파싱 중 오류: {e}")
                    continue
            
            logger.info(f"[KisMasterService] {market} 마스터 파일 파싱 완료: {count}개 종목")
            return count
            
        except Exception as e:
            logger.error(f"[KisMasterService] 마스터 파일 파싱 중 오류: {e}")
            return 0

    def load_master_data(self, force_reload: bool = False) -> bool:
        """
        마스터 데이터를 로드합니다.
        
        Args:
            force_reload: True이면 기존 캐시를 무시하고 재다운로드
            
        Returns:
            bool: 로드 성공 여부
        """
        if self._loaded and not force_reload:
            logger.info("[KisMasterService] 이미 로드된 마스터 데이터 사용")
            return True
        
        try:
            # KOSPI 마스터 파일 다운로드 및 압축 해제
            kospi_file = self._download_and_extract_master_file(
                self.KOSPI_MASTER_URLS,
                "kospi_code.zip",
                "kospi_code.mst"
            )
            
            # KOSDAQ 마스터 파일 다운로드 및 압축 해제
            kosdaq_file = self._download_and_extract_master_file(
                self.KOSDAQ_MASTER_URLS,
                "kosdaq_code.zip",
                "kosdaq_code.mst"
            )
            
            # 파싱
            kospi_count = 0
            kosdaq_count = 0
            
            if kospi_file:
                kospi_count = self._parse_master_file(kospi_file, "KOSPI")
            
            if kosdaq_file:
                kosdaq_count = self._parse_master_file(kosdaq_file, "KOSDAQ")
            
            total_count = kospi_count + kosdaq_count
            
            if total_count > 0:
                self._loaded = True
                logger.info(f"[KisMasterService] 마스터 데이터 로드 완료: 총 {total_count}개 종목 (KOSPI: {kospi_count}, KOSDAQ: {kosdaq_count})")
                return True
            else:
                logger.warning("[KisMasterService] 마스터 데이터 로드 실패: 파싱된 종목이 없음")
                return False
                
        except Exception as e:
            logger.error(f"[KisMasterService] 마스터 데이터 로드 중 오류: {e}")
            return False

    def get_ticker_by_name(self, name: str) -> Optional[str]:
        """
        종목명으로 티커를 찾습니다.
        
        Args:
            name: 종목명 (예: "삼성전자")
            
        Returns:
            Optional[str]: 티커 (예: "005930.KS") 또는 None
        """
        if not self._loaded:
            logger.warning("[KisMasterService] 마스터 데이터가 로드되지 않음")
            return None
        
        if not name or not name.strip():
            return None
        
        name = name.strip()
        
        # 1. 정확한 매칭
        ticker = self._name_to_code.get(name)
        if ticker:
            return ticker
        
        # 2. 공백 제거 후 정확한 매칭
        name_no_space = name.replace(" ", "")
        ticker = self._name_to_code.get(name_no_space)
        if ticker:
            return ticker
        
        # 3. 부분 매칭 (대소문자 무시, 한글은 대소문자 구분 없음)
        # 한글은 대소문자가 없으므로 정확히 매칭
        for stock_name, stock_ticker in self._name_to_code.items():
            if stock_name == name:
                return stock_ticker
            # 공백 제거 후 비교
            if stock_name.replace(" ", "") == name_no_space:
                return stock_ticker
        
        # 4. 포함 검색 (정확한 매칭이 없을 경우)
        # 가장 긴 매칭을 우선 선택
        best_match = None
        best_length = 0
        
        for stock_name, stock_ticker in self._name_to_code.items():
            if name in stock_name:
                if len(stock_name) > best_length:
                    best_match = stock_ticker
                    best_length = len(stock_name)
            elif stock_name in name:
                if len(name) > best_length:
                    best_match = stock_ticker
                    best_length = len(name)
        
        return best_match

    def get_detail_by_ticker(self, ticker: str) -> Optional[Dict]:
        """
        티커로 상세 정보를 가져옵니다.
        
        Args:
            ticker: 티커 (예: "005930.KS")
            
        Returns:
            Optional[Dict]: 상세 정보 딕셔너리 또는 None
        """
        if not self._loaded:
            return None
        
        return self._code_to_detail.get(ticker.upper())

    def get_name_by_ticker(self, ticker: str) -> Optional[str]:
        """
        티커로 종목명을 가져옵니다.
        
        Args:
            ticker: 티커 (예: "005930.KS")
            
        Returns:
            Optional[str]: 종목명 또는 None
        """
        detail = self.get_detail_by_ticker(ticker)

        if detail:
            return detail.get("name")
        return None

    def search_tickers(self, query: str, max_results: int = 5) -> List[Tuple[str, str]]:
        """
        종목명으로 티커를 검색합니다 (부분 매칭).
        
        Args:
            query: 검색어
            max_results: 최대 결과 수
            
        Returns:
            List[Tuple[str, str]]: [(종목명, 티커), ...] 리스트
        """
        if not self._loaded:
            return []
        
        query_upper = query.upper()
        results = []
        
        for stock_name, ticker in self._name_to_code.items():
            if query_upper in stock_name.upper():
                results.append((stock_name, ticker))
                if len(results) >= max_results:
                    break
        return results
