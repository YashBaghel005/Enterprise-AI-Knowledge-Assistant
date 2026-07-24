from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.db.models.user import User
from app.repositories.chat_message import (
    delete_messages_by_conversation,
    get_messages_by_conversation,
)

from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)

from app.services.rag_service import rag_service

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return await rag_service.answer(
        db=db,
        user_id=current_user.id,
        question=request.question,
        conversation_id=request.conversation_id,
    )


@router.post("/stream")
def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    token_generator, conversation_id = rag_service.answer_stream(
        db=db,
        user_id=current_user.id,
        question=request.question,
        conversation_id=request.conversation_id,
    )

    return StreamingResponse(
        token_generator,
        media_type="text/plain",
        headers={"X-Conversation-Id": conversation_id},
    )


@router.get(
    "/history",
    response_model=list[ChatMessageResponse],
)
def get_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return get_messages_by_conversation(db, conversation_id, current_user.id)


@router.delete("/history")
def clear_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    deleted_count = delete_messages_by_conversation(db, conversation_id, current_user.id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return {
        "message": "Chat history deleted successfully"
    }