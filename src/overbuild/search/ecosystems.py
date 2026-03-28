import asyncio
import re
from typing import cast

import httpx

from overbuild.api.models import SearchResult, SearchSource
from overbuild.search.cache import get_cached, set_cached

BASE_URL = "https://packages.ecosyste.ms/api/v1/packages/lookup"
_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "without",
    "rate",
    "limiting",
    "limit",
    "build",
    "tool",
    "script",
    "create",
    "need",
    "add",
    "per",
    "ip",
}

_LANGUAGE_TO_ECOSYSTEM = {
    "python": "pypi",
    "javascript": "npm",
    "typescript": "npm",
    "node": "npm",
    "rust": "cargo",
    "go": "go",
    "ruby": "rubygems",
    "php": "packagist",
    "java": "maven",
    "csharp": "nuget",
}


def _candidate_names(query: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9_+-]+", query.lower())
    candidates: list[str] = []
    for token in tokens:
        if len(token) < 3:
            continue
        if token in _STOPWORDS:
            continue
        if token not in candidates:
            candidates.append(token)
    return candidates[:3] if candidates else ["fastapi"]


def _to_result(item: dict[str, object]) -> SearchResult:
    repo_metadata = item.get("repo_metadata")
    stars = None
    if isinstance(repo_metadata, dict):
        star_value = repo_metadata.get("stargazers_count") or repo_metadata.get("stars")
        if isinstance(star_value, int):
            stars = star_value
    return SearchResult(
        source=SearchSource.ECOSYSTEMS,
        name=str(item.get("name") or ""),
        description=str(item.get("description") or "")[:200],
        url=str(item.get("repository_url") or item.get("homepage") or item.get("registry_url") or ""),
        stars=stars,
        downloads_monthly=item.get("downloads") if isinstance(item.get("downloads"), int) else None,
        dependents_count=item.get("dependent_repos_count")
        if isinstance(item.get("dependent_repos_count"), int)
        else None,
        last_updated=str(item.get("latest_release_published_at") or item.get("updated_at") or ""),
        is_maintained=True if item.get("last_synced_at") else None,
        license=str(item.get("licenses") or "") or None,
        language=str(item.get("ecosystem") or "") or None,
        package_manager=str(item.get("ecosystem") or "") or None,
        relevance_score=0.0,
    )


async def search_ecosystems(query: str, language: str | None = None) -> list[SearchResult]:
    cache_key = f"ecosystems:{query.lower()}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cast(list[SearchResult], cached)

    ecosystem = _LANGUAGE_TO_ECOSYSTEM.get((language or "").lower())
    names = _candidate_names(query)

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        for name in names:
            params: dict[str, str] = {"name": name}
            if ecosystem:
                params["ecosystem"] = ecosystem
            tasks.append(client.get(BASE_URL, params=params))
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    deduped: dict[str, SearchResult] = {}
    for response in responses:
        if isinstance(response, BaseException):
            continue
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            continue
        data = response.json()
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            result = _to_result(item)
            key = result.url or result.name
            if key and key not in deduped:
                deduped[key] = result

    results = list(deduped.values())
    set_cached(cache_key, results)
    return results
