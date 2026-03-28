from collections import Counter
from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger()

_metrics: dict[str, Any] = {
    "total_requests": 0,
    "total_llm_cost_usd": 0.0,
    "verdicts": Counter(),
    "last_request_at": None,
}


async def track_request(
    request_id: str,
    elapsed_ms: int,
    llm_cost_usd: float,
    verdict: str,
) -> None:
    logger.info(
        "analysis_complete",
        request_id=request_id,
        elapsed_ms=elapsed_ms,
        llm_cost_usd=round(llm_cost_usd, 6),
        verdict=verdict,
    )
    record_metric(verdict, llm_cost_usd)


def record_metric(verdict: str, cost: float) -> None:
    _metrics["total_requests"] += 1
    _metrics["total_llm_cost_usd"] += cost
    _metrics["verdicts"][verdict] += 1
    _metrics["last_request_at"] = datetime.now(UTC).isoformat()


def get_metrics() -> dict[str, Any]:
    total_requests = _metrics["total_requests"]
    return {
        "total_requests": total_requests,
        "total_llm_cost_usd": round(float(_metrics["total_llm_cost_usd"]), 6),
        "avg_cost_per_request": round(
            float(_metrics["total_llm_cost_usd"]) / max(total_requests, 1),
            6,
        ),
        "verdicts": dict(_metrics["verdicts"]),
        "last_request_at": _metrics["last_request_at"],
    }
