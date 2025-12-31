# ETF Analysis Feature Guide

## 📊 Overview

This feature extends the stock analysis system to support **ETF (Exchange-Traded Funds)** analysis with specialized metrics and AI-powered insights.

## 🎯 Key Features

### 1. **Asset Type Detection**
- Automatic detection of asset type (STOCK vs ETF) using Yahoo Finance `quoteType`
- Different analysis pipelines for stocks and ETFs

### 2. **ETF-Specific Metrics**

| Metric | Description | Source |
|--------|-------------|--------|
| **Expense Ratio** | Annual fund operating expense (%) | Yahoo Finance `annualReportExpenseRatio` |
| **Total Assets (AUM)** | Assets Under Management | Yahoo Finance `totalAssets` |
| **Premium/Discount** | NAV vs Market Price deviation (%) | Calculated from `navPrice` |
| **Dividend Yield** | Annual dividend yield (%) | Yahoo Finance `yield` or `dividendYield` |
| **Inception Date** | Fund establishment date | Yahoo Finance `fundInceptionDate` |
| **Top Holdings** | Top 3 constituent assets | (Future enhancement) |

### 3. **ETF-Specific Scoring Algorithm**

**Scoring Formula:**
```
Total Score = (Cost Efficiency × 0.4) + (Tracking Stability × 0.3) + (Momentum × 0.2) + (Size Stability × 0.1)
```

**Components:**

1. **Cost Efficiency (40%)**
   - Lower expense ratio = Higher score
   - 0.00-0.10%: 100 points
   - 0.10-0.30%: 80-100 points
   - 0.30-0.50%: 60-80 points
   - 0.50-1.00%: 40-60 points
   - >1.00%: 0-40 points

2. **Tracking Stability (30%)**
   - Lower premium/discount = Higher score
   - 0.00-0.50%: 100 points
   - 0.50-1.00%: 80-100 points
   - 1.00-2.00%: 60-80 points
   - 2.00-5.00%: 40-60 points
   - >5.00%: 0-40 points

3. **Momentum (20%)**
   - 52-week price position (same as stocks)

4. **Size Stability (10%)**
   - Larger AUM = Higher score
   - >$10B: 100 points
   - $1B-$10B: 80-100 points
   - $100M-$1B: 60-80 points
   - $10M-$100M: 40-60 points
   - <$10M: 0-40 points

### 4. **ETF-Specific AI Analysis**

The AI analysis prompt is customized for ETFs to focus on:
- **Fee efficiency** (expense ratio appropriateness)
- **Tracking accuracy** (premium/discount stability)
- **Theme/sector fit** (investment theme relevance)
- **Liquidity risks** (AUM size considerations)

---

## 🧪 Testing Guide

### Test ETFs (US Market)

| Ticker | Name | Type | Expected Metrics |
|--------|------|------|------------------|
| **SPY** | SPDR S&P 500 ETF | Large-cap equity | Low expense ratio (0.09%), high AUM ($400B+) |
| **QQQ** | Invesco QQQ Trust | Tech-focused | Low expense ratio (0.20%), high AUM ($200B+) |
| **VOO** | Vanguard S&P 500 ETF | Large-cap equity | Very low expense ratio (0.03%), high AUM ($300B+) |
| **IWM** | iShares Russell 2000 | Small-cap equity | Moderate expense ratio (0.19%) |
| **AGG** | iShares Core US Aggregate Bond | Bond ETF | Low expense ratio (0.03%), high AUM ($90B+) |

### Test Scenarios

#### Scenario 1: Basic ETF Analysis (SPY)

**API Request:**
```bash
POST /api/v1/stock/analyze
{
  "ticker": "SPY"
}
```

**Expected Response Fields:**
```json
{
  "stock_data": {
    "name": "SPDR S&P 500 ETF Trust",
    "symbol": "SPY",
    "asset_type": "ETF",
    "current_price": 450.25,
    "expense_ratio": 0.09,
    "expense_ratio_str": "0.09%",
    "total_assets": 450000000000,
    "total_assets_str": "$450.0B",
    "premium_discount": 0.02,
    "premium_discount_str": "+0.02%",
    "dividend_yield": 1.25,
    "dividend_yield_str": "1.25%",
    "inception_date": "1993-01-22",
    "score": 85.5
  },
  "ai_analysis": {
    "score": 85.5,
    "signal": "매수",
    "one_line": "초저비용 대형주 ETF로 장기 투자에 최적화",
    "summary": [
      "운용보수 0.09%로 매우 경쟁력 있는 비용 구조",
      "괴리율 0.02%로 우수한 추적 성능",
      "순자산 $450B로 압도적인 유동성과 안정성"
    ],
    "risk": "시장 전반 하락 시 직접적인 영향"
  }
}
```

#### Scenario 2: Stock vs ETF Comparison

**Stock (AAPL):**
- Shows: PER, PBR, ROE, EPS, 부채비율, 목표가
- Score based on: Profitability (40%), Valuation (30%), Momentum (20%), Stability (10%)

**ETF (SPY):**
- Shows: Expense Ratio, AUM, Premium/Discount, Dividend Yield
- Score based on: Cost Efficiency (40%), Tracking Stability (30%), Momentum (20%), Size Stability (10%)

#### Scenario 3: Field Null Handling

Some ETFs may not have all fields (e.g., NAV price for calculation):

```json
{
  "expense_ratio": 0.15,
  "total_assets": 5000000000,
  "premium_discount": null,  // NAV not available
  "dividend_yield": 2.5,
  "inception_date": "2015-06-10"
}
```

**Expected Behavior:**
- Missing fields display as "N/A" in formatted strings
- Score calculation uses neutral values (50 points) for missing components

---

## 🔧 Implementation Architecture

### Backend Flow

```
1. User searches "SPY"
   ↓
2. YahooStockProvider.get_stock_info("SPY")
   ↓
3. AssetTypeDetector.detect_from_info(info)
   → Returns AssetType.ETF
   ↓
4. ETFCalculator.extract_*() methods
   → Extract expense_ratio, total_assets, premium_discount, etc.
   ↓
5. StockService.get_stock_info()
   → Formats ETF fields
   → Calls calculator.calculate_etf_score()
   ↓
6. AIService.analyze_stock()
   → Uses ETF-specific prompts
   ↓
7. Returns ETF analysis response
```

### Key Classes

| Class | Purpose | Location |
|-------|---------|----------|
| `AssetType` | Enum for STOCK/ETF | `server/app/services/stock/asset_type.py` |
| `AssetTypeDetector` | Detects asset type from Yahoo data | `server/app/services/stock/asset_type.py` |
| `ETFCalculator` | Extracts/calculates ETF metrics | `server/app/services/stock/etf_calculator.py` |
| `StockCalculator` | Extended with `calculate_etf_score()` | `server/app/services/stock/calculator.py` |
| `StockFormatter` | Extended with ETF formatting methods | `server/app/services/stock/formatter.py` |
| `YahooStockProvider` | Extended to handle ETF data | `server/app/services/stock/yahoo_provider.py` |
| `AIService` | Added `_build_etf_analysis_prompts()` | `server/app/services/ai_service.py` |

---

## 🐛 Known Limitations

1. **Tracking Error**: Not calculated (requires benchmark data)
2. **Top Holdings**: Not available via Yahoo Finance `info` (requires separate API call)
3. **NAV Price**: May not be available for all ETFs (affects premium/discount calculation)
4. **Korean ETFs**: Limited support (Yahoo Finance data may be incomplete)

---

## 🚀 Future Enhancements

1. **Benchmark Tracking**
   - Fetch benchmark index data
   - Calculate tracking error accurately

2. **Holdings Data**
   - Integrate with Yahoo Finance holdings API
   - Display top 5-10 holdings with weights

3. **Sector Allocation**
   - Visualize sector breakdown
   - Compare with benchmark allocation

4. **Performance Metrics**
   - Sharpe ratio
   - Maximum drawdown
   - Alpha/Beta vs benchmark

5. **Korean ETF Support**
   - Integrate KRX ETF data
   - Support KR-specific metrics (거래량, 거래대금)

---

## 📝 Testing Checklist

- [ ] Test US equity ETF (SPY, QQQ, VOO)
- [ ] Test bond ETF (AGG, BND)
- [ ] Test sector ETF (XLE, XLF)
- [ ] Test international ETF (EFA, VWO)
- [ ] Verify expense ratio formatting
- [ ] Verify AUM formatting (B/M units)
- [ ] Verify premium/discount calculation
- [ ] Verify ETF-specific AI prompts
- [ ] Verify score calculation (0-100 range)
- [ ] Test null handling for missing NAV
- [ ] Frontend displays ETF fields correctly
- [ ] Frontend hides stock-only fields for ETFs (PER, PBR, ROE, EPS)

---

## 🎓 Example API Responses

### Example 1: SPY (Large-cap Equity ETF)

```bash
curl -X POST http://localhost:8000/api/v1/stock/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "SPY"}'
```

**Response:**
```json
{
  "stock_data": {
    "name": "SPDR S&P 500 ETF Trust",
    "symbol": "SPY",
    "asset_type": "ETF",
    "current_price": 450.25,
    "previous_close": 448.90,
    "market_cap": null,
    "expense_ratio": 0.09,
    "expense_ratio_str": "0.09%",
    "total_assets": 450000000000,
    "total_assets_str": "$450.0B",
    "premium_discount": 0.02,
    "premium_discount_str": "+0.02%",
    "dividend_yield": 1.25,
    "dividend_yield_str": "1.25%",
    "inception_date": "1993-01-22",
    "fifty_two_week_low": 380.50,
    "fifty_two_week_high": 455.00,
    "sector": "Large Blend",
    "summary": "The SPDR S&P 500 ETF Trust seeks to provide investment results...",
    "score": 85.5,
    "pe_ratio": null,
    "pb_ratio": null,
    "roe": null,
    "eps": null,
    "debt_ratio": null
  },
  "ai_analysis": {
    "score": 85.5,
    "signal": "매수",
    "one_line": "초저비용 대형주 ETF로 장기 투자에 최적화된 선택",
    "summary": [
      "운용보수 0.09%로 매우 경쟁력 있는 비용 구조를 보유하고 있어",
      "괴리율 +0.02%로 NAV 대비 우수한 추적 성능을 보여주고 있어",
      "순자산 $450B로 압도적인 유동성과 안정성을 자랑해"
    ],
    "risk": "시장 전반 하락 시 직접적인 영향을 받을 수 있어"
  }
}
```

### Example 2: VOO (Ultra-low-cost ETF)

Expected score: **90+** (extremely low expense ratio 0.03%)

### Example 3: High-fee ETF

Expected score: **<60** (expense ratio >0.50%)

---

## 📞 Support

For questions or issues related to the ETF feature:
1. Check logs: `server/logs/app.log`
2. Verify Yahoo Finance data availability
3. Test with known ETF tickers (SPY, QQQ, VOO)

---

**Last Updated:** 2025-12-31
**Feature Status:** ✅ Implemented
**Next Steps:** End-to-end testing, frontend UI updates for ETF display
