import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
