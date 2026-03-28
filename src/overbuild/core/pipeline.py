import time
import uuid

from overbuild.api.models import AnalyzeRequest, AnalyzeResponse
from overbuild.core.parser import parse_intent
from overbuild.core.scorer import calculate_overbuild_score
from overbuild.core.synthesizer import synthesize_recommendation
from overbuild.observability.metrics import track_request
from overbuild.search.aggregator import deduplicate_and_rank, search_all_sources


async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Main pipeline: parse -> search -> rank -> synthesize -> score."""
    request_id = str(uuid.uuid4())[:8]
    started = time.monotonic()
    total_llm_cost = 0.0

    parsed_intent, parse_cost = await parse_intent(
        problem=request.problem,
        language=request.language,
        context=request.context,
    )
    total_llm_cost += parse_cost

    search_results, sources_searched = await search_all_sources(
        queries=parsed_intent.search_queries,
        keywords=parsed_intent.keywords,
        language=parsed_intent.target_language,
        os_relevant=parsed_intent.os_relevant,
    )

    ranked_results = deduplicate_and_rank(search_results, parsed_intent)

    recommendation, synth_cost = await synthesize_recommendation(
        parsed_intent=parsed_intent,
        ranked_results=ranked_results[:15],
        original_problem=request.problem,
    )
    total_llm_cost += synth_cost

    score = calculate_overbuild_score(
        problem_complexity=parsed_intent.expected_complexity,
        best_existing=ranked_results[0] if ranked_results else None,
        recommendation=recommendation,
    )

    elapsed_ms = int((time.monotonic() - started) * 1000)
    response = AnalyzeResponse(
        verdict=recommendation.verdict,
        overbuild_score=score,
        summary=recommendation.summary,
        existing_solutions=recommendation.existing_solutions,
        one_liner=parsed_intent.potential_one_liner or recommendation.one_liner,
        if_you_must_build=recommendation.if_you_must_build,
        sources_searched=sources_searched,
        total_results_found=len(search_results),
        search_time_ms=elapsed_ms,
        llm_cost_usd=round(total_llm_cost, 6),
        request_id=request_id,
    )

    await track_request(request_id, elapsed_ms, total_llm_cost, recommendation.verdict.value)
    return response
