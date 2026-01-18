from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "M-SUITE"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./m_suite.db"

    # JWT
    secret_key: str = "your-secret-key-change-in-production-msuite2024"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Yield-Drive AI
    default_platform_fee_percent: float = 15.0

    # LLM Provider Settings
    llm_provider: str = "auto"  # "cloud", "local", "mock", "auto"
    llm_fallback_enabled: bool = True

    # LLM (Qwen Cloud) Settings
    qwen_api_key: str = ""
    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"
    qwen_model_fast: str = "qwen-turbo"
    qwen_max_tokens: int = 2048
    qwen_temperature: float = 0.7
    qwen_timeout: int = 30

    # Ollama (Local) Settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:1.7b"
    ollama_model_fast: str = "qwen3:1.7b"
    ollama_timeout: int = 60
    ollama_num_ctx: int = 4096
    ollama_temperature: float = 0.7

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
