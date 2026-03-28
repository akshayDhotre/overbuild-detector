from datetime import UTC, datetime, timedelta
from typing import cast

import httpx

from overbuild.api.models import SearchResult, SearchSource
from overbuild.config import settings
from overbuild.search.cache import get_cached, set_cached


def _is_maintained(last_updated: str | None) -> bool | None:
    if not last_updated:
        return None
    try:
        ts = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        return ts >= datetime.now(UTC) - timedelta(days=365)
    except ValueError:
        return None


async def search_github(query: str, language: str | None = None) -> list[SearchResult]:
    cache_key = f"github:{query.lower()}:{(language or '').lower()}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cast(list[SearchResult], cached)

    search_query = query
    if language:
        search_query = f"{search_query} language:{language}"

    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": search_query, "sort": "stars", "order": "desc", "per_page": 10},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    results: list[SearchResult] = []
    for item in data.get("items", []):
        results.append(
            SearchResult(
                source=SearchSource.GITHUB,
                name=item.get("full_name") or item.get("name", ""),
                description=(item.get("description") or "")[:200],
                url=item.get("html_url", ""),
                stars=item.get("stargazers_count"),
                dependents_count=None,
                last_updated=item.get("updated_at"),
                is_maintained=_is_maintained(item.get("updated_at")),
                license=(item.get("license") or {}).get("spdx_id"),
                language=item.get("language"),
                package_manager=None,
                relevance_score=0.0,
            )
        )

    set_cached(cache_key, results)
    return results
