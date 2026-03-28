from overbuild.api.models import OverBuildScore, SearchResult, SynthesisResult


def calculate_overbuild_score(
    problem_complexity: int,
    best_existing: SearchResult | None,
    recommendation: SynthesisResult,
) -> OverBuildScore:
    """Compute OverBuild score using deterministic heuristics."""
    if best_existing and best_existing.relevance_score > 0.7:
        best_existing_complexity = max(1, problem_complexity - 2)
    elif best_existing and best_existing.relevance_score > 0.4:
        best_existing_complexity = problem_complexity
    else:
        best_existing_complexity = min(10, problem_complexity + 2)

    custom_build_complexity = min(10, problem_complexity + 3)
    if recommendation.one_liner and problem_complexity <= 2:
        best_existing_complexity = 0

    score = custom_build_complexity / max(problem_complexity, 1)
    if score <= 1.45:
        explanation = "Low overbuild risk: custom build is close to problem complexity"
    elif score <= 1.9:
        explanation = "Moderate overbuild risk: prefer adapting existing tools first"
    elif score <= 2.6:
        explanation = "High overbuild risk: existing solutions are likely the better default"
    else:
        explanation = "Very high overbuild risk: a package or one-liner is usually enough"

    return OverBuildScore(
        problem_complexity=problem_complexity,
        best_existing_complexity=best_existing_complexity,
        custom_build_complexity=custom_build_complexity,
        score=round(score, 2),
        explanation=explanation,
    )
