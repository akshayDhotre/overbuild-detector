import json
from pathlib import Path

import httpx
import pytest
import respx

from overbuild.search.librariesio import search_librariesio


@pytest.mark.asyncio
async def test_librariesio_normalization(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payload = json.loads(
        (Path(__file__).parent / "fixtures" / "librariesio_response.json").read_text()
    )
    monkeypatch.setattr("overbuild.search.librariesio.settings.librariesio_api_key", "test-key")
    with respx.mock(assert_all_called=True) as mock_router:
        mock_router.get("https://libraries.io/api/search").mock(
            return_value=httpx.Response(200, json=payload)
        )
        results = await search_librariesio("fastapi rate limiter", "python")
    assert len(results) == 1
    assert results[0].name == "slowapi"
    assert results[0].package_manager == "pypi"
    assert results[0].relevance_score == 0.0


@pytest.mark.asyncio
async def test_librariesio_skips_when_key_missing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("overbuild.search.librariesio.settings.librariesio_api_key", "")
    results = await search_librariesio("fastapi rate limiter", "python")
    assert results == []
