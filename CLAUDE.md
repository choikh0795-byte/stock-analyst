# CLAUDE.md - AI Assistant Guide for Stock Analysis Dashboard

> **Last Updated:** 2025-12-29
> **Purpose:** Comprehensive guide for AI assistants working with this codebase

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Design Patterns](#architecture--design-patterns)
3. [Codebase Structure](#codebase-structure)
4. [Technology Stack](#technology-stack)
5. [Core Principles](#core-principles)
6. [Development Workflows](#development-workflows)
7. [Coding Standards](#coding-standards)
8. [Common Tasks Guide](#common-tasks-guide)
9. [Key Files Reference](#key-files-reference)
10. [Database Schema](#database-schema)
11. [API Endpoints](#api-endpoints)
12. [Testing & Deployment](#testing--deployment)

---

## 🎯 Project Overview

**Stock Analysis Dashboard** is a full-stack AI-powered stock analysis web service built with **React (Vite)** frontend and **FastAPI** backend. The service provides real-time stock information, financial metrics, and AI-driven investment analysis.

### Key Features
- **Real-time Stock Data**: Live prices, 52-week ranges, financial metrics (PER, PBR, ROE, EPS, Beta, Dividend Yield)
- **Multi-Provider Strategy**:
  - Korean stocks (.KS, .KQ): KIS API (primary) → Yahoo Finance (fallback)
  - US/International stocks: Yahoo Finance
- **AI Analysis**: OpenAI GPT-4o-mini powered investment insights with sector-specific context
- **Modern UI**: Mobile-first Bento Grid design inspired by Toss/Robinhood
- **Database Caching**: Supabase (PostgreSQL) for analysis result caching (1-hour TTL)
- **Korean Stock Support**: Automatic Korean name mapping via KIS master data

### Current Status
- **Deployed**:
  - Frontend: Vercel
  - Backend: Render (Free Tier)
- **Database**: Supabase PostgreSQL with SQLAlchemy ORM
- **Active Development**: Feature enhancement phase (after MVP deployment)

---

## 🏗️ Architecture & Design Patterns

### 1. Layered Architecture (Backend)

**Strict separation of concerns** - NEVER mix layers!

```
┌─────────────────────────────────────┐
│  Router Layer (API Endpoints)       │  ← Only handles HTTP requests/responses
├─────────────────────────────────────┤
│  Service Layer (Business Logic)     │  ← Core business logic (Class-based)
├─────────────────────────────────────┤
│  Provider Layer (Data Sources)      │  ← External API calls, data fetching
├─────────────────────────────────────┤
│  Model/Schema Layer (Data)          │  ← Database models & Pydantic schemas
└─────────────────────────────────────┘
```

**Example Flow:**
```
Request → Router (stocks.py)
        → Service (StockService)
        → Provider (KisProvider/YahooProvider)
        → External API
        → Calculator (StockCalculator)
        → Formatter (StockFormatter)
        → Response
```

### 2. Design Patterns

#### Facade Pattern
**StockService** acts as a unified interface combining multiple subsystems:
```python
class StockService:
    def __init__(self):
        self.provider = StockProvider()      # Data fetching
        self.calculator = StockCalculator()  # Calculations
        self.formatter = StockFormatter()    # Formatting
```

#### Strategy Pattern
**StockProvider** selects the appropriate data provider based on ticker:
```python
class StockProvider:
    def get_stock_data(self, ticker: str):
        if ticker.endswith(('.KS', '.KQ')):
            # Try KIS first, fallback to Yahoo
            return self.kis_provider.fetch() or self.yahoo_provider.fetch()
        else:
            return self.yahoo_provider.fetch()
```

#### Singleton Pattern (Frontend)
**StockApiClient** ensures single API client instance:
```typescript
class StockApiClient {
    private static instance: StockApiClient | null = null;

    public static getInstance(): StockApiClient {
        if (!StockApiClient.instance) {
            StockApiClient.instance = new StockApiClient();
        }
        return StockApiClient.instance;
    }
}
```

#### Dependency Injection
Services are injected via FastAPI's `Depends()`:
```python
@router.post("/analyze")
async def analyze_stock(
    stock_service: StockService = Depends(get_stock_service),
    ai_service: AIService = Depends(get_ai_service),
    db: Session = Depends(get_db)
):
    # Use injected services
```

---

## 📁 Codebase Structure

```
stock-analyst/
├── client/                         # React Frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── api/                   # API Client Layer (Class-based Singleton)
│   │   │   └── stockApi.ts       # StockApiClient - All API calls
│   │   ├── components/            # Reusable UI Components
│   │   │   ├── Header.tsx
│   │   │   ├── SearchBox.tsx
│   │   │   ├── StockInfo.tsx
│   │   │   ├── StockCard.tsx
│   │   │   ├── AIAnalysis.tsx
│   │   │   ├── PriceRangeBar.tsx
│   │   │   ├── MetricModal.tsx   # Mobile: Bottom Sheet / Desktop: Center Modal
│   │   │   ├── UpdateLogModal.tsx
│   │   │   ├── Loading.tsx
│   │   │   └── ErrorMessage.tsx
│   │   ├── pages/                 # Page-level Components
│   │   │   └── StockAnalysisPage.tsx
│   │   ├── hooks/                 # Custom React Hooks
│   │   │   └── useStockAnalysis.ts
│   │   ├── stores/                # Zustand State Management
│   │   │   └── useUpdateLogStore.ts
│   │   ├── store/
│   │   │   └── useStockStore.ts
│   │   ├── types/                 # TypeScript Type Definitions
│   │   │   └── stock.ts
│   │   ├── utils/                 # Utility Functions
│   │   │   └── stockUtils.ts
│   │   ├── constants/
│   │   │   └── metrics.ts        # Metric definitions & descriptions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── server/                         # FastAPI Backend (Python)
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   └── stocks.py # Stock API Endpoints (Router Layer)
│   │   │   │   └── __init__.py   # API Router aggregation
│   │   │   └── routers/
│   │   │       └── update_log_router.py
│   │   ├── services/              # Business Logic Layer (All Class-based)
│   │   │   ├── stock/
│   │   │   │   ├── service.py        # StockService (Facade)
│   │   │   │   ├── provider.py       # StockProvider (Strategy Context)
│   │   │   │   ├── base_provider.py  # BaseProvider (Abstract Base)
│   │   │   │   ├── kis_provider.py   # KisStockProvider (KIS API)
│   │   │   │   ├── yahoo_provider.py # YahooStockProvider (yfinance)
│   │   │   │   ├── calculator.py     # StockCalculator (Calculations)
│   │   │   │   ├── formatter.py      # StockFormatter (String formatting)
│   │   │   │   ├── kis_master_service.py  # Korean stock name mapping
│   │   │   │   └── token_manager.py  # KIS API token management
│   │   │   ├── ai_service.py     # AIService (OpenAI integration)
│   │   │   └── update_log_service.py
│   │   ├── models/                # SQLAlchemy Database Models
│   │   │   ├── stock.py          # StockAnalysisLog model
│   │   │   └── update_log.py     # UpdateLog model
│   │   ├── schemas/               # Pydantic Request/Response Schemas
│   │   │   ├── stock.py          # StockInfo, StockAnalysisRequest, etc.
│   │   │   └── update_log.py
│   │   ├── core/                  # Core Configuration & Dependencies
│   │   │   ├── config.py         # Settings (env variables)
│   │   │   ├── database.py       # DB connection & session
│   │   │   └── dependencies.py   # Dependency injection factories
│   │   ├── main.py               # FastAPI app initialization & lifecycle
│   │   └── __init__.py
│   └── requirements.txt
│
├── .env                           # Environment variables (NEVER commit!)
├── .gitignore
├── .cursorrules                   # Cursor AI specific rules
├── .vscode/
│   └── settings.json
├── README.md                      # User-facing documentation
├── PROJECT_HANDOVER.md            # Project context & status
├── GEMINI.md                      # Gemini AI specific rules
├── CLAUDE.md                      # This file - AI assistant guide
└── package.json                   # Root package.json (shared dependencies)
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.109.0+ (async ASGI)
- **Server**: Uvicorn (development), Gunicorn (production)
- **Language**: Python 3.12+
- **Data Validation**: Pydantic 2.6.0+
- **Database ORM**: SQLAlchemy 2.0.0+
- **Database Driver**: psycopg2-binary (PostgreSQL)
- **Stock Data APIs**:
  - `yfinance 0.2.40` (US stocks, fallback for KR stocks)
  - KIS OpenAPI (Korean stocks - primary)
- **AI**: OpenAI API (GPT-4o-mini)
- **HTTP Client**: requests 2.31.0
- **Environment**: python-dotenv 1.0.1+
- **SSL**: certifi (for SSL verification)

### Frontend
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0.0 (fast HMR, optimized builds)
- **Language**: TypeScript 5.2.2
- **Styling**:
  - TailwindCSS 3.4.1 (utility-first CSS)
  - PostCSS 8.4.35
  - Autoprefixer 10.4.17
- **State Management**: Zustand 5.0.9 (lightweight, hooks-based)
- **HTTP Client**: Axios 1.6.0 (with interceptors)
- **Animation**: Framer Motion 12.23.26
- **Icons**: Lucide React 0.559.0
- **Utilities**:
  - clsx 2.1.1 (conditional classnames)
  - tailwind-merge 3.4.0 (merge Tailwind classes)

### Database
- **Platform**: Supabase (Managed PostgreSQL)
- **Purpose**: Analysis result caching (1-hour TTL), update logs

### Deployment
- **Frontend**: Vercel (automatic deployments from Git)
- **Backend**: Render Free Tier
- **Database**: Supabase (cloud PostgreSQL)

---

## 🎯 Core Principles

> **CRITICAL**: These principles are NON-NEGOTIABLE and must be followed at all times.

### 1. Maintainability
- **Modular Code**: Every piece of logic should be in its own module
- **No Spaghetti Code**: If functions have slightly different purposes, separate them into different modules
- **Clear Separation**: Each file/class should have a single, well-defined responsibility

### 2. Object-Oriented Programming (OOP)
- **Backend**: ALL business logic MUST be Class-based
  - ✅ `StockService`, `AIService`, `StockProvider`, `StockCalculator`
  - ❌ Procedural functions scattered across files
- **Frontend**: API communication MUST use Class-based clients
  - ✅ `StockApiClient` (Singleton pattern)
  - ❌ Direct `axios.get()` calls in components
- **When to Create a Class**: If logic is more than a simple utility function, make it a class

### 3. Scalability
- **Layered Architecture**: Prepare for future DB expansion and feature additions
- **Dependency Injection**: Services should be injectable and testable
- **Configuration Management**: All settings via environment variables (`app/core/config.py`)

### 4. Mobile-First Design
- **Touch Targets**: Minimum 44px height for buttons
- **Font Sizes**:
  - Body text: minimum 14px
  - Input fields: 16px (prevents iOS zoom)
- **Responsive Modals**:
  - Mobile: Bottom Sheet (slides from bottom)
  - Desktop: Center Modal
- **Bento Grid Layout**: Card-based, visually clear information hierarchy

### 5. Type Safety
- **Backend**: Type hints REQUIRED for all functions
  ```python
  def calculate_roe(net_income: float, equity: float) -> Optional[float]:
      # Implementation
  ```
- **Frontend**: TypeScript strict mode, no `any` types without good reason
  ```typescript
  interface StockInfo {
      symbol: string;
      current_price: number;
      // ...
  }
  ```

---

## 💼 Development Workflows

### Git Strategy

#### Branch Naming
```
main              # Production-ready code
develop           # Integration branch
feature/*         # New features (e.g., feature/add-news-analysis)
fix/*             # Bug fixes (e.g., fix/modal-positioning)
hotfix/*          # Urgent production fixes
claude/*          # Claude AI development branches (auto-created)
```

#### Commit Message Convention
```
<type>: <subject>

<body> (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no behavior change)
- `style`: Code formatting, whitespace
- `docs`: Documentation changes
- `test`: Test additions/modifications
- `chore`: Build tasks, dependency updates

**Examples:**
```bash
feat: 지표 상세 모달 기능 추가
fix: PC 화면에서 모달 중앙 정렬 수정
refactor: StockCard 컴포넌트 리팩토링
docs: API 엔드포인트 문서 업데이트
```

#### Feature Development Workflow
```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Develop & commit
git add .
git commit -m "feat: feature description"

# 4. Push to remote
git push -u origin feature/your-feature-name

# 5. Create Pull Request → merge to develop
# (After code review & CI/CD checks)

# 6. Deploy to production (from develop to main)
git checkout main
git merge develop
git tag -a v1.0.0 -m "Release version"
git push origin main --tags
```

### Environment Setup

#### Backend Setup
```bash
cd server

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate
# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with required variables
cat > .env << EOF
OPENAI_API_KEY=your_openai_key
KIS_APP_KEY=your_kis_key
KIS_APP_SECRET=your_kis_secret
DATABASE_URL=postgresql://user:pass@host:5432/db
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
EOF

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Environment Variables Required:**
- `OPENAI_API_KEY`: OpenAI API key (required)
- `KIS_APP_KEY`: KIS API app key (required for Korean stocks)
- `KIS_APP_SECRET`: KIS API app secret (required for Korean stocks)
- `DATABASE_URL`: PostgreSQL connection string (optional, for caching)
- `CORS_ORIGINS`: Comma-separated allowed origins (default: *)

#### Frontend Setup
```bash
cd client

# Install dependencies
npm install

# Create .env file (optional)
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 📝 Coding Standards

### Backend (Python)

#### Naming Conventions
- **Classes**: `PascalCase` (e.g., `StockService`, `AIService`)
- **Functions/Methods**: `snake_case` (e.g., `get_stock_info`, `calculate_roe`)
- **Variables**: `snake_case` (e.g., `stock_data`, `analysis_result`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `CACHE_TTL`)
- **Private Methods**: `_leading_underscore` (e.g., `_fetch_from_api`)

#### Type Hints (MANDATORY)
```python
from typing import Dict, List, Optional, Tuple

def get_stock_info(
    ticker: str,
    db: Session
) -> Tuple[Dict[str, any], List[str]]:
    """
    Fetch stock information and news.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL", "005930.KS")
        db: Database session

    Returns:
        Tuple of (stock_data dict, news list)

    Raises:
        ValueError: If ticker is invalid
    """
    # Implementation
```

#### Error Handling
- **Service Layer**: Catch specific exceptions, log errors, re-raise or convert
  ```python
  try:
      data = self._fetch_data(ticker)
  except RequestException as e:
      logger.error(f"API request failed: {e}")
      raise ValueError(f"Failed to fetch data for {ticker}")
  ```

- **Router Layer**: Catch ValueError/other exceptions, return HTTPException
  ```python
  try:
      result = stock_service.get_stock_info(ticker, db)
  except ValueError as e:
      raise HTTPException(status_code=404, detail=str(e))
  except Exception as e:
      logger.error(f"Unexpected error: {e}")
      raise HTTPException(status_code=500, detail="Internal server error")
  ```

#### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)  # Include traceback
```

### Frontend (TypeScript/React)

#### Naming Conventions
- **Components**: `PascalCase` (e.g., `StockInfo.tsx`, `AIAnalysis.tsx`)
- **Hooks**: `camelCase` with `use` prefix (e.g., `useStockAnalysis.ts`)
- **Utility Functions**: `camelCase` (e.g., `formatPrice`, `calculateChange`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `CACHE_DURATION`)
- **Types/Interfaces**: `PascalCase` (e.g., `StockInfo`, `APIResponse`)

#### Component Structure
```tsx
import { useState, useEffect } from 'react'
import type { StockInfo } from '../types/stock'

interface StockCardProps {
  stock: StockInfo
  onSelect?: (symbol: string) => void
}

export function StockCard({ stock, onSelect }: StockCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  useEffect(() => {
    // Side effects
  }, [dependency])

  const handleClick = () => {
    onSelect?.(stock.symbol)
  }

  return (
    <div className="stock-card">
      {/* JSX */}
    </div>
  )
}
```

#### API Client Usage (NEVER use axios directly in components)
```tsx
// ❌ BAD - Direct axios in component
function MyComponent() {
  const fetchData = async () => {
    const response = await axios.get('/api/stock/AAPL')
    // ...
  }
}

// ✅ GOOD - Use StockApiClient
import { stockApi } from '../api/stockApi'

function MyComponent() {
  const fetchData = async () => {
    const data = await stockApi.getStockInfo('AAPL')
    // ...
  }
}
```

#### State Management
- **Local State**: `useState` for component-specific state
- **Global State**: Zustand stores for shared state
  ```tsx
  // stores/useStockStore.ts
  import { create } from 'zustand'

  interface StockState {
    currentSymbol: string | null
    setCurrentSymbol: (symbol: string) => void
  }

  export const useStockStore = create<StockState>((set) => ({
    currentSymbol: null,
    setCurrentSymbol: (symbol) => set({ currentSymbol: symbol }),
  }))
  ```

#### Styling
- **Tailwind Classes**: Use Tailwind utility classes
- **Conditional Classes**: Use `clsx` or `cn` utility
  ```tsx
  import { clsx } from 'clsx'

  <div className={clsx(
    'base-class',
    isActive && 'active-class',
    error && 'error-class'
  )}>
  ```
- **Custom CSS**: Only when Tailwind is insufficient (create `.css` file)

---

## 🎯 Common Tasks Guide

### Task 1: Adding a New API Endpoint

**Scenario**: Add a `/api/v1/stock/compare` endpoint to compare two stocks.

#### Step 1: Define Schemas (`server/app/schemas/stock.py`)
```python
class StockCompareRequest(BaseModel):
    ticker1: str
    ticker2: str

class StockCompareResponse(BaseModel):
    stock1: StockInfo
    stock2: StockInfo
    comparison: Dict[str, str]  # Comparison insights
```

#### Step 2: Add Service Method (`server/app/services/stock/service.py`)
```python
class StockService:
    # ... existing methods ...

    def compare_stocks(
        self,
        ticker1: str,
        ticker2: str,
        db: Session
    ) -> Tuple[Dict, Dict, Dict]:
        """Compare two stocks and return insights."""
        stock1_data, _ = self.get_stock_info(ticker1, db)
        stock2_data, _ = self.get_stock_info(ticker2, db)

        comparison = self._generate_comparison(stock1_data, stock2_data)
        return stock1_data, stock2_data, comparison

    def _generate_comparison(self, stock1: Dict, stock2: Dict) -> Dict:
        # Comparison logic
        return {...}
```

#### Step 3: Add Router Endpoint (`server/app/api/v1/endpoints/stocks.py`)
```python
@router.post("/compare", response_model=StockCompareResponse)
async def compare_stocks(
    request: StockCompareRequest,
    stock_service: StockService = Depends(get_stock_service),
    db: Session = Depends(get_db)
) -> StockCompareResponse:
    """Compare two stocks side-by-side."""
    try:
        stock1, stock2, comparison = stock_service.compare_stocks(
            request.ticker1, request.ticker2, db
        )
        return StockCompareResponse(
            stock1=StockInfo(**stock1),
            stock2=StockInfo(**stock2),
            comparison=comparison
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

#### Step 4: Add Frontend Type (`client/src/types/stock.ts`)
```typescript
export interface StockCompareRequest {
  ticker1: string
  ticker2: string
}

export interface StockCompareResponse {
  stock1: StockInfo
  stock2: StockInfo
  comparison: Record<string, string>
}
```

#### Step 5: Add API Client Method (`client/src/api/stockApi.ts`)
```typescript
class StockApiClient {
  // ... existing methods ...

  async compareStocks(
    ticker1: string,
    ticker2: string
  ): Promise<StockCompareResponse> {
    const response = await this.axiosInstance.post<StockCompareResponse>(
      '/api/v1/stock/compare',
      { ticker1, ticker2 }
    )
    return response.data
  }
}
```

#### Step 6: Use in Component
```tsx
import { stockApi } from '../api/stockApi'

function CompareStocksPage() {
  const handleCompare = async (ticker1: string, ticker2: string) => {
    try {
      const result = await stockApi.compareStocks(ticker1, ticker2)
      // Use result...
    } catch (error) {
      console.error('Comparison failed:', error)
    }
  }
}
```

---

### Task 2: Adding a New UI Component

**Scenario**: Create a `NewsCard` component to display stock news.

#### Step 1: Create Component File (`client/src/components/NewsCard.tsx`)
```tsx
import { motion } from 'framer-motion'

interface NewsCardProps {
  title: string
  summary: string
  publishedAt: string
  url: string
}

export function NewsCard({ title, summary, publishedAt, url }: NewsCardProps) {
  return (
    <motion.div
      className="rounded-lg bg-white p-4 shadow-sm"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
    >
      <h3 className="text-base font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-sm text-gray-600">{summary}</p>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-gray-500">{publishedAt}</span>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-blue-600 hover:underline"
        >
          자세히 보기
        </a>
      </div>
    </motion.div>
  )
}
```

#### Step 2: Create CSS (if needed) (`client/src/components/NewsCard.css`)
```css
/* Only if Tailwind is insufficient */
.news-card-special-effect {
  /* Custom styles */
}
```

#### Step 3: Export from Index (`client/src/components/index.ts`)
```typescript
export { NewsCard } from './NewsCard'
export { StockInfo } from './StockInfo'
// ... other exports
```

#### Step 4: Use in Parent Component
```tsx
import { NewsCard } from '../components'

function NewsSection({ news }: { news: NewsItem[] }) {
  return (
    <div className="grid gap-4">
      {news.map((item) => (
        <NewsCard
          key={item.id}
          title={item.title}
          summary={item.summary}
          publishedAt={item.publishedAt}
          url={item.url}
        />
      ))}
    </div>
  )
}
```

---

### Task 3: Adding Database Model

**Scenario**: Add a `Watchlist` model to track user's favorite stocks.

#### Step 1: Create Model (`server/app/models/watchlist.py`)
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    ticker = Column(String, nullable=False)
    name = Column(String, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Watchlist(user={self.user_id}, ticker={self.ticker})>"
```

#### Step 2: Create Schema (`server/app/schemas/watchlist.py`)
```python
from pydantic import BaseModel
from datetime import datetime

class WatchlistCreate(BaseModel):
    user_id: str
    ticker: str
    name: str

class WatchlistResponse(BaseModel):
    id: int
    user_id: str
    ticker: str
    name: str
    added_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2
```

#### Step 3: Create Service (`server/app/services/watchlist_service.py`)
```python
from typing import List
from sqlalchemy.orm import Session
from app.models.watchlist import Watchlist
from app.schemas.watchlist import WatchlistCreate

class WatchlistService:
    def add_to_watchlist(
        self,
        data: WatchlistCreate,
        db: Session
    ) -> Watchlist:
        """Add stock to user's watchlist."""
        watchlist_item = Watchlist(**data.dict())
        db.add(watchlist_item)
        db.commit()
        db.refresh(watchlist_item)
        return watchlist_item

    def get_user_watchlist(
        self,
        user_id: str,
        db: Session
    ) -> List[Watchlist]:
        """Get all stocks in user's watchlist."""
        return db.query(Watchlist).filter(
            Watchlist.user_id == user_id
        ).all()

    def remove_from_watchlist(
        self,
        watchlist_id: int,
        db: Session
    ) -> bool:
        """Remove stock from watchlist."""
        item = db.query(Watchlist).filter(
            Watchlist.id == watchlist_id
        ).first()
        if item:
            db.delete(item)
            db.commit()
            return True
        return False
```

#### Step 4: Update Models Init (`server/app/models/__init__.py`)
```python
from .stock import StockAnalysisLog
from .update_log import UpdateLog
from .watchlist import Watchlist  # Add this

__all__ = ["StockAnalysisLog", "UpdateLog", "Watchlist"]
```

#### Step 5: Run Database Migration
```bash
# Auto-create tables on next server start
# Or manually via Alembic if using migrations:
alembic revision --autogenerate -m "Add watchlist table"
alembic upgrade head
```

---

### Task 4: Debugging API Issues

#### Check Backend Logs
```bash
# In server directory
tail -f /path/to/logs/app.log

# Or if using uvicorn directly
uvicorn app.main:app --reload --log-level debug
```

#### Check Frontend Network Requests
```typescript
// Already included in stockApi.ts interceptors
// Check browser DevTools > Network tab

// For additional debugging:
console.log('[DEBUG] Request:', { ticker, params })
console.log('[DEBUG] Response:', response.data)
```

#### Common Issues

**Issue: CORS Error**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/stock/AAPL'
from origin 'http://localhost:3000' has been blocked by CORS policy
```
**Solution**: Check `server/.env` has correct CORS_ORIGINS
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Issue: 422 Validation Error**
```json
{
  "detail": [
    {
      "loc": ["body", "ticker"],
      "msg": "field required"
    }
  ]
}
```
**Solution**: Check request body matches Pydantic schema exactly

**Issue: Database Connection Error**
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**: Verify DATABASE_URL in `.env` is correct and DB is running

---

### Task 5: Updating Dependencies

#### Backend
```bash
cd server

# Update a specific package
pip install --upgrade yfinance

# Update all packages (carefully!)
pip list --outdated
pip install --upgrade package_name

# Freeze new dependencies
pip freeze > requirements.txt
```

#### Frontend
```bash
cd client

# Update a specific package
npm update axios

# Check outdated packages
npm outdated

# Update all packages (major versions)
npm update

# Update package.json and package-lock.json
npm install package_name@latest
```

---

## 📚 Key Files Reference

### Backend Critical Files

| File | Purpose | Key Contents |
|------|---------|--------------|
| `server/app/main.py` | Application entry point | FastAPI app initialization, CORS, lifespan events, router registration |
| `server/app/core/config.py` | Configuration management | Environment variable loading, Settings class, CORS origins |
| `server/app/core/database.py` | Database setup | SQLAlchemy engine, session factory, Base class |
| `server/app/core/dependencies.py` | Dependency injection | Service factories for DI (`get_stock_service`, `get_ai_service`, `get_db`) |
| `server/app/services/stock/service.py` | Stock service facade | Main `StockService` class orchestrating all stock operations |
| `server/app/services/stock/provider.py` | Data provider router | Selects KIS or Yahoo provider based on ticker |
| `server/app/services/stock/calculator.py` | Financial calculations | ROE, EPS, change calculations with null-safety |
| `server/app/services/stock/formatter.py` | Data formatting | Currency formatting (KRW/USD), percentage formatting |
| `server/app/services/ai_service.py` | AI analysis | OpenAI integration, prompt engineering, scoring algorithm |
| `server/app/api/v1/endpoints/stocks.py` | Stock API endpoints | All stock-related HTTP endpoints |
| `server/app/schemas/stock.py` | Request/response models | Pydantic schemas for API validation |
| `server/app/models/stock.py` | Database models | SQLAlchemy `StockAnalysisLog` model |

### Frontend Critical Files

| File | Purpose | Key Contents |
|------|---------|--------------|
| `client/src/main.tsx` | Application entry point | React root rendering |
| `client/src/App.tsx` | Root component | Main app structure, routing (if applicable) |
| `client/src/api/stockApi.ts` | API client | Singleton `StockApiClient`, all API methods |
| `client/src/types/stock.ts` | Type definitions | TypeScript interfaces for stock data |
| `client/src/hooks/useStockAnalysis.ts` | Stock analysis hook | Custom hook for fetching and managing stock analysis |
| `client/src/stores/useUpdateLogStore.ts` | Update log state | Zustand store for update log modal |
| `client/src/store/useStockStore.ts` | Stock state | Zustand store for current stock |
| `client/src/pages/StockAnalysisPage.tsx` | Main page | Primary stock analysis page component |
| `client/src/components/StockInfo.tsx` | Stock info display | Main stock information component |
| `client/src/components/AIAnalysis.tsx` | AI analysis display | AI-generated analysis display |
| `client/src/constants/metrics.ts` | Metric definitions | Metric metadata, descriptions, icons |
| `client/vite.config.ts` | Vite configuration | Build settings, plugins |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (NEVER commit!) |
| `.gitignore` | Git ignore patterns |
| `server/requirements.txt` | Python dependencies |
| `client/package.json` | Node.js dependencies |
| `client/tailwind.config.js` | Tailwind CSS configuration |
| `client/tsconfig.json` | TypeScript compiler options |

---

## 🗄️ Database Schema

### Current Tables

#### `stock_analysis_logs`
```sql
CREATE TABLE stock_analysis_logs (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR NOT NULL,
    stock_data JSONB NOT NULL,
    news JSONB,
    ai_analysis JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_ticker_created (ticker, created_at)
);
```

**Purpose**: Cache stock analysis results to reduce API calls and improve performance.

**TTL**: 1 hour (queries check `created_at > NOW() - INTERVAL '1 hour'`)

**Usage**:
- Before fetching fresh data, check if recent cached analysis exists
- Store new analysis after successful API fetch
- Update expired entries

#### `update_logs`
```sql
CREATE TABLE update_logs (
    id SERIAL PRIMARY KEY,
    version VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    changes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Purpose**: Track application updates and display changelog to users.

---

## 🌐 API Endpoints

### Stock Endpoints (`/api/v1/stock`)

#### `POST /api/v1/stock/search`
Search for ticker by name or symbol.

**Request:**
```json
{
  "query": "삼성전자"  // or "Samsung" or "005930"
}
```

**Response:**
```json
{
  "ticker": "005930.KS",
  "name": "삼성전자"
}
```

#### `GET /api/v1/stock/{ticker}`
Get stock information without AI analysis.

**Response:**
```json
{
  "stock_data": {
    "name": "Apple Inc.",
    "symbol": "AAPL",
    "current_price": 175.50,
    "previous_close": 174.50,
    "pe_ratio": 30.5,
    "pb_ratio": 1.5,
    "roe": 18.5,
    "eps": 5.40,
    // ... more fields
  },
  "news": [
    "Apple announces new product line...",
    "iPhone sales exceed expectations..."
  ]
}
```

#### `POST /api/v1/stock/analyze`
Get stock information WITH AI analysis.

**Request:**
```json
{
  "ticker": "AAPL"
}
```

**Response:**
```json
{
  "stock_data": { /* same as above */ },
  "news": [ /* news array */ ],
  "ai_analysis": {
    "score": 78.4,
    "signal": "매수",
    "one_line": "강력한 성장세와 안정적인 재무구조",
    "summary": [
      "높은 시장 점유율과 브랜드 가치",
      "지속적인 혁신과 R&D 투자",
      "건전한 재무 지표"
    ],
    "risk": "시장 변동성과 경쟁 심화 주의",
    "metric_insights": {
      "pe_ratio": "현재 PER 30.5는 업계 평균보다 높아 성장 기대감을 반영하고 있어",
      "roe": "ROE 18.5%는 우수한 자본 효율성을 보여주고 있어"
      // ... other metrics
    }
  }
}
```

#### `POST /api/v1/stock/analyze-ai`
Get ONLY AI analysis (assumes stock data already fetched).

**Request:** Same as `/analyze`

**Response:**
```json
{
  "score": 78.4,
  "signal": "매수",
  "one_line": "...",
  "summary": [...],
  "risk": "...",
  "metric_insights": {...}
}
```

### Update Log Endpoints

#### `GET /api/updates`
Get all update logs (ordered by most recent).

**Response:**
```json
[
  {
    "id": 1,
    "version": "v1.2.0",
    "title": "ROE/EPS 지표 추가",
    "description": "재무 분석 강화",
    "changes": ["ROE 계산", "EPS 표시"],
    "created_at": "2025-12-29T10:00:00Z"
  }
]
```

### Health Check

#### `GET /`
Basic health check.

**Response:**
```json
{
  "status": "ok"
}
```

#### `GET /health`
Detailed health check.

**Response:**
```json
{
  "status": "ok"
}
```

---

## 🧪 Testing & Deployment

### Local Testing

#### Backend
```bash
cd server

# Run server
uvicorn app.main:app --reload

# Test endpoints with curl
curl http://localhost:8000/health

# Test stock endpoint
curl -X POST http://localhost:8000/api/v1/stock/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

#### Frontend
```bash
cd client

# Development mode
npm run dev

# Build production
npm run build

# Preview production build
npm run preview
```

### Deployment Checklist

#### Pre-Deployment
- [ ] All environment variables set in production
- [ ] Database migrations applied
- [ ] Dependencies updated and locked
- [ ] Build successful locally
- [ ] No console errors in browser
- [ ] API endpoints tested
- [ ] CORS configured for production domains

#### Backend (Render)
1. Push to Git repository
2. Render automatically detects `requirements.txt`
3. Set environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `KIS_APP_KEY`
   - `KIS_APP_SECRET`
   - `DATABASE_URL`
   - `CORS_ORIGINS`
4. Deploy and verify health endpoint

#### Frontend (Vercel)
1. Push to Git repository
2. Vercel automatically detects Vite project
3. Set environment variables:
   - `VITE_API_BASE_URL` (backend URL)
4. Deploy and test

#### Post-Deployment
- [ ] Test production URLs
- [ ] Verify CORS working
- [ ] Check database connections
- [ ] Monitor logs for errors
- [ ] Test critical user flows

---

## 🎨 Design System Guidelines

### Colors (Tailwind)
```css
/* Primary (Blue) */
bg-blue-500, text-blue-600, border-blue-300

/* Success (Green) */
bg-green-50, text-green-600, border-green-300

/* Danger (Red) */
bg-red-50, text-red-600, border-red-300

/* Neutral (Gray) */
bg-gray-50, text-gray-600, text-gray-900, border-gray-200

/* Background */
bg-white, bg-gray-50, bg-gray-100
```

### Typography
```css
/* Headings */
text-2xl font-bold      /* Page title */
text-xl font-semibold   /* Section title */
text-lg font-medium     /* Card title */

/* Body */
text-base               /* Normal text (16px) */
text-sm                 /* Small text (14px) */
text-xs                 /* Extra small (12px) */
```

### Spacing (Mobile-First)
```css
/* Padding */
p-4   /* Standard card padding (16px) */
p-6   /* Section padding (24px) */

/* Gaps */
gap-2  /* Tight gap (8px) */
gap-4  /* Standard gap (16px) */
gap-6  /* Section gap (24px) */
```

### Animations (Framer Motion)
```tsx
// Fade in with slide up
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>

// Hover scale
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
```

### Responsive Breakpoints
```css
sm: 640px   /* Small devices */
md: 768px   /* Tablets */
lg: 1024px  /* Laptops */
xl: 1280px  /* Desktops */
2xl: 1536px /* Large screens */
```

---

## 🚨 Common Pitfalls & How to Avoid Them

### 1. Direct API Calls in Components
❌ **Bad:**
```tsx
function MyComponent() {
  const fetchData = async () => {
    const res = await axios.get('http://localhost:8000/api/stock/AAPL')
  }
}
```

✅ **Good:**
```tsx
import { stockApi } from '../api/stockApi'

function MyComponent() {
  const fetchData = async () => {
    const data = await stockApi.getStockInfo('AAPL')
  }
}
```

### 2. Business Logic in Routers
❌ **Bad:**
```python
@router.get("/stock/{ticker}")
async def get_stock(ticker: str):
    # Calculating ROE directly in router
    net_income = yfinance.Ticker(ticker).info.get('netIncome')
    equity = yfinance.Ticker(ticker).info.get('totalStockholderEquity')
    roe = net_income / equity if equity else None
    return {"roe": roe}
```

✅ **Good:**
```python
@router.get("/stock/{ticker}")
async def get_stock(
    ticker: str,
    stock_service: StockService = Depends(get_stock_service)
):
    stock_data = stock_service.get_stock_info(ticker)
    return stock_data
```

### 3. Missing Type Hints
❌ **Bad:**
```python
def calculate_roe(net_income, equity):
    if equity and equity != 0:
        return net_income / equity
```

✅ **Good:**
```python
def calculate_roe(
    net_income: Optional[float],
    equity: Optional[float]
) -> Optional[float]:
    """Calculate Return on Equity."""
    if equity and equity != 0:
        return net_income / equity
    return None
```

### 4. Hardcoded Values
❌ **Bad:**
```python
response = requests.get(
    'https://openapi.koreainvestment.com:9443/api/v1/...',
    headers={'appkey': 'PS1234567890'}
)
```

✅ **Good:**
```python
from app.core.config import settings

response = requests.get(
    f'{settings.KIS_BASE_URL}/api/v1/...',
    headers={'appkey': settings.KIS_APP_KEY}
)
```

### 5. Ignoring Error Cases
❌ **Bad:**
```python
def get_stock_info(ticker: str):
    data = yfinance.Ticker(ticker).info
    return data['currentPrice']  # KeyError if missing!
```

✅ **Good:**
```python
def get_stock_info(ticker: str) -> Optional[float]:
    try:
        data = yfinance.Ticker(ticker).info
        return data.get('currentPrice')
    except Exception as e:
        logger.error(f"Failed to fetch {ticker}: {e}")
        raise ValueError(f"Invalid ticker: {ticker}")
```

---

## 📖 Additional Resources

### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Vite**: https://vitejs.dev/
- **TailwindCSS**: https://tailwindcss.com/
- **Framer Motion**: https://www.framer.com/motion/
- **Zustand**: https://github.com/pmndrs/zustand
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/

### API Documentation
- **yfinance**: https://github.com/ranaroussi/yfinance
- **KIS OpenAPI**: https://apiportal.koreainvestment.com/
- **OpenAI API**: https://platform.openai.com/docs/

---

## 🔄 Changelog

### 2025-12-29 - Initial Creation
- Created comprehensive CLAUDE.md guide
- Documented architecture, patterns, and workflows
- Added detailed task guides and examples
- Included coding standards and best practices

---

## 📝 Notes for AI Assistants

### When Starting a New Session
1. **Read this file first** to understand project context
2. Check `.cursorrules` and `PROJECT_HANDOVER.md` for additional context
3. Review recent commits to understand current work
4. Check open issues/PRs if working on GitHub

### Before Making Changes
1. **Understand the architecture** - Don't violate layering
2. **Follow design patterns** - Use existing patterns (Facade, Strategy, Singleton)
3. **Maintain type safety** - Always add type hints/interfaces
4. **Test locally** - Run server and client before committing

### When Adding Features
1. **Plan first** - Design schemas → services → endpoints → UI
2. **Follow the structure** - Use Task 1 (Adding API Endpoint) as template
3. **Update documentation** - Update this file if architecture changes
4. **Commit properly** - Use conventional commit messages

### Communication Style
- **Backend Logs**: Professional, technical (English)
- **Frontend UI**: Friendly, approachable (Korean)
- **AI Analysis Tone**: "Friendly senior developer" persona
  - Use informal Korean: "~해", "~야", "~임"
  - No periods at end of sentences
  - Avoid overly formal language

---

**End of CLAUDE.md**
