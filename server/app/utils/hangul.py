"""
한글 처리 유틸리티 함수 모음

유니코드 한글 음절 범위: 0xAC00(가) ~ 0xD7A3(힣)
- 초성: 19개
- 중성: 21개
- 종성: 28개
- 계산 공식: (코드포인트 - 0xAC00) // (21 * 28) = 초성 인덱스
"""

from typing import Final

# 한글 초성 테이블 (19개)
INITIAL_CONSONANTS: Final[tuple[str, ...]] = (
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ',
    'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ',
    'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ',
    'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
)

# 한글 음절 유니코드 범위
HANGUL_SYLLABLE_START: Final[int] = 0xAC00  # '가'
HANGUL_SYLLABLE_END: Final[int] = 0xD7A3    # '힣'

# 중성, 종성 개수
MEDIAL_COUNT: Final[int] = 21
FINAL_COUNT: Final[int] = 28


def extract_initial_consonants(text: str) -> str:
    """
    한글 문자열에서 초성만 추출하여 반환합니다.

    유니코드 한글 음절(가-힣) 범위의 문자만 처리하며,
    한글이 아닌 문자(영문, 숫자, 특수문자 등)는 무시됩니다.

    Args:
        text: 초성을 추출할 문자열

    Returns:
        초성 문자열 (한글이 없으면 빈 문자열)

    Examples:
        >>> extract_initial_consonants("삼성전자")
        'ㅅㅅㅈㅈ'
        >>> extract_initial_consonants("LG에너지솔루션")
        'ㅇㄴㅈㅅㄹㅅ'
        >>> extract_initial_consonants("NAVER")
        ''
        >>> extract_initial_consonants("삼성전자123")
        'ㅅㅅㅈㅈ'
        >>> extract_initial_consonants("카카오뱅크")
        'ㅋㅋㅇㅂㅋ'
        >>> extract_initial_consonants("현대자동차")
        'ㅎㄷㅈㄷㅊ'
        >>> extract_initial_consonants("")
        ''
        >>> extract_initial_consonants("123ABC!@#")
        ''
        >>> extract_initial_consonants("네이버NAVER")
        'ㄴㅇㅂ'
        >>> extract_initial_consonants("SK하이닉스")
        'ㅎㅇㄴㅅ'
    """
    result: list[str] = []

    for char in text:
        code_point = ord(char)

        # 한글 음절 범위 체크
        if HANGUL_SYLLABLE_START <= code_point <= HANGUL_SYLLABLE_END:
            # 초성 인덱스 계산
            syllable_index = code_point - HANGUL_SYLLABLE_START
            initial_index = syllable_index // (MEDIAL_COUNT * FINAL_COUNT)

            # 초성 추가
            result.append(INITIAL_CONSONANTS[initial_index])

    return ''.join(result)


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
