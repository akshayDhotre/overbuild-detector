from overbuild.api.models import (
    AnalyzeRequest,
    ExistingSolution,
    ParsedIntent,
    SearchResult,
    SearchSource,
    SynthesisResult,
    Verdict,
)
from overbuild.core.pipeline import analyze


async def _fake_parse(problem: str, language: str | None = None, context: str | None = None):  # type: ignore[no-untyped-def]
    _ = problem, context
    return (
        ParsedIntent(
            problem_summary="Rate limiter",
            target_language=language or "python",
            domain="web-backend",
            keywords=["rate", "limit"],
            os_relevant=False,
            expected_complexity=3,
            search_queries=["rate limiter python", "fastapi limiter package"],
            potential_one_liner=None,
        ),
        0.001,
    )


async def _fake_search(**kwargs):  # type: ignore[no-untyped-def]
    _ = kwargs
    return (
        [
            SearchResult(
                source=SearchSource.GITHUB,
                name="slowapi",
                description="FastAPI rate limiter",
                url="https://github.com/laurentS/slowapi",
                relevance_score=0.8,
                stars=3000,
                language="python",
                is_maintained=True,
            )
        ],
        [SearchSource.GITHUB],
    )


async def _fake_synth(parsed_intent, ranked_results, original_problem):  # type: ignore[no-untyped-def]
    _ = parsed_intent, ranked_results, original_problem
    return (
        SynthesisResult(
            verdict=Verdict.USE_EXISTING,
            summary="Use existing package.",
            existing_solutions=[
                ExistingSolution(
                    name="slowapi",
                    description="Rate limiter",
                    url="https://github.com/laurentS/slowapi",
                    pros=["mature"],
                    cons=["integration"],
                    source=SearchSource.GITHUB,
                )
            ],
            one_liner=None,
            if_you_must_build=None,
        ),
        0.002,
    )


def test_pipeline_integration(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import asyncio

    monkeypatch.setattr("overbuild.core.pipeline.parse_intent", _fake_parse)
    monkeypatch.setattr("overbuild.core.pipeline.search_all_sources", _fake_search)
    monkeypatch.setattr("overbuild.core.pipeline.synthesize_recommendation", _fake_synth)
    request = AnalyzeRequest(problem="Need rate limiting", language="python")
    result = asyncio.run(analyze(request))
    assert result.verdict.value == "USE_EXISTING"
    assert result.total_results_found == 1
    assert result.llm_cost_usd == 0.003
