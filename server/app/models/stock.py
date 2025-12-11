from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base
from typing import Dict, Any
import json


class StockAnalysisLog(Base):
    """
    주식 분석 결과를 캐싱하기 위한 데이터 모델
    
    Attributes:
        ticker: 종목 코드 (Primary Key)
        price: 저장 당시 가격
        analysis_json: AI 분석 결과 및 주요 지표 전체를 JSON 형태로 저장
        updated_at: 마지막 업데이트 시간 (자동 갱신)
    """
    __tablename__ = "stock_analysis_logs"
    
    ticker = Column(String(20), primary_key=True, index=True, nullable=False)
    price = Column(Float, nullable=False)
    analysis_json = Column(JSON, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<StockAnalysisLog(ticker={self.ticker}, price={self.price}, updated_at={self.updated_at})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        모델을 딕셔너리로 변환합니다.
        
        Returns:
            Dict[str, Any]: 모델 데이터를 딕셔너리로 변환한 결과
        """
        return {
            "ticker": self.ticker,
            "price": self.price,
            "analysis_json": self.analysis_json,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

