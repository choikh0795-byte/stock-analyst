from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Base 클래스 생성 (모든 모델이 상속받을 클래스)
Base = declarative_base()

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    echo=False  # SQL 쿼리 로깅 (개발 시 True로 변경 가능)
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 함수
    
    FastAPI의 Depends에서 사용할 수 있도록 Generator로 구현합니다.
    요청이 끝나면 자동으로 세션이 닫힙니다.
    
    Yields:
        Session: SQLAlchemy 세션 객체
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"[Database] 세션 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()

