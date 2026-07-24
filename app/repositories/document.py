from sqlalchemy.orm import Session

from app.db.models.documents import Document


def create_document(db: Session, document: Document) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents_by_user(db: Session, user_id: int) -> list[Document]:
    return db.query(Document).filter(Document.user_id == user_id).all()


def delete_document(db: Session, document_id: int) -> bool:

    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if document is None:
        return False

    db.delete(document)
    db.commit()

    return True