from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(String(255))

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )

    storage_path: Mapped[str] = mapped_column(String(500))

    file_size: Mapped[int] = mapped_column(BigInteger)

    mime_type: Mapped[str] = mapped_column(String(100))

    upload_status: Mapped[str] = mapped_column(
        String(20),
        default=UploadStatus.PENDING.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship(
        "User",
        back_populates="documents",
    )
