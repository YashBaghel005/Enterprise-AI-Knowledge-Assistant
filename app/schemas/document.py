from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_size: int
    mime_type: str
    upload_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
