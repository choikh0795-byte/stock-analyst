from fastapi import APIRouter
from app.api.v1.endpoints import stocks, assets

api_router = APIRouter()

# 엔드포인트 라우터 등록
api_router.include_router(stocks.router, prefix="/stock", tags=["stocks"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])

