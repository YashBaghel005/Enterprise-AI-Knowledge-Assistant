from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.logger import logger

from app.db.models.documents import Document, UploadStatus
from app.repositories.document import create_document, delete_document, get_document_by_id
from app.schemas.document import DocumentResponse

from app.services.pdf_service import PDFService
from app.services.chunk_service import ChunkService
from app.services.embedding_service import embedding_service
from app.services.vector_service import vector_service


ALLOWED_TYPES = [
    "application/pdf",
]

MAX_SIZE = 10 * 1024 * 1024


def upload_to_storage(file, storage_path: Path, stored_filename: str) -> Path:
    storage_path.mkdir(parents=True, exist_ok=True)

    file_path = storage_path / stored_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def upload_document(
    db: Session,
    user_id: int,
    file: UploadFile,
):
    """
    Complete document upload pipeline.

    Validate
        ↓
    Save File
        ↓
    Save Metadata
        ↓
    Extract PDF Text
        ↓
    Create Chunks
        ↓
    Generate Embeddings
        ↓
    Store Vectors
    """

    # ---------------------------------------------------
    # Validate File
    # ---------------------------------------------------

    if not file.filename:
        raise ValueError("Filename is required")

    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("Only PDF files are allowed")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size == 0:
        raise ValueError("File is empty")

    if size > MAX_SIZE:
        raise ValueError("File is too large")

    logger.info("File validation successful")

    # ---------------------------------------------------
    # Save File
    # ---------------------------------------------------

    upload_dir = Path("uploads")

    extension = Path(file.filename).suffix

    stored_name = f"{uuid.uuid4().hex}{extension}"

    file_path = upload_to_storage(file, upload_dir, stored_name)

    logger.info(f"File saved at {file_path}")

    # ---------------------------------------------------
    # Save Metadata
    # ---------------------------------------------------

    document = Document(
        user_id=user_id,
        original_filename=file.filename,
        stored_filename=stored_name,
        storage_path=str(file_path),
        file_size=size,
        mime_type=file.content_type,
        upload_status=UploadStatus.READY.value,
    )

    document = create_document(db, document)

    logger.info(
        f"Document metadata saved (ID={document.id})"
    )

    # ---------------------------------------------------
    # Extract Text
    # ---------------------------------------------------

    pdf_service = PDFService()

    pages = pdf_service.extract_text(
        str(file_path)
    )

    logger.info(
        f"Extracted {len(pages)} pages"
    )

    # ---------------------------------------------------
    # Create Chunks
    # ---------------------------------------------------

    chunk_service = ChunkService()

    chunks = chunk_service.create_chunks(
        pages,
        document.id,
    )

    logger.info(
        f"Created {len(chunks)} chunks"
    )

    # ---------------------------------------------------
    # Generate Embeddings
    # ---------------------------------------------------

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embedding_service.generate_embeddings(
        texts
    )


    # ---------------------------------------------------
    # Store in LanceDB
    # ---------------------------------------------------

    vector_service.insert_chunks(
        chunks,
        embeddings,
    )

    logger.info("Vectors stored successfully")

    return DocumentResponse.model_validate(document)


def delete_uploaded_document(
    db: Session,
    document_id: int,
    user_id: int,
):
    """
    Delete document from disk, Vector DB, and MySQL.
    """

    document = get_document_by_id(db, document_id)

    if document is None:
        raise ValueError("Document not found")

    if document.user_id != user_id:
        raise PermissionError("You do not have access to this document")

    vector_service.delete_document(
        document_id
    )

    file_path = Path(document.storage_path)

    if file_path.exists():
        file_path.unlink()

    delete_document(
        db,
        document_id,
    )

    logger.info(
        f"Deleted document {document_id}"
    )

    return {
        "message": "Document deleted successfully"
    }