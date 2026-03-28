from fastapi.testclient import TestClient

from overbuild.api.models import AnalyzeResponse
from overbuild.main import create_app


def test_home_route() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "OverBuild Detector" in response.text
    assert "Analyze" in response.text
    assert "Export JSON" in response.text
    assert "Export Markdown" in response.text


def test_health_route() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_analyze_route(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    app = create_app()
    client = TestClient(app)

    async def fake_analyze(request):  # type: ignore[no-untyped-def]
        return AnalyzeResponse.model_validate(
            {
                "verdict": "USE_EXISTING",
                "overbuild_score": {
                    "problem_complexity": 3,
                    "best_existing_complexity": 2,
                    "custom_build_complexity": 6,
                    "score": 2.0,
                    "explanation": "Mild over-engineering risk",
                },
                "summary": "Use existing package",
                "existing_solutions": [],
                "one_liner": None,
                "if_you_must_build": None,
                "sources_searched": ["github"],
                "total_results_found": 1,
                "search_time_ms": 100,
                "llm_cost_usd": 0.0,
                "request_id": "abc123",
            }
        )

    monkeypatch.setattr("overbuild.api.routes.analyze", fake_analyze)
    response = client.post("/analyze", json={"problem": "Need rate limiter", "language": "python"})
    assert response.status_code == 200
    assert response.json()["verdict"] == "USE_EXISTING"


def test_metrics_route() -> None:
    client = TestClient(create_app())
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "total_requests" in response.json()
