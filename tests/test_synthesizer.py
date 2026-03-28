import json

from overbuild.api.models import ParsedIntent, SearchResult, SearchSource, Verdict
from overbuild.core.synthesizer import synthesize_recommendation


def _fake_response(content: dict) -> object:
    class Usage:
        input_tokens = 100
        output_tokens = 50

    class TextBlock:
        type = "text"
        text = json.dumps(content)

    class Response:
        usage = Usage()
        content = [TextBlock()]

    return Response()


async def _fake_create(**kwargs):  # type: ignore[no-untyped-def]
    return _fake_response(
        {
            "verdict": "USE_EXISTING",
            "summary": "Use an existing package.",
            "existing_solutions": [
                {
                    "name": "slowapi",
                    "description": "Rate limiter",
                    "url": "https://github.com/laurentS/slowapi",
                    "install_command": "pip install slowapi",
                    "usage_example": None,
                    "pros": ["mature"],
                    "cons": ["integration effort"],
                    "source": "github",
                    "stars": 1000,
                    "last_updated": "2026-01-01T00:00:00Z",
                }
            ],
            "one_liner": None,
            "if_you_must_build": None,
        }
    )


def test_synthesize_heuristic_one_liner(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    monkeypatch.setattr("overbuild.core.synthesizer.has_llm_config", lambda: False)
    parsed = ParsedIntent(
        problem_summary="Docker cleanup",
        target_language="bash",
        domain="devops",
        keywords=["docker", "cleanup"],
        os_relevant=True,
        expected_complexity=1,
        search_queries=["docker cleanup", "docker prune command"],
        potential_one_liner="docker system prune --filter 'until=48h' -f",
    )
    result, cost = asyncio.run(
        synthesize_recommendation(
            parsed_intent=parsed,
            ranked_results=[],
            original_problem="Cleanup docker images",
        )
    )
    assert result.verdict == Verdict.JUST_USE_A_ONE_LINER
    assert cost == 0.0


def test_synthesize_cost_calculation(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    parsed = ParsedIntent(
        problem_summary="Rate limit",
        target_language="python",
        domain="web-backend",
        keywords=["rate", "limit"],
        os_relevant=False,
        expected_complexity=3,
        search_queries=["rate limiter", "python retry rate limiting package"],
        potential_one_liner=None,
    )
    results = [
        SearchResult(
            source=SearchSource.GITHUB,
            name="slowapi",
            description="FastAPI rate limiter",
            url="https://github.com/laurentS/slowapi",
            relevance_score=0.8,
            stars=3000,
            language="python",
        )
    ]
    async def fake_call_llm_json(*args, **kwargs):  # type: ignore[no-untyped-def]
        _ = (args, kwargs)
        return (
            json.dumps(
                {
                    "verdict": "USE_EXISTING",
                    "summary": "Use an existing package.",
                    "existing_solutions": [
                        {
                            "name": "slowapi",
                            "description": "Rate limiter",
                            "url": "https://github.com/laurentS/slowapi",
                            "install_command": "pip install slowapi",
                            "usage_example": None,
                            "pros": ["mature"],
                            "cons": ["integration effort"],
                            "source": "github",
                            "stars": 1000,
                            "last_updated": "2026-01-01T00:00:00Z",
                        }
                    ],
                    "one_liner": None,
                    "if_you_must_build": None,
                }
            ),
            (100 * 0.003 + 50 * 0.015) / 1000,
        )

    monkeypatch.setattr("overbuild.core.synthesizer.has_llm_config", lambda: True)
    monkeypatch.setattr("overbuild.core.synthesizer.call_llm_json", fake_call_llm_json)
    synthesized, cost = asyncio.run(
        synthesize_recommendation(
            parsed_intent=parsed,
            ranked_results=results,
            original_problem="Need a FastAPI rate limiter",
        )
    )
    assert synthesized.verdict == Verdict.USE_EXISTING
    assert round(cost, 6) == round((100 * 0.003 + 50 * 0.015) / 1000, 6)


def test_synthesize_falls_back_on_invalid_llm_payload(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    async def fake_bad_call(*args, **kwargs):  # type: ignore[no-untyped-def]
        _ = (args, kwargs)
        return ("{ bad json", 0.5)

    parsed = ParsedIntent(
        problem_summary="Docker cleanup",
        target_language="bash",
        domain="devops",
        keywords=["docker", "cleanup"],
        os_relevant=True,
        expected_complexity=1,
        search_queries=["docker cleanup", "docker prune command"],
        potential_one_liner="docker system prune --filter 'until=48h' -f",
    )

    monkeypatch.setattr("overbuild.core.synthesizer.has_llm_config", lambda: True)
    monkeypatch.setattr("overbuild.core.synthesizer.call_llm_json", fake_bad_call)
    synthesized, cost = asyncio.run(
        synthesize_recommendation(
            parsed_intent=parsed,
            ranked_results=[],
            original_problem="Cleanup docker images",
        )
    )
    assert synthesized.verdict == Verdict.JUST_USE_A_ONE_LINER
    assert cost == 0.0
