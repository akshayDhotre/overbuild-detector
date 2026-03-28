import json

from overbuild.core.parser import parse_intent


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
            "problem_summary": "Rate limit FastAPI",
            "target_language": "python",
            "domain": "web-backend",
            "keywords": ["rate", "limit", "fastapi"],
            "os_relevant": False,
            "expected_complexity": 3,
            "search_queries": ["fastapi rate limiter", "python rate limiter package"],
            "potential_one_liner": None,
        }
    )


def test_parse_intent_heuristic_one_liner(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    monkeypatch.setattr("overbuild.core.parser.has_llm_config", lambda: False)
    result, cost = asyncio.run(
        parse_intent("Clean up Rust target folders older than 7 days", language="rust")
    )
    assert result.expected_complexity <= 2
    assert result.potential_one_liner is not None
    assert cost == 0.0


def test_parse_intent_cost_calculation(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    async def fake_call_llm_json(*args, **kwargs):  # type: ignore[no-untyped-def]
        _ = (args, kwargs)
        return (
            json.dumps(
                {
                    "problem_summary": "Rate limit FastAPI",
                    "target_language": "python",
                    "domain": "web-backend",
                    "keywords": ["rate", "limit", "fastapi"],
                    "os_relevant": False,
                    "expected_complexity": 3,
                    "search_queries": ["fastapi rate limiter", "python rate limiter package"],
                    "potential_one_liner": None,
                }
            ),
            (100 * 0.003 + 50 * 0.015) / 1000,
        )

    monkeypatch.setattr("overbuild.core.parser.has_llm_config", lambda: True)
    monkeypatch.setattr("overbuild.core.parser.call_llm_json", fake_call_llm_json)
    parsed, cost = asyncio.run(parse_intent("Need rate limiting", language="python"))
    assert parsed.target_language == "python"
    assert round(cost, 6) == round((100 * 0.003 + 50 * 0.015) / 1000, 6)


def test_parse_intent_falls_back_on_invalid_llm_payload(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    async def fake_bad_call(*args, **kwargs):  # type: ignore[no-untyped-def]
        _ = (args, kwargs)
        return ("not json", 0.123)

    monkeypatch.setattr("overbuild.core.parser.has_llm_config", lambda: True)
    monkeypatch.setattr("overbuild.core.parser.call_llm_json", fake_bad_call)

    parsed, cost = asyncio.run(parse_intent("Need to cleanup docker images", language="bash"))
    assert parsed.target_language == "bash"
    assert cost == 0.0
