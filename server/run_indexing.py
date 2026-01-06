#!/usr/bin/env python3
"""
자산 검색 인덱스 생성 스크립트

KIS 마스터 데이터를 기반으로 한국/미국 주식 및 ETF의 검색 인덱스를 생성합니다.

Usage:
    python run_indexing.py [--force] [--kr-only] [--us-only]

Options:
    --force     기존 인덱스를 삭제하고 새로 생성
    --kr-only   한국 주식만 인덱싱
    --us-only   미국 주식만 인덱싱
"""

import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, engine
from app.models.asset_search_index import AssetSearchIndex, AssetType, Base
from app.services.stock.kis_master_service import KisMasterService
from app.services.search.index_builder import AssetSearchIndexBuilder, AssetSourceItem

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_index(db) -> None:
    """
    기존 인덱스를 모두 삭제합니다.

    Args:
        db: 데이터베이스 세션
    """
    logger.info("[RunIndexing] 기존 인덱스 삭제 중...")
    count = db.query(AssetSearchIndex).delete()
    db.commit()
    logger.info(f"[RunIndexing] 기존 인덱스 삭제 완료: {count}개")


def map_market_to_asset_type(market: str) -> AssetType:
    """
    시장 코드를 AssetType으로 매핑합니다.

    Args:
        market: 시장 코드 (KOSPI, KOSDAQ, NASDAQ, NYSE, AMEX)

    Returns:
        AssetType
    """
    if market in ("KOSPI", "KOSDAQ"):
        return AssetType.STOCK_KR
    elif market in ("NASDAQ", "NYSE", "AMEX"):
        return AssetType.STOCK_US
    else:
        # 기본값 (한국 주식)
        return AssetType.STOCK_KR


def index_stocks(
    db,
    kis_service: KisMasterService,
    builder: AssetSearchIndexBuilder,
    kr_only: bool = False,
    us_only: bool = False
) -> int:
    """
    주식 데이터를 인덱싱합니다.

    Args:
        db: 데이터베이스 세션
        kis_service: KIS 마스터 서비스
        builder: 인덱스 빌더
        kr_only: True이면 한국 주식만 인덱싱
        us_only: True이면 미국 주식만 인덱싱

    Returns:
        int: 인덱싱된 종목 수
    """
    # KIS 마스터 데이터 로드
    include_us = not kr_only
    logger.info(f"[RunIndexing] KIS 마스터 데이터 로드 중 (include_us={include_us})...")

    if not kis_service.load_master_data(force_reload=True, include_us=include_us):
        logger.error("[RunIndexing] KIS 마스터 데이터 로드 실패")
        return 0

    # 전체 종목 데이터 가져오기
    all_stocks = kis_service.get_all_stocks()
    logger.info(f"[RunIndexing] 전체 종목 수: {len(all_stocks)}개")

    if not all_stocks:
        logger.warning("[RunIndexing] 인덱싱할 종목이 없습니다.")
        return 0

    # AssetSourceItem으로 변환
    items = []
    for stock in all_stocks:
        market = stock.get("market")

        # 필터링
        if kr_only and market not in ("KOSPI", "KOSDAQ"):
            continue
        if us_only and market not in ("NASDAQ", "NYSE", "AMEX"):
            continue

        asset_type = map_market_to_asset_type(market)

        items.append(AssetSourceItem(
            ticker=stock["ticker"],
            name_kr=stock.get("name_kr"),
            name_en=stock.get("name_en"),
            asset_type=asset_type,
            exchange=stock.get("exchange", market)
        ))

    logger.info(f"[RunIndexing] 인덱싱할 종목 수: {len(items)}개")

    # 인덱스 빌드
    count = builder.build(items)
    return count


def main():
    """
    메인 함수
    """
    # 커맨드 라인 인자 파싱
    parser = argparse.ArgumentParser(description='자산 검색 인덱스 생성')
    parser.add_argument('--force', action='store_true', help='기존 인덱스를 삭제하고 새로 생성')
    parser.add_argument('--kr-only', action='store_true', help='한국 주식만 인덱싱')
    parser.add_argument('--us-only', action='store_true', help='미국 주식만 인덱싱')
    args = parser.parse_args()

    # 테이블 생성 (없는 경우)
    logger.info("[RunIndexing] 데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)

    # 데이터베이스 세션 생성
    db = SessionLocal()

    try:
        # 기존 인덱스 삭제 (--force 옵션)
        if args.force:
            clear_index(db)

        # KIS 마스터 서비스 초기화
        kis_service = KisMasterService()

        # 인덱스 빌더 초기화
        builder = AssetSearchIndexBuilder(db)

        # 인덱싱 시작
        logger.info("[RunIndexing] 인덱싱 시작...")
        start_time = __import__('time').time()

        count = index_stocks(
            db,
            kis_service,
            builder,
            kr_only=args.kr_only,
            us_only=args.us_only
        )

        elapsed = __import__('time').time() - start_time
        logger.info(f"[RunIndexing] 인덱싱 완료: {count}개 종목 (소요 시간: {elapsed:.2f}초)")

        # 인덱스 통계
        total_count = db.query(AssetSearchIndex).count()
        kr_count = db.query(AssetSearchIndex).filter(
            AssetSearchIndex.asset_type == AssetType.STOCK_KR
        ).count()
        us_count = db.query(AssetSearchIndex).filter(
            AssetSearchIndex.asset_type == AssetType.STOCK_US
        ).count()
        etf_count = db.query(AssetSearchIndex).filter(
            AssetSearchIndex.asset_type == AssetType.ETF
        ).count()

        logger.info(
            f"[RunIndexing] 인덱스 통계: "
            f"전체={total_count}, "
            f"한국주식={kr_count}, "
            f"미국주식={us_count}, "
            f"ETF={etf_count}"
        )

    except Exception as e:
        logger.exception(f"[RunIndexing] 인덱싱 중 오류 발생: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()

    logger.info("[RunIndexing] 모든 작업 완료")


if __name__ == "__main__":
    main()
