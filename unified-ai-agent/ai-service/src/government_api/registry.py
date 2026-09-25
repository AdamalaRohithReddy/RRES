"""Registry for Government API Adapters (Milestone 8)."""

import logging
from typing import Dict, List, Optional

from src.government_api.adapters.base import BaseGovernmentAPIAdapter
from src.government_api.exceptions import AdapterNotFoundError

logger = logging.getLogger(__name__)


class GovernmentAPIRegistry:
    """Registry maintaining authorized government API adapters."""

    def __init__(self):
        self._adapters: Dict[str, BaseGovernmentAPIAdapter] = {}

    def register(self, adapter: BaseGovernmentAPIAdapter) -> None:
        """Register a verified government API adapter."""
        if not isinstance(adapter, BaseGovernmentAPIAdapter):
            raise TypeError(f"Adapter must inherit from BaseGovernmentAPIAdapter, got {type(adapter).__name__}")
        self._adapters[adapter.adapter_id] = adapter
        logger.info("Registered Government API Adapter: %s", adapter.adapter_id)

    def get(self, adapter_id: str) -> BaseGovernmentAPIAdapter:
        """Retrieve registered adapter or raise AdapterNotFoundError."""
        if adapter_id not in self._adapters:
            raise AdapterNotFoundError(
                f"Government API Adapter '{adapter_id}' is not registered. "
                f"Available adapters: {', '.join(self.list_adapters())}"
            )
        return self._adapters[adapter_id]

    def list_adapters(self) -> List[str]:
        """List all registered adapter IDs."""
        return list(self._adapters.keys())

    def __contains__(self, adapter_id: str) -> bool:
        return adapter_id in self._adapters


_GLOBAL_REGISTRY: Optional[GovernmentAPIRegistry] = None


def get_api_registry() -> GovernmentAPIRegistry:
    """Retrieve singleton GovernmentAPIRegistry instance."""
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = GovernmentAPIRegistry()
    return _GLOBAL_REGISTRY
