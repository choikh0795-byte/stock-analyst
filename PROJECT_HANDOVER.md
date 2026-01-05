**[Project Handover: Stock Dashboard Service]**

현재 **React(Vite) + FastAPI** 기반의 AI 주식/ETF 분석 웹 서비스를 개발하여 배포 및 운영 중입니다.
기존 채팅에서 기본 기능 구현, 배포, DB 연동까지 마쳤으며, 이제부터 **기능 고도화 및 DB 확장** 단계로 넘어갑니다.

---

## 1. 현재 시스템 현황 (Current Status)

### Frontend (React + TypeScript + TailwindCSS)
- **프레임워크**: React 18.2.0 + Vite 5.0.0
- **언어**: TypeScript 5.2.2
- **스타일링**: 
  - TailwindCSS 3.4.1
  - PostCSS 8.4.35
  - Autoprefixer 10.4.17
- **상태 관리**: Zustand 5.0.9 (검색 상태, 로딩 메시지, 업데이트 로그 등)
- **애니메이션**: Framer Motion 12.23.26
- **아이콘**: Lucide React 0.559.0
- **HTTP 클라이언트**: Axios 1.6.0
- **디자인**: 
  - Bento Grid 스타일, 모바일 퍼스트
  - Modern Fintech 디자인 (토스, 로빈후드 스타일)
- **배포**: Vercel (예상)

### Backend (Python FastAPI)
- **프레임워크**: FastAPI 0.109.0+
- **서버**: Uvicorn 0.27.0+ (ASGI 서버)
- **언어**: Python 3.12+
- **데이터 검증**: Pydantic 2.6.0+
- **환경 변수**: python-dotenv 1.0.1+
- **HTTP 클라이언트**: 
  - httpx (내부 사용)
  - curl_cffi 0.5.10+ (KIS API용)
- **주식 데이터**: 
  - yfinance 0.2.40+ (Yahoo Finance)
  - FinanceDataReader (한국 종목 리스트)
- **AI 분석**: OpenAI API (GPT-4o-mini)
- **데이터베이스**: 
  - SQLAlchemy 2.0.0+ (ORM)
  - psycopg2-binary 2.9.0+ (PostgreSQL 드라이버)
- **테스팅**: pytest 7.4.0+
- **배포**: Render (Free Tier, 예상)

### Database (Supabase - PostgreSQL)
- **ORM**: SQLAlchemy 2.0.0+
- **연결**: psycopg2-binary
- **현재 기능**: 
  - 종목 분석 결과 캐싱 (`StockAnalysisLog` 테이블, 1시간 TTL)
  - 업데이트 로그 저장 (`UpdateLog` 테이블)

---

## 2. 프로젝트 핵심 규칙 (Cursor Rules 요약)

### 아키텍처 (Layered Architecture)
- **백엔드**: Router → Service → Provider/Calculator/Formatter
  - **Router Layer** (`app/api/v1/endpoints/`): 요청 수신 및 응답 반환만 담당
  - **Service Layer** (`app/services/`): 모든 비즈니스 로직을 Class로 캡슐화
  - **Provider Layer**: 외부 API 데이터 수집 (Strategy Pattern)
  - **Calculator Layer**: 결측치 방어 계산
  - **Formatter Layer**: 화면용 문자열 포맷팅
- **프론트엔드**: API Client Class 분리 (`src/api/stockApi.ts`)
  - 컴포넌트에서 직접 `axios` 사용 금지
  - Singleton Pattern으로 구현된 API 클라이언트 사용

### 객체지향 (OOP) - 필수 원칙
모든 비즈니스 로직은 **Class**로 캡슐화해야 합니다. 절차지향적 코드를 엄격히 지양합니다.

**백엔드 클래스 구조:**
- `StockService` (Facade Pattern): Provider, Calculator, Formatter를 통합
- `StockProvider` (Router/Context): 전략 패턴의 Context 역할
- `KisStockProvider`, `YahooStockProvider` (Concrete Strategy): BaseStockProvider 상속
- `StockCalculator`, `ETFCalculator`: 재무 지표 계산
- `StockFormatter`: 데이터 포맷팅
- `AIService`: OpenAI API 통신
- `KisMasterService`: 한국 종목 마스터 데이터 관리
- `NaverStockSearchService`: 네이버 종목 검색
- `UpdateLogService`: 업데이트 로그 관리

**프론트엔드:**
- `StockApiClient` (Singleton Pattern): 모든 API 통신 클래스

### 디자인 패턴
1. **Facade Pattern**: `StockService`가 Provider, Calculator, Formatter를 통합
2. **Strategy Pattern**: `StockProvider`가 ticker에 따라 `KisStockProvider`, `YahooStockProvider` 선택
3. **Singleton Pattern**: 프론트엔드 `StockApiClient`
4. **Template Method Pattern**: `BaseStockProvider` (Abstract Base Class)

### UI/UX 원칙
- **모바일 퍼스트**: 
  - 바텀 시트 모달 (모바일)
  - 중앙 모달 (데스크톱)
  - 터치 타겟 최소 44px
  - 폰트 크기 최소 14px (본문), 16px (입력창)
- **AI 페르소나**: "친근한 선배" 톤 (마침표 없음, "~해", "~야", "~임")
- **Bento Grid 레이아웃**: 정보를 직관적인 카드 형태로 배치

### 확장성
신규 기능 추가 시 다음 순서로 구조적 설계를 선행합니다:
1. DB 모델 설계 (`app/models/`)
2. Pydantic 스키마 정의 (`app/schemas/`)
3. 서비스 로직 구현 (`app/services/`)
4. API 라우터 구현 (`app/api/v1/endpoints/`)
5. 프론트엔드 타입 정의 (`src/types/`)
6. API 클라이언트 메서드 추가 (`src/api/`)
7. UI 컴포넌트 구현 (`src/components/`, `src/pages/`)

---

## 3. 주요 기능 (Current Features)

### 주식 정보 조회
- 실시간 주가 정보 및 등락률
- 52주 최고가/최저가 위치 시각화 (`PriceRangeBar`)
- 주요 재무 지표:
  - PER, PBR, ROE, EPS
  - 배당률, Beta
  - 목표가, 시가총액
- 한국 종목 한글명 자동 매핑 (KIS 마스터 데이터)
- 종목 검색 기능 (티커, 한글 종목명, 기업명 지원)

### AI 기반 분석
- OpenAI GPT-4o-mini를 활용한 종합 분석
- 투자 매력도 점수 (0-100점, 가중치 기반 알고리즘)
- 매수/중립/주의 신호 제공
- 3줄 요약 및 리스크 분석
- 지표별 개별 AI 코멘트:
  - 섹터/산업 맥락 고려
  - Value Trap/Dividend Trap 경고 포함

### 데이터 제공자 전략
- **한국 주식 (.KS, .KQ)**:
  - Primary: KIS API (한국투자증권 API) - 실시간 데이터
  - Secondary: Yahoo Finance (재무제표 데이터) - 병렬 호출하여 병합
  - Fallback: KIS 실패 시 Yahoo만 사용
- **미국/해외 주식**:
  - Primary: Yahoo Finance
- **종목 검색**:
  - FinanceDataReader (한국 종목 리스트, 메모리 캐싱)
  - 네이버 증권 검색 (NaverStockSearchService)

### 데이터 캐싱
- DB 기반 분석 결과 캐싱 (1시간 TTL)
- 메모리 기반 종목 마스터 데이터 캐싱

---

## 4. 프로젝트 구조 (Project Structure)

```
stock-dashboard/
├── client/                          # React 클라이언트 (프론트엔드)
│   ├── src/
│   │   ├── api/                     # API 클라이언트 (Class 기반, Singleton)
│   │   │   └── stockApi.ts          # StockApiClient
│   │   ├── components/              # UI 컴포넌트
│   │   │   ├── AIAnalysis.tsx       # AI 분석 카드
│   │   │   ├── ErrorMessage.tsx     # 에러 메시지
│   │   │   ├── Header.tsx           # 헤더
│   │   │   ├── Loading.tsx          # 로딩 스피너
│   │   │   ├── MetricModal.tsx      # 지표 상세 모달
│   │   │   ├── PriceRangeBar.tsx    # 52주 가격 범위 바
│   │   │   ├── ProgressTracker.tsx  # 진행 상황 트래커
│   │   │   ├── SearchBox.tsx        # 검색 박스
│   │   │   ├── StockCard.tsx        # 주식 정보 카드
│   │   │   ├── StockInfo.tsx        # 주식 정보 표시
│   │   │   ├── UpdateLogModal.tsx   # 업데이트 로그 모달
│   │   │   └── index.ts             # 컴포넌트 export
│   │   ├── constants/               # 상수 정의
│   │   │   └── metrics.ts           # 재무 지표 상수
│   │   ├── hooks/                   # 커스텀 훅
│   │   │   ├── useStockAnalysis.ts  # 주식 분석 훅
│   │   │   └── index.ts
│   │   ├── pages/                   # 페이지 컴포넌트
│   │   │   ├── StockAnalysisPage.tsx
│   │   │   └── index.ts
│   │   ├── store/                   # Zustand 스토어 (주식 관련)
│   │   │   └── useStockStore.ts
│   │   ├── stores/                  # Zustand 스토어 (기타)
│   │   │   └── useUpdateLogStore.ts
│   │   ├── types/                   # TypeScript 타입 정의
│   │   │   └── stock.ts
│   │   ├── utils/                   # 유틸리티 함수
│   │   │   └── stockUtils.ts
│   │   ├── App.tsx                  # 메인 앱 컴포넌트
│   │   ├── App.css
│   │   ├── index.css                # 글로벌 스타일
│   │   └── main.tsx                 # 엔트리 포인트
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
│
└── server/                          # FastAPI 서버 (백엔드)
    ├── app/
    │   ├── api/                     # API 라우터
    │   │   ├── routers/             # 공통 라우터
    │   │   │   └── update_log_router.py
    │   │   └── v1/                  # API v1
    │   │       ├── endpoints/       # 엔드포인트 라우터
    │   │       │   └── stocks.py    # 주식 관련 엔드포인트
    │   │       └── __init__.py      # API 라우터 통합
    │   ├── core/                    # 핵심 설정 및 의존성
    │   │   ├── config.py            # 환경 변수 설정 (Settings)
    │   │   ├── database.py          # SQLAlchemy 설정 (Base, engine, get_db)
    │   │   └── dependencies.py      # 의존성 주입 함수
    │   ├── models/                  # SQLAlchemy 모델 (DB 테이블)
    │   │   ├── stock.py             # StockAnalysisLog 모델
    │   │   └── update_log.py        # UpdateLog 모델
    │   ├── schemas/                 # Pydantic 스키마 (요청/응답 모델)
    │   │   ├── stock.py             # 주식 관련 스키마
    │   │   └── update_log.py        # 업데이트 로그 스키마
    │   ├── services/                # 비즈니스 로직 (Service Layer)
    │   │   ├── stock/               # 주식 관련 서비스
    │   │   │   ├── service.py       # StockService (Facade)
    │   │   │   ├── provider.py      # StockProvider (Router/Strategy Context)
    │   │   │   ├── base_provider.py # BaseStockProvider (Abstract)
    │   │   │   ├── kis_provider.py  # KisStockProvider (한국 주식)
    │   │   │   ├── yahoo_provider.py # YahooStockProvider (미국/해외)
    │   │   │   ├── calculator.py    # StockCalculator (재무 지표 계산)
    │   │   │   ├── etf_calculator.py # ETFCalculator
    │   │   │   ├── formatter.py     # StockFormatter (데이터 포맷팅)
    │   │   │   ├── data_merger.py   # DataMerger (데이터 병합)
    │   │   │   ├── kis_api_client.py # KIS API 클라이언트
    │   │   │   ├── kis_data_parser.py # KIS 데이터 파서
    │   │   │   ├── kis_defense_engine.py # KIS 방어 로직
    │   │   │   ├── kis_master_service.py # KisMasterService (종목 마스터)
    │   │   │   ├── kis_sector_mapping.py # 섹터 매핑
    │   │   │   ├── naver_search_service.py # NaverStockSearchService
    │   │   │   ├── token_manager.py # KIS 토큰 관리
    │   │   │   ├── asset_type.py    # 자산 타입 유틸
    │   │   │   └── __init__.py
    │   │   ├── ai_service.py        # AIService (OpenAI 통신)
    │   │   ├── update_log_service.py # UpdateLogService
    │   │   └── __init__.py
    │   ├── main.py                  # FastAPI 앱 생성 및 설정
    │   └── __init__.py
    ├── tests/                       # 테스트 코드
    │   └── test_stock_search.py
    ├── requirements.txt             # Python 의존성
    ├── run.py                       # 서버 실행 스크립트
    └── README.md
```

---

## 5. API 엔드포인트 (API Endpoints)

### 주식 관련 API (`/api/v1/stock`)
- `POST /api/v1/stock/search`: 종목명/기업명을 티커로 변환
- `GET /api/v1/stock/{ticker}`: 주식 정보 조회 (캐시 확인)
- `POST /api/v1/stock/analyze`: 주식 정보 + AI 분석 (캐시 확인)
- `POST /api/v1/stock/analyze-ai`: AI 분석만 수행 (캐시 무시)

### 업데이트 로그 API (`/api/updates`)
- `GET /api/updates/`: 업데이트 로그 전체 조회 (최신순)

### 공통 API
- `GET /`: 서버 상태 확인
- `GET /health`: 헬스 체크
- `GET /docs`: Swagger API 문서
- `GET /redoc`: ReDoc API 문서

---

## 6. 환경 변수 설정 (Environment Variables)

### Backend (`.env` 파일)
```env
# OpenAI 설정
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# KIS API 설정 (한국투자증권)
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
KIS_BASE_URL=https://openapi.koreainvestment.com:9443
KIS_CANO=your_account_prefix  # 선택사항 (계좌번호 앞 8자리)
KIS_ACNT_PRDT_CD=your_account_suffix  # 선택사항 (계좌번호 뒤 2자리)

# 데이터베이스 설정 (Supabase PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# CORS 설정 (선택사항, 없으면 모든 출처 허용)
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# 서버 설정 (선택사항)
HOST=0.0.0.0
PORT=8000
```

### Frontend (`.env` 파일)
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 7. 데이터베이스 모델 (Database Models)

### StockAnalysisLog
주식 분석 결과를 캐싱하기 위한 테이블 (1시간 TTL)

**컬럼:**
- `ticker` (String, PK): 종목 코드
- `price` (Float): 저장 당시 가격
- `analysis_json` (JSON): AI 분석 결과 및 주요 지표 전체
- `updated_at` (DateTime): 마지막 업데이트 시간 (자동 갱신, 인덱스)

### UpdateLog
서비스 업데이트 이력을 저장하는 테이블

**컬럼:**
- `id` (BigInteger, PK, Auto Increment)
- `created_at` (DateTime): 생성 시간 (자동)
- `version` (String): 버전 정보
- `category` (String): 업데이트 카테고리
- `content` (String): 업데이트 내용

---

## 8. 다음 목표 (Next Goals)

이제 DB를 활용한 심화 기능들을 개발하려고 합니다.

### DB 확장 계획
- 사용자(User) 테이블 추가
- 관심 종목(Watchlist) 기능
- 포트폴리오 관리
- 알림 설정

### 기능 추가 계획
- 뉴스 심층 분석
- 포트폴리오 관리 및 백테스팅
- 실시간 알림 기능
- 차트 기능 강화
- 비교 분석 (여러 종목 동시 분석)

---

## 9. 주요 참고 문서

프로젝트 루트 디렉토리에 다음 문서들이 있습니다:
- `README.md`: 프로젝트 개요 및 시작 가이드
- `PR_INSTRUCTIONS.md`: Pull Request 작성 가이드
- `ETF_FEATURE_GUIDE.md`: ETF 기능 가이드
- `KIS_MASTER_ANALYSIS_REPORT.md`: KIS API 마스터 데이터 분석 리포트
- `IMPLEMENTATION_VERIFICATION.md`: 구현 검증 문서
- 기타 기술 문서들

---

**[Action]**
위 내용을 바탕으로 프로젝트 컨텍스트를 파악해 주세요.
준비가 되었다면, **"프로젝트 인계 완료. 다음으로 어떤 기능을 개발할까요?"**라고 답변해 주세요.
