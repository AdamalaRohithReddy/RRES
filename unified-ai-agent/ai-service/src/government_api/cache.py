"""In-memory TTL Cache for public Government API metadata (Milestone 8)."""

import hashlib
import json
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class MetadataCache:
    """Thread-safe TTL cache for public government metadata (e.g. scheme listings).

    SECURITY INVARIANT:
    This cache MUST ONLY be used for public, non-sensitive scheme catalogs and metadata.
    Citizen personal records, Aadhaar, PAN, or certificate verification results MUST NEVER be cached.
    """

    def __init__(self, default_ttl_seconds: int = 300):
        self._default_ttl = default_ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def generate_key(adapter_id: str, operation: str, params: Dict[str, Any]) -> str:
        """Create deterministic SHA256 cache key from operation and canonical parameters."""
        canonical_params = json.dumps(params, sort_keys=True, default=str)
        raw_key = f"{adapter_id}:{operation}:{canonical_params}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if not expired."""
        with self._lock:
            if key not in self._store:
                return None
            expiry, value = self._store[key]
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value with expiration."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expiry = time.time() + ttl
        with self._lock:
            self._store[key] = (expiry, value)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
