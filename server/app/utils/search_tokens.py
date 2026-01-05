"""
검색 인덱스를 위한 토큰 생성 유틸리티

이 모듈은 prefix 기반 검색을 지원하기 위한 토큰 생성 함수를 제공합니다.
"""

from typing import Optional


def build_prefix_tokens(text: Optional[str]) -> set[str]:
    """
    주어진 문자열에서 prefix 기반 검색 토큰을 생성합니다.

    공백을 모두 제거하고, 영문은 소문자로 변환한 후,
    첫 글자부터 시작하여 점진적으로 길이를 늘려가며 prefix 토큰을 생성합니다.

    Args:
        text: 토큰을 생성할 문자열 (None 가능)

    Returns:
        생성된 prefix 토큰들의 집합

    Examples:
        >>> sorted(build_prefix_tokens("삼성전자"))
        ['삼', '삼성', '삼성전', '삼성전자']

        >>> tokens = build_prefix_tokens("Samsung Electronics")
        >>> 's' in tokens and 'samsung' in tokens and 'samsungelectronics' in tokens
        True

        >>> sorted(build_prefix_tokens("005930"))
        ['0', '00', '005', '0059', '00593', '005930']

        >>> build_prefix_tokens("")
        set()

        >>> build_prefix_tokens(None)
        set()

        >>> sorted(build_prefix_tokens("  Apple  "))
        ['a', 'ap', 'app', 'appl', 'apple']

        >>> tokens = build_prefix_tokens("TSLA")
        >>> sorted(tokens)
        ['t', 'ts', 'tsl', 'tsla']
    """
    # None 체크
    if text is None:
        return set()

    # 공백 제거 및 소문자 변환
    cleaned = text.replace(" ", "").lower()

    # 빈 문자열 체크
    if not cleaned:
        return set()

    # prefix 토큰 생성
    tokens = set()
    for i in range(1, len(cleaned) + 1):
        tokens.add(cleaned[:i])

    return tokens
