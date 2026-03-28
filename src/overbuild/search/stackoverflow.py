from datetime import UTC, datetime, timedelta
from typing import cast

import httpx

from overbuild.api.models import SearchResult, SearchSource
from overbuild.config import settings
from overbuild.search.cache import get_cached, set_cached


def _is_recent(epoch: int | None) -> bool | None:
    if epoch is None:
        return None
    ts = datetime.fromtimestamp(epoch, tz=UTC)
    return ts >= datetime.now(UTC) - timedelta(days=365)


async def search_stackoverflow(query: str, language: str | None = None) -> list[SearchResult]:
    cache_key = f"stackoverflow:{query.lower()}:{(language or '').lower()}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cast(list[SearchResult], cached)

    tagged = (language or "").lower()
    params: dict[str, str | int] = {
        "order": "desc",
        "sort": "votes",
        "intitle": query,
        "site": "stackoverflow",
        "pagesize": 10,
    }
    if tagged:
        params["tagged"] = tagged
    if settings.stackoverflow_api_key:
        params["key"] = settings.stackoverflow_api_key

    def _strip_key_param(source: dict[str, str | int]) -> dict[str, str | int]:
        return {key: value for key, value in source.items() if key != "key"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get("https://api.stackexchange.com/2.3/search", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # StackExchange may return 400 for invalid key usage. Retry once without key.
            if exc.response.status_code == 400 and "key" in params:
                fallback_params = _strip_key_param(params)
                response = await client.get(
                    "https://api.stackexchange.com/2.3/search",
                    params=fallback_params,
                )
                response.raise_for_status()
            else:
                raise
        data = response.json()

    results: list[SearchResult] = []
    for item in data.get("items", []):
        results.append(
            SearchResult(
                source=SearchSource.STACKOVERFLOW,
                name=item.get("title", ""),
                description=f"StackOverflow question with {item.get('answer_count', 0)} answers",
                url=item.get("link", ""),
                relevance_score=0.0,
                stackoverflow_score=item.get("score"),
                answer_count=item.get("answer_count"),
                last_updated=datetime.fromtimestamp(
                    item.get("last_activity_date", item.get("creation_date", 0)),
                    tz=UTC,
                ).isoformat(),
                is_maintained=_is_recent(item.get("last_activity_date")),
                license="CC BY-SA",
            )
        )

    set_cached(cache_key, results)
    return results
