import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from overbuild.api.models import ParsedIntent, SearchResult, SearchSource
from overbuild.search.cache import clear_cache


@pytest.fixture(autouse=True)
def clean_cache() -> None:
    clear_cache()


@pytest.fixture
def sample_parsed_intent() -> ParsedIntent:
    return ParsedIntent(
        problem_summary="Rate limit FastAPI",
        target_language="python",
        domain="web-backend",
        keywords=["rate", "limit", "fastapi"],
        os_relevant=False,
        expected_complexity=3,
        search_queries=["fastapi rate limiter", "python rate limit package"],
        potential_one_liner=None,
    )


@pytest.fixture
def sample_search_results() -> list[SearchResult]:
    return [
        SearchResult(
            source=SearchSource.GITHUB,
            name="laurentS/slowapi",
            description="Rate limiting for FastAPI apps.",
            url="https://github.com/laurentS/slowapi",
            relevance_score=0.9,
            stars=3200,
            is_maintained=True,
            language="python",
        ),
        SearchResult(
            source=SearchSource.LIBRARIES_IO,
            name="fastapi-limiter",
            description="FastAPI request limiter",
            url="https://pypi.org/project/fastapi-limiter",
            relevance_score=0.8,
            stars=800,
            is_maintained=True,
            language="python",
            package_manager="pypi",
        ),
    ]
