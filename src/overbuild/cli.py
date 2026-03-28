import asyncio
import sys

import click

from overbuild.api.models import AnalyzeRequest
from overbuild.core.pipeline import analyze

DEMO_SCENARIOS = [
    {
        "name": "The 82K-line cleanup daemon",
        "problem": "I need a tool that watches my Rust project directories and deletes "
        "build artifacts (target/ folders) older than 7 days to free disk space",
        "language": "rust",
        "expected_verdict": "JUST_USE_A_ONE_LINER",
    },
    {
        "name": "Rate limiter",
        "problem": "I need to add rate limiting to my FastAPI endpoints, 100 requests per minute per IP",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
    },
    {
        "name": "File watcher",
        "problem": "Create a tool that watches a directory for file changes and runs tests",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
    },
    {
        "name": "Custom JSON logger",
        "problem": "Build a structured JSON logging library for Python with context fields",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
    },
    {
        "name": "Healthcare rule engine",
        "problem": "Build a domain-specific rule engine for healthcare prior authorization with audit trails",
        "language": "python",
        "expected_verdict": "BUILD_CUSTOM",
    },
]


@click.command()
@click.argument("problem", required=False)
@click.option("--language", "-l", help="Target programming language")
@click.option("--context", "-c", help="Additional context")
@click.option("--demo", is_flag=True, help="Run built-in demo scenarios")
@click.option("--json-output", is_flag=True, help="Print raw JSON output")
def main(
    problem: str | None, language: str | None, context: str | None, demo: bool, json_output: bool
) -> None:
    """OverBuild Detector: Before you build, check if it already exists."""
    if demo:
        asyncio.run(_run_demos(json_output))
        return
    if problem:
        asyncio.run(_run_single(problem, language, context, json_output))
        return

    click.echo("Usage: overbuild 'describe what you want to build'")
    click.echo("       overbuild --demo")
    sys.exit(1)


async def _run_single(
    problem: str,
    language: str | None,
    context: str | None,
    json_output: bool,
) -> None:
    request = AnalyzeRequest(problem=problem, language=language, context=context)
    result = await analyze(request)
    if json_output:
        click.echo(result.model_dump_json(indent=2))
    else:
        _print_result(result)


async def _run_demos(json_output: bool) -> None:
    for scenario in DEMO_SCENARIOS:
        click.echo(f"\n{'=' * 60}")
        click.echo(f"SCENARIO: {scenario['name']}")
        click.echo(f"Problem: {scenario['problem']}")
        click.echo(f"Expected: {scenario['expected_verdict']}")
        click.echo(f"{'=' * 60}\n")
        request = AnalyzeRequest(
            problem=scenario["problem"],
            language=scenario["language"],
            context=None,
        )
        result = await analyze(request)
        if json_output:
            click.echo(result.model_dump_json(indent=2))
        else:
            _print_result(result)
        match = "PASS" if result.verdict.value == scenario["expected_verdict"] else "MISS"
        click.echo(
            f"\n[{match}] Expected: {scenario['expected_verdict']}, Got: {result.verdict.value}"
        )


def _print_result(result) -> None:  # type: ignore[no-untyped-def]
    verdict_colors = {
        "USE_EXISTING": "green",
        "ADAPT_EXISTING": "yellow",
        "BUILD_CUSTOM": "blue",
        "JUST_USE_A_ONE_LINER": "cyan",
    }
    click.echo()
    click.secho(
        f"  VERDICT: {result.verdict.value}", fg=verdict_colors.get(result.verdict.value, "white")
    )
    click.echo(
        f"  OverBuild Score: {result.overbuild_score.score} ({result.overbuild_score.explanation})"
    )
    click.echo(f"  LLM Cost: ${result.llm_cost_usd:.4f}")
    click.echo(f"  Search Time: {result.search_time_ms}ms")
    click.echo(f"  Results Found: {result.total_results_found}")
    click.echo()
    click.echo(f"  {result.summary}")

    if result.one_liner:
        click.echo()
        click.secho("  ONE-LINER:", fg="cyan")
        click.echo(f"    {result.one_liner}")

    if result.existing_solutions:
        click.echo()
        click.secho("  EXISTING SOLUTIONS:", fg="green")
        for idx, solution in enumerate(result.existing_solutions[:3], start=1):
            click.echo(f"    {idx}. {solution.name}")
            click.echo(f"       {solution.description}")
            if solution.install_command:
                click.echo(f"       Install: {solution.install_command}")


if __name__ == "__main__":
    main()
