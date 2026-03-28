import asyncio
import math
import re
from collections import OrderedDict

import structlog

from overbuild.api.models import ParsedIntent, SearchResult, SearchSource
from overbuild.search.ecosystems import search_ecosystems
from overbuild.search.github_search import search_github
from overbuild.search.librariesio import search_librariesio
from overbuild.search.npm_registry import search_npm
from overbuild.search.stackoverflow import search_stackoverflow

logger = structlog.get_logger()

_SECRET_PATTERNS = [
    re.compile(r"([?&]api_key=)([^&\s]+)", re.IGNORECASE),
    re.compile(r"([?&]key=)([^&\s]+)", re.IGNORECASE),
    re.compile(r"([?&]token=)([^&\s]+)", re.IGNORECASE),
    re.compile(r"([?&]access_token=)([^&\s]+)", re.IGNORECASE),
    re.compile(r"(Bearer\s+)([A-Za-z0-9._\-]+)", re.IGNORECASE),
]


def _norm_text(value: str) -> str:
    return value.lower().strip()


def _tokenize(value: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_+-]+", value.lower()))


def _sanitize_error(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(r"\1***REDACTED***", redacted)
    return redacted


def _dedup_key(result: SearchResult) -> str:
    if result.url:
        return _norm_text(result.url.rstrip("/"))
    return _norm_text(result.name)


def _match_ratio(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    keyword_tokens = set()
    for keyword in keywords:
        keyword_tokens.update(_tokenize(keyword))
    if not keyword_tokens:
        return 0.0
    return len(tokens.intersection(keyword_tokens)) / len(keyword_tokens)


def _scaled(value: int | None, cap: int) -> float:
    if not value or value <= 0:
        return 0.0
    return min(math.log10(value + 1) / math.log10(cap + 1), 1.0)


def _language_match(result: SearchResult, parsed: ParsedIntent) -> float:
    if not result.language:
        return 0.1
    return 1.0 if _norm_text(result.language) == _norm_text(parsed.target_language) else 0.0


def deduplicate_and_rank(results: list[SearchResult], parsed: ParsedIntent) -> list[SearchResult]:
    """Deduplicate, score, and rank results deterministically."""
    deduped: OrderedDict[str, SearchResult] = OrderedDict()
    for result in results:
        key = _dedup_key(result)
        current = deduped.get(key)
        if current is None:
            deduped[key] = result
            continue
        # Keep the richer result variant if duplicate key already exists.
        current_score = (current.stars or 0) + (current.dependents_count or 0)
        incoming_score = (result.stars or 0) + (result.dependents_count or 0)
        if incoming_score > current_score:
            deduped[key] = result

    ranked: list[SearchResult] = []
    for result in deduped.values():
        text = f"{result.name} {result.description}"
        score = 0.0
        score += 0.45 * _match_ratio(text, parsed.keywords)
        score += 0.2 * _scaled(result.stars, 150_000)
        score += 0.15 * _scaled(result.dependents_count, 50_000)
        score += 0.1 * (1.0 if result.is_maintained else 0.0)
        score += 0.1 * _language_match(result, parsed)
        result.relevance_score = round(max(0.0, min(score, 1.0)), 3)
        ranked.append(result)

    return sorted(ranked, key=lambda item: item.relevance_score, reverse=True)


async def search_all_sources(
    queries: list[str],
    keywords: list[str],
    language: str,
    os_relevant: bool,
) -> tuple[list[SearchResult], list[SearchSource]]:
    """Search all providers in parallel and return partial results on failures."""
    _ = os_relevant
    primary_query = queries[0] if queries else " ".join(keywords[:3])
    primary_query = primary_query.strip() or "developer tool"

    tasks: dict[SearchSource, asyncio.Task[list[SearchResult]]] = {
        SearchSource.LIBRARIES_IO: asyncio.create_task(search_librariesio(primary_query, language)),
        SearchSource.GITHUB: asyncio.create_task(search_github(primary_query, language)),
        SearchSource.STACKOVERFLOW: asyncio.create_task(
            search_stackoverflow(primary_query, language)
        ),
        SearchSource.ECOSYSTEMS: asyncio.create_task(search_ecosystems(primary_query, language)),
    }
    if _norm_text(language) in {"javascript", "typescript", "node", "js", "ts"}:
        tasks[SearchSource.NPM] = asyncio.create_task(search_npm(primary_query, language))

    gathered: list[list[SearchResult] | BaseException] = await asyncio.gather(
        *tasks.values(), return_exceptions=True
    )

    all_results: list[SearchResult] = []
    sources_searched: list[SearchSource] = []
    for source, result in zip(tasks.keys(), gathered, strict=False):
        if isinstance(result, BaseException):
            logger.warning("search_failed", source=source.value, error=_sanitize_error(str(result)))
            continue
        all_results.extend(result)
        sources_searched.append(source)

    return all_results, sources_searched
