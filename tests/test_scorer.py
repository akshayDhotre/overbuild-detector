from overbuild.api.models import SearchResult, SearchSource, SynthesisResult, Verdict
from overbuild.core.scorer import calculate_overbuild_score


def test_scorer_high_relevance_reduces_existing_complexity() -> None:
    best_existing = SearchResult(
        source=SearchSource.GITHUB,
        name="slowapi",
        description="Rate limiter",
        url="https://github.com/laurentS/slowapi",
        relevance_score=0.9,
        stars=3000,
    )
    recommendation = SynthesisResult(
        verdict=Verdict.USE_EXISTING,
        summary="Use existing package",
        existing_solutions=[],
    )
    score = calculate_overbuild_score(4, best_existing, recommendation)
    assert score.problem_complexity == 4
    assert score.best_existing_complexity <= 4
    assert score.score > 1.0


def test_scorer_one_liner_sets_best_complexity_zero() -> None:
    recommendation = SynthesisResult(
        verdict=Verdict.JUST_USE_A_ONE_LINER,
        summary="Use one-liner",
        existing_solutions=[],
        one_liner="docker system prune --filter 'until=48h' -f",
    )
    score = calculate_overbuild_score(1, None, recommendation)
    assert score.best_existing_complexity == 0


def test_scorer_explanation_bands_are_human_readable() -> None:
    recommendation = SynthesisResult(
        verdict=Verdict.ADAPT_EXISTING,
        summary="Adapt existing tools",
        existing_solutions=[],
    )
    low = calculate_overbuild_score(10, None, recommendation)
    very_high = calculate_overbuild_score(1, None, recommendation)
    assert "Low overbuild risk" in low.explanation
    assert "Very high overbuild risk" in very_high.explanation
