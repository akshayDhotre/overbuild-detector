import httpx
import pytest
import respx

from overbuild.search.ecosystems import search_ecosystems


@pytest.mark.asyncio
async def test_ecosystems_lookup_normalization_and_dedup() -> None:
    payload_one = [
        {
            "name": "fastapi",
            "description": "High performance Python web framework",
            "repository_url": "https://github.com/fastapi/fastapi",
            "downloads": 123456,
            "dependent_repos_count": 5000,
            "latest_release_published_at": "2026-01-01T00:00:00Z",
            "last_synced_at": "2026-03-01T00:00:00Z",
            "licenses": "MIT",
            "ecosystem": "pypi",
            "repo_metadata": {"stargazers_count": 77000},
        }
    ]
    payload_two = [
        {
            "name": "fastapi",
            "description": "Duplicate entry",
            "repository_url": "https://github.com/fastapi/fastapi",
            "downloads": 123456,
            "dependent_repos_count": 5000,
            "latest_release_published_at": "2026-01-01T00:00:00Z",
            "last_synced_at": "2026-03-01T00:00:00Z",
            "licenses": "MIT",
            "ecosystem": "pypi",
            "repo_metadata": {"stargazers_count": 77000},
        }
    ]

    with respx.mock(assert_all_called=True) as mock_router:
        route = mock_router.get("https://packages.ecosyste.ms/api/v1/packages/lookup").mock(
            side_effect=[
                httpx.Response(200, json=payload_one),
                httpx.Response(200, json=payload_two),
            ]
        )
        results = await search_ecosystems("fastapi slowapi", "python")

    assert route.call_count == 2
    assert len(results) == 1
    assert results[0].name == "fastapi"
    assert results[0].package_manager == "pypi"
    assert results[0].stars == 77000


@pytest.mark.asyncio
async def test_ecosystems_tolerates_partial_lookup_failures() -> None:
    payload_ok = [
        {
            "name": "docker",
            "description": "Docker SDK",
            "repository_url": "https://github.com/docker/docker-py",
            "downloads": 1000,
            "dependent_repos_count": 100,
            "latest_release_published_at": "2026-01-01T00:00:00Z",
            "last_synced_at": "2026-03-01T00:00:00Z",
            "licenses": "Apache-2.0",
            "ecosystem": "pypi",
            "repo_metadata": {"stargazers_count": 8000},
        }
    ]
    with respx.mock(assert_all_called=True) as mock_router:
        route = mock_router.get("https://packages.ecosyste.ms/api/v1/packages/lookup").mock(
            side_effect=[
                httpx.Response(404),
                httpx.Response(200, json=payload_ok),
                httpx.Response(404),
            ]
        )
        results = await search_ecosystems("docker dangling images cleanup", "python")

    assert route.call_count == 3
    assert len(results) == 1
    assert results[0].name == "docker"
