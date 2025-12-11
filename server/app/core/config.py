from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    환경변수에서 자동으로 로드됩니다.
    """
    # API 설정
    API_TITLE: str = "Stock Analysis API"
    API_VERSION: str = "1.0.0"
    
    # CORS 설정
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173"
    ]
    
    # OpenAI 설정
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()

