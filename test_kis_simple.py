#!/usr/bin/env python3
"""
KIS 마스터 파일 원시 구조 분석 (pandas 없이)
"""
import ssl
import urllib.request
import zipfile
from pathlib import Path

cache_dir = Path("/tmp/kis_test")
cache_dir.mkdir(parents=True, exist_ok=True)


def download_and_extract(url, zip_name, mst_name):
    """다운로드 및 압축 해제"""
    mst_path = cache_dir / mst_name

    if mst_path.exists():
        print(f"✓ 기존 파일 사용: {mst_name}")
        return mst_path

    zip_path = cache_dir / zip_name

    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        print(f"다운로드 중: {url}")
        urllib.request.urlretrieve(url, str(zip_path))
        print(f"✓ 다운로드 완료: {zip_path.stat().st_size:,} bytes")
    except Exception as e:
        print(f"✗ 다운로드 실패: {e}")
        return None

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(cache_dir)
        zip_path.unlink()
        print(f"✓ 압축 해제 완료")
        return mst_path
    except Exception as e:
        print(f"✗ 압축 해제 실패: {e}")
        return None


def analyze_file(file_path, market):
    """파일 구조 분석"""
    print(f"\n{'='*80}")
    print(f"{market} 마스터 파일 분석")
    print(f"{'='*80}")

    try:
        with open(file_path, "r", encoding="cp949") as f:
            lines = f.readlines()

        total_lines = len(lines)
        print(f"총 라인 수: {total_lines:,}")

        if total_lines == 0:
            print("✗ 파일이 비어있음!")
            return

        # 첫 3줄 길이 분석
        print(f"\n라인 길이 분석 (처음 5줄):")
        for i in range(min(5, total_lines)):
            line = lines[i]
            print(f"  Line {i+1}: {len(line)} 문자 (개행 포함)")

        # 첫 줄 상세 분석
        first_line = lines[0]
        line_len = len(first_line.rstrip('\n\r'))
        print(f"\n첫 번째 라인 길이 (개행 제외): {line_len}")

        # Part1 분리 (앞 30자 정도)
        part1 = first_line[:30]
        print(f"\nPart1 (처음 30자):")
        print(f"  단축코드(9): '{part1[0:9]}'")
        print(f"  표준코드(12): '{part1[9:21]}'")
        print(f"  한글명(9+): '{part1[21:30]}'")

        # Part2 길이 추정
        # KOSPI: 228자, KOSDAQ: 222자
        if market == "KOSPI":
            part2_suffix = 228
        else:
            part2_suffix = 222

        print(f"\n{market} Part2 예상 길이: {part2_suffix}")
        print(f"실제 Part2 시작 위치: {line_len - part2_suffix}")

        # Part2 샘플
        part2_start = line_len - part2_suffix
        if part2_start > 0:
            part2 = first_line[part2_start:part2_start + 50]
            print(f"Part2 샘플 (처음 50자): '{part2}'")

            # Part2 필드 계산
            if market == "KOSPI":
                field_specs = [
                    2, 1, 4, 4, 4, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 9, 5, 5, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 2, 1, 1, 1, 1, 9, 5,
                    9, 9, 9, 5, 9, 8, 9, 3, 1, 1,
                    1, 9, 9, 1, 1, 1, 9, 9, 9, 5, 9
                ]
            else:
                field_specs = [
                    2, 1, 4, 4, 4, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 1, 1, 1, 1, 1, 9, 5, 5, 1,
                    1, 1, 2, 1, 1, 1, 2, 2, 2, 3,
                    1, 3, 12, 12, 8, 15, 21, 2, 7, 1,
                    1, 1, 1, 9, 9, 9, 5, 9, 8, 9,
                    3, 1, 1, 1, 1, 1
                ]

            field_sum = sum(field_specs)
            print(f"\n필드 스펙 총합: {field_sum}")
            print(f"Part2 예상 길이: {part2_suffix}")
            print(f"차이: {field_sum - part2_suffix}")

            if field_sum != part2_suffix:
                print(f"\n⚠️  경고: 필드 스펙과 Part2 길이가 일치하지 않음!")
            else:
                print(f"\n✓ 필드 스펙이 정확함")

        else:
            print(f"\n✗ 오류: Part2 시작 위치가 음수! ({part2_start})")
            print(f"   라인 길이가 너무 짧거나 part2_suffix 값이 잘못됨")

        # 샘플 데이터 파싱 (처음 3줄)
        print(f"\n샘플 데이터 (처음 3종목):")
        print(f"{'='*80}")

        for i in range(min(3, total_lines)):
            line = lines[i]
            line_len = len(line.rstrip('\n\r'))

            # Part1
            short_code = line[0:9].rstrip()
            standard_code = line[9:21].rstrip()
            name = line[21:line_len - part2_suffix].strip()

            print(f"\n종목 {i+1}:")
            print(f"  단축코드: {short_code}")
            print(f"  표준코드: {standard_code}")
            print(f"  종목명: {name}")

    except Exception as e:
        print(f"✗ 분석 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("\n" + "="*80)
    print("KIS 마스터 파일 구조 분석 (원시 파싱)")
    print("="*80 + "\n")

    # KOSPI
    print("\n[1] KOSPI 마스터 파일")
    print("-" * 80)
    kospi_file = download_and_extract(
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
        "kospi_code.zip",
        "kospi_code.mst"
    )

    if kospi_file:
        analyze_file(kospi_file, "KOSPI")

    # KOSDAQ
    print("\n\n[2] KOSDAQ 마스터 파일")
    print("-" * 80)
    kosdaq_file = download_and_extract(
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
        "kosdaq_code.zip",
        "kosdaq_code.mst"
    )

    if kosdaq_file:
        analyze_file(kosdaq_file, "KOSDAQ")

    print("\n" + "="*80)
    print("분석 완료")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
