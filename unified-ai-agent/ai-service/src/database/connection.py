"""Database connection and session lifecycle management for Milestone 7.

Provides connection pooling, engine initialization, session context management,
safe credential masking, and connection health verification.
"""
from __future__ import annotations

import logging
import re
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

from src.config.settings import get_settings
from src.database.models import Base

logger = logging.getLogger(__name__)

# Global engine and sessionmaker singletons
_ENGINE: Optional[Engine] = None
_SESSION_FACTORY: Optional[sessionmaker] = None


def mask_connection_url(url: str) -> str:
    """Sanitize connection URL by masking password field for safe logging."""
    if not url:
        return ""
    return re.sub(r":([^:@]+)@", r":***@", url)


def get_engine(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """Create or return existing SQLAlchemy engine.
    
    If database_url is provided, a dedicated engine is instantiated (useful for tests).
    Otherwise, the cached global engine configured via application settings is used.
    """
    global _ENGINE

    if database_url:
        return _build_engine(database_url, echo=echo)

    if _ENGINE is None:
        settings = get_settings()
        url = settings.get_database_url()
        _ENGINE = _build_engine(url, echo=echo)
        logger.info(f"Database engine initialized for {mask_connection_url(url)}")

    return _ENGINE


def _build_engine(url: str, echo: bool = False) -> Engine:
    """Build and configure SQLAlchemy engine with connection pooling."""
    settings = get_settings()

    if url.startswith("sqlite"):
        # SQLite configuration (e.g. for testing in-memory or file)
        connect_args = {"check_same_thread": False}
        if ":memory:" in url:
            return create_engine(
                url,
                connect_args=connect_args,
                poolclass=StaticPool,
                echo=echo,
            )
        return create_engine(url, connect_args=connect_args, echo=echo)

    # MySQL / PyMySQL configuration with robust connection pooling
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=settings.mysql_pool_size,
        max_overflow=settings.mysql_max_overflow,
        pool_recycle=settings.mysql_pool_recycle,
        pool_timeout=settings.mysql_pool_timeout,
        pool_pre_ping=True,
        echo=echo,
    )


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """Get or create sessionmaker bound to the given engine."""
    global _SESSION_FACTORY

    target_engine = engine or get_engine()
    if engine is not None:
        return sessionmaker(
            bind=target_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            bind=target_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    return _SESSION_FACTORY


@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Transactional context manager for database sessions.
    
    Automatically commits on normal exit and rolls back if an unhandled exception occurs.
    Guarantees session cleanup in finally block.
    """
    factory = get_session_factory(engine)
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection_health(engine: Optional[Engine] = None) -> Dict[str, Any]:
    """Perform a safe health check ping (SELECT 1) against the database.
    
    Never exposes passwords in log output or error dictionaries.
    """
    target_engine = engine or get_engine()
    masked_url = mask_connection_url(str(target_engine.url))
    start_time = time.perf_counter()

    try:
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "healthy": True,
            "latency_ms": elapsed_ms,
            "url": masked_url,
            "error": None,
        }
    except SQLAlchemyError as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # Redact any passwords that might appear in error string
        sanitized_error = mask_connection_url(str(exc))
        logger.warning(f"Database health check failed for {masked_url}: {sanitized_error}")
        return {
            "healthy": False,
            "latency_ms": elapsed_ms,
            "url": masked_url,
            "error": sanitized_error,
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        sanitized_error = mask_connection_url(str(exc))
        logger.warning(f"Unexpected health check error for {masked_url}: {sanitized_error}")
        return {
            "healthy": False,
            "latency_ms": elapsed_ms,
            "url": masked_url,
            "error": sanitized_error,
        }


def init_db(engine: Optional[Engine] = None) -> None:
    """Create all database tables defined in Base.metadata."""
    target_engine = engine or get_engine()
    Base.metadata.create_all(bind=target_engine)


def drop_db(engine: Optional[Engine] = None) -> None:
    """Drop all database tables defined in Base.metadata."""
    target_engine = engine or get_engine()
    Base.metadata.drop_all(bind=target_engine)
