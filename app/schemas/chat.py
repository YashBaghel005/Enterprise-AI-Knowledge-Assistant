from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):
    document_id: int
    filename: str
    page_number: int
    chunk_id: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    conversation_id: str

class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)