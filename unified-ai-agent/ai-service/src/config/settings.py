"""Configuration module for RAG foundation."""
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv

# Automatically load .env if present in current directory or ai-service root
current_dir = Path(__file__).resolve().parent
ai_service_root = current_dir.parent.parent
env_path = ai_service_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    """Application settings for AI Service."""

    def __init__(self):
        # Base paths
        self.ai_service_root: Path = ai_service_root
        self.raw_data_dir: Path = Path(os.getenv("RAW_DATA_DIR", str(ai_service_root / "data" / "raw")))
        self.processed_data_dir: Path = Path(os.getenv("PROCESSED_DATA_DIR", str(ai_service_root / "data" / "processed")))

        # Ingestion & OCR detection thresholds
        self.ocr_char_threshold_per_page: int = int(os.getenv("OCR_CHAR_THRESHOLD_PER_PAGE", "50"))

        # Embedding configuration
        self.embedding_model_name: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.embedding_device: str = os.getenv("EMBEDDING_DEVICE", "cpu")
        self.embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))

        # Qdrant configuration
        self.qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "scheme_documents")
        # If QDRANT_URL is set, client connects via HTTP/gRPC. Otherwise, local storage path or in-memory is used.
        self.qdrant_url: Optional[str] = os.getenv("QDRANT_URL", None)
        self.qdrant_api_key: Optional[str] = os.getenv("QDRANT_API_KEY", None)
        qdrant_path_str = os.getenv("QDRANT_PATH", str(self.processed_data_dir / "qdrant_storage"))
        self.qdrant_path: str = qdrant_path_str

        # Retrieval defaults
        self.default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "5"))
        self.score_threshold: float = float(os.getenv("SCORE_THRESHOLD", "0.35"))

        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton of settings."""
    return Settings()
