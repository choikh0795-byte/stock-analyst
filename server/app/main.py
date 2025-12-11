from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    FastAPI 애플리케이션을 생성하고 설정합니다.
    
    Returns:
        FastAPI: 설정된 FastAPI 애플리케이션 인스턴스
    """
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # API 라우터 등록
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        """루트 엔드포인트 - 서버 상태 확인용"""
        return {"status": "ok"}
    
    logger.info(f"{settings.API_TITLE} v{settings.API_VERSION} 초기화 완료")
    
    return app


# 애플리케이션 인스턴스 생성
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

