"""
KIS API 업종 코드 매핑 상수 모듈

한국 주식 시장의 업종 코드를 사람이 읽을 수 있는 업종명으로 매핑하는 상수를 정의합니다.
"""

# 한국 주식 시장의 주요 업종 코드 매핑
# 실제 KIS API 문서를 참조하여 정확한 매핑 테이블을 작성해야 합니다.
SECTOR_CODE_MAPPING = {
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

# KIS API 필드명 매핑
# KIS API에서 사용하는 필드명과 표준 필드명 매핑
FIELD_NAME_MAPPING = {
    # 가격 정보
    "stck_prpr": "current_price",  # 현재가
    "prdy_clpr": "previous_close",  # 전일 종가
    "stck_hgpr": "fifty_two_week_high",  # 52주 최고가
    "stck_lwpr": "fifty_two_week_low",  # 52주 최저가

    # 시가총액 및 재무 지표
    "hts_avls": "market_cap",  # 시가총액
    "per": "pe_ratio",  # PER (주가수익비율)
    "pbr": "pb_ratio",  # PBR (주가순자산비율)
    "eps": "eps",  # EPS (주당순이익)
    "dvyd": "dividend_yield",  # 배당수익률

    # 종목명
    "hts_kor_isnm": "name",  # 한글 종목명
}

# 다양한 필드명 후보 리스트 (방어 로직에서 사용)
# ROE 필드명 후보
ROE_FIELD_CANDIDATES = ["roe", "ROE", "rtn_on_equity", "rtn_on_eqty", "return_on_equity"]

# 배당수익률 필드명 후보
DIVIDEND_YIELD_FIELD_CANDIDATES = ["dvyd", "dividend_yield", "dividendYield", "배당수익률", "배당률"]

# 목표가 필드명 후보
TARGET_PRICE_FIELD_CANDIDATES = [
    "target_price", "targetPrice", "목표가", "tgt_prc", "tgt_prc_amt",
    "analyst_target_price", "mean_target_price"
]

# 당기순이익 필드명 후보
NET_INCOME_FIELD_CANDIDATES = [
    "net_income", "netIncome", "당기순이익", "thstrm_ntin",
    "thstrm_ntin_amt", "frm_trm_ntin", "frm_trm_ntin_amt"
]

# 자본총계 필드명 후보
EQUITY_FIELD_CANDIDATES = [
    "total_equity", "totalEquity", "자본총계", "eqty_tot",
    "eqty_tot_amt", "eqty", "eqty_amt"
]

# 주당배당금(DPS) 필드명 후보
DPS_FIELD_CANDIDATES = ["dps", "DPS", "dividend_per_share", "주당배당금", "stck_dvdn_amt", "stck_dvdn"]

# 섹터 필드명 후보
SECTOR_FIELD_CANDIDATES = [
    "bstp_nm",  # 업종명
    "bstp_kor_nm",  # 업종 한글명
    "itms_mrkt_cls_code",  # 시장 구분 코드
    "sector",  # 섹터
    "sector_name",  # 섹터명
    "업종명",
    "업종",
]

# 산업 필드명 후보
INDUSTRY_FIELD_CANDIDATES = [
    "induty_nm",  # 산업명
    "induty_kor_nm",  # 산업 한글명
    "industry",  # 산업
    "industry_name",  # 산업명
    "산업명",
    "산업",
]

# 업종 코드 필드명 후보
SECTOR_CODE_FIELD_CANDIDATES = ["bstp_cd", "sector_code", "업종코드"]
