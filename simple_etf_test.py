#!/usr/bin/env python3
"""
ETF 데이터 추출 간단 테스트

yfinance를 직접 사용하여 ETF 데이터 추출을 검증합니다.
"""

try:
    import yfinance as yf
except ImportError:
    print("❌ yfinance not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "yfinance", "-q"])
    import yfinance as yf


def test_etf_data(ticker: str):
    """ETF 데이터 추출 테스트"""
    print(f"\n{'='*80}")
    print(f"🔍 Testing: {ticker}")
    print(f"{'='*80}\n")

    try:
        # yfinance로 데이터 가져오기
        stock = yf.Ticker(ticker)
        info = stock.info

        # 1. Asset Type 확인
        quote_type = info.get('quoteType')
        print(f"[1] Quote Type: {quote_type}")

        is_etf = (quote_type == 'ETF')
        print(f"    → Is ETF: {'✅ YES' if is_etf else '❌ NO'}")

        if not is_etf:
            print(f"\n⚠️ {ticker} is not an ETF (quoteType: {quote_type})")
            return

        # 2. 기본 정보
        print(f"\n[2] Basic Info:")
        print(f"    • Name: {info.get('shortName') or info.get('longName')}")
        print(f"    • Current Price: ${info.get('currentPrice') or info.get('regularMarketPrice', 'N/A')}")
        print(f"    • Sector: {info.get('sector', 'N/A')}")

        # 3. ETF 전용 지표 추출
        print(f"\n[3] ETF-Specific Metrics:")

        # Expense Ratio (운용보수)
        expense_ratio_raw = info.get('annualReportExpenseRatio')
        if expense_ratio_raw is not None:
            expense_ratio = float(expense_ratio_raw) * 100
            print(f"    • Expense Ratio: {expense_ratio:.2f}%")
        else:
            print(f"    • Expense Ratio: N/A")

        # Total Assets (AUM)
        total_assets = info.get('totalAssets')
        if total_assets:
            if total_assets >= 1_000_000_000:
                total_assets_str = f"${total_assets / 1_000_000_000:.1f}B"
            elif total_assets >= 1_000_000:
                total_assets_str = f"${total_assets / 1_000_000:.0f}M"
            else:
                total_assets_str = f"${total_assets:,.0f}"
            print(f"    • Total Assets (AUM): {total_assets_str}")
        else:
            print(f"    • Total Assets: N/A")

        # NAV Price & Premium/Discount
        nav_price = info.get('navPrice')
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if nav_price and current_price:
            premium_discount = ((current_price - nav_price) / nav_price) * 100
            print(f"    • NAV Price: ${nav_price:.2f}")
            print(f"    • Premium/Discount: {premium_discount:+.2f}%")
        else:
            print(f"    • NAV Price: N/A")
            print(f"    • Premium/Discount: N/A")

        # Dividend Yield
        dividend_yield_raw = info.get('yield') or info.get('dividendYield')
        if dividend_yield_raw:
            dividend_yield = float(dividend_yield_raw) * 100
            print(f"    • Dividend Yield: {dividend_yield:.2f}%")
        else:
            print(f"    • Dividend Yield: N/A")

        # Inception Date
        inception_date_raw = info.get('fundInceptionDate')
        if inception_date_raw:
            from datetime import datetime
            if isinstance(inception_date_raw, (int, float)):
                inception_date = datetime.fromtimestamp(inception_date_raw).strftime('%Y-%m-%d')
                print(f"    • Inception Date: {inception_date}")
        else:
            print(f"    • Inception Date: N/A")

        # 4. 점수 계산 시뮬레이션
        print(f"\n[4] Score Calculation Simulation:")

        # Cost Efficiency (40%)
        if expense_ratio_raw is not None:
            expense_ratio_pct = float(expense_ratio_raw) * 100
            if expense_ratio_pct <= 0.10:
                cost_score = 100.0
            elif expense_ratio_pct <= 0.30:
                cost_score = 100.0 - ((expense_ratio_pct - 0.10) / 0.20) * 20.0
            else:
                cost_score = 80.0 - ((expense_ratio_pct - 0.30) / 0.20) * 20.0
            print(f"    • Cost Efficiency Score: {cost_score:.1f}/100 (weight: 40%)")
        else:
            cost_score = 50.0
            print(f"    • Cost Efficiency Score: 50.0/100 (neutral)")

        # Tracking Stability (30%)
        if nav_price and current_price:
            abs_premium = abs(premium_discount)
            if abs_premium <= 0.50:
                tracking_score = 100.0
            elif abs_premium <= 1.00:
                tracking_score = 100.0 - ((abs_premium - 0.50) / 0.50) * 20.0
            else:
                tracking_score = 80.0
            print(f"    • Tracking Stability Score: {tracking_score:.1f}/100 (weight: 30%)")
        else:
            tracking_score = 50.0
            print(f"    • Tracking Stability Score: 50.0/100 (neutral)")

        # Size Stability (10%)
        if total_assets:
            if total_assets >= 10_000_000_000:
                size_score = 100.0
            elif total_assets >= 1_000_000_000:
                size_score = 80.0 + ((total_assets - 1_000_000_000) / 9_000_000_000) * 20.0
            else:
                size_score = 60.0
            print(f"    • Size Stability Score: {size_score:.1f}/100 (weight: 10%)")
        else:
            size_score = 50.0
            print(f"    • Size Stability Score: 50.0/100 (neutral)")

        # Momentum (20%) - 가정값
        momentum_score = 70.0  # 임시
        print(f"    • Momentum Score: {momentum_score:.1f}/100 (weight: 20%)")

        # Total Score
        total_score = (cost_score * 0.4) + (tracking_score * 0.3) + (momentum_score * 0.2) + (size_score * 0.1)
        print(f"\n    ╔{'═'*50}╗")
        print(f"    ║  TOTAL ETF SCORE: {total_score:.1f}/100{' ' * (29 - len(str(int(total_score))))}║")
        print(f"    ╚{'═'*50}╝")

        if total_score >= 70:
            signal = "✅ 매수 (Strong Buy)"
        elif total_score >= 50:
            signal = "⚠️ 중립 (Hold)"
        else:
            signal = "❌ 주의 (Caution)"
        print(f"    Signal: {signal}\n")

        print(f"✅ Test PASSED for {ticker}")

    except Exception as e:
        print(f"\n❌ Test FAILED for {ticker}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    print("\n" + "="*80)
    print("🚀 ETF Data Extraction Validation Test")
    print("="*80)

    test_etfs = [
        ("SPY", "SPDR S&P 500 ETF"),
        ("QQQ", "Invesco QQQ Trust"),
        ("VOO", "Vanguard S&P 500 ETF"),
    ]

    for ticker, name in test_etfs:
        print(f"\n📌 {name} ({ticker})")
        test_etf_data(ticker)

    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
