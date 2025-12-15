from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.dependencies import get_update_log_service
from app.schemas.update_log import UpdateLogResponse
from app.services.update_log_service import UpdateLogService

router = APIRouter(prefix="/api/updates", tags=["updates"])


@router.get("/", response_model=List[UpdateLogResponse])
async def list_update_logs(
    update_log_service: UpdateLogService = Depends(get_update_log_service),
) -> List[UpdateLogResponse]:
    """
    업데이트 로그 전체를 최신순으로 반환합니다.
    """
    try:
        return update_log_service.get_all_logs()
    except SQLAlchemyError as exc:
        # 서비스 레이어에서 로깅되므로 여기서는 사용자용 예외로 변환
        raise HTTPException(status_code=500, detail="업데이트 로그 조회 중 오류가 발생했습니다.") from exc

