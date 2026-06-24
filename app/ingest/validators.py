"""Validate uploaded file types and sizes."""

from fastapi import HTTPException, UploadFile

from app.config import Settings, get_settings


def validate_file(file: UploadFile, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    allowed = (
        settings.allowed_image_types
        | settings.allowed_pdf_types
        | settings.allowed_audio_types
    )
    content_type = file.content_type or ""
    if content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: image, PDF, audio.",
        )
