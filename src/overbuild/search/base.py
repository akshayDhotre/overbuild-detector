from abc import ABC, abstractmethod

from overbuild.api.models import SearchResult


class SearchProvider(ABC):
    """Base class for async search providers."""

    @abstractmethod
    async def search(self, query: str, language: str | None = None) -> list[SearchResult]:
        """Search provider and return normalized results."""
