from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class SearchResult(BaseModel):
    score: float
    document_id: int
    filename: str
    chunk_id: int
    page_number: int
    text: str


class SearchResponse(BaseModel):
    results: list[SearchResult]