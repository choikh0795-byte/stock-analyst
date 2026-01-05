# ETF 운용보수 추출 문제 해결

## 🔍 문제 원인

Yahoo Finance의 `annualReportExpenseRatio` 필드가 **많은 ETF에서 null을 반환**하는 알려진 이슈.

**참고:**
- [GitHub Issue #2040](https://github.com/ranaroussi/yfinance/issues/2040)
- 1,100개 이상의 NYSE/Nasdaq 상장 ETF에 영향

## 💡 해결 방법

yfinance 0.2.40+ (2024년 9월)에서 추가된 **새로운 API 사용**:

```python
ticker = yf.Ticker('SPY')
funds_data = ticker.funds_data
fund_operations = funds_data.fund_operations
# fund_operations에서 'Annual Report Expense Ratio' 추출
```

## 🔧 구현 내용

### 1. ETFCalculator 수정 (`server/app/services/stock/etf_calculator.py`)

**변경 전:**
```python
def extract_expense_ratio(self, info: Dict) -> Optional[float]:
    # 오직 annualReportExpenseRatio만 확인
    expense_ratio = info.get("annualReportExpenseRatio")
    if expense_ratio is not None:
        return float(expense_ratio) * 100
    return None  # 실패
```

**변경 후:**
```python
def extract_expense_ratio(self, ticker_obj, info: Dict) -> Optional[float]:
    # 1순위: funds_data.fund_operations (신규 API)
    try:
        if hasattr(ticker_obj, 'funds_data'):
            funds_data = ticker_obj.funds_data
            if hasattr(funds_data, 'fund_operations'):
                fund_ops = funds_data.fund_operations
                # DataFrame 또는 dict에서 'Annual Report Expense Ratio' 추출
                ...
    except Exception as e:
        logger.debug(f"funds_data 접근 실패: {e}")

    # 2순위: annualReportExpenseRatio (레거시 fallback)
    expense_ratio = info.get("annualReportExpenseRatio")
    if expense_ratio is not None:
        return float(expense_ratio) * 100

    return None
```

**핵심 변경사항:**
- ✅ Ticker 객체를 파라미터로 받도록 수정
- ✅ `funds_data.fund_operations` 우선 시도
- ✅ DataFrame과 dict 형식 모두 지원
- ✅ 레거시 필드 fallback으로 유지 (하위 호환성)

### 2. YahooStockProvider 수정 (`server/app/services/stock/yahoo_provider.py`)

**변경 전:**
```python
expense_ratio = self._etf_calculator.extract_expense_ratio(info)
```

**변경 후:**
```python
expense_ratio = self._etf_calculator.extract_expense_ratio(stock, info)
```

**핵심 변경사항:**
- ✅ Ticker 객체(`stock`)를 ETFCalculator에 전달

## 📊 예상 결과

### 이전 (문제 상황)
```
[ETFCalculator] 운용보수 추출 실패: annualReportExpenseRatio 없음
→ expense_ratio: None
→ UI에 "N/A" 표시
```

### 이후 (수정 완료)
```
[ETFCalculator] 운용보수 추출 (funds_data): 0.09%
→ expense_ratio: 0.09
→ UI에 "0.09%" 표시
```

## ✅ 테스트 방법

### 1. 백엔드 테스트
```bash
python test_expense_ratio_fix.py
```

### 2. API 엔드포인트 테스트
```bash
curl -X POST http://localhost:8000/api/v1/stock/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "SPY"}' \
  | jq '.stock_data.expense_ratio'
```

**예상 결과:**
```json
0.09
```

### 3. 프론트엔드 테스트
1. 프론트엔드 실행: `cd client && npm run dev`
2. ETF 검색: "SPY", "QQQ", "VOO" 등
3. 운용보수 카드 확인: "0.09%" 등으로 표시되어야 함

## 🔄 호환성

- ✅ yfinance 0.2.40+ (funds_data API 지원)
- ✅ yfinance < 0.2.40 (레거시 필드로 fallback)
- ✅ 기존 주식 데이터 처리에는 영향 없음

## 📚 관련 이슈

- [yfinance Issue #2040](https://github.com/ranaroussi/yfinance/issues/2040) - annualReportExpenseRatio missing
- [yfinance PR #2041](https://github.com/ranaroussi/yfinance/pull/2041) - Implement fund-level data support

## 📝 요약

| 항목 | 내용 |
|------|------|
| **문제** | annualReportExpenseRatio 필드가 많은 ETF에서 null 반환 |
| **원인** | Yahoo Finance API의 알려진 제한사항 |
| **해결** | yfinance 신규 API (funds_data.fund_operations) 사용 |
| **영향 범위** | ETF 운용보수 표시만 (주식 데이터는 영향 없음) |
| **파일 수정** | 2개 (etf_calculator.py, yahoo_provider.py) |
