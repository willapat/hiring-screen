from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    model_name: str = "gemini-3.1-flash-lite"
    mock_llm: bool = False
    cors_origin: str = "http://localhost:3000"
    max_upload_bytes: int = 5 * 1024 * 1024
    max_upload_pages: int = 10
    build_dir: str = "/tmp/hiring-screen-builds"


@lru_cache
def get_settings() -> Settings:
    return Settings()
