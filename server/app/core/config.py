from pydantic_settings import BaseSettings
from typing import List
import os


def get_cors_origins() -> List[str]:
    """
    CORS 허용 출처를 환경변수에서 가져옵니다.
    환경변수가 없거나 "*"인 경우 모든 출처를 허용합니다.
    """
    cors_env = os.getenv("CORS_ORIGINS", "")
    if not cors_env or cors_env == "*":
        return ["*"]
    # 쉼표로 구분된 여러 출처를 리스트로 변환
    return [origin.strip() for origin in cors_env.split(",") if origin.strip()]


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    환경변수에서 자동으로 로드됩니다.
    """
    # API 설정
    API_TITLE: str = "Stock Analysis API"
    API_VERSION: str = "1.0.0"
    
    # CORS 설정
    # 환경변수 CORS_ORIGINS가 있으면 사용, 없으면 모든 출처 허용 (배포 환경 대응)
    CORS_ORIGINS: List[str] = get_cors_origins()
    
    # OpenAI 설정
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 데이터베이스 설정
    DATABASE_URL: str = ""

    # KIS API 설정
    KIS_APP_KEY: str
    KIS_APP_SECRET: str
    KIS_BASE_URL: str = "https://openapi.koreainvestment.com:9443"
    KIS_CANO: str | None = None  # 계좌번호 앞 8자리, Optional
    KIS_ACNT_PRDT_CD: str | None = None  # 계좌번호 뒤 2자리, Optional
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()

