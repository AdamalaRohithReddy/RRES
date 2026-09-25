"""Abstract base class for Government API Adapters."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from src.government_api.exceptions import GovernmentAPIError
from src.government_api.models import GovernmentSource, NormalizedGovernmentResponse


class BaseGovernmentAPIAdapter(ABC):
    """Abstract base class for all official Government API adapters."""

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Unique identifier of the adapter."""
        pass

    @property
    @abstractmethod
    def source(self) -> GovernmentSource:
        """Associated authoritative government source metadata."""
        pass

    def validate_operation(self, operation: str) -> None:
        """Verify that the requested operation is permitted for this adapter's source."""
        if operation not in self.source.allowed_operations:
            raise GovernmentAPIError(
                f"Unauthorized operation '{operation}' for adapter '{self.adapter_id}'. "
                f"Permitted operations: {', '.join(self.source.allowed_operations)}"
            )

    @abstractmethod
    def execute(self, operation: str, params: Dict[str, Any]) -> NormalizedGovernmentResponse:
        """Execute a permitted operation and return a normalized government response."""
        pass
