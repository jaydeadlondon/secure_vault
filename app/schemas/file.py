from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class FileResponse(BaseModel):
    id: UUID
    original_filename: str
    size: int
    content_type: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
