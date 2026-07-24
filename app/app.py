from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.llm import router as llm_router
from app.api.prompt_test import router as prompt_test_router
from app.api.chat import router as chat_router

from app.db.base import Base
from app.db.sessions import engine


app = FastAPI(
    title="AI Backend",
    version="1.0.0"
)

# Create any tables that don't exist yet (e.g. new models added later).
# Existing tables are left untouched.
Base.metadata.create_all(bind=engine)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(llm_router)
app.include_router(prompt_test_router)
app.include_router(chat_router)