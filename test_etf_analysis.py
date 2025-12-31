#!/usr/bin/env python3
"""
ETF 분석 기능 테스트 스크립트

실제 ETF 티커(SPY, QQQ, VOO)로 데이터 추출 및 점수 계산을 테스트합니다.
"""

import sys
sys.path.insert(0, '/home/user/stock-analyst/server')

from app.services.stock.yahoo_provider import YahooStockProvider
from app.services.stock.calculator import StockCalculator
from app.services.stock.formatter import StockFormatter


def test_etf_analysis(ticker: str):
    """ETF 분석 테스트"""
    print(f"\n{'='*80}")
    print(f"🔍 Testing ETF Analysis: {ticker}")
    print(f"{'='*80}\n")

    # 1. Provider로 데이터 추출
    provider = YahooStockProvider()
    calculator = StockCalculator()
    formatter = StockFormatter()

    try:
        print(f"[1/4] Fetching data from Yahoo Finance...")
        stock_data = provider.get_stock_info(ticker)

        print(f"[2/4] Asset Type: {stock_data.get('asset_type')}")

        if stock_data.get('asset_type') != 'ETF':
            print(f"❌ Expected ETF but got {stock_data.get('asset_type')}")
            return

        # 2. ETF 필드 확인
        print(f"\n[3/4] ETF Metrics:")
        print(f"  • Name: {stock_data.get('name')}")
        print(f"  • Current Price: ${stock_data.get('current_price', 0):.2f}")
        print(f"  • Expense Ratio: {stock_data.get('expense_ratio')}%")
        print(f"  • Total Assets (AUM): ${stock_data.get('total_assets', 0):,.0f}")
        print(f"  • Premium/Discount: {stock_data.get('premium_discount')}%")
        print(f"  • Dividend Yield: {stock_data.get('dividend_yield')}%")
        print(f"  • Inception Date: {stock_data.get('inception_date')}")
        print(f"  • Sector: {stock_data.get('sector')}")

        # 3. 점수 계산
        print(f"\n[4/4] Calculating ETF Score...")
        score = calculator.calculate_etf_score(
            stock_data=stock_data,
            expense_ratio=stock_data.get('expense_ratio'),
            premium_discount=stock_data.get('premium_discount'),
            total_assets=stock_data.get('total_assets'),
        )

        print(f"\n{'='*80}")
        print(f"📊 FINAL SCORE: {score}/100")
        print(f"{'='*80}")

        # 점수 해석
        if score >= 70:
            signal = "✅ 매수 (Strong Buy)"
        elif score >= 50:
            signal = "⚠️ 중립 (Hold)"
        else:
            signal = "❌ 주의 (Caution)"

        print(f"Signal: {signal}")

        # 4. 포맷팅 테스트
        print(f"\n{'='*80}")
        print(f"📝 Formatted Strings:")
        print(f"{'='*80}")
        expense_ratio_str = formatter.format_expense_ratio(stock_data.get('expense_ratio'))
        total_assets_str = formatter.format_total_assets(stock_data.get('total_assets'), is_korean=False)
        premium_discount_str = formatter.format_premium_discount(stock_data.get('premium_discount'))

        print(f"  • Expense Ratio: {expense_ratio_str}")
        print(f"  • Total Assets: {total_assets_str}")
        print(f"  • Premium/Discount: {premium_discount_str}")

        print(f"\n✅ Test PASSED for {ticker}\n")

    except Exception as e:
        print(f"\n❌ Test FAILED for {ticker}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 테스트 함수"""
    print("\n" + "="*80)
    print("🚀 ETF Analysis Feature Test Suite")
    print("="*80)

    # 테스트할 ETF 리스트
    test_etfs = [
        ("SPY", "SPDR S&P 500 ETF - Large-cap equity, low expense ratio"),
        ("QQQ", "Invesco QQQ Trust - Tech-focused, moderate expense ratio"),
        ("VOO", "Vanguard S&P 500 ETF - Ultra-low expense ratio"),
    ]

    results = []

    for ticker, description in test_etfs:
        print(f"\n📌 {description}")
        try:
            test_etf_analysis(ticker)
            results.append((ticker, "✅ PASSED"))
        except Exception as e:
            results.append((ticker, f"❌ FAILED: {str(e)}"))

    # 최종 요약
    print("\n" + "="*80)
    print("📊 Test Summary")
    print("="*80)
    for ticker, status in results:
        print(f"  {ticker}: {status}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
