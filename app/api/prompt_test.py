from fastapi import APIRouter

from app.services.prompt_builder import PromptBuilder

router = APIRouter()


@router.get("/test-prompt")
async def test_prompt():

    prompt = PromptBuilder.build(
        question="What is FastAPI?",
        chunks=[
            "FastAPI is a modern Python framework.",
            "It is very fast.",
            "It supports async programming."
        ],
        history=[
            "User: Hello",
            "Assistant: Hi! How can I help?"
        ]
    )

    return {
        "prompt": prompt
    }