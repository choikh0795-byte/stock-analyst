# Stock Dashboard Client

React + TypeScript + Vite 기반 주식 대시보드 클라이언트입니다.
**관심사 분리(Separation of Concerns)** 원칙에 따라 구조화되었습니다.

## 프로젝트 구조

```
client/src/
├── api/
│   └── stockApi.ts          # API 클라이언트 (Singleton Pattern)
├── components/               # 재사용 가능한 UI 컴포넌트
│   ├── SearchBox.tsx
│   ├── StockInfo.tsx
│   ├── AIAnalysis.tsx
│   ├── ErrorMessage.tsx
│   ├── Loading.tsx
│   └── Header.tsx
├── hooks/                   # 커스텀 훅 (비즈니스 로직 분리)
│   └── useStockAnalysis.ts
├── pages/                   # 페이지 컴포넌트
│   └── StockAnalysisPage.tsx
├── types/                   # TypeScript 타입 정의
│   └── stock.ts
├── utils/                   # 유틸리티 함수
│   └── stockUtils.ts
├── App.tsx                  # 메인 App 컴포넌트
└── main.tsx                 # 진입점
```

## 아키텍처 특징

### 1. API 계층 분리 (Singleton Pattern)
- `StockApiClient` 클래스로 모든 API 호출을 중앙화
- 컴포넌트에서 직접 axios를 사용하지 않음
- 요청/응답 인터셉터로 로깅 및 에러 처리

### 2. 컴포넌트 분리
- 재사용 가능한 작은 컴포넌트로 분리
- 각 컴포넌트는 단일 책임 원칙 준수
- Props를 통한 명확한 인터페이스

### 3. 커스텀 훅
- 비즈니스 로직을 훅으로 분리
- 상태 관리와 API 호출 로직 캡슐화
- 컴포넌트는 UI 렌더링에만 집중

### 4. TypeScript
- 타입 안정성 보장
- 인터페이스로 데이터 구조 명확화
- 개발자 경험 향상

## 설치 방법

```bash
npm install
```

## 실행 방법

```bash
npm run dev
```

개발 서버는 `http://localhost:3000`에서 실행됩니다.

## 빌드

```bash
npm run build
```

빌드된 파일은 `dist` 폴더에 생성됩니다.

## 환경 설정

서버 API URL은 `src/api/stockApi.ts`의 `StockApiClient` 생성자에서 설정할 수 있습니다.
기본값은 `http://localhost:8000`입니다.

## 주요 파일 설명

### API 계층 (`src/api/stockApi.ts`)
```typescript
// Singleton Pattern으로 구현된 API 클라이언트
const stockApi = StockApiClient.getInstance()

// 사용 예시
const data = await stockApi.getStockAnalysis({ ticker: 'AAPL' })
```

### 커스텀 훅 (`src/hooks/useStockAnalysis.ts`)
```typescript
// 비즈니스 로직을 캡슐화한 훅
const { ticker, setTicker, loading, stockData, analyzeStock } = useStockAnalysis()
```

### 컴포넌트 사용 예시
```typescript
// 재사용 가능한 컴포넌트
<SearchBox 
  ticker={ticker}
  onTickerChange={setTicker}
  onSearch={analyzeStock}
  loading={loading}
/>
```

## 확장 가이드

### 새로운 API 엔드포인트 추가
1. `src/api/stockApi.ts`의 `StockApiClient` 클래스에 메서드 추가
2. `src/types/stock.ts`에 필요한 타입 정의 추가

### 새로운 페이지 추가
1. `src/pages/` 폴더에 새 페이지 컴포넌트 생성
2. 필요시 라우터 라이브러리 추가 (react-router-dom 등)

### 새로운 컴포넌트 추가
1. `src/components/` 폴더에 컴포넌트 생성
2. `src/components/index.ts`에 export 추가

