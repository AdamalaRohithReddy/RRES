"""Health check endpoints (Liveness vs. Readiness)."""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Response, status

from src.config.settings import get_settings
from src.database.connection import check_connection_health
from src.vector_store.qdrant_store import QdrantVectorStore
from src.embeddings.sentence_transformer_embedder import get_embedder

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
def liveness_probe() -> Dict[str, str]:
    """Lightweight liveness probe verifying HTTP event loop responsiveness."""
    return {"status": "UP"}


@router.get("/ready")
def readiness_probe(response: Response) -> Dict[str, Any]:
    """Readiness probe evaluating operational status of core dependencies."""
    settings = get_settings()
    components: Dict[str, Any] = {}
    is_ready = True

    # 1. MySQL Database check
    db_health = check_connection_health()
    if db_health.get("healthy"):
        components["mysql"] = {"status": "UP", "database": settings.mysql_database, "latency_ms": db_health.get("latency_ms")}
    else:
        components["mysql"] = {"status": "DOWN", "error": db_health.get("error")}
        is_ready = False

    # 2. Qdrant Vector Store check
    try:
        vs = QdrantVectorStore()
        count = vs.count()
        components["vector_store"] = {
            "status": "UP",
            "collection": settings.qdrant_collection_name,
            "document_chunks": count,
        }
    except Exception as e:
        logger.warning(f"Health check Qdrant warning: {e}")
        components["vector_store"] = {"status": "DOWN", "error": str(e)}
        is_ready = False

    # 3. Embeddings Model check
    try:
        embedder = get_embedder()
        components["embeddings"] = {
            "status": "UP",
            "model": settings.embedding_model_name,
            "dimension": embedder.dimension,
        }
    except Exception as e:
        logger.warning(f"Health check Embedder warning: {e}")
        components["embeddings"] = {"status": "DOWN", "error": str(e)}
        is_ready = False

    # 4. LLM status check (Does NOT make service DOWN if quota exhausted!)
    if not settings.openai_api_key:
        components["llm"] = {
            "status": "DEGRADED",
            "state": "disabled",
            "notice": "No OPENAI_API_KEY configured. Direct tool fallback active.",
        }
    else:
        components["llm"] = {
            "status": "DEGRADED",
            "state": "configured",
            "notice": "OpenAI API key configured. Live or direct tool fallback active.",
        }

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "DOWN", "ready": False, "components": components}

    overall_status = "DEGRADED" if components["llm"]["status"] == "DEGRADED" else "UP"
    return {"status": overall_status, "ready": True, "components": components}
