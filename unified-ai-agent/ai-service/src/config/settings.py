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

        # OpenAI LLM settings (Milestone 2)
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

        # MySQL Relational Database Settings (Milestone 7)
        self.mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
        self.mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
        self.mysql_database: str = os.getenv("MYSQL_DATABASE", "citizen_ai_db")
        self.mysql_user: str = os.getenv("MYSQL_USER", "root")
        self.mysql_password: Optional[str] = os.getenv("MYSQL_PASSWORD", None)
        self.mysql_pool_size: int = int(os.getenv("MYSQL_POOL_SIZE", "5"))
        self.mysql_max_overflow: int = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))
        self.mysql_pool_recycle: int = int(os.getenv("MYSQL_POOL_RECYCLE", "3600"))
        self.mysql_pool_timeout: int = int(os.getenv("MYSQL_POOL_TIMEOUT", "30"))
        # Strictly False by default: a MySQL failure must NEVER silently return mock citizen data
        self.allow_mock_fallback: bool = os.getenv("ALLOW_MOCK_FALLBACK", "false").lower() in ("true", "1", "yes")

        # Database URL override (e.g. for testing with sqlite:///:memory: or full custom connection string)
        self.database_url: Optional[str] = os.getenv("DATABASE_URL", None)

        # Government API Integration (Milestone 8)
        self.gov_api_enabled: bool = os.getenv("GOV_API_ENABLED", "false").lower() in ("true", "1", "yes")
        self.gov_api_environment: str = os.getenv("GOV_API_ENVIRONMENT", "sandbox").lower()
        self.gov_api_timeout_seconds: float = float(os.getenv("GOV_API_TIMEOUT_SECONDS", "10.0"))
        self.gov_api_max_retries: int = int(os.getenv("GOV_API_MAX_RETRIES", "2"))
        self.gov_api_cache_ttl_seconds: int = int(os.getenv("GOV_API_CACHE_TTL_SECONDS", "300"))
        self.gov_api_rate_limit_per_sec: float = float(os.getenv("GOV_API_RATE_LIMIT_PER_SEC", "5.0"))
        self.apisetu_base_url: str = os.getenv("APISETU_BASE_URL", "https://apisetu.gov.in/api/v1")
        self.apisetu_client_id: Optional[str] = os.getenv("APISETU_CLIENT_ID", None)
        self.apisetu_api_key: Optional[str] = os.getenv("APISETU_API_KEY", None)
        self.data_gov_in_base_url: str = os.getenv("DATA_GOV_IN_BASE_URL", "https://api.data.gov.in/")
        self.data_gov_in_api_key: Optional[str] = os.getenv("DATA_GOV_IN_API_KEY", None)
        self.run_live_gov_api_tests: bool = os.getenv("RUN_LIVE_GOV_API_TESTS", "false").lower() in ("true", "1", "yes")

        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def get_database_url(self) -> str:
        """Construct database connection URL using PyMySQL driver."""
        if self.database_url:
            return self.database_url
        import urllib.parse
        encoded_pwd = urllib.parse.quote_plus(self.mysql_password) if self.mysql_password else ""
        pwd_part = f":{encoded_pwd}" if encoded_pwd else ""
        return f"mysql+pymysql://{self.mysql_user}{pwd_part}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"

    def get_masked_database_url(self) -> str:
        """Construct sanitized connection string with password redacted for safe logging."""
        if self.database_url:
            # Mask potential password in custom URL
            import re
            return re.sub(r":([^:@]+)@", r":***@", self.database_url)
        pwd_mask = ":***" if self.mysql_password else ""
        return f"mysql+pymysql://{self.mysql_user}{pwd_mask}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton of settings."""
    return Settings()
