import json
from pathlib import Path

import httpx
import pytest
import respx

from overbuild.search.stackoverflow import search_stackoverflow


@pytest.mark.asyncio
async def test_stackoverflow_normalization() -> None:
    payload = json.loads(
        (Path(__file__).parent / "fixtures" / "stackoverflow_response.json").read_text()
    )
    with respx.mock(assert_all_called=True) as mock_router:
        mock_router.get("https://api.stackexchange.com/2.3/search").mock(
            return_value=httpx.Response(200, json=payload)
        )
        results = await search_stackoverflow("fastapi rate limiter", "python")
    assert len(results) == 1
    assert results[0].answer_count == 5
    assert results[0].source.value == "stackoverflow"


@pytest.mark.asyncio
async def test_stackoverflow_retries_without_key_on_400(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    payload = json.loads(
        (Path(__file__).parent / "fixtures" / "stackoverflow_response.json").read_text()
    )
    monkeypatch.setattr("overbuild.search.stackoverflow.settings.stackoverflow_api_key", "bad-key")

    with respx.mock(assert_all_called=True) as mock_router:
        route = mock_router.get("https://api.stackexchange.com/2.3/search").mock(
            side_effect=[
                httpx.Response(400, json={"error_id": 400, "error_message": "bad_parameter"}),
                httpx.Response(200, json=payload),
            ]
        )
        results = await search_stackoverflow("fastapi rate limiter", "python")

    assert route.call_count == 2
    assert len(results) == 1
