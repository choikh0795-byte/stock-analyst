# Autocomplete Service (자동완성 서비스)

## 개요

이 모듈은 **자산 자동완성 검색 기능을 완전한 메모리 기반으로 제공**합니다.

**핵심 원칙**: **요청 처리 시 DB 접근 절대 금지 (0% 가능성)**

## DB 접근 정책

### ✅ DB 접근 허용 (서버 startup 시에만)
- **시점**: `main.py` lifespan 함수에서 서버 시작 시
- **목적**: `asset_search_index` 테이블 데이터를 메모리에 로드
- **메서드**: `AutocompleteMemoryIndex.load_from_db(db: Session)`

### ❌ DB 접근 절대 금지 (API 요청 처리 중)
- **시점**: 모든 자동완성 API 요청 처리 중
- **이유**: 성능 최적화 (메모리 검색 >> DB 쿼리)
- **보장**: `AutocompleteService`는 DB Session을 의존성으로 받지 않음

## 모듈 구성

```
autocomplete/
├── __init__.py              # 모듈 export
├── autocomplete_service.py  # 자동완성 검색 Service (메모리만 사용)
├── memory_index.py          # 메모리 인덱스 (Singleton)
├── index_builder.py         # 검색 인덱스 구축 (배치 작업용)
└── README.md                # 이 파일
```

### 1. `AutocompleteService`
- **역할**: 자동완성 검색 로직
- **의존성**: `AutocompleteMemoryIndex` (메모리만)
- **DB 접근**: 절대 없음 (❌)
- **검색 타입**:
  - 초성: "ㅅㅅㅈㅈ" → 삼성전자
  - 한글: "삼성" → 삼성전자, 삼성물산, ...
  - 영문: "aapl" → AAPL

### 2. `AutocompleteMemoryIndex`
- **역할**: 메모리 인덱스 관리 (Singleton)
- **DB 접근**: `load_from_db()` 메서드에서만 (startup 시)
- **데이터 구조**:
  ```python
  {
      "id": int,
      "ticker": str,
      "name_kr": str,
      "name_en": str,
      "initial_kr": str,  # 초성 ("삼성전자" → "ㅅㅅㅈㅈ")
      "asset_type": str,  # STOCK_KR, STOCK_US, ETF
      "exchange": str,
      "search_tokens": List[str]
  }
  ```

### 3. `AssetSearchIndexBuilder`
- **역할**: DB 검색 인덱스 구축 (배치 작업용)
- **사용 시점**: 데이터 초기 로딩 또는 갱신 시
- **DB 접근**: 있음 (✅) - 배치 작업이므로 허용

## API 사용법

### Endpoint
```
GET /api/v1/assets/search?q={query}&limit={limit}
```

### Request
```bash
curl "http://localhost:8000/api/v1/assets/search?q=삼성&limit=10"
```

### Response
```json
{
  "results": [
    {
      "id": 1,
      "ticker": "005930.KS",
      "name_kr": "삼성전자",
      "name_en": "Samsung Electronics",
      "asset_type": "STOCK_KR",
      "exchange": "KRX",
      "country": "KR",
      "currency": "KRW"
    }
  ],
  "total": 1
}
```

## 일반 검색과의 차이

| 항목 | 자동완성 (이 모듈) | 일반 검색 (StockProvider) |
|------|-------------------|-------------------------|
| **Endpoint** | `GET /api/v1/assets/search` | `POST /api/v1/stock/search` |
| **검색 방식** | Prefix 검색 (메모리 기반) | 정확한 종목명→티커 변환 |
| **DB 접근** | 절대 없음 (❌) | 가능 (✅) |
| **데이터 소스** | 메모리 인덱스 | KisMasterService, yfinance API |
| **성능** | 매우 빠름 (~1ms) | 느림 (네트워크 지연) |
| **사용 사례** | 검색창 실시간 자동완성 | 정확한 티커 변환 |
| **결과 개수** | 제한 (limit 파라미터) | 1개 (정확한 매칭) |

## 확장 가이드

### 우선순위 로직 추가
자동완성 결과에 우선순위(인기순, 거래대금 등)를 추가하려면:

1. **메모리 인덱스에 필드 추가**:
   ```python
   # memory_index.py
   self._assets.append({
       ...
       "popularity_score": asset.popularity_score,  # 새 필드
       "trading_volume": asset.trading_volume,      # 새 필드
   })
   ```

2. **Service에서 정렬**:
   ```python
   # autocomplete_service.py
   def search(self, query: str, limit: int) -> List[Dict]:
       results = self._search_by_ticker(query, limit * 2)  # 더 많이 조회

       # 우선순위 정렬 (인기순)
       results.sort(
           key=lambda x: x.get("popularity_score", 0),
           reverse=True
       )

       return results[:limit]  # limit만큼만 반환
   ```

### Trie 자료구조 도입 (성능 최적화)
현재는 선형 탐색 (O(n))이지만, Trie를 사용하면 O(m) (m=query 길이)로 개선 가능:

```python
# memory_index.py
from pygtrie import CharTrie

class AutocompleteMemoryIndex:
    def __init__(self):
        self._trie = CharTrie()  # Prefix 검색 최적화

    def load_from_db(self, db: Session):
        for asset in results:
            # Ticker로 Trie 구성
            self._trie[asset.ticker.lower()] = asset

            # Name으로도 Trie 구성
            if asset.name_kr:
                self._trie[asset.name_kr.lower()] = asset
```

## 테스트

### Unit Test 예시
```python
def test_autocomplete_no_db_access():
    """자동완성 Service가 DB에 접근하지 않는지 확인"""
    memory_index = AutocompleteMemoryIndex()
    memory_index._assets = [
        {"ticker": "AAPL", "name_en": "Apple", ...}
    ]
    memory_index._initialized = True

    service = AutocompleteService(memory_index)

    # DB Session을 전달하지 않음 (타입 체크로 보장)
    results = service.search("AAP", limit=5)

    assert len(results) > 0
    assert results[0]["ticker"] == "AAPL"
```

## 주의사항

### ⚠️ DB Session을 절대로 주입하지 마세요!
```python
# ❌ 잘못된 예시 - DB Session 주입
class AutocompleteService:
    def __init__(self, memory_index, db: Session):  # ❌ 금지!
        self.db = db
```

```python
# ✅ 올바른 예시 - 메모리 인덱스만 주입
class AutocompleteService:
    def __init__(self, memory_index: AutocompleteMemoryIndex):  # ✅
        self.memory_index = memory_index
```

### ⚠️ 메모리 인덱스 갱신
메모리 인덱스는 서버 startup 시에만 로드되므로, 실시간 데이터 갱신이 필요하면:
1. 서버 재시작 (간단하지만 다운타임 발생)
2. 별도 갱신 API 추가 (hot reload)

## 아키텍처 다이어그램

```
┌────────────────────────────────────────────────────────────┐
│                   서버 Startup (main.py)                     │
│                                                              │
│  1. AutocompleteMemoryIndex.load_from_db(db)                │
│     - DB 접근 ✅ (유일한 DB 접근 시점)                        │
│     - asset_search_index 테이블 → 메모리 로드                │
│                                                              │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                 API 요청 처리 (요청마다)                      │
│                                                              │
│  GET /api/v1/assets/search?q=삼성                            │
│           │                                                  │
│           ▼                                                  │
│  AutocompleteService.search()                                │
│           │                                                  │
│           ▼                                                  │
│  AutocompleteMemoryIndex.get_all_assets()                    │
│           │                                                  │
│           ▼                                                  │
│  메모리 검색 (DB 접근 ❌)                                     │
│           │                                                  │
│           ▼                                                  │
│  결과 반환 (JSON)                                            │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

## 관련 파일

### Backend
- `app/api/v1/endpoints/assets.py` - Autocomplete API endpoint
- `app/core/dependencies.py` - `get_autocomplete_service()` DI 함수
- `app/main.py` - Startup 시 메모리 인덱스 로딩

### Database
- `app/models/asset_search_index.py` - DB 모델
- `asset_search_index` 테이블 (PostgreSQL)

### Frontend
- 클라이언트에서는 `/api/v1/assets/search`를 호출하여 자동완성 사용

## 문의

이 모듈에 대한 질문이나 제안사항은 이슈를 등록해주세요.
