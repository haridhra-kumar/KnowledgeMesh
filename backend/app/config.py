import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend (root of backend)
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(BACKEND_DIR / ".env"), str(PROJECT_ROOT / ".env")],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM Settings
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    groq_timeout: float = 8.0

    # Pipeline Safety Limits
    max_llm_extraction_calls: int = 5
    max_relationship_llm_calls: int = 15
    max_candidate_pairs: int = 40

    # Storage paths
    database_path: str = str(BACKEND_DIR / "data" / "knowledgemesh.db")
    upload_dir: str = str(BACKEND_DIR / "data" / "uploads")

    def model_post_init(self, __context) -> None:
        p_db = Path(self.database_path)
        if not p_db.is_absolute():
            clean = str(p_db).replace("backend/", "", 1) if str(p_db).startswith("backend/") else str(p_db)
            self.database_path = str((BACKEND_DIR / clean).resolve())
        p_up = Path(self.upload_dir)
        if not p_up.is_absolute():
            clean_up = str(p_up).replace("backend/", "", 1) if str(p_up).startswith("backend/") else str(p_up)
            self.upload_dir = str((BACKEND_DIR / clean_up).resolve())

    # Network / Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # Extraction & Grounding Thresholds
    grounding_verified_threshold: float = 0.85
    grounding_partial_threshold: float = 0.60
    min_confidence_threshold: float = 0.50

    # Chunker settings
    chunk_size_words: int = 1200
    chunk_overlap_words: int = 150
    max_pages_per_chunk: int = 3

    # Safety limits
    max_upload_size_mb: int = 50

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def ensure_directories(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
