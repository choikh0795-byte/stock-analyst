from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UpdateLogResponse(BaseModel):
    id: int
    created_at: datetime
    version: Optional[str] = None
    category: str
    content: str

    class Config:
        from_attributes = True

