"""Application configuration using pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "InfraSphere AI"
    app_env: Literal["development", "staging", "production"] = "development"
    api_prefix: str = "/api/v1"
    version: str = "1.0.0"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/infrasphere.db"

    # Security
    jwt_secret: str = Field(..., min_length=32)
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # LLM
    llm_provider: Literal["mock", "openai", "openai_compatible", "gemini"] = "mock"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    # Embeddings
    embedding_provider: Literal["mock", "sentence_transformers"] = "mock"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Storage
    vector_storage_path: str = "./data/qdrant"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 10

    # External integrations
    ffwc_enabled: bool = False
    ffwc_api_base_url: str = ""
    ffwc_api_key: str = ""
    osm_enabled: bool = False

    # Agent limits
    max_agent_steps: int = 8
    max_agent_retries: int = 2
    max_agent_duration_seconds: int = 120
    max_parallel_agents: int = 3

    # Demo / seed
    enable_demo_data: bool = True
    enable_synthetic_incidents: bool = True

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_async_sqlite(cls, v: str) -> str:
        # Allow sqlite:// shorthand and upgrade to async driver
        if v.startswith("sqlite:///") and not v.startswith("sqlite+aiosqlite"):
            return v.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
