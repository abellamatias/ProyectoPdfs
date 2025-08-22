from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_DIR: Path = Path(__file__).resolve().parent
    ROOT_DIR: Path = APP_DIR.parent
    STORAGE_DIR: Path = ROOT_DIR / "storage"
    PDF_STORAGE_DIR: Path = STORAGE_DIR / "pdfs"
    DATABASE_URL: str = f"sqlite:///{(ROOT_DIR / 'db.sqlite3').as_posix()}"
    CORS_ALLOW_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*",
    ]
    PDFS_STATIC_MOUNT: str = "/files/pdfs"
    CLASSIFIER_API_URL: str = "https://2ca077df075c.ngrok-free.app/upload-pdf"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


def ensure_dirs() -> None:
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
