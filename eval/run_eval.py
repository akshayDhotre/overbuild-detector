"""
Evaluation harness for OverBuild Detector.

Usage:
    python eval/run_eval.py
    python eval/run_eval.py --output eval/results/run_YYYYMMDD.json
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from overbuild.api.models import AnalyzeRequest
from overbuild.core.pipeline import analyze


def load_scenarios() -> list[dict]:
    scenarios_path = Path(__file__).parent / "scenarios.json"
    return json.loads(scenarios_path.read_text())


async def run_evaluation(output_path: str | None = None) -> dict:
    scenarios = load_scenarios()
    results: list[dict] = []
    correct = 0
    total = len(scenarios)

    for idx, scenario in enumerate(scenarios, start=1):
        print(f"[{idx}/{total}] {scenario['name']}...")
        request = AnalyzeRequest(
            problem=scenario["problem"],
            language=scenario.get("language"),
            context=scenario.get("context"),
        )
        try:
            result = await analyze(request)
            is_correct = result.verdict.value == scenario["expected_verdict"]
            correct += int(is_correct)
            results.append(
                {
                    "scenario": scenario["name"],
                    "problem": scenario["problem"],
                    "expected": scenario["expected_verdict"],
                    "actual": result.verdict.value,
                    "correct": is_correct,
                    "overbuild_score": result.overbuild_score.score,
                    "solutions_found": len(result.existing_solutions),
                    "search_time_ms": result.search_time_ms,
                    "llm_cost_usd": result.llm_cost_usd,
                    "summary": result.summary,
                }
            )
            status = "PASS" if is_correct else "MISS"
            print(
                f"  [{status}] Expected: {scenario['expected_verdict']}, "
                f"Got: {result.verdict.value}, Score: {result.overbuild_score.score}"
            )
        except Exception as exc:  # pragma: no cover - defensive
            results.append({"scenario": scenario["name"], "error": str(exc), "correct": False})
            print(f"  [ERROR] {exc}")

    accuracy = (correct / total * 100) if total else 0.0
    total_cost = sum(item.get("llm_cost_usd", 0.0) for item in results)
    avg_time = sum(item.get("search_time_ms", 0.0) for item in results) / max(total, 1)
    summary = {
        "run_date": datetime.now().isoformat(),
        "total_scenarios": total,
        "correct": correct,
        "accuracy_pct": round(accuracy, 1),
        "total_llm_cost_usd": round(total_cost, 4),
        "avg_search_time_ms": round(avg_time),
        "results": results,
    }
    print(f"\n{'=' * 40}")
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    print(f"Total LLM Cost: ${total_cost:.4f}")
    print(f"Avg Search Time: {avg_time:.0f}ms")

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2))
        print(f"Results saved to {output}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", help="Output JSON path")
    args = parser.parse_args()
    asyncio.run(run_evaluation(args.output))
