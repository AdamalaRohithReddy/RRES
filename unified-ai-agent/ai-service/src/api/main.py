"""FastAPI Application Entrypoint for Python AI Service (Milestone 9)."""
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings
from src.api.routes import health, agent, needs, schemes, eligibility, documents

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler for FastAPI startup and shutdown."""
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("Unified AI Service (FastAPI Layer) starting up...")
    logger.info(f"Host: {settings.ai_service_host}:{settings.ai_service_port}")
    logger.info(f"Database: {settings.mysql_database} on {settings.mysql_host}:{settings.mysql_port}")
    logger.info(f"Qdrant collection: {settings.qdrant_collection_name}")
    logger.info("=" * 60)
    yield
    logger.info("Unified AI Service shutting down cleanly.")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Unified AI Agent Service",
        description="Internal AI service for Citizen Financial & Social Support (RAG, Needs, Eligibility, OCR, Government APIs)",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration (Only allows localhost / internal Spring Boot gateway)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request timing & Correlation ID middleware
    @app.middleware("http")
    async def add_correlation_and_timing(request: Request, call_next):
        start_time = time.perf_counter()
        correlation_id = request.headers.get("X-Correlation-ID", "")
        response = await call_next(request)
        process_time = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(process_time)
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        return response

    # Global Exception Handler (Conforms to RFC 7807 problem details)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "https://errors.unifiedai.gov.in/internal-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An internal error occurred while processing the AI request.",
                "instance": request.url.path,
            },
        )

    # Register routers
    app.include_router(health.router)
    app.include_router(agent.router)
    app.include_router(needs.router)
    app.include_router(schemes.router)
    app.include_router(eligibility.router)
    app.include_router(documents.router)

    return app


app = create_app()
