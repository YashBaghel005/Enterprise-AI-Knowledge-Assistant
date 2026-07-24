from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.dependencies import get_db
from app.db.models.documents import Document
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.embedding_service import embedding_service
from app.services.vector_service import VectorService

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
):

    vector_service = VectorService()

    query_embedding = embedding_service.generate_embedding(request.query)

    matches = vector_service.search(
        query_embedding,
        request.limit,
    )

    # ---------------------------------------------
    # Get Filenames for Matches
    # ---------------------------------------------

    document_ids = []

    for match in matches:
        if match["document_id"] not in document_ids:
            document_ids.append(match["document_id"])

    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()

    filename_by_document_id = {}

    for document in documents:
        filename_by_document_id[document.id] = document.original_filename

    # ---------------------------------------------
    # Build Results
    # ---------------------------------------------

    results = []

    for match in matches:

        similarity = 1 - match["_distance"]

        if similarity < settings.SIMILARITY_THRESHOLD:
            continue

        results.append(
            SearchResult(
                score=similarity,
                document_id=match["document_id"],
                filename=filename_by_document_id.get(match["document_id"], "Unknown"),
                chunk_id=match["chunk_id"],
                page_number=match["page_number"],
                text=match["text"],
            )
        )

    return SearchResponse(results=results)