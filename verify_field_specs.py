#!/usr/bin/env python3
"""
KIS 마스터 파일 필드 스펙 검증
"""

# KOSPI Part2 필드 (kis_master_service.py에서 복사)
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

# KOSDAQ Part2 필드 (kis_master_service.py에서 복사)
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


def verify_specs():
    """필드 스펙 검증"""
    print("="*80)
    print("KIS 마스터 파일 필드 스펙 검증")
    print("="*80)

    # KOSPI 검증
    kospi_sum = sum(PART2_FIELD_SPECS_KOSPI)
    kospi_count = len(PART2_FIELD_SPECS_KOSPI)
    kospi_expected = 228

    print(f"\n[KOSPI]")
    print(f"  필드 개수: {kospi_count}")
    print(f"  필드 합계: {kospi_sum}")
    print(f"  예상 길이: {kospi_expected}")
    print(f"  차이: {kospi_sum - kospi_expected}")

    if kospi_sum == kospi_expected:
        print(f"  ✓ KOSPI 필드 스펙 정확함")
    else:
        print(f"  ✗ KOSPI 필드 스펙 불일치! ({kospi_sum} != {kospi_expected})")

    # KOSDAQ 검증
    kosdaq_sum = sum(PART2_FIELD_SPECS_KOSDAQ)
    kosdaq_count = len(PART2_FIELD_SPECS_KOSDAQ)
    kosdaq_expected = 222

    print(f"\n[KOSDAQ]")
    print(f"  필드 개수: {kosdaq_count}")
    print(f"  필드 합계: {kosdaq_sum}")
    print(f"  예상 길이: {kosdaq_expected}")
    print(f"  차이: {kosdaq_sum - kosdaq_expected}")

    if kosdaq_sum == kosdaq_expected:
        print(f"  ✓ KOSDAQ 필드 스펙 정확함")
    else:
        print(f"  ✗ KOSDAQ 필드 스펙 불일치! ({kosdaq_sum} != {kosdaq_expected})")

    # 상세 비교
    print(f"\n{'='*80}")
    print("상세 분석")
    print(f"{'='*80}")

    print(f"\nKOSPI 필드 분포:")
    print(f"  1자리 필드: {PART2_FIELD_SPECS_KOSPI.count(1)}개")
    print(f"  2자리 필드: {PART2_FIELD_SPECS_KOSPI.count(2)}개")
    print(f"  3자리 필드: {PART2_FIELD_SPECS_KOSPI.count(3)}개")
    print(f"  4자리 필드: {PART2_FIELD_SPECS_KOSPI.count(4)}개")
    print(f"  5자리 필드: {PART2_FIELD_SPECS_KOSPI.count(5)}개")
    print(f"  9자리 필드: {PART2_FIELD_SPECS_KOSPI.count(9)}개")

    print(f"\nKOSDAQ 필드 분포:")
    print(f"  1자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(1)}개")
    print(f"  2자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(2)}개")
    print(f"  3자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(3)}개")
    print(f"  4자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(4)}개")
    print(f"  5자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(5)}개")
    print(f"  7자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(7)}개")
    print(f"  8자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(8)}개")
    print(f"  9자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(9)}개")
    print(f"  12자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(12)}개")
    print(f"  15자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(15)}개")
    print(f"  21자리 필드: {PART2_FIELD_SPECS_KOSDAQ.count(21)}개")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    verify_specs()
