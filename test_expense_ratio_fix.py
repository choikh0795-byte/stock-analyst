#!/usr/bin/env python3
"""
ETF 운용보수 추출 테스트
funds_data API를 사용한 새로운 방식 검증
"""

import sys
import os

# 서버 경로를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

try:
    import yfinance as yf
except ImportError:
    print("❌ yfinance not installed")
    sys.exit(1)


def test_funds_data_api(ticker_symbol: str):
    """funds_data API를 사용해서 운용보수 추출 테스트"""
    print(f"\n{'='*80}")
    print(f"🔍 Testing: {ticker_symbol}")
    print(f"{'='*80}\n")

    ticker = yf.Ticker(ticker_symbol)

    # 1. 기존 방식 (annualReportExpenseRatio)
    print("[1] 레거시 방식 (annualReportExpenseRatio):")
    info = ticker.info
    legacy_expense = info.get('annualReportExpenseRatio')
    if legacy_expense is not None:
        print(f"    ✅ annualReportExpenseRatio: {legacy_expense} ({legacy_expense * 100:.2f}%)")
    else:
        print(f"    ❌ annualReportExpenseRatio: None")

    # 2. 새로운 방식 (funds_data.fund_operations)
    print("\n[2] 신규 방식 (funds_data.fund_operations):")
    try:
        if hasattr(ticker, 'funds_data'):
            print("    ✅ ticker.funds_data 존재")
            funds_data = ticker.funds_data

            if funds_data is not None:
                print("    ✅ funds_data is not None")

                if hasattr(funds_data, 'fund_operations'):
                    print("    ✅ funds_data.fund_operations 존재")
                    fund_ops = funds_data.fund_operations

                    if fund_ops is not None:
                        print(f"    ✅ fund_operations 타입: {type(fund_ops)}")

                        # DataFrame인 경우
                        if hasattr(fund_ops, 'to_dict'):
                            print("\n    📊 fund_operations (DataFrame):")
                            print(fund_ops)

                            fund_ops_dict = fund_ops.to_dict('records')
                            if fund_ops_dict and len(fund_ops_dict) > 0:
                                expense_ratio = fund_ops_dict[0].get('Annual Report Expense Ratio')
                                print(f"\n    💰 Annual Report Expense Ratio: {expense_ratio}")
                                if expense_ratio is not None:
                                    ratio = float(expense_ratio)
                                    if ratio < 1.0:
                                        ratio = ratio * 100
                                    print(f"    ✅ 최종 운용보수: {ratio:.2f}%")
                        # dict인 경우
                        elif isinstance(fund_ops, dict):
                            print(f"\n    📊 fund_operations (dict): {fund_ops}")
                            expense_ratio = fund_ops.get('Annual Report Expense Ratio')
                            print(f"\n    💰 Annual Report Expense Ratio: {expense_ratio}")
                    else:
                        print("    ❌ fund_operations is None")
                else:
                    print("    ❌ funds_data.fund_operations 없음")
            else:
                print("    ❌ funds_data is None")
        else:
            print("    ❌ ticker.funds_data 없음")
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()

    # 3. 실제 ETFCalculator 테스트
    print("\n[3] ETFCalculator 테스트:")
    try:
        from app.services.stock.etf_calculator import ETFCalculator
        calculator = ETFCalculator()
        expense_ratio = calculator.extract_expense_ratio(ticker, info)
        if expense_ratio is not None:
            print(f"    ✅ ETFCalculator.extract_expense_ratio(): {expense_ratio}%")
        else:
            print(f"    ❌ ETFCalculator.extract_expense_ratio(): None")
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    print("\n" + "="*80)
    print("🚀 ETF 운용보수 추출 테스트 (funds_data API)")
    print("="*80)

    test_etfs = [
        "SPY",   # SPDR S&P 500 ETF
        "QQQ",   # Invesco QQQ Trust
        "VOO",   # Vanguard S&P 500 ETF
    ]

    for ticker_symbol in test_etfs:
        test_funds_data_api(ticker_symbol)

    print("\n" + "="*80)
    print("✅ 테스트 완료!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
