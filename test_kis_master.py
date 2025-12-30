#!/usr/bin/env python3
"""
KIS 마스터 파일 파싱 테스트 스크립트
독립적으로 실행 가능
"""
import logging
import os
import ssl
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KisMasterTester:
    """KIS 마스터 파일 테스트용 간소화 클래스"""

    KOSPI_URL = "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip"
    KOSDAQ_URL = "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip"

    # KOSPI Part2 필드 (228자리)
    PART2_FIELD_SPECS_KOSPI = [
        2, 1, 4, 4, 4, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 9, 5, 5, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 2, 1, 1, 1, 1, 9, 5,
        9, 9, 9, 5, 9, 8, 9, 3, 1, 1,
        1, 9, 9, 1, 1, 1, 9, 9, 9, 5, 9
    ]

    # KOSDAQ Part2 필드 (222자리)
    PART2_FIELD_SPECS_KOSDAQ = [
        2, 1, 4, 4, 4, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        1, 1, 1, 1, 1, 1, 9, 5, 5, 1,
        1, 1, 2, 1, 1, 1, 2, 2, 2, 3,
        1, 3, 12, 12, 8, 15, 21, 2, 7, 1,
        1, 1, 1, 9, 9, 9, 5, 9, 8, 9,
        3, 1, 1, 1, 1, 1
    ]

    def __init__(self):
        self.cache_dir = Path("/tmp/kis_master_test")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_and_extract(self, url: str, zip_name: str, mst_name: str) -> Optional[Path]:
        """마스터 파일 다운로드 및 압축 해제"""
        mst_path = self.cache_dir / mst_name

        # 이미 있으면 재사용
        if mst_path.exists():
            logger.info(f"기존 파일 사용: {mst_path}")
            return mst_path

        zip_path = self.cache_dir / zip_name

        # 다운로드
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            logger.info(f"다운로드 중: {url}")
            urllib.request.urlretrieve(url, str(zip_path))
            logger.info(f"다운로드 완료: {zip_path.stat().st_size} bytes")
        except Exception as e:
            logger.error(f"다운로드 실패: {e}")
            return None

        # 압축 해제
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.cache_dir)
            zip_path.unlink()
            logger.info(f"압축 해제 완료: {mst_path}")
            return mst_path
        except Exception as e:
            logger.error(f"압축 해제 실패: {e}")
            return None

    def parse_file(self, file_path: Path, market: str) -> int:
        """마스터 파일 파싱"""
        if market == "KOSPI":
            part2_suffix = 228
            part1_columns = ['단축코드', '표준코드', '한글명']
            field_specs = self.PART2_FIELD_SPECS_KOSPI
        else:  # KOSDAQ
            part2_suffix = 222
            part1_columns = ['단축코드', '표준코드', '한글종목명']
            field_specs = self.PART2_FIELD_SPECS_KOSDAQ

        try:
            tmp_file1 = self.cache_dir / f"{market}_part1.tmp"
            tmp_file2 = self.cache_dir / f"{market}_part2.tmp"

            # 파일 분리
            logger.info(f"{market} 파싱 시작...")
            with open(file_path, "r", encoding="cp949") as f:
                wf1 = open(tmp_file1, "w", encoding="utf-8")
                wf2 = open(tmp_file2, "w", encoding="utf-8")

                line_count = 0
                for row in f:
                    line_count += 1
                    try:
                        # Part1: 앞부분
                        rf1 = row[0:len(row) - part2_suffix]
                        rf1_1 = rf1[0:9].rstrip()  # 단축코드
                        rf1_2 = rf1[9:21].rstrip()  # 표준코드
                        rf1_3 = rf1[21:].strip()   # 한글명
                        wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')

                        # Part2: 뒷부분
                        rf2 = row[-part2_suffix:]
                        wf2.write(rf2)
                    except Exception as e:
                        logger.error(f"{market} Line {line_count} 파싱 오류: {e}")
                        logger.error(f"Line length: {len(row)}, Expected suffix: {part2_suffix}")
                        continue

                wf1.close()
                wf2.close()
                logger.info(f"{market} 총 {line_count}줄 처리")

            # Part1 CSV 읽기
            df1 = pd.read_csv(tmp_file1, header=None, names=part1_columns, encoding='utf-8')
            logger.info(f"{market} Part1 로드: {len(df1)}행")

            # Part2 고정폭 읽기
            field_sum = sum(field_specs)
            logger.info(f"{market} Part2 필드 총합: {field_sum} (기대값: {part2_suffix})")

            df2 = pd.read_fwf(tmp_file2, widths=field_specs, encoding='utf-8')
            logger.info(f"{market} Part2 로드: {len(df2)}행")

            # 병합
            df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)

            # 샘플 출력
            logger.info(f"\n{market} 샘플 데이터 (처음 3개):")
            print(df[part1_columns].head(3))

            # 임시 파일 삭제
            tmp_file1.unlink(missing_ok=True)
            tmp_file2.unlink(missing_ok=True)

            return len(df)

        except Exception as e:
            logger.error(f"{market} 파싱 실패: {e}", exc_info=True)
            return 0


def main():
    print("\n" + "="*80)
    print("KIS 마스터 파일 파싱 테스트")
    print("="*80 + "\n")

    tester = KisMasterTester()

    # KOSPI 테스트
    print("\n[1] KOSPI 마스터 파일 테스트")
    print("-" * 80)
    kospi_file = tester.download_and_extract(
        tester.KOSPI_URL,
        "kospi_code.zip",
        "kospi_code.mst"
    )

    if kospi_file:
        kospi_count = tester.parse_file(kospi_file, "KOSPI")
        print(f"✓ KOSPI 파싱 완료: {kospi_count}개 종목\n")
    else:
        print("✗ KOSPI 다운로드 실패\n")

    # KOSDAQ 테스트
    print("\n[2] KOSDAQ 마스터 파일 테스트")
    print("-" * 80)
    kosdaq_file = tester.download_and_extract(
        tester.KOSDAQ_URL,
        "kosdaq_code.zip",
        "kosdaq_code.mst"
    )

    if kosdaq_file:
        kosdaq_count = tester.parse_file(kosdaq_file, "KOSDAQ")
        print(f"✓ KOSDAQ 파싱 완료: {kosdaq_count}개 종목\n")
    else:
        print("✗ KOSDAQ 다운로드 실패\n")

    print("\n" + "="*80)
    print("테스트 완료")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
