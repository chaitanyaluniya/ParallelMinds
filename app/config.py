from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    whisper_model: str = "base"

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    max_upload_size_mb: int = 25
    max_files_per_request: int = 10

    upload_dir: Path = Path("uploads")
    allowed_image_types: set[str] = {"image/jpeg", "image/png", "image/jpg"}
    allowed_pdf_types: set[str] = {"application/pdf"}
    allowed_audio_types: set[str] = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/mp4",
        "audio/x-m4a",
        "audio/m4a",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
