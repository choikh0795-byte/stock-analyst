# Stock Analysis API Server

FastAPI 기반 주식 분석 API 서버입니다. **Layered Architecture (계층화 아키텍처)**로 설계되었습니다.

## 프로젝트 구조

```
server/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # 라우터 (요청/응답 처리)
│   │       │   └── stocks.py
│   │       └── __init__.py
│   ├── core/
│   │   ├── config.py           # 설정 및 환경변수 관리
│   │   └── dependencies.py     # Dependency Injection
│   ├── schemas/
│   │   └── stock.py            # Pydantic 모델 (DTO)
│   ├── services/
│   │   ├── stock_service.py    # 주식 정보 비즈니스 로직
│   │   └── ai_service.py       # AI 분석 비즈니스 로직
│   ├── main.py                 # FastAPI 앱 초기화
│   └── __init__.py
├── run.py                      # 서버 실행 스크립트
└── requirements.txt
```

## 아키텍처 특징

- **Layered Architecture**: 관심사의 분리로 유지보수성 향상
- **Dependency Injection**: 테스트 용이성 및 느슨한 결합
- **Class-based Services**: 객체지향적 설계
- **Pydantic Schemas**: 타입 안정성 및 데이터 검증

## 설치 방법

```bash
# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```
OPENAI_API_KEY=your_api_key_here
```

## 실행 방법

```bash
# 방법 1: run.py 사용 (권장)
python run.py

# 방법 2: uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 방법 3: app.main 모듈 직접 실행
python -m app.main
```

서버는 `http://localhost:8000`에서 실행됩니다.

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

## API 엔드포인트

- `GET /` - API 정보
- `GET /api/v1/stock/{ticker}` - 주식 정보 조회
- `POST /api/v1/stock/analyze` - 주식 정보 + AI 분석
- `POST /api/v1/stock/analyze-ai` - AI 분석만

## 코드 구조 설명

### 1. Core Layer (`app/core/`)
- **config.py**: 환경변수 및 애플리케이션 설정 관리
- **dependencies.py**: FastAPI의 Dependency Injection을 통한 서비스 인스턴스 생성

### 2. Schema Layer (`app/schemas/`)
- Pydantic 모델로 요청/응답 데이터 구조 정의
- 데이터 검증 및 직렬화 담당

### 3. Service Layer (`app/services/`)
- 비즈니스 로직을 처리하는 클래스들
- `StockService`: yfinance를 사용한 주식 정보 조회
- `AIService`: OpenAI를 사용한 주식 분석

### 4. API Layer (`app/api/v1/endpoints/`)
- FastAPI 라우터로 HTTP 요청 처리
- Service 클래스를 주입받아 사용
- 요청 검증 및 응답 변환만 담당

## 테스트 작성 예시

Dependency Injection 덕분에 테스트 작성이 쉽습니다:

```python
from app.services.stock_service import StockService

def test_get_stock_info():
    service = StockService()
    data, news = service.get_stock_info("AAPL")
    assert data["symbol"] == "AAPL"
```

