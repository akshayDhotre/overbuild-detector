from typing import cast

import httpx

from overbuild.api.models import SearchResult, SearchSource
from overbuild.search.cache import get_cached, set_cached


async def search_npm(query: str, language: str | None = None) -> list[SearchResult]:
    _ = language
    cache_key = f"npm:{query.lower()}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cast(list[SearchResult], cached)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://registry.npmjs.org/-/v1/search",
            params={"text": query, "size": 10},
        )
        response.raise_for_status()
        data = response.json()

    results: list[SearchResult] = []
    for item in data.get("objects", []):
        package = item.get("package", {})
        score = item.get("score", {}).get("final", 0.0)
        results.append(
            SearchResult(
                source=SearchSource.NPM,
                name=package.get("name", ""),
                description=(package.get("description") or "")[:200],
                url=package.get("links", {}).get("npm")
                or package.get("links", {}).get("repository")
                or "",
                downloads_monthly=None,
                last_updated=package.get("date"),
                is_maintained=True,
                license=package.get("license"),
                language="javascript",
                package_manager="npm",
                relevance_score=max(0.0, min(float(score), 1.0)),
            )
        )

    set_cached(cache_key, results)
    return results
