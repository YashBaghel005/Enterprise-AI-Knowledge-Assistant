from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    VECTOR_DB_PATH: str = "storage/vectordb"
    VECTOR_TABLE_NAME: str = "knowledge"
    UPLOAD_DIR: str = "uploads"

    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.5

    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.2
    groq_max_tokens: int = 1024

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()