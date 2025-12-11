# Stock Dashboard

AI 기반 주식 분석 대시보드 프로젝트입니다.

## 프로젝트 구조

```
stock-dashboard/
├── client/          # React 클라이언트 (프론트엔드)
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
└── server/          # FastAPI 서버 (백엔드)
    ├── main.py
    └── requirements.txt
```

## 시작하기

### 1. 서버 설정 및 실행

```bash
cd server

# 가상환경 생성 (선택사항)
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성 (OpenAI API 키 설정)
# OPENAI_API_KEY=your_api_key_here

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.
API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

### 2. 클라이언트 설정 및 실행

```bash
cd client

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

클라이언트는 `http://localhost:3000`에서 실행됩니다.

## 주요 기능

### 주식 정보 조회
- 실시간 주가 정보 및 등락률
- 52주 최고가/최저가 위치 시각화
- 주요 재무 지표 (PER, PBR, ROE, 배당률, Beta, 목표가)

### AI 기반 분석
- OpenAI GPT-4o-mini를 활용한 종합 분석
- 투자 매력도 점수 (0-100점)
- 매수/중립/주의 신호 제공
- 3줄 요약 및 리스크 분석
- 지표별 개별 AI 코멘트

### 사용자 인터페이스
- 모바일 퍼스트 반응형 디자인
- Bento Grid 스타일 레이아웃
- 지표 상세 모달 (모바일: Bottom Sheet, 데스크톱: Center Modal)
- 부드러운 애니메이션 (Framer Motion)
- Modern Fintech 디자인 (토스, 로빈후드 스타일)

## 기술 스택

### Backend
- **프레임워크**: FastAPI 0.104.1
- **서버**: Uvicorn (ASGI 서버)
- **언어**: Python 3.12+
- **데이터 검증**: Pydantic 2.5.0
- **환경 변수**: python-dotenv 1.0.0
- **HTTP 클라이언트**: httpx 0.25.0
- **주식 데이터**: yfinance 0.2.28
- **AI 분석**: OpenAI API (GPT-4o-mini)

### Frontend
- **프레임워크**: React 18.2.0
- **빌드 도구**: Vite 5.0.0
- **언어**: TypeScript 5.2.2
- **스타일링**: 
  - TailwindCSS 3.4.1
  - PostCSS 8.4.35
  - Autoprefixer 10.4.17
- **상태 관리**: Zustand 5.0.9
- **HTTP 클라이언트**: Axios 1.6.0
- **애니메이션**: Framer Motion 12.23.26
- **아이콘**: Lucide React 0.559.0

### 개발 도구
- **프론트엔드**: 
  - @vitejs/plugin-react
  - TypeScript 타입 정의
- **백엔드**: 
  - FastAPI 자동 API 문서화 (Swagger/OpenAPI)
  - Pydantic 설정 관리

## API 엔드포인트

- `GET /` - API 정보
- `GET /api/stock/{ticker}` - 주식 정보 조회
- `POST /api/stock/analyze` - 주식 정보 + AI 분석
- `POST /api/stock/analyze-ai` - AI 분석만

## Git 전략

### 브랜치 전략

- `main`: 프로덕션 배포용 브랜치 (안정적인 코드만 유지)
- `develop`: 개발 통합 브랜치 (기능 개발 완료 후 머지)
- `feature/*`: 기능 개발 브랜치 (예: `feature/add-metric-modal`)
- `fix/*`: 버그 수정 브랜치 (예: `fix/modal-positioning`)
- `hotfix/*`: 긴급 수정 브랜치 (프로덕션 이슈 즉시 수정)

### 워크플로우

1. **기능 개발**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   # 개발 작업
   git commit -m "feat: 기능 설명"
   git push origin feature/your-feature-name
   # Pull Request 생성 → develop 머지
   ```

2. **버그 수정**
   ```bash
   git checkout develop
   git checkout -b fix/bug-description
   # 수정 작업
   git commit -m "fix: 버그 설명"
   git push origin fix/bug-description
   # Pull Request 생성 → develop 머지
   ```

3. **프로덕션 배포**
   ```bash
   git checkout main
   git merge develop
   git tag -a v1.0.0 -m "릴리즈 버전"
   git push origin main --tags
   ```

### 커밋 메시지 규칙

커밋 메시지는 다음 형식을 따릅니다:

```
<type>: <subject>

<body> (선택사항)
```

**Type 종류:**
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅, 세미콜론 누락 등
- `refactor`: 코드 리팩토링
- `test`: 테스트 코드 추가/수정
- `chore`: 빌드 업무 수정, 패키지 매니저 설정 등

**예시:**
```bash
feat: 지표 상세 모달 기능 추가
fix: PC 화면에서 모달 중앙 정렬 수정
refactor: StockCard 컴포넌트 리팩토링
```

