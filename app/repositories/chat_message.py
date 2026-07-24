from sqlalchemy.orm import Session

from app.db.models.chat_message import ChatMessage


def get_messages_by_conversation(
    db: Session,
    conversation_id: str,
    user_id: int,
) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.user_id == user_id,
        )
        .order_by(ChatMessage.created_at)
        .all()
    )


def delete_messages_by_conversation(
    db: Session,
    conversation_id: str,
    user_id: int,
) -> int:
    deleted_count = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.user_id == user_id,
        )
        .delete(synchronize_session=False)
    )

    db.commit()

    return deleted_count
