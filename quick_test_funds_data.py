#!/usr/bin/env python3
"""
funds_data API 실제 작동 여부 긴급 테스트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

print("="*80)
print("yfinance funds_data API 실제 작동 테스트")
print("="*80)

try:
    import yfinance as yf
    print(f"\n✅ yfinance 버전: {yf.__version__}")
except ImportError as e:
    print(f"\n❌ yfinance import 실패: {e}")
    sys.exit(1)

# SPY로 테스트
ticker_symbol = "SPY"
print(f"\n테스트 티커: {ticker_symbol}")

try:
    ticker = yf.Ticker(ticker_symbol)
    print("✅ Ticker 객체 생성 성공")

    # 1. funds_data 속성 확인
    print("\n[1] funds_data 속성 확인:")
    if hasattr(ticker, 'funds_data'):
        print("    ✅ ticker.funds_data 존재")
        try:
            funds_data = ticker.funds_data
            print(f"    ✅ funds_data 타입: {type(funds_data)}")
            print(f"    ✅ funds_data 내용: {funds_data}")

            # 2. fund_operations 확인
            if hasattr(funds_data, 'fund_operations'):
                print("\n[2] fund_operations 확인:")
                print("    ✅ fund_operations 존재")
                fund_ops = funds_data.fund_operations
                print(f"    타입: {type(fund_ops)}")
                print(f"    내용:\n{fund_ops}")
            else:
                print("\n[2] ❌ fund_operations 속성 없음")
                print(f"    funds_data 사용 가능한 속성: {dir(funds_data)}")

        except Exception as e:
            print(f"    ❌ funds_data 접근 실패: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("    ❌ ticker.funds_data 속성 없음")
        print(f"    ticker 사용 가능한 속성 샘플: {[attr for attr in dir(ticker) if not attr.startswith('_')][:20]}")

    # 3. 레거시 info 확인
    print("\n[3] 레거시 info.annualReportExpenseRatio 확인:")
    info = ticker.info
    expense = info.get('annualReportExpenseRatio')
    print(f"    값: {expense}")

    # 4. info에서 expense/ratio 관련 모든 필드 찾기
    print("\n[4] info에서 'expense' 또는 'ratio' 포함된 모든 필드:")
    expense_fields = {k: v for k, v in info.items() if ('expense' in k.lower() or 'ratio' in k.lower()) and v is not None}
    if expense_fields:
        for k, v in expense_fields.items():
            print(f"    • {k}: {v}")
    else:
        print("    ❌ 관련 필드 없음")

    # 5. Yahoo Finance에서 직접 확인할 수 있는 다른 방법들
    print("\n[5] 기타 ETF 관련 필드 확인:")
    etf_fields = ['totalAssets', 'navPrice', 'yield', 'fundFamily', 'category', 'beta', 'threeYearAverageReturn']
    for field in etf_fields:
        value = info.get(field)
        status = "✅" if value is not None else "❌"
        print(f"    {status} {field}: {value}")

except Exception as e:
    print(f"\n❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("테스트 종료")
print("="*80)
