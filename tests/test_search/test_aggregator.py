import pytest

from overbuild.api.models import ParsedIntent, SearchResult, SearchSource
from overbuild.search.aggregator import _sanitize_error, deduplicate_and_rank, search_all_sources


def _parsed() -> ParsedIntent:
    return ParsedIntent(
        problem_summary="rate limit",
        target_language="python",
        domain="web-backend",
        keywords=["rate", "limit", "fastapi"],
        os_relevant=False,
        expected_complexity=3,
        search_queries=["fastapi rate limiter", "python rate limit package"],
        potential_one_liner=None,
    )


def test_deduplicate_and_rank() -> None:
    parsed = _parsed()
    results = [
        SearchResult(
            source=SearchSource.GITHUB,
            name="slowapi",
            description="FastAPI rate limiter package",
            url="https://github.com/laurentS/slowapi",
            relevance_score=0.0,
            stars=3200,
            is_maintained=True,
            language="python",
        ),
        SearchResult(
            source=SearchSource.GITHUB,
            name="slowapi",
            description="duplicate",
            url="https://github.com/laurentS/slowapi/",
            relevance_score=0.0,
            stars=3000,
            is_maintained=True,
            language="python",
        ),
    ]
    ranked = deduplicate_and_rank(results, parsed)
    assert len(ranked) == 1
    assert ranked[0].relevance_score > 0.5


def test_sanitize_error_redacts_secrets() -> None:
    raw = (
        "403 for url https://example.test/search?api_key=abc123&key=xyz789&token=t0k3n "
        "Authorization: Bearer supersecret"
    )
    sanitized = _sanitize_error(raw)
    assert "abc123" not in sanitized
    assert "xyz789" not in sanitized
    assert "t0k3n" not in sanitized
    assert "supersecret" not in sanitized
    assert "***REDACTED***" in sanitized


@pytest.mark.asyncio
async def test_search_all_sources_tolerates_failures(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_ok(query: str, language: str | None = None):  # type: ignore[no-untyped-def]
        _ = query, language
        return [
            SearchResult(
                source=SearchSource.GITHUB,
                name="slowapi",
                description="FastAPI rate limiter",
                url="https://github.com/laurentS/slowapi",
                relevance_score=0.0,
                stars=1000,
            )
        ]

    async def fake_fail(query: str, language: str | None = None):  # type: ignore[no-untyped-def]
        _ = query, language
        raise RuntimeError("provider failed")

    monkeypatch.setattr("overbuild.search.aggregator.search_librariesio", fake_ok)
    monkeypatch.setattr("overbuild.search.aggregator.search_github", fake_fail)
    monkeypatch.setattr("overbuild.search.aggregator.search_stackoverflow", fake_ok)
    monkeypatch.setattr("overbuild.search.aggregator.search_ecosystems", fake_ok)

    results, sources = await search_all_sources(
        queries=["fastapi rate limiter"],
        keywords=["fastapi", "rate", "limiter"],
        language="python",
        os_relevant=False,
    )
    assert len(results) == 3
    assert SearchSource.GITHUB not in sources
