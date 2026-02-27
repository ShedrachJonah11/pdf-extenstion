from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Auth
    secret_key: str = "change-me-to-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # FAISS
    faiss_persist_dir: str = "./faiss_indexes"

    # Upload
    max_upload_size_mb: int = 50

    # Rate limiting
    rate_limit: str = "20/minute"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def persist_path(self) -> Path:
        path = Path(self.faiss_persist_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
