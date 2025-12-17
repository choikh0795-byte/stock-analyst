***모든 생각과 응답은 반드시 한국어로 응답, 생각합니다***
# 프로젝트 컨텍스트
이 프로젝트는 React(Frontend)와 FastAPI(Backend)로 구성된 핀테크 주식/ETF 분석 서비스입니다.
핵심 목표는 모바일 중심의 직관적인 UI(Bento Grid)와 확장 가능한 객체지향적 아키텍처를 유지하는 것입니다.

# 핵심 원칙 (Core Principles)
1. **유지보수성 (Maintainability):** 모든 코드는 모듈화되어야 하며, 스파게티 코드를 엄격히 지양합니다.
2. **객체지향 (OOP):** 백엔드 비즈니스 로직과 프론트엔드 API 통신은 반드시 **Class(클래스)** 기반으로 작성합니다. 성격이 조금만 다른 함수가 있어도 모듈로 분리해냅니다. 
3. **확장성 (Scalability):** 추후 DB 도입 및 기능 확장을 고려하여 **Layered Architecture(계층화 아키텍처)**를 준수합니다.
4. **모바일 퍼스트 (Mobile-First):** UI는 모바일 환경(터치 타겟, 가독성)을 최우선으로 고려합니다.


---

# 1. 백엔드 가이드라인 (FastAPI)

## 아키텍처 구조 (Layered Pattern)
**관심사의 분리(Separation of Concerns)**를 엄격히 준수하세요. 라우터에 비즈니스 로직을 넣지 마세요.

- `app/api/v1/endpoints/`: **라우터 (Router)**
  - 오직 요청(Request)을 받고 응답(Response)을 반환하는 역할만 합니다.
  - 로직 처리는 반드시 `Service` 클래스에게 위임하세요.
- `app/services/`: **비즈니스 로직 (Service Layer)**
  - **[필수]** 모든 로직은 `StockService`와 같이 **Class**로 캡슐화해야 합니다.
  - 의존성 주입(Dependency Injection)을 활용하여 테스트와 확장이 용이하게 설계하세요.
- `app/schemas/`: **데이터 모델 (Pydantic)**
  - 요청/응답 데이터의 타입을 엄격하게 정의하세요.
- `app/core/`: **설정 (Config)**
  - 환경변수 및 공통 설정을 관리합니다.

## 코딩 표준
- **Type Hinting:** 모든 함수와 메서드에 파이썬 타입 힌트를 필수적으로 작성하세요.
- **Error Handling:** `try-except`는 Service 계층에서 처리하고, Router에서는 명확한 `HTTPException`을 발생시키세요.
- **Naming:** 클래스는 `PascalCase`, 함수/변수는 `snake_case`를 사용하세요.

---

# 2. 프론트엔드 가이드라인 (React + Vite + TailwindCSS)

## 아키텍처 구조
- **API 계층 분리 (Singleton Class):**
  - 컴포넌트 내부에서 `axios`나 `fetch`를 직접 사용하지 마세요.
  - `src/api/` 폴더 내에 `StockClient`와 같은 **Class 기반의 API 클라이언트**를 만들고 메서드로 호출하세요.
- **컴포넌트 분리:**
  - `src/components/`: 재사용 가능한 UI 조각 (비즈니스 로직 최소화)
  - `src/pages/`: 페이지 단위 조합 및 상태 관리
  - `src/hooks/`: 복잡한 로직은 커스텀 훅으로 분리

## 디자인 시스템 (UI/UX)
- **스타일:** 토스(Toss), 로빈후드 스타일의 **Modern Fintech** 지향. (보라색/네온 컬러 사용 금지)
- **Bento Grid:** 정보를 직관적인 카드 형태의 그리드 레이아웃으로 배치하세요.
- **모바일 최적화:**
  - 폰트 크기: 본문 최소 `14px`, 입력창 `16px`.
  - 터치 타겟: 버튼 높이 최소 `44px`.

---

# 3. 🔥 신규 기능 구현 프로세스 (New Feature Workflow)

사용자가 "새로운 기능(예: 뉴스 분석)을 추가해줘"라고 요청하면, 즉시 코드를 짜지 말고 **아래 순서대로 구조를 잡아서 제안**하세요.

1.  **Backend 설계:**
    - `schemas/news.py`: 데이터 모델 정의
    - `services/news_service.py`: `NewsService` 클래스 및 메서드 구현
    - `api/.../news.py`: 라우터에서 서비스 주입 및 엔드포인트 생성
2.  **Frontend 설계:**
    - `types/news.ts`: 타입 정의
    - `api/newsClient.ts`: API 통신 클래스 메서드 추가
    - `components/NewsCard.tsx`: UI 컴포넌트 구현

**"무조건 위 구조를 먼저 생각하고 코드를 작성할 것."**