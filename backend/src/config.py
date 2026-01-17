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

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
