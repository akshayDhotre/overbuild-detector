from datetime import UTC, datetime, timedelta
from typing import cast

import httpx

from overbuild.api.models import SearchResult, SearchSource
from overbuild.config import settings
from overbuild.search.cache import get_cached, set_cached

BASE_URL = "https://libraries.io/api/search"


def _is_maintained(last_release: str | None) -> bool | None:
    if not last_release:
        return None
    try:
        ts = datetime.fromisoformat(last_release.replace("Z", "+00:00"))
        return ts >= datetime.now(UTC) - timedelta(days=365)
    except ValueError:
        return None


async def search_librariesio(query: str, language: str | None = None) -> list[SearchResult]:
    cache_key = f"librariesio:{query.lower()}:{(language or '').lower()}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cast(list[SearchResult], cached)
    if not settings.librariesio_api_key.strip():
        return []

    params: dict[str, str | int] = {
        "q": query,
        "api_key": settings.librariesio_api_key,
        "per_page": 10,
    }
    platform_map = {
        "python": "pypi",
        "javascript": "npm",
        "typescript": "npm",
        "node": "npm",
        "rust": "cargo",
        "go": "go",
        "ruby": "rubygems",
        "java": "maven",
        "csharp": "nuget",
        "php": "packagist",
    }
    if language and language.lower() in platform_map:
        params["platforms"] = platform_map[language.lower()]

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    results: list[SearchResult] = []
    for item in data:
        license_str: str | None
        licenses = item.get("licenses")
        if isinstance(licenses, list):
            license_str = ", ".join(licenses[:3])
        else:
            license_str = licenses or None
        results.append(
            SearchResult(
                source=SearchSource.LIBRARIES_IO,
                name=item.get("name", ""),
                description=(item.get("description") or "")[:200],
                url=item.get("repository_url") or item.get("homepage") or "",
                stars=item.get("stars"),
                dependents_count=item.get("dependents_count")
                or item.get("dependent_repositories_count"),
                last_updated=item.get("latest_release_published_at"),
                is_maintained=_is_maintained(item.get("latest_release_published_at")),
                license=license_str,
                language=item.get("language"),
                package_manager=item.get("platform"),
                relevance_score=0.0,
            )
        )

    set_cached(cache_key, results)
    return results
