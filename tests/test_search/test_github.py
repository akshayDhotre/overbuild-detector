import json
from pathlib import Path

import httpx
import pytest
import respx

from overbuild.search.github_search import search_github


@pytest.mark.asyncio
async def test_github_normalization() -> None:
    payload = json.loads((Path(__file__).parent / "fixtures" / "github_response.json").read_text())
    with respx.mock(assert_all_called=True) as mock_router:
        mock_router.get("https://api.github.com/search/repositories").mock(
            return_value=httpx.Response(200, json=payload)
        )
        results = await search_github("fastapi rate limiter", "python")
    assert len(results) == 1
    assert results[0].source.value == "github"
    assert results[0].stars == 3000
    assert results[0].language == "Python"
