"""
자산(Asset) 관련 Pydantic 스키마 정의

자산 검색 API의 요청/응답 모델을 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class AssetSchema(BaseModel):
    """
    자산 정보 스키마
    """
    id: int = Field(..., description="자산 ID")
    ticker: str = Field(..., description="티커 심볼")
    name_en: str = Field(..., description="영문명")
    name_kr: Optional[str] = Field(None, description="한글명")
    exchange: str = Field(..., description="거래소")
    asset_type: str = Field(..., description="자산 유형 (주식, ETF 등)")
    country: str = Field(..., description="국가 코드")
    currency: str = Field(..., description="통화 코드")
    search_keywords: Optional[str] = Field(None, description="검색 키워드")

    class Config:
        from_attributes = True


class AssetSearchResponse(BaseModel):
    """
    자산 검색 응답 스키마
    """
    results: List[AssetSchema] = Field(..., description="검색 결과 리스트")
    total: int = Field(..., description="총 결과 개수")

    class Config:
        from_attributes = True
