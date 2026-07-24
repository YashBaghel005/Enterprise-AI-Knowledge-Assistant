from fastapi import APIRouter

from app.services.llm_service import llm_service

router = APIRouter()


@router.get("/test-llm")
async def test_llm():

    response = await llm_service.generate(
        "Explain FastAPI in one sentence."
    )

    return {
        "response": response
    }