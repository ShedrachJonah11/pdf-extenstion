from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
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

    # CORS — comma separated, "*" by default for local dev
    cors_allow_origins: str = "*"

    # Logging
    log_level: str = "INFO"

    # LLM call timeout in seconds
    llm_request_timeout: float = 30.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @field_validator("access_token_expire_minutes")
    @classmethod
    def _positive_token_ttl(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        return value

    @field_validator("max_upload_size_mb")
    @classmethod
    def _positive_upload_cap(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be positive")
        return value

    @field_validator("llm_request_timeout")
    @classmethod
    def _positive_llm_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("LLM_REQUEST_TIMEOUT must be positive")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def persist_path(self) -> Path:
        path = Path(self.faiss_persist_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
