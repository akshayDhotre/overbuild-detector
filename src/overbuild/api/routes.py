from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from overbuild.api.models import AnalyzeRequest, AnalyzeResponse
from overbuild.api.ui import get_home_html
from overbuild.core.pipeline import analyze
from overbuild.observability.metrics import get_metrics

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> HTMLResponse:
    return HTMLResponse(get_home_html())


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_problem(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a problem and return build-vs-reuse recommendation."""
    try:
        return await analyze(request)
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "overbuild-detector"}


@router.get("/metrics")
async def metrics() -> dict[str, object]:
    return get_metrics()
