# Search Index Guide

## 개요

이 문서는 자산 검색 인덱스 시스템의 구조와 운영 방법을 설명합니다.

## 시스템 구조

### 1. 데이터 소스

- **한국 주식**: KIS API 마스터 파일 (KOSPI, KOSDAQ)
- **미국 주식**: KIS API 마스터 파일 (NASDAQ, NYSE, AMEX)

### 2. 핵심 컴포넌트

#### KisMasterService (`app/services/stock/kis_master_service.py`)
- KIS 마스터 파일 다운로드 및 파싱
- 한국어/영어 종목명 매핑 제공
- 메서드:
  - `load_master_data(force_reload, include_us)`: 마스터 데이터 로드
  - `get_all_stocks()`: 전체 종목 정보 반환 (인덱싱용)

#### AssetSearchIndexBuilder (`app/services/search/index_builder.py`)
- 검색 인덱스 생성 및 업데이트
- Bulk upsert 지원 (1,000개 단위)
- 자동 토큰 생성:
  - 한글 초성 추출
  - Prefix 토큰 생성 (예: '엔비디아' → ['엔', '엔비', '엔비디', '엔비디아'])

#### AssetSearchIndex 모델 (`app/models/asset_search_index.py`)
- 검색 인덱스 테이블 정의
- Unique constraint: (ticker, asset_type)
- GIN 인덱스: search_tokens (빠른 배열 검색)

### 3. 토큰 생성 로직

#### Prefix 토큰 (`app/utils/search_tokens.py`)
```python
build_prefix_tokens("엔비디아")
# 결과: ['엔', '엔비', '엔비디', '엔비디아']

build_prefix_tokens("NVDA")
# 결과: ['n', 'nv', 'nvd', 'nvda']
```

#### 초성 추출 (`app/utils/hangul.py`)
```python
extract_initial_consonants("엔비디아")
# 결과: 'ㅇㅂㄷㅇ'

extract_initial_consonants("삼성전자")
# 결과: 'ㅅㅅㅈㅈ'
```

## 인덱싱 프로세스

### 1. 초기 설정

#### 데이터베이스 마이그레이션

기존 테이블이 있는 경우, unique constraint를 추가해야 합니다:

```bash
cd server
psql $DATABASE_URL -f migrations/add_unique_constraint_asset_search_index.sql
```

또는 새 테이블 생성:

```bash
python run_indexing.py --force
```

### 2. 전체 인덱싱

#### 한국 + 미국 주식 모두 인덱싱

```bash
cd server
python run_indexing.py --force
```

#### 한국 주식만 인덱싱

```bash
python run_indexing.py --force --kr-only
```

#### 미국 주식만 인덱싱

```bash
python run_indexing.py --force --us-only
```

### 3. 증분 업데이트

기존 인덱스를 유지하면서 업데이트:

```bash
python run_indexing.py
```

### 4. 실행 로그 예시

```
2026-01-06 10:00:00 - INFO - [RunIndexing] 데이터베이스 테이블 생성 중...
2026-01-06 10:00:01 - INFO - [RunIndexing] KIS 마스터 데이터 로드 중 (include_us=True)...
2026-01-06 10:00:05 - INFO - [KisMasterService] KOSPI 마스터 파일 파싱 완료: 950개 종목
2026-01-06 10:00:08 - INFO - [KisMasterService] KOSDAQ 마스터 파일 파싱 완료: 1,600개 종목
2026-01-06 10:00:12 - INFO - [KisMasterService] NASDAQ 마스터 파일 파싱 완료: 3,500개 종목
2026-01-06 10:00:15 - INFO - [KisMasterService] NYSE 마스터 파일 파싱 완료: 2,800개 종목
2026-01-06 10:00:18 - INFO - [KisMasterService] AMEX 마스터 파일 파싱 완료: 300개 종목
2026-01-06 10:00:18 - INFO - [KisMasterService] 마스터 데이터 로드 완료: 총 9,150개 종목
2026-01-06 10:00:20 - INFO - [AssetSearchIndexBuilder] 인덱싱 시작: 9,150개 항목
2026-01-06 10:00:25 - INFO - [AssetSearchIndexBuilder] 배치 처리 완료: 1000/9150 (1000개)
2026-01-06 10:00:30 - INFO - [AssetSearchIndexBuilder] 배치 처리 완료: 2000/9150 (1000개)
...
2026-01-06 10:01:00 - INFO - [AssetSearchIndexBuilder] 인덱싱 완료: 9,150개 항목
2026-01-06 10:01:00 - INFO - [RunIndexing] 인덱싱 완료: 9,150개 종목 (소요 시간: 60.00초)
2026-01-06 10:01:00 - INFO - [RunIndexing] 인덱스 통계: 전체=9150, 한국주식=2550, 미국주식=6600, ETF=0
```

## 검색 동작 방식

### 1. 검색 타입 자동 감지

AssetSearchService는 입력된 쿼리를 분석하여 검색 타입을 결정합니다:

- **초성만**: `ㅅㅅ` → `initial_kr LIKE 'ㅅㅅ%'`
- **한글 음절**: `삼성` → `name_kr LIKE '삼성%'`
- **영문/숫자**: `nvda` → `ticker LIKE 'nvda%'` 또는 `search_tokens @> ['nvda']`

### 2. 우선순위 정렬

검색 결과는 다음 우선순위로 정렬됩니다:

1. **완전일치** (EXACT): `엔비디아` = `엔비디아`
2. **접두사 일치** (PREFIX): `엔비디아`가 `엔비`로 시작
3. **토큰 일치** (TOKEN): `search_tokens`에 `엔비` 포함

### 3. 검색 예시

#### 한글 검색
```
입력: "엔비"
→ search_tokens에 "엔비" 포함된 종목 검색
→ 결과: "엔비디아" (NVDA)
```

#### 초성 검색
```
입력: "ㅅㅅ"
→ initial_kr LIKE 'ㅅㅅ%'
→ 결과: "삼성전자", "삼성SDI", ...
```

#### 영문 검색
```
입력: "app"
→ ticker LIKE 'app%' OR name_en LIKE 'app%' OR search_tokens @> ['app']
→ 결과: "Apple Inc." (AAPL), "Applied Materials" (AMAT), ...
```

## 성능 최적화

### 1. 인덱스

- **GIN 인덱스**: `search_tokens` 배열 검색용
- **복합 인덱스**: `(asset_type, is_active)` 필터링용
- **Unique 인덱스**: `(ticker, asset_type)` upsert용

### 2. Bulk Upsert

- 1,000개 단위로 배치 처리
- PostgreSQL의 `INSERT ... ON CONFLICT DO UPDATE` 사용
- Fallback: 실패 시 개별 upsert

### 3. 캐싱

- KisMasterService는 마스터 데이터를 메모리에 캐싱
- `load_master_data()` 호출 시 한 번만 다운로드

## 문제 해결

### 1. Unique constraint violation

**증상**: `IntegrityError: duplicate key value violates unique constraint`

**원인**: (ticker, asset_type) 중복

**해결**:
```bash
# 마이그레이션 실행하여 중복 제거
psql $DATABASE_URL -f migrations/add_unique_constraint_asset_search_index.sql
```

### 2. 마스터 파일 다운로드 실패

**증상**: `[KisMasterService] 모든 URL에서 마스터 파일 다운로드 실패`

**원인**: 네트워크 문제 또는 URL 변경

**해결**:
- 네트워크 연결 확인
- KIS API 문서에서 최신 URL 확인
- `KisMasterService.KOSPI_MASTER_URLS` 등 업데이트

### 3. 인덱싱 속도 느림

**증상**: 인덱싱에 5분 이상 소요

**원인**: 배치 크기가 너무 작거나 DB 연결 느림

**해결**:
- `AssetSearchIndexBuilder.BATCH_SIZE` 증가 (1000 → 5000)
- 데이터베이스 인덱스 확인
- 데이터베이스 연결 풀 설정 확인

## API 사용 예시

### Python에서 검색 인덱스 사용

```python
from app.core.database import SessionLocal
from app.services.search.search_service import AssetSearchService

# 세션 생성
db = SessionLocal()

# 검색 서비스 초기화
search_service = AssetSearchService(db)

# 검색 수행
results = search_service.search("엔비", limit=10)

# 결과 출력
for result in results:
    print(f"{result['ticker']}: {result['name_kr']} ({result['name_en']})")

# 세션 종료
db.close()
```

### FastAPI 엔드포인트에서 사용

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.search.search_service import AssetSearchService

router = APIRouter()

@router.get("/search")
async def search_assets(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """자산 검색 API"""
    search_service = AssetSearchService(db)
    results = search_service.search(query, limit=limit)
    return {"results": results}
```

## 추가 리소스

- [KIS OpenAPI 문서](https://apiportal.koreainvestment.com/)
- [PostgreSQL GIN 인덱스](https://www.postgresql.org/docs/current/gin.html)
- [SQLAlchemy Bulk Operations](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html)

## 변경 이력

### 2026-01-06
- 초기 문서 작성
- 한국/미국 주식 통합 인덱싱 지원
- Bulk upsert 구현
- Prefix 토큰 생성 로직 추가
