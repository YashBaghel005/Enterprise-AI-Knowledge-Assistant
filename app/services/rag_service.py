import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger

from app.db.models.chat_message import ChatMessage
from app.db.models.documents import Document

from app.schemas.chat import ChatResponse, Source

from app.services.embedding_service import embedding_service
from app.services.vector_service import vector_service
from app.services.prompt_builder import PromptBuilder
from app.services.llm_service import llm_service


MAX_HISTORY_MESSAGES = 10


def save_message(db: Session, conversation_id: str, user_id: int, role: str, content: str):
    """
    Small helper so we don't repeat the same 3 lines every time we save a message.
    """

    message = ChatMessage(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
    )

    db.add(message)
    db.commit()


class RAGService:
    """
    Orchestrates the complete Retrieval-Augmented Generation pipeline.
    """

    async def answer(
        self,
        db: Session,
        user_id: int,
        question: str,
        conversation_id: str | None = None,
    ) -> ChatResponse:

        logger.info("Starting RAG Pipeline")

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        # ---------------------------------------------
        # Load Conversation History
        # ---------------------------------------------

        previous_messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        previous_messages = previous_messages[-MAX_HISTORY_MESSAGES:]

        history = []

        for message in previous_messages:
            if message.role == "user":
                history.append(f"User: {message.content}")
            else:
                history.append(f"Assistant: {message.content}")

        # ---------------------------------------------
        # Generate Embedding
        # ---------------------------------------------

        embedding = embedding_service.generate_embedding(
            question
        )

        # ---------------------------------------------
        # Retrieve Relevant Chunks
        # ---------------------------------------------

        results = vector_service.search(
            embedding=embedding,
            limit=settings.TOP_K,
        )

        # ---------------------------------------------
        # Filter by Similarity Threshold
        # ---------------------------------------------

        relevant_results = []

        for result in results:
            similarity_score = 1 - result["_distance"]

            if similarity_score >= settings.SIMILARITY_THRESHOLD:
                relevant_results.append(result)

        results = relevant_results

        if not results:

            logger.warning("No chunks passed the similarity threshold.")

            answer = "I couldn't find enough information in the uploaded documents."

            save_message(db, conversation_id, user_id, "user", question)
            save_message(db, conversation_id, user_id, "assistant", answer)

            return ChatResponse(
                answer=answer,
                sources=[],
                conversation_id=conversation_id,
            )

        # ---------------------------------------------
        # Extract Context
        # ---------------------------------------------

        chunks = [
            result["text"]
            for result in results
        ]

        # ---------------------------------------------
        # Build Prompt
        # ---------------------------------------------

        prompt = PromptBuilder.build(
            question=question,
            chunks=chunks,
            history=history,
        )

        # ---------------------------------------------
        # Generate Answer
        # ---------------------------------------------

        answer = await llm_service.generate(
            prompt
        )

        # ---------------------------------------------
        # Save Conversation Memory
        # ---------------------------------------------

        save_message(db, conversation_id, user_id, "user", question)
        save_message(db, conversation_id, user_id, "assistant", answer)

        # ---------------------------------------------
        # Get Filenames for Sources
        # ---------------------------------------------

        document_ids = []

        for result in results:
            if result["document_id"] not in document_ids:
                document_ids.append(result["document_id"])

        documents = db.query(Document).filter(Document.id.in_(document_ids)).all()

        filename_by_document_id = {}

        for document in documents:
            filename_by_document_id[document.id] = document.original_filename

        # ---------------------------------------------
        # Build Sources
        # ---------------------------------------------

        sources = []

        for result in results:

            sources.append(
                Source(
                    document_id=result["document_id"],
                    filename=filename_by_document_id.get(result["document_id"], "Unknown"),
                    chunk_id=result["chunk_id"],
                    page_number=result["page_number"],
                )
            )

        logger.info("RAG Pipeline Completed")

        return ChatResponse(
            answer=answer,
            sources=sources,
            conversation_id=conversation_id,
        )

    def answer_stream(
        self,
        db: Session,
        user_id: int,
        question: str,
        conversation_id: str | None = None,
    ):
        """
        Same pipeline as answer(), but the answer is streamed token by token.
        Returns (token_generator, conversation_id).
        """

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        # ---------------------------------------------
        # Load Conversation History
        # ---------------------------------------------

        previous_messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        previous_messages = previous_messages[-MAX_HISTORY_MESSAGES:]

        history = []

        for message in previous_messages:
            if message.role == "user":
                history.append(f"User: {message.content}")
            else:
                history.append(f"Assistant: {message.content}")

        # ---------------------------------------------
        # Retrieve Relevant Chunks
        # ---------------------------------------------

        embedding = embedding_service.generate_embedding(question)

        results = vector_service.search(
            embedding=embedding,
            limit=settings.TOP_K,
        )

        relevant_results = []

        for result in results:
            similarity_score = 1 - result["_distance"]

            if similarity_score >= settings.SIMILARITY_THRESHOLD:
                relevant_results.append(result)

        results = relevant_results

        if not results:

            fallback_answer = "I couldn't find enough information in the uploaded documents."

            def fallback_generator():
                yield fallback_answer

                save_message(db, conversation_id, user_id, "user", question)
                save_message(db, conversation_id, user_id, "assistant", fallback_answer)

            return fallback_generator(), conversation_id

        chunks = [
            result["text"]
            for result in results
        ]

        prompt = PromptBuilder.build(
            question=question,
            chunks=chunks,
            history=history,
        )

        def token_generator():
            full_answer = ""

            for token in llm_service.generate_stream(prompt):
                full_answer += token
                yield token

            save_message(db, conversation_id, user_id, "user", question)
            save_message(db, conversation_id, user_id, "assistant", full_answer)

        return token_generator(), conversation_id


rag_service = RAGService()
