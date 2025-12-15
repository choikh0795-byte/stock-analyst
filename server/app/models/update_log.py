from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class UpdateLog(Base):
    """
    서비스 업데이트 이력을 저장하는 테이블 모델.
    """

    __tablename__ = "update_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    version = Column(String, nullable=True)
    category = Column(String, nullable=False)
    content = Column(String, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<UpdateLog(id={self.id}, version={self.version}, "
            f"category={self.category}, created_at={self.created_at})>"
        )

