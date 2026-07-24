from pathlib import Path
from uuid import uuid4

import fitz
import pytest
from fastapi.testclient import TestClient

from app.app import app
from app.core.security import create_access_token
from app.db.base import Base
from app.db.models.documents import Document
from app.db.models.user import User
from app.db.sessions import SessionLocal, engine
from app.services import document as document_service


def make_sample_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Sample PDF content for testing.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture(scope="module", autouse=True)
def ensure_tables_exist():
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_user(db_session):
    user = User(
        name="Test User",
        email=f"test-{uuid4().hex}@example.com",
        password_hash="hashed-password",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    db_session.query(Document).filter(Document.user_id == user.id).delete(
        synchronize_session=False,
    )
    db_session.delete(user)
    db_session.commit()


def test_upload_document_saves_metadata_and_file(tmp_path: Path, monkeypatch, db_session, test_user):
    upload_dir = tmp_path / "uploads"
    original_upload_to_storage = document_service.upload_to_storage

    def upload_to_temp_storage(file, storage_path, stored_filename):
        return original_upload_to_storage(file, upload_dir, stored_filename)

    monkeypatch.setattr(document_service, "upload_to_storage", upload_to_temp_storage)

    sample_pdf_bytes = make_sample_pdf_bytes()

    client = TestClient(app)
    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {create_access_token(test_user.id)}"},
        files={
            "file": (
                "sample.pdf",
                sample_pdf_bytes,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()

    assert payload["original_filename"] == "sample.pdf"
    assert payload["mime_type"] == "application/pdf"
    assert payload["upload_status"] == "ready"
    assert payload["file_size"] == len(sample_pdf_bytes)
    assert payload["id"] > 0
    assert payload["created_at"]

    stored_files = list(upload_dir.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == sample_pdf_bytes

    verify_db = SessionLocal()
    try:
        document = verify_db.query(Document).filter(Document.id == payload["id"]).first()
        assert document is not None
        assert document.original_filename == "sample.pdf"
        assert document.mime_type == "application/pdf"
        assert document.upload_status == "ready"
        assert Path(document.storage_path).exists()
        assert Path(document.storage_path).read_bytes() == sample_pdf_bytes
    finally:
        verify_db.close()
