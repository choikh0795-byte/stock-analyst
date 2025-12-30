#!/usr/bin/env python3
"""
KOSDAQ 마스터 파일 파싱 테스트 스크립트
"""
import sys
import os

# 서버 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.services.stock.kis_master_service import KisMasterService

def test_kosdaq_parsing():
    """KOSDAQ 마스터 파일 파싱 테스트"""

    print("=" * 70)
    print("KOSDAQ 마스터 파일 파싱 테스트")
    print("=" * 70)

    # 필드 스펙 검증
    print("\n1. 필드 스펙 검증")
    print("-" * 70)
    field_count = len(KisMasterService.PART2_FIELD_SPECS_KOSDAQ)
    column_count = len(KisMasterService.PART2_COLUMNS_KOSDAQ)
    field_sum = sum(KisMasterService.PART2_FIELD_SPECS_KOSDAQ)

    print(f"  필드 개수: {field_count}")
    print(f"  컬럼 개수: {column_count}")
    print(f"  필드 합계: {field_sum}")
    print(f"  개수 일치: {'✓' if field_count == column_count else '✗'}")

    if field_count != column_count:
        print(f"\n  ⚠️  오류: 필드 개수({field_count}) != 컬럼 개수({column_count})")
        return False

    # 마스터 서비스 초기화
    print("\n2. KisMasterService 초기화")
    print("-" * 70)
    service = KisMasterService(enable_naver_fallback=True)
    print("  ✓ 초기화 완료")

    # 마스터 데이터 로드
    print("\n3. 마스터 데이터 로드")
    print("-" * 70)
    try:
        success = service.load_master_data()
        if success:
            print("  ✓ 마스터 데이터 로드 성공")
        else:
            print("  ✗ 마스터 데이터 로드 실패")
            return False
    except Exception as e:
        print(f"  ✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

    # KOSDAQ 종목 검색 테스트
    print("\n4. KOSDAQ 종목 검색 테스트")
    print("-" * 70)

    test_stocks = [
        ("카카오", "035720.KQ"),
        ("셀트리온", "068270.KQ"),
        ("에코프로비엠", "247540.KQ"),
    ]

    for name, expected_ticker in test_stocks:
        ticker = service.get_ticker_by_name(name)
        if ticker == expected_ticker:
            print(f"  ✓ {name}: {ticker}")
        else:
            print(f"  ✗ {name}: 예상={expected_ticker}, 실제={ticker}")

    # 상세 정보 확인
    print("\n5. KOSDAQ 종목 상세 정보")
    print("-" * 70)

    detail = service.get_detail_by_ticker("035720.KQ")
    if detail:
        print(f"  티커: 035720.KQ")
        print(f"  종목명: {detail.get('name')}")
        print(f"  시장: {detail.get('market')}")
        print(f"  섹터코드: {detail.get('sector_code')}")
        print(f"  종목코드: {detail.get('stock_code')}")
        print(f"  상장일자: {detail.get('listing_date')}")
        print(f"  예비필드1: {detail.get('예비필드1', 'N/A')}")
        print(f"  예비필드2: {detail.get('예비필드2', 'N/A')}")
    else:
        print("  ✗ 상세 정보 조회 실패")

    print("\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = test_kosdaq_parsing()
    sys.exit(0 if success else 1)
