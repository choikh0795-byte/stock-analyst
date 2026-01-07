from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import update_log_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models import StockAnalysisLog
from app.services.stock import StockService  # [추가] 서비스 로딩을 위해 import
from app.services.autocomplete.memory_index import AutocompleteMemoryIndex

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    서버 수명 주기 관리 (Startup & Shutdown)
    서버가 시작되기 전 무거운 작업을 미리 처리합니다.
    """
    # [Startup] 서버 시작 시 실행
    logger.info("🚀 [Startup] 서버 시작 프로세스 진입")

    # 자동완성 메모리 인덱스 초기화
    # 중요: 이것이 DB 접근이 발생하는 유일한 시점입니다 (startup 시).
    # 이후 API 요청 처리 중에는 절대로 DB에 접근하지 않습니다.
    if settings.DATABASE_URL:
        try:
            logger.info("[Startup] 자동완성 메모리 인덱스 로딩 시작...")
            memory_index = AutocompleteMemoryIndex()

            # DB 세션 생성 및 데이터 로드 (startup 시에만 DB 접근)
            db = SessionLocal()
            try:
                memory_index.load_from_db(db)
                logger.info(
                    f"[Startup] ✅ 자동완성 메모리 인덱스 로딩 완료 "
                    f"(총 {memory_index.get_asset_count()}개 자산)"
                )
                logger.info("[Startup] ℹ️  이후 자동완성 요청은 메모리만 사용 (DB 접근 없음)")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[Startup] ❌ 자동완성 메모리 인덱스 로딩 실패: {e}")
            logger.warning("[Startup] 자동완성 기능이 비활성화됩니다.")
    else:
        logger.warning("[Startup] DATABASE_URL이 없어 자동완성 메모리 인덱스를 건너뜁니다.")

    yield  # 애플리케이션 작동 구간 (여기서부터 API 요청 수신)

    # [Shutdown] 서버 종료 시 실행 (필요 시 리소스 정리)
    logger.info("👋 [Shutdown] 서버 종료 프로세스 진행 중...")


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
        redoc_url="/redoc",
        lifespan=lifespan  # [추가] 수명 주기 관리자 등록
    )
    
    # 데이터베이스 테이블 자동 생성
    if settings.DATABASE_URL:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("[Database] 테이블 생성 완료")
        except Exception as e:
            logger.error(f"[Database] 테이블 생성 실패: {e}")
    else:
        logger.warning("[Database] DATABASE_URL이 설정되지 않아 테이블 생성을 건너뜁니다.")
    
    # CORS 설정
    logger.info(f"[CORS] 설정된 허용 출처: {settings.CORS_ORIGINS}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, PUT, DELETE 등)
        allow_headers=["*"],  # 모든 헤더 허용
    )
    
    # API 라우터 등록
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(update_log_router)
    
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
    # 로컬 개발 시에는 워커 1개이므로 한 번만 로딩됩니다.
    # 배포 시(gunicorn 등) 워커가 여러 개면 워커 수만큼 로딩 로그가 뜹니다.
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "ok"}    