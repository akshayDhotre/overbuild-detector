import json
from typing import Any

from overbuild.api.models import (
    ExistingSolution,
    ParsedIntent,
    SearchResult,
    SynthesisResult,
    Verdict,
)
from overbuild.core.llm import call_llm_json, extract_json_payload, has_llm_config

SYNTH_SYSTEM_PROMPT = """You are an engineering reviewer deciding if a problem should be
solved with existing tools or custom code.
Respond ONLY with valid JSON:
{
  "verdict": "USE_EXISTING|ADAPT_EXISTING|BUILD_CUSTOM|JUST_USE_A_ONE_LINER",
  "summary": "2-3 sentence recommendation",
  "existing_solutions": [
    {
      "name": "string",
      "description": "string",
      "url": "string",
      "install_command": "string or null",
      "usage_example": "string or null",
      "pros": ["string"],
      "cons": ["string"],
      "source": "libraries_io|github|npm|stackoverflow|ecosystems",
      "stars": 0,
      "last_updated": "string or null"
    }
  ],
  "one_liner": "string or null",
  "if_you_must_build": "string or null"
}
"""


def _install_hint(result: SearchResult) -> str | None:
    if result.package_manager == "pypi":
        return f"pip install {result.name}"
    if result.package_manager == "npm":
        return f"npm install {result.name}"
    if result.package_manager == "cargo":
        return f"cargo add {result.name}"
    return None


def _to_existing_solution(result: SearchResult) -> ExistingSolution:
    pros = ["Mature ecosystem option", "Reduces implementation time"]
    cons = []
    if result.is_maintained is False:
        cons.append("Maintenance appears stale")
    if not result.stars:
        cons.append("Limited popularity signals")
    if not cons:
        cons = ["May require integration effort"]

    return ExistingSolution(
        name=result.name,
        description=result.description or "Potential existing solution",
        url=result.url,
        install_command=_install_hint(result),
        usage_example=None,
        pros=pros,
        cons=cons,
        source=result.source,
        stars=result.stars,
        last_updated=result.last_updated,
    )


def _contains_domain_specific(problem: str) -> bool:
    text = problem.lower()
    flags = [
        "healthcare",
        "hipaa",
        "differential privacy",
        "proprietary",
        "regulatory",
        "domain-specific rule engine",
    ]
    return any(flag in text for flag in flags)


def _is_well_solved_problem(problem: str) -> bool:
    text = problem.lower()
    solved_patterns = [
        "rate limiting",
        "rate limiter",
        "file changes",
        "runs tests",
        "json logging",
        "git hooks",
        "environment variables",
        ".env",
        "retry logic",
        "exponential backoff",
        "markdown",
        "to html",
    ]
    return any(pattern in text for pattern in solved_patterns)


def _is_one_liner_problem(problem: str) -> bool:
    text = problem.lower()
    one_liner_patterns = [
        "csv",
        "to json",
        "docker containers",
        "dangling images",
        "target/ folders",
    ]
    return any(pattern in text for pattern in one_liner_patterns)


def _heuristic_verdict(
    parsed_intent: ParsedIntent,
    ranked_results: list[SearchResult],
    original_problem: str,
) -> Verdict:
    if parsed_intent.potential_one_liner or _is_one_liner_problem(original_problem):
        return Verdict.JUST_USE_A_ONE_LINER
    top_score = ranked_results[0].relevance_score if ranked_results else 0.0
    if _contains_domain_specific(original_problem) and parsed_intent.expected_complexity >= 7:
        return Verdict.BUILD_CUSTOM
    if _is_well_solved_problem(original_problem):
        return Verdict.USE_EXISTING
    if top_score >= 0.65:
        return Verdict.USE_EXISTING
    if top_score >= 0.35:
        return Verdict.ADAPT_EXISTING
    if parsed_intent.expected_complexity >= 7:
        return Verdict.BUILD_CUSTOM
    if parsed_intent.expected_complexity <= 3:
        return Verdict.USE_EXISTING
    return Verdict.ADAPT_EXISTING


def _heuristic_summary(verdict: Verdict, parsed_intent: ParsedIntent) -> str:
    if verdict == Verdict.JUST_USE_A_ONE_LINER:
        return "This problem is operationally simple and already solvable with a command-level approach. Building custom software would add unnecessary maintenance overhead."
    if verdict == Verdict.USE_EXISTING:
        return "This is a well-solved problem with mature tooling available. Integrating an existing package is lower risk and faster than building from scratch."
    if verdict == Verdict.ADAPT_EXISTING:
        return "Existing building blocks are available, but some customization is likely required. Start from established libraries and add only thin project-specific logic."
    return "The problem appears domain-specific enough that a custom implementation is justified. Reuse infrastructure libraries, but keep business logic bespoke."


def _must_build_guidance(parsed_intent: ParsedIntent) -> str:
    return (
        "Keep the first version narrow: define the minimal API, isolate domain rules in a testable module, "
        "and rely on standard libraries for logging, validation, and retries."
        if parsed_intent.expected_complexity >= 6
        else "Use existing packages internally and implement only the smallest missing extension points."
    )


def _heuristic_synthesize(
    parsed_intent: ParsedIntent,
    ranked_results: list[SearchResult],
    original_problem: str,
) -> SynthesisResult:
    verdict = _heuristic_verdict(parsed_intent, ranked_results, original_problem)
    top_solutions = [_to_existing_solution(result) for result in ranked_results[:5]]
    return SynthesisResult(
        verdict=verdict,
        summary=_heuristic_summary(verdict, parsed_intent),
        existing_solutions=top_solutions,
        one_liner=parsed_intent.potential_one_liner,
        if_you_must_build=_must_build_guidance(parsed_intent)
        if verdict in {Verdict.BUILD_CUSTOM, Verdict.ADAPT_EXISTING}
        else None,
    )


async def synthesize_recommendation(
    parsed_intent: ParsedIntent,
    ranked_results: list[SearchResult],
    original_problem: str,
) -> tuple[SynthesisResult, float]:
    """Generate the final recommendation from parsed intent and ranked results."""
    if not has_llm_config():
        return _heuristic_synthesize(parsed_intent, ranked_results, original_problem), 0.0

    payload: dict[str, Any] = {
        "original_problem": original_problem,
        "parsed_intent": parsed_intent.model_dump(),
        "ranked_results": [result.model_dump() for result in ranked_results[:15]],
    }

    try:
        text_payload, cost = await call_llm_json(
            system_prompt=SYNTH_SYSTEM_PROMPT,
            user_message=json.dumps(payload),
            max_tokens=1500,
        )
        result = SynthesisResult.model_validate(json.loads(extract_json_payload(text_payload)))
        return result, cost
    except Exception:
        return _heuristic_synthesize(parsed_intent, ranked_results, original_problem), 0.0
