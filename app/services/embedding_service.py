from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logger import logger


class EmbeddingService:

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):

        if EmbeddingService._model is None:

            logger.info("Loading BGE Model...")

            EmbeddingService._model = SentenceTransformer(
                settings.EMBEDDING_MODEL
            )

            logger.info("Model Loaded")

    def generate_embedding(self, text):

        self._load_model()

        embedding = self._model.encode(
            text,
            normalize_embeddings=True,
        )

        logger.info("Generated 1 Embedding")

        return embedding.tolist()

    def generate_embeddings(self, texts):

        self._load_model()

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
        )

        logger.info(f"Generated {len(texts)} Embeddings")

        return embeddings.tolist()
    

embedding_service = EmbeddingService()