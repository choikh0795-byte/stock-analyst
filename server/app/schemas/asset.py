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
    
    # Optional[str]로 변경하여 None(null) 값을 허용합니다.
    name_en: Optional[str] = Field(None, description="영문명")
    name_kr: Optional[str] = Field(None, description="한글명")
    
    # 거래소 및 자산 유형도 데이터 상황에 따라 Optional로 설정하는 것이 안전합니다.
    exchange: Optional[str] = Field(None, description="거래소")
    asset_type: str = Field(..., description="자산 유형 (STOCK_KR, STOCK_US, ETF)")
    
    # DB 모델에 없는 필드들은 기본값을 None으로 설정하여 에러를 방지합니다.
    country: Optional[str] = Field(None, description="국가 코드")
    currency: Optional[str] = Field(None, description="통화 코드")
    search_keywords: Optional[str] = Field(None, description="검색 키워드")

    class Config:
        # Pydantic v2에서는 from_attributes = True를 사용하여 
        # SQLAlchemy 모델 객체를 스키마로 자동 변환합니다.
        from_attributes = True


class AssetSearchResponse(BaseModel):
    """
    자산 검색 응답 스키마
    """
    results: List[AssetSchema] = Field(..., description="검색 결과 리스트")
    total: int = Field(..., description="총 결과 개수")

    class Config:
        from_attributes = True