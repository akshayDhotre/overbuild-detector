import pytest

from overbuild.api.models import AnalyzeResponse
from overbuild.mcp.server import call_tool, list_tools


@pytest.mark.asyncio
async def test_list_tools_has_check_before_building() -> None:
    tools = await list_tools()
    assert any(tool.name == "check_before_building" for tool in tools)


@pytest.mark.asyncio
async def test_call_tool_formats_output(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    async def fake_analyze(request):  # type: ignore[no-untyped-def]
        _ = request
        return AnalyzeResponse.model_validate(
            {
                "verdict": "JUST_USE_A_ONE_LINER",
                "overbuild_score": {
                    "problem_complexity": 1,
                    "best_existing_complexity": 0,
                    "custom_build_complexity": 4,
                    "score": 4.0,
                    "explanation": "Significant over-engineering risk",
                },
                "summary": "A command is enough.",
                "existing_solutions": [],
                "one_liner": "docker system prune --filter 'until=48h' -f",
                "if_you_must_build": None,
                "sources_searched": ["github"],
                "total_results_found": 1,
                "search_time_ms": 10,
                "llm_cost_usd": 0.0,
                "request_id": "req123",
            }
        )

    monkeypatch.setattr("overbuild.mcp.server.analyze", fake_analyze)
    output = await call_tool("check_before_building", {"problem": "cleanup docker images"})
    assert len(output) == 1
    assert "JUST_USE_A_ONE_LINER" in output[0].text
    assert "docker system prune" in output[0].text
