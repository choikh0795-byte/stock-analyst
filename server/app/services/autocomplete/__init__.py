"""
자동완성 관련 서비스 모듈 (메모리 기반)

**중요**: 이 모듈의 모든 Service는 자동완성 요청 처리 시 DB에 절대 접근하지 않습니다.
DB 접근은 서버 startup 시 메모리 인덱스 로딩 시에만 발생합니다.

**모듈 구성**:
- autocomplete_service.py: 자동완성 검색 Service (메모리만 사용)
- memory_index.py: 메모리 인덱스 (Singleton, startup 시 DB에서 로드)
- index_builder.py: 검색 인덱스 구축 (배치 작업용, DB 접근)

**일반 검색은 여기 아님**:
일반 검색(full-text, DB 기반)은 services/stock/provider.py를 사용하세요.
"""

from .index_builder import AssetSearchIndexBuilder, AssetSourceItem
from .autocomplete_service import AutocompleteService
from .memory_index import AutocompleteMemoryIndex

__all__ = [
    "AssetSearchIndexBuilder",
    "AssetSourceItem",
    "AutocompleteService",
    "AutocompleteMemoryIndex"
]
