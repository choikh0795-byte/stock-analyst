**[Project Handover: Stock Dashboard Service]**

현재 **React(Vite) + FastAPI** 기반의 AI 주식/ETF 분석 웹 서비스를 개발하여 배포 및 운영 중입니다.
기존 채팅에서 기본 기능 구현, 배포, DB 연동까지 마쳤으며, 이제부터 **기능 고도화 및 DB 확장** 단계로 넘어갑니다.

**1. 현재 시스템 현황 (Current Status)**
- **Frontend:** React + TypeScript + TailwindCSS (Vite).
  - 디자인: Bento Grid 스타일, 모바일 퍼스트, Modern Fintech 디자인 (토스, 로빈후드 스타일).
  - 상태 관리: Zustand (검색 상태, 로딩 메시지, 업데이트 로그 등).
  - 애니메이션: Framer Motion.
  - 아이콘: Lucide React.
  - 배포: Vercel 
- **Backend:** Python FastAPI.
  - 핵심 로직: `StockService` (Class 기반 Facade 패턴), `StockProvider` (전략 패턴), `StockCalculator`, `StockFormatter`.
  - 데이터 제공자: 
    - `KisStockProvider`: 한국 주식 (.KS, .KQ) - KIS API 사용
    - `YahooStockProvider`: 미국/기타 주식 - yfinance 사용
    - `StockProvider`: 라우터 역할, ticker에 따라 적절한 Provider 선택 및 Fallback 처리
  - AI: OpenAI (GPT-4o-mini) 연동 (`AIService` 클래스).
  - 배포: Render (Free Tier) (예상).
- **Database:** Supabase (PostgreSQL).
  - 연결: SQLAlchemy (ORM) + psycopg2.
  - 현재 기능: 종목 분석 결과 캐싱 (`StockAnalysisLog` 테이블, 1시간 TTL).

**2. 프로젝트 핵심 규칙 (Cursor Rules 요약)**
- **아키텍처:** 
  - 백엔드: Layered Architecture (Router → Service → Provider/Calculator/Formatter).
  - 프론트엔드: API Client Class 분리 (`src/api/stockApi.ts`).
- **객체지향 (OOP):** 모든 비즈니스 로직은 **Class**로 캡슐화. (절차지향적 코드 지양).
  - 백엔드: `StockService`, `StockProvider`, `StockCalculator`, `StockFormatter`, `AIService` 등 모두 클래스 기반.
  - 프론트엔드: API 통신은 Class 기반 클라이언트 사용.
- **디자인 패턴:**
  - 전략 패턴: `StockProvider`가 `KisStockProvider`, `YahooStockProvider`를 선택.
  - Facade 패턴: `StockService`가 Provider, Calculator, Formatter를 통합.
- **UI/UX:** 
  - 모바일 최적화 필수 (바텀 시트 모달, 터치 타겟 최소 44px, 폰트 최소 14px).
  - "친근한 선배" 페르소나의 AI 멘트 (마침표 없음, "~해", "~야", "~임" 톤).
  - Bento Grid 레이아웃.
- **확장성:** 신규 기능 추가 시 [DB 모델 → 서비스 로직 → API → 프론트 UI] 순서로 구조적 설계 선행.

**3. 주요 기능 (Current Features)**
- **주식 정보 조회:**
  - 실시간 주가 정보 및 등락률.
  - 52주 최고가/최저가 위치 시각화 (`PriceRangeBar`).
  - 주요 재무 지표 (PER, PBR, ROE, EPS, 배당률, Beta, 목표가, 시가총액).
  - 한국 종목 한글명 자동 매핑.
- **AI 기반 분석:**
  - OpenAI GPT-4o-mini를 활용한 종합 분석.
  - 투자 매력도 점수 (0-100점, 가중치 기반 알고리즘).
  - 매수/중립/주의 신호 제공.
  - 3줄 요약 및 리스크 분석.
  - 지표별 개별 AI 코멘트 (섹터/산업 맥락 고려, Value Trap/Dividend Trap 경고 포함).
- **데이터 제공자 전략:**
  - 한국 주식: KIS API 우선, 실패 시 Yahoo Finance Fallback.
  - 미국/기타 주식: Yahoo Finance 사용.
  - FinanceDataReader를 통한 한국 종목 리스트 및 재무 정보 메모리 캐싱.

**4. 프로젝트 구조 (Project Structure)**
```
stock-dashboard/
├── client/                    # React 클라이언트
│   ├── src/
│   │   ├── api/              # API 클라이언트 (Class 기반)
│   │   ├── components/        # UI 컴포넌트
│   │   ├── pages/            # 페이지 컴포넌트
│   │   ├── hooks/            # 커스텀 훅
│   │   ├── store/            # Zustand 스토어
│   │   ├── types/            # TypeScript 타입 정의
│   │   └── utils/            # 유틸리티 함수
│   └── package.json
│
└── server/                    # FastAPI 서버
    ├── app/
    │   ├── api/v1/endpoints/ # 라우터 (Router Layer)
    │   ├── services/          # 비즈니스 로직 (Service Layer)
    │   │   ├── stock/         # 주식 관련 서비스
    │   │   │   ├── service.py      # StockService (Facade)
    │   │   │   ├── provider.py     # StockProvider (Router/Strategy Context)
    │   │   │   ├── base_provider.py # BaseProvider (Abstract)
    │   │   │   ├── kis_provider.py # KisStockProvider
    │   │   │   ├── yahoo_provider.py # YahooStockProvider
    │   │   │   ├── calculator.py   # StockCalculator
    │   │   │   └── formatter.py    # StockFormatter
    │   │   └── ai_service.py  # AIService
    │   ├── models/            # SQLAlchemy 모델
    │   ├── schemas/           # Pydantic 스키마
    │   └── core/              # 설정 및 의존성
    └── requirements.txt
```

**5. 다음 목표 (Next Goal)**
이제 DB를 활용한 심화 기능들을 개발하려고 합니다.
- **DB 확장:** 사용자(User) 테이블, 관심 종목(Watchlist) 기능 등 추가 예정.
- **기능 추가:** 뉴스 심층 분석, 포트폴리오 관리, 알림 기능 등.

**[Action]**
위 내용을 바탕으로 프로젝트 컨텍스트를 파악해 주세요.
준비가 되었다면, **"프로젝트 인계 완료. 다음으로 어떤 기능을 개발할까요?"**라고 답변해 주세요.




