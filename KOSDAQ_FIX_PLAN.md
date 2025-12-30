# KOSDAQ 마스터 파일 파싱 오류 수정 플랜

## 📊 문제 분석

### 현재 상황
```
KOSDAQ 필드 스펙:
  - 필드 개수: 66개
  - 필드 합계: 223자
  - 실제 Part2 길이: 222자
  - 컬럼 개수: 64개

오류:
  ✗ 필드 개수 (66) != 컬럼 개수 (64) → 2개 차이
  ✗ 필드 합계 (223) != Part2 길이 (222) → 1자리 초과
```

### 근본 원인
`pd.read_fwf(widths=field_specs, names=part2_columns)` 호출 시:
- `widths` (field_specs): 66개 → 223자
- `names` (part2_columns): 64개
- 실제 데이터: 222자

**결과**: pandas가 "Length of colspecs must match length of names" 오류 발생

## 🎯 수정 방안 (3가지 옵션)

### Option 1: 필드 스펙 조정 (권장) ⭐⭐⭐⭐⭐

**방법**: 필드 스펙을 정확한 구조로 수정

#### 분석 필요 사항
1. line 88의 마지막 필드 중 일부가 잘못됨
   - 현재: `1, 1, 1, 1, 1` (5개)
   - 예상: `1, 1, 1` (3개) 또는 `2, 1, 1` (3개)

2. 또는 line 83의 필드 길이 조정
   - 현재: `2, 2, 2, 3, 1` (합계 10)
   - 가능: `2, 2, 2, 4, 1` (합계 11)

#### 작업 단계
1. **임시 수정으로 파싱 성공 확인**
   ```python
   # Option A: 마지막 필드 2개 제거
   PART2_FIELD_SPECS_KOSDAQ = [
       # ... (line 75-87 동일)
       1, 1, 1  # 회사신용한도초과여부, 담보대출가능여부, 대주가능여부 (5개 → 3개)
   ]

   # Option B: 증거금 비율 필드 조정 + 마지막 2개 제거
   PART2_FIELD_SPECS_KOSDAQ = [
       # ... line 83 수정
       2, 2, 2, 4, 1,  # 락구분, 액면가변경, 증자, 증거금비율(3→4), 신용주문
       # ... line 88 수정
       1, 1, 1  # (5개 → 3개)
   ]
   ```

2. **컬럼 이름 확인 및 매칭**
   ```python
   # 누락된 컬럼이 있는지 확인
   # line 105-106의 컬럼 이름과 필드를 정확히 매칭
   ```

3. **테스트**
   - 카카오(035720.KQ) 검색 확인
   - 파싱된 데이터 샘플 확인
   - 필드가 올바르게 매핑되었는지 검증

#### 장점
- 근본 원인 해결
- 성능 최적 (O(1) 검색)
- 네이버 폴백 불필요

#### 단점
- 정확한 필드 구조 파악 필요
- 테스트 필요

---

### Option 2: 컬럼 2개 추가 (임시 해결) ⭐⭐⭐

**방법**: 필드 스펙은 그대로 두고, 컬럼 이름 2개 추가

```python
PART2_COLUMNS_KOSDAQ = [
    # ... 기존 64개 ...
    '예비필드1', '예비필드2'  # 임시로 추가
]
```

#### 작업 단계
1. 컬럼 2개 추가
2. 파싱 성공 확인
3. 파싱된 데이터 확인하여 실제 필드 이름 찾기
4. 필드 이름 업데이트

#### 장점
- 빠른 수정
- 파싱 데이터로 역추적 가능

#### 단점
- 임시 방편
- 필드 이름이 부정확
- 나중에 재수정 필요

---

### Option 3: 파싱 오류 무시 + 네이버 100% 사용 ⭐⭐⭐⭐

**방법**: KOSDAQ 마스터 파일 파싱을 포기하고 네이버 API만 사용

```python
def _parse_master_file(self, file_path: Path, market: str) -> int:
    # KOSDAQ는 파싱 건너뛰기
    if market == "KOSDAQ":
        logger.info(f"[KisMasterService] KOSDAQ는 네이버 API 사용, 파싱 스킵")
        return 0

    # KOSPI만 파싱
    # ...
```

#### 장점
- 즉시 적용 가능
- 유지보수 간편
- 네이버 API가 항상 최신 데이터 제공

#### 단점
- KOSDAQ 검색이 느림 (200ms vs 1ms)
- 네트워크 의존

---

## 🚀 권장 실행 플랜

### Phase 1: 임시 수정 (지금 당장)
```python
# Option 2 적용: 컬럼 2개 추가
PART2_COLUMNS_KOSDAQ = [
    # ... 기존 64개 ...
    '예비필드1', '예비필드2'
]
```

### Phase 2: 데이터 확인 (파싱 후)
```python
# 파싱된 데이터 샘플 출력
service = KisMasterService()
service.load_master_data()
detail = service.get_detail_by_ticker("035720.KQ")
print(detail)  # 필드 확인
```

### Phase 3: 정확한 수정 (데이터 분석 후)
- 파싱된 데이터에서 '예비필드1', '예비필드2'의 실제 값 확인
- KIS 문서와 비교하여 정확한 필드 이름 찾기
- 필드 스펙 및 컬럼 이름 최종 수정

---

## 📋 즉시 실행 코드

```python
# server/app/services/stock/kis_master_service.py
# Line 91-106 수정

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
    '기준년월', '전일기준 시가총액 (억)', '그룹사 코드', '회사신용한도초과여부', '담보대출가능여부', '대주가능여부',
    '예비필드1', '예비필드2'  # 임시 추가 (나중에 정확한 이름으로 변경)
]
```

---

## ✅ 검증 방법

```python
# 1. 필드 개수 확인
assert len(PART2_FIELD_SPECS_KOSDAQ) == len(PART2_COLUMNS_KOSDAQ)
assert len(PART2_FIELD_SPECS_KOSDAQ) == 66
assert sum(PART2_FIELD_SPECS_KOSDAQ) == 223

# 2. 파싱 테스트
service = KisMasterService()
success = service.load_master_data()
assert success == True

# 3. KOSDAQ 종목 검색
ticker = service.get_ticker_by_name("카카오")
assert ticker == "035720.KQ"

detail = service.get_detail_by_ticker("035720.KQ")
assert detail["name"] == "카카오"
assert detail["market"] == "KOSDAQ"
```

---

## 🔍 다음 단계

1. **즉시**: Option 2 적용 (컬럼 2개 추가)
2. **테스트**: KOSDAQ 종목 검색 확인
3. **분석**: 파싱된 '예비필드1', '예비필드2' 데이터 확인
4. **최종**: 정확한 필드 이름으로 업데이트

---

**작성일**: 2025-12-30
**작성자**: Claude AI Assistant
