# OverBuild Detector — Project Specification & Scaffolding Guide

**Working Name:** "Cron or Code?"  
**Tagline:** Before you build, check if it already exists.  
**Version:** v0.1 MVP  
**Last Updated:** March 17, 2026  

---

## 1. Project Overview

### What It Does

You describe a problem in plain English — *"I need to clean up old Rust build artifacts that fill my disk"* — and the tool:

1. **Parses** intent, target language, domain, and expected complexity (LLM call #1)
2. **Searches in parallel** across Libraries.io (30+ package managers), GitHub, npm, StackOverflow, Ecosyste.ms
3. **Deduplicates and ranks** results by relevance, popularity, maintenance status
4. **Synthesizes** a recommendation with an OverBuild Score (LLM call #2)
5. **Returns verdict:** `USE_EXISTING` / `ADAPT_EXISTING` / `BUILD_CUSTOM` / `JUST_USE_A_ONE_LINER`

### Why It Matters

AI coding agents systematically over-engineer because they respond to prompt complexity, not problem complexity. The 82,000-line cleanup daemon that could be replaced with `find ... -mtime +7 -exec rm` is a pattern, not an edge case. This tool intervenes at the critical moment — **before code generation begins**.

### Career Portfolio Signals

This project demonstrates: LLM tool-use integration, async Python services, FastAPI production APIs, MCP protocol implementation, Docker deployment, CI/CD pipelines, cost-aware AI services, structured evaluation. It is intentionally built with a **lean stack** (no framework overhead) to show clean engineering judgment.

---

## 2. Architecture

### High-Level Flow

```
User Input (natural language problem description)
    │
    ▼
┌─────────────────────────────────────┐
│  LLM Call #1: Parse Intent          │
│  → language, domain, keywords,      │
│    expected_complexity (1-10),       │
│    search_queries[]                  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  Parallel Search (asyncio.gather)   │
│  ┌───────────┐  ┌────────────────┐  │
│  │Libraries.io│  │ GitHub Search  │  │
│  └───────────┘  └────────────────┘  │
│  ┌───────────┐  ┌────────────────┐  │
│  │ npm Reg.  │  │ StackOverflow  │  │
│  └───────────┘  └────────────────┘  │
│  ┌───────────┐                      │
│  │Ecosyste.ms│                      │
│  └───────────┘                      │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  Deduplicate & Rank Results         │
│  (deterministic, no LLM needed)     │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  LLM Call #2: Synthesize            │
│  → verdict, overbuild_score,        │
│    existing_solutions[],             │
│    one_liner (if applicable),        │
│    complexity_comparison,            │
│    recommendation_text               │
└─────────────────┬───────────────────┘
                  │
                  ▼
         Structured JSON Response
```

### Design Principles

- **Two LLM calls, not an agent loop.** This is a pipeline, not a conversation. Parse → Search → Synthesize. No retry loops, no agent state machines. LangGraph would be over-engineering here (ironic for a tool that detects over-engineering).
- **Parallel I/O, not sequential.** All 5 API searches fire simultaneously via `asyncio.gather()`. Total search time = slowest API, not sum of all APIs.
- **Deterministic ranking.** Deduplication and ranking use heuristic scoring (stars, dependents, last updated, description match), not LLM calls. LLMs are expensive; use them only where judgment is needed.
- **Structured outputs everywhere.** Both LLM calls return validated JSON via Pydantic models. No free-text parsing.

---

## 3. Tech Stack

| Component | Choice | Reasoning |
|-----------|--------|-----------|
| Language | Python 3.11+ | Async-native, best LLM ecosystem |
| Web Framework | FastAPI | Async, auto-docs, Pydantic validation built-in |
| HTTP Client | httpx | Async HTTP for parallel API calls |
| LLM | Anthropic Claude API (claude-sonnet-4-20250514) | Structured output support, cost-effective for 2 calls/request |
| MCP Server | mcp Python SDK | Expose analyzer as tool for AI coding agents |
| Containerization | Docker (multi-stage build) | Production deployment + portfolio visibility |
| CI/CD | GitHub Actions | Lint → Test → Build → Push (free for public repos) |
| Deployment | Railway free tier / Render free tier / $5 VPS | Cost-effective for personal project; IaC files for AWS ECS kept in repo |
| Caching | In-memory TTL cache (cachetools) | Zero-cost; Redis config toggle preserved for production readiness |
| Logging | structlog | Structured JSON logging with cost tracking |
| Testing | pytest + pytest-asyncio | Async test support |
| Linting | ruff | Fast, replaces flake8+isort+black |

---

## 4. Project Structure

```
overbuild-detector/
├── README.md                       # Project overview, demo, architecture diagram
├── Dockerfile                      # Multi-stage production build
├── docker-compose.yml              # Local dev (app + redis)
├── pyproject.toml                  # Project config, dependencies, ruff config
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Lint + test on every PR
│       └── deploy.yml              # Build + push + deploy on main
│
├── src/
│   └── overbuild/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app entry point
│       ├── config.py               # Settings via pydantic-settings (env vars)
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py           # POST /analyze, GET /health, GET /demo/{scenario}
│       │   └── models.py           # Request/Response Pydantic models
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── pipeline.py         # Main orchestrator: parse → search → synthesize
│       │   ├── parser.py           # LLM Call #1: parse intent
│       │   ├── synthesizer.py      # LLM Call #2: synthesize recommendation
│       │   └── scorer.py           # OverBuild Score calculation (deterministic)
│       │
│       ├── search/
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract base class for search providers
│       │   ├── librariesio.py      # Libraries.io API client
│       │   ├── github_search.py    # GitHub Search API client
│       │   ├── npm_registry.py     # npm Registry API client
│       │   ├── stackoverflow.py    # StackOverflow API client
│       │   ├── ecosystems.py       # Ecosyste.ms API client
│       │   ├── aggregator.py       # Parallel search + dedup + rank
│       │   └── cache.py            # TTL cache for search results
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── server.py           # MCP server exposing analyze tool
│       │
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── logging.py          # Structured logging setup (structlog)
│       │   ├── metrics.py          # Request metrics, LLM token/cost tracking
│       │   └── middleware.py       # FastAPI middleware for request tracing
│       │
│       └── cli.py                  # CLI entry point (click or typer)
│
├── tests/
│   ├── conftest.py                 # Shared fixtures, mock API responses
│   ├── test_parser.py              # Unit tests for LLM parsing
│   ├── test_search/
│   │   ├── test_librariesio.py
│   │   ├── test_github.py
│   │   ├── test_aggregator.py
│   │   └── fixtures/               # Saved API response fixtures for testing
│   │       ├── librariesio_response.json
│   │       ├── github_response.json
│   │       └── stackoverflow_response.json
│   ├── test_synthesizer.py
│   ├── test_scorer.py
│   ├── test_pipeline.py            # Integration test: full pipeline
│   └── test_mcp_server.py
│
├── eval/
│   ├── scenarios.json              # Evaluation scenarios with expected verdicts
│   ├── run_eval.py                 # Run all scenarios, measure accuracy
│   └── results/                    # Evaluation run outputs (git-ignored)
│       └── .gitkeep
│
├── scripts/
│   ├── demo.py                     # Quick demo runner (5 built-in scenarios)
│   └── seed_cache.py               # Pre-populate cache for demo
│
└── infra/                          # Infrastructure as Code (optional, for AWS deploy)
    ├── Dockerfile.prod             # Production-optimized Dockerfile (if different)
    └── terraform/                  # Terraform files for AWS ECS deployment
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## 5. Data Models

### 5.1 API Request

```python
# src/overbuild/api/models.py

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class AnalyzeRequest(BaseModel):
    """User's problem description to analyze."""
    problem: str = Field(
        ...,
        description="Natural language description of what you want to build",
        min_length=10,
        max_length=2000,
        examples=[
            "I need to clean up old Rust build artifacts older than 7 days",
            "Build a rate limiter for my FastAPI endpoints",
            "Create a tool that watches a directory for file changes and runs tests"
        ]
    )
    language: Optional[str] = Field(
        None,
        description="Target programming language (auto-detected if not provided)",
        examples=["python", "rust", "javascript", "go"]
    )
    context: Optional[str] = Field(
        None,
        description="Additional context: OS, constraints, existing stack",
        max_length=500
    )
```

### 5.2 LLM Call #1 Output (Parse Intent)

```python
class ParsedIntent(BaseModel):
    """Structured output from LLM Call #1."""
    problem_summary: str = Field(description="One-line summary of what the user wants")
    target_language: str = Field(description="Primary language/ecosystem")
    domain: str = Field(description="Problem domain: cli-tool, web-backend, data-processing, devops, etc.")
    keywords: list[str] = Field(description="3-6 search keywords for package/tool discovery")
    os_relevant: bool = Field(description="Could this be solved with OS-level tools/commands?")
    expected_complexity: int = Field(
        ge=1, le=10,
        description="How complex SHOULD the solution be? 1=one-liner, 5=small library, 10=complex system"
    )
    search_queries: list[str] = Field(
        description="3-5 specific search queries for different sources",
        min_length=2, max_length=6
    )
    potential_one_liner: Optional[str] = Field(
        None, description="If the problem might have a shell one-liner solution, suggest it here"
    )
```

### 5.3 Search Result (Unified)

```python
class SearchSource(str, Enum):
    LIBRARIES_IO = "libraries_io"
    GITHUB = "github"
    NPM = "npm"
    STACKOVERFLOW = "stackoverflow"
    ECOSYSTEMS = "ecosystems"


class SearchResult(BaseModel):
    """Normalized search result from any source."""
    source: SearchSource
    name: str
    description: str
    url: str
    relevance_score: float = Field(ge=0.0, le=1.0, description="Computed relevance 0-1")

    # Popularity signals (not all sources provide all fields)
    stars: Optional[int] = None
    downloads_monthly: Optional[int] = None
    dependents_count: Optional[int] = None

    # Health signals
    last_updated: Optional[str] = None       # ISO date string
    is_maintained: Optional[bool] = None     # Updated within last 12 months
    license: Optional[str] = None

    # Source-specific
    language: Optional[str] = None
    package_manager: Optional[str] = None    # npm, pypi, cargo, etc.
    stackoverflow_score: Optional[int] = None
    answer_count: Optional[int] = None
```

### 5.4 OverBuild Score

```python
class OverBuildScore(BaseModel):
    """Quantified comparison: problem complexity vs minimum solution complexity."""
    problem_complexity: int = Field(
        ge=1, le=10,
        description="How complex is the PROBLEM? (from LLM parse)"
    )
    best_existing_complexity: int = Field(
        ge=0, le=10,
        description="Complexity of using best existing solution. 0 = one-liner exists"
    )
    custom_build_complexity: int = Field(
        ge=1, le=10,
        description="Estimated complexity of building from scratch"
    )
    score: float = Field(
        description="OverBuild Score = custom_build_complexity / max(problem_complexity, 1). "
                    "1.0 = right-sized, 3.0 = 3x more complex than needed"
    )
    explanation: str = Field(description="One-line explanation of the score")
```

### 5.5 API Response (Final)

```python
class Verdict(str, Enum):
    USE_EXISTING = "USE_EXISTING"
    ADAPT_EXISTING = "ADAPT_EXISTING"
    BUILD_CUSTOM = "BUILD_CUSTOM"
    JUST_USE_A_ONE_LINER = "JUST_USE_A_ONE_LINER"


class ExistingSolution(BaseModel):
    """A specific existing solution recommended."""
    name: str
    description: str
    url: str
    install_command: Optional[str] = None    # e.g., "pip install watchdog", "brew install fswatch"
    usage_example: Optional[str] = None      # Short code/command snippet
    pros: list[str]
    cons: list[str]
    source: SearchSource
    stars: Optional[int] = None
    last_updated: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Complete analysis response."""
    verdict: Verdict
    overbuild_score: OverBuildScore
    summary: str = Field(description="2-3 sentence plain-English recommendation")
    existing_solutions: list[ExistingSolution] = Field(
        description="Top 3-5 existing solutions, ranked by relevance"
    )
    one_liner: Optional[str] = Field(
        None, description="Shell/CLI one-liner if applicable"
    )
    if_you_must_build: Optional[str] = Field(
        None,
        description="If building custom, what's the minimal viable approach? "
                    "Which existing libraries should it use internally?"
    )

    # Metadata
    sources_searched: list[SearchSource]
    total_results_found: int
    search_time_ms: int
    llm_cost_usd: float = Field(description="Total LLM API cost for this request")
    request_id: str
```

---

## 6. Core Pipeline Implementation

### 6.1 Main Orchestrator

```python
# src/overbuild/core/pipeline.py

import time
import uuid
from overbuild.core.parser import parse_intent
from overbuild.core.synthesizer import synthesize_recommendation
from overbuild.core.scorer import calculate_overbuild_score
from overbuild.search.aggregator import search_all_sources
from overbuild.observability.metrics import track_request
from overbuild.api.models import AnalyzeRequest, AnalyzeResponse


async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Main pipeline: Parse → Search → Deduplicate → Score → Synthesize."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.monotonic()
    total_llm_cost = 0.0

    # Step 1: Parse intent (LLM Call #1)
    parsed, parse_cost = await parse_intent(
        problem=request.problem,
        language=request.language,
        context=request.context,
    )
    total_llm_cost += parse_cost

    # Step 2: Parallel search across all sources
    search_results, sources_searched = await search_all_sources(
        queries=parsed.search_queries,
        keywords=parsed.keywords,
        language=parsed.target_language,
        os_relevant=parsed.os_relevant,
    )

    # Step 3: Deduplicate and rank (deterministic, no LLM)
    ranked_results = deduplicate_and_rank(search_results, parsed)

    # Step 4: Synthesize recommendation (LLM Call #2)
    recommendation, synth_cost = await synthesize_recommendation(
        parsed_intent=parsed,
        ranked_results=ranked_results[:15],  # Top 15 to stay within context
        original_problem=request.problem,
    )
    total_llm_cost += synth_cost

    # Step 5: Calculate OverBuild Score (deterministic)
    score = calculate_overbuild_score(
        problem_complexity=parsed.expected_complexity,
        best_existing=ranked_results[0] if ranked_results else None,
        recommendation=recommendation,
    )

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    response = AnalyzeResponse(
        verdict=recommendation.verdict,
        overbuild_score=score,
        summary=recommendation.summary,
        existing_solutions=recommendation.existing_solutions,
        one_liner=parsed.potential_one_liner or recommendation.one_liner,
        if_you_must_build=recommendation.if_you_must_build,
        sources_searched=sources_searched,
        total_results_found=len(search_results),
        search_time_ms=elapsed_ms,
        llm_cost_usd=total_llm_cost,
        request_id=request_id,
    )

    # Track metrics
    await track_request(request_id, elapsed_ms, total_llm_cost, recommendation.verdict)

    return response
```

### 6.2 LLM Call #1: Parse Intent

```python
# src/overbuild/core/parser.py

import anthropic
from overbuild.api.models import ParsedIntent
from overbuild.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

PARSE_SYSTEM_PROMPT = """You are an expert software engineer analyzing a problem description.
Your job is to understand WHAT the user wants to achieve and determine:
1. The target language/ecosystem
2. The problem domain
3. Keywords that would find existing packages/tools solving this
4. Whether OS-level tools (cron, find, systemd, etc.) might solve it
5. How complex the solution SHOULD be (not how complex it COULD be)
6. Specific search queries for package registries and GitHub
7. If there's an obvious one-liner (shell command, built-in function, etc.)

Be aggressive about low complexity estimates. Most problems developers describe
can be solved with much simpler solutions than they think. A cleanup job is complexity 1-2,
a rate limiter is 3-4, a full web framework is 7-8.

Respond ONLY with valid JSON matching the schema. No other text."""

async def parse_intent(
    problem: str,
    language: str | None = None,
    context: str | None = None,
) -> tuple[ParsedIntent, float]:
    """Parse user's problem description into structured search intent.
    Returns (parsed_intent, cost_usd)."""

    user_message = f"Problem: {problem}"
    if language:
        user_message += f"\nLanguage: {language}"
    if context:
        user_message += f"\nContext: {context}"

    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=1000,
        system=PARSE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Calculate cost (Claude Sonnet 4 pricing)
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000

    # Parse JSON response
    parsed = ParsedIntent.model_validate_json(response.content[0].text)
    return parsed, cost
```

### 6.3 Parallel Search Aggregator

```python
# src/overbuild/search/aggregator.py

import asyncio
from overbuild.search.librariesio import search_librariesio
from overbuild.search.github_search import search_github
from overbuild.search.npm_registry import search_npm
from overbuild.search.stackoverflow import search_stackoverflow
from overbuild.search.ecosystems import search_ecosystems
from overbuild.api.models import SearchResult, SearchSource


async def search_all_sources(
    queries: list[str],
    keywords: list[str],
    language: str,
    os_relevant: bool,
) -> tuple[list[SearchResult], list[SearchSource]]:
    """Search all sources in parallel. Returns (results, sources_that_responded)."""

    primary_query = queries[0] if queries else " ".join(keywords[:3])

    tasks = {
        "librariesio": search_librariesio(primary_query, language),
        "github": search_github(primary_query, language),
        "stackoverflow": search_stackoverflow(primary_query, language),
    }

    # npm only for JavaScript/TypeScript problems
    if language in ("javascript", "typescript", "node", "js", "ts"):
        tasks["npm"] = search_npm(primary_query)

    # Ecosyste.ms as additional cross-ecosystem search
    tasks["ecosystems"] = search_ecosystems(primary_query)

    # Fire all searches in parallel
    results_map = {}
    for key, coro in tasks.items():
        results_map[key] = coro

    gathered = await asyncio.gather(
        *results_map.values(),
        return_exceptions=True,
    )

    all_results = []
    sources_searched = []

    for key, result in zip(results_map.keys(), gathered):
        if isinstance(result, Exception):
            # Log error but don't fail the whole request
            # structlog.get_logger().warning("search_failed", source=key, error=str(result))
            continue
        all_results.extend(result)
        sources_searched.append(SearchSource(key) if key != "ecosystems" else SearchSource.ECOSYSTEMS)

    return all_results, sources_searched
```

### 6.4 OverBuild Score Calculator

```python
# src/overbuild/core/scorer.py

from overbuild.api.models import OverBuildScore, SearchResult


def calculate_overbuild_score(
    problem_complexity: int,
    best_existing: SearchResult | None,
    recommendation,
) -> OverBuildScore:
    """Calculate OverBuild Score: custom_complexity / problem_complexity.

    Score interpretation:
    - 0.0-0.5: Problem is trivially solvable (one-liner territory)
    - 0.5-1.0: Right-sized — building custom is proportional to the problem
    - 1.0-2.0: Mild over-engineering risk
    - 2.0-5.0: Significant over-engineering — existing solutions strongly recommended
    - 5.0+: Extreme over-engineering — you're building an 82K-line cleanup daemon
    """

    # Estimate existing solution complexity
    if best_existing and best_existing.relevance_score > 0.7:
        best_existing_complexity = max(1, problem_complexity - 2)
    elif best_existing and best_existing.relevance_score > 0.4:
        best_existing_complexity = problem_complexity
    else:
        best_existing_complexity = problem_complexity + 2

    # Estimate custom build complexity
    # This is heuristic — in v2, could use static analysis on existing code
    custom_build_complexity = min(10, problem_complexity + 3)

    # If strong one-liner or trivial existing solution exists
    if problem_complexity <= 2 and best_existing:
        best_existing_complexity = 0

    score = custom_build_complexity / max(problem_complexity, 1)

    if score <= 0.5:
        explanation = "Trivially solvable — use the existing one-liner or tool"
    elif score <= 1.0:
        explanation = "Building custom is reasonable if existing solutions don't fit"
    elif score <= 2.0:
        explanation = "Mild over-engineering risk — check existing solutions first"
    elif score <= 5.0:
        explanation = "Significant over-engineering likely — strong existing solutions available"
    else:
        explanation = "Extreme over-engineering — you almost certainly don't need custom code"

    return OverBuildScore(
        problem_complexity=problem_complexity,
        best_existing_complexity=best_existing_complexity,
        custom_build_complexity=custom_build_complexity,
        score=round(score, 2),
        explanation=explanation,
    )
```

---

## 7. Search Provider Implementations

### 7.1 Base Class

```python
# src/overbuild/search/base.py

from abc import ABC, abstractmethod
from overbuild.api.models import SearchResult


class SearchProvider(ABC):
    """Base class for all search providers."""

    @abstractmethod
    async def search(self, query: str, language: str | None = None) -> list[SearchResult]:
        """Search this source and return normalized results."""
        ...
```

### 7.2 Libraries.io (Primary — 30+ package managers)

```python
# src/overbuild/search/librariesio.py

import httpx
from overbuild.api.models import SearchResult, SearchSource
from overbuild.config import settings

BASE_URL = "https://libraries.io/api"

# Rate limit: 60 requests/minute (free tier)
# Returns results across: npm, PyPI, Maven, NuGet, Cargo, RubyGems, Go, CocoaPods,
# Homebrew, Packagist, Hex, Pub, CPAN, CRAN, Hackage, and 15+ more


async def search_librariesio(query: str, language: str | None = None) -> list[SearchResult]:
    """Search Libraries.io across 30+ package managers."""
    params = {
        "q": query,
        "api_key": settings.librariesio_api_key,
        "per_page": 10,
    }
    if language:
        # Map language to Libraries.io platform filter
        platform_map = {
            "python": "pypi", "javascript": "npm", "typescript": "npm",
            "rust": "cargo", "go": "go", "ruby": "rubygems",
            "java": "maven", "csharp": "nuget", "php": "packagist",
        }
        if language.lower() in platform_map:
            params["platforms"] = platform_map[language.lower()]

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BASE_URL}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data:
        results.append(SearchResult(
            source=SearchSource.LIBRARIES_IO,
            name=item.get("name", ""),
            description=item.get("description", "")[:200],
            url=item.get("repository_url") or item.get("homepage") or "",
            stars=item.get("stars"),
            downloads_monthly=item.get("latest_download_url"),  # varies by platform
            dependents_count=item.get("dependents_count"),
            last_updated=item.get("latest_release_published_at"),
            is_maintained=_is_maintained(item.get("latest_release_published_at")),
            license=item.get("licenses"),
            language=item.get("language"),
            package_manager=item.get("platform"),
            relevance_score=0.0,  # Will be computed by aggregator
        ))

    return results


def _is_maintained(last_release: str | None) -> bool | None:
    """Check if package was updated in the last 12 months."""
    if not last_release:
        return None
    from datetime import datetime, timezone, timedelta
    try:
        dt = datetime.fromisoformat(last_release.replace("Z", "+00:00"))
        return dt > datetime.now(timezone.utc) - timedelta(days=365)
    except (ValueError, TypeError):
        return None
```

### 7.3 GitHub Search

```python
# src/overbuild/search/github_search.py

import httpx
from overbuild.api.models import SearchResult, SearchSource
from overbuild.config import settings

# Rate limit: 10 requests/minute (unauthenticated), 30/min (authenticated)
# Use authenticated requests with a GitHub PAT


async def search_github(query: str, language: str | None = None) -> list[SearchResult]:
    """Search GitHub repositories."""
    search_query = query
    if language:
        search_query += f" language:{language}"

    headers = {}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    headers["Accept"] = "application/vnd.github+json"

    params = {
        "q": search_query,
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.github.com/search/repositories",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("items", []):
        results.append(SearchResult(
            source=SearchSource.GITHUB,
            name=item["full_name"],
            description=(item.get("description") or "")[:200],
            url=item["html_url"],
            stars=item.get("stargazers_count"),
            last_updated=item.get("pushed_at"),
            is_maintained=_is_recently_pushed(item.get("pushed_at")),
            license=item.get("license", {}).get("spdx_id") if item.get("license") else None,
            language=item.get("language"),
            relevance_score=0.0,
        ))

    return results


def _is_recently_pushed(pushed_at: str | None) -> bool | None:
    if not pushed_at:
        return None
    from datetime import datetime, timezone, timedelta
    try:
        dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        return dt > datetime.now(timezone.utc) - timedelta(days=365)
    except (ValueError, TypeError):
        return None
```

### 7.4 StackOverflow

```python
# src/overbuild/search/stackoverflow.py

import httpx
from overbuild.api.models import SearchResult, SearchSource

# Rate limit: 300 requests/day (unauthenticated), 10,000/day (with key)
# API: https://api.stackexchange.com/2.3/


async def search_stackoverflow(query: str, language: str | None = None) -> list[SearchResult]:
    """Search StackOverflow for existing answers."""
    tagged = language if language else ""

    params = {
        "order": "desc",
        "sort": "relevance",
        "intitle": query,
        "site": "stackoverflow",
        "pagesize": 5,
        "filter": "withbody",  # Include answer preview
    }
    if tagged:
        params["tagged"] = tagged

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.stackexchange.com/2.3/search/advanced",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("items", []):
        if not item.get("is_answered"):
            continue
        results.append(SearchResult(
            source=SearchSource.STACKOVERFLOW,
            name=item.get("title", ""),
            description=item.get("title", ""),
            url=item.get("link", ""),
            stackoverflow_score=item.get("score"),
            answer_count=item.get("answer_count"),
            relevance_score=0.0,
        ))

    return results
```

### 7.5 npm Registry & Ecosyste.ms

```python
# src/overbuild/search/npm_registry.py

import httpx
from overbuild.api.models import SearchResult, SearchSource

# npm registry: no auth needed, generous rate limits
# Endpoint: https://registry.npmjs.org/-/v1/search


async def search_npm(query: str) -> list[SearchResult]:
    """Search npm registry directly."""
    params = {"text": query, "size": 10}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://registry.npmjs.org/-/v1/search",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for obj in data.get("objects", []):
        pkg = obj.get("package", {})
        results.append(SearchResult(
            source=SearchSource.NPM,
            name=pkg.get("name", ""),
            description=(pkg.get("description") or "")[:200],
            url=pkg.get("links", {}).get("npm") or pkg.get("links", {}).get("homepage") or "",
            last_updated=pkg.get("date"),
            package_manager="npm",
            language="javascript",
            relevance_score=0.0,
        ))

    return results
```

```python
# src/overbuild/search/ecosystems.py

import httpx
from overbuild.api.models import SearchResult, SearchSource

# Ecosyste.ms: Open API, no auth needed
# Endpoint: https://packages.ecosyste.ms/api/v1/packages/search


async def search_ecosystems(query: str) -> list[SearchResult]:
    """Search Ecosyste.ms (cross-ecosystem package search)."""
    params = {"q": query, "per_page": 10}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://packages.ecosyste.ms/api/v1/packages/search",
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data:
        results.append(SearchResult(
            source=SearchSource.ECOSYSTEMS,
            name=item.get("name", ""),
            description=(item.get("description") or "")[:200],
            url=item.get("repository_url") or item.get("homepage") or "",
            stars=item.get("stars"),
            downloads_monthly=item.get("downloads"),
            last_updated=item.get("latest_release_published_at"),
            package_manager=item.get("ecosystem"),
            language=item.get("language"),
            relevance_score=0.0,
        ))

    return results
```

---

## 8. MCP Server Implementation

This is the **career-differentiating addition**. Exposes the OverBuild Detector as an MCP tool that AI coding agents (Cursor, Claude Code, Windsurf, etc.) can call before generating code.

```python
# src/overbuild/mcp/server.py

"""
MCP Server for OverBuild Detector.

Usage:
    # Run as standalone MCP server (stdio transport for IDE integration)
    python -m overbuild.mcp.server

    # Or register in Claude Desktop / Cursor MCP config:
    # {
    #   "mcpServers": {
    #     "overbuild": {
    #       "command": "python",
    #       "args": ["-m", "overbuild.mcp.server"]
    #     }
    #   }
    # }
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

from overbuild.core.pipeline import analyze
from overbuild.api.models import AnalyzeRequest


server = Server("overbuild-detector")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="check_before_building",
            description=(
                "Before writing code for a task, check if existing packages, OS tools, "
                "or one-liners already solve the problem. Prevents over-engineering by "
                "finding simpler alternatives. Call this BEFORE generating any code for "
                "a new feature, utility, or tool."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "problem": {
                        "type": "string",
                        "description": "What you're about to build, in plain English"
                    },
                    "language": {
                        "type": "string",
                        "description": "Target programming language",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context: OS, constraints, existing stack",
                    },
                },
                "required": ["problem"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "check_before_building":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    request = AnalyzeRequest(**arguments)
    result = await analyze(request)

    # Format for LLM consumption
    output = f"""## OverBuild Analysis

**Verdict: {result.verdict.value}**
**OverBuild Score: {result.overbuild_score.score}** ({result.overbuild_score.explanation})

{result.summary}
"""

    if result.one_liner:
        output += f"\n### One-Liner Solution\n```\n{result.one_liner}\n```\n"

    if result.existing_solutions:
        output += "\n### Existing Solutions\n"
        for i, sol in enumerate(result.existing_solutions[:3], 1):
            output += f"\n**{i}. {sol.name}**\n"
            output += f"   {sol.description}\n"
            output += f"   URL: {sol.url}\n"
            if sol.install_command:
                output += f"   Install: `{sol.install_command}`\n"

    if result.if_you_must_build:
        output += f"\n### If You Must Build Custom\n{result.if_you_must_build}\n"

    return [TextContent(type="text", text=output)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 9. CLI Interface

```python
# src/overbuild/cli.py

"""
CLI entry point for OverBuild Detector.

Usage:
    overbuild "I need to clean up old Rust build artifacts"
    overbuild "Build a rate limiter for FastAPI" --language python
    overbuild --demo  # Run all 5 demo scenarios
"""

import asyncio
import json
import sys
import click

from overbuild.core.pipeline import analyze
from overbuild.api.models import AnalyzeRequest


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
        "problem": "I need to add rate limiting to my FastAPI endpoints - "
                   "100 requests per minute per IP address",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
    },
    {
        "name": "File watcher",
        "problem": "Create a tool that watches a directory for file changes "
                   "and automatically runs my test suite when Python files change",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
    },
    {
        "name": "Custom JSON logger",
        "problem": "Build a structured JSON logging library for Python "
                   "with log levels, timestamps, and context fields",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
    },
    {
        "name": "Genuinely custom (should recommend building)",
        "problem": "Build a domain-specific rule engine that evaluates healthcare "
                   "prior authorization requests against insurance policy criteria "
                   "with audit trails and explainability",
        "language": "python",
        "expected_verdict": "BUILD_CUSTOM",
    },
]


@click.command()
@click.argument("problem", required=False)
@click.option("--language", "-l", help="Target programming language")
@click.option("--context", "-c", help="Additional context")
@click.option("--demo", is_flag=True, help="Run all demo scenarios")
@click.option("--json-output", is_flag=True, help="Output raw JSON")
def main(problem, language, context, demo, json_output):
    """OverBuild Detector: Before you build, check if it already exists."""
    if demo:
        asyncio.run(_run_demos(json_output))
    elif problem:
        asyncio.run(_run_single(problem, language, context, json_output))
    else:
        click.echo("Usage: overbuild 'describe what you want to build'")
        click.echo("       overbuild --demo")
        sys.exit(1)


async def _run_single(problem, language, context, json_output):
    request = AnalyzeRequest(problem=problem, language=language, context=context)
    result = await analyze(request)

    if json_output:
        click.echo(result.model_dump_json(indent=2))
    else:
        _print_result(result)


async def _run_demos(json_output):
    for scenario in DEMO_SCENARIOS:
        click.echo(f"\n{'='*60}")
        click.echo(f"SCENARIO: {scenario['name']}")
        click.echo(f"Problem: {scenario['problem']}")
        click.echo(f"Expected: {scenario['expected_verdict']}")
        click.echo(f"{'='*60}\n")

        request = AnalyzeRequest(
            problem=scenario["problem"],
            language=scenario.get("language"),
        )
        result = await analyze(request)

        if json_output:
            click.echo(result.model_dump_json(indent=2))
        else:
            _print_result(result)

        match = "PASS" if result.verdict.value == scenario["expected_verdict"] else "MISS"
        click.echo(f"\n[{match}] Expected: {scenario['expected_verdict']}, Got: {result.verdict.value}")
        click.echo()


def _print_result(result):
    """Pretty-print result to terminal."""
    verdict_colors = {
        "USE_EXISTING": "green",
        "ADAPT_EXISTING": "yellow",
        "BUILD_CUSTOM": "blue",
        "JUST_USE_A_ONE_LINER": "cyan",
    }
    color = verdict_colors.get(result.verdict.value, "white")

    click.echo()
    click.secho(f"  VERDICT: {result.verdict.value}", fg=color, bold=True)
    click.echo(f"  OverBuild Score: {result.overbuild_score.score} "
               f"({result.overbuild_score.explanation})")
    click.echo(f"  LLM Cost: ${result.llm_cost_usd:.4f}")
    click.echo(f"  Search Time: {result.search_time_ms}ms")
    click.echo(f"  Results Found: {result.total_results_found}")
    click.echo()
    click.echo(f"  {result.summary}")

    if result.one_liner:
        click.echo()
        click.secho("  ONE-LINER:", fg="cyan", bold=True)
        click.echo(f"    {result.one_liner}")

    if result.existing_solutions:
        click.echo()
        click.secho("  EXISTING SOLUTIONS:", fg="green", bold=True)
        for i, sol in enumerate(result.existing_solutions[:3], 1):
            click.echo(f"    {i}. {sol.name}")
            click.echo(f"       {sol.description}")
            if sol.install_command:
                click.echo(f"       Install: {sol.install_command}")


if __name__ == "__main__":
    main()
```

---

## 10. Configuration

```python
# src/overbuild/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    # API Keys
    anthropic_api_key: str
    librariesio_api_key: str
    github_token: str = ""              # Optional but recommended (higher rate limits)
    stackoverflow_api_key: str = ""     # Optional (higher rate limits)

    # LLM Config
    llm_model: str = "claude-sonnet-4-20250514"

    # Server Config
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Cache Config
    cache_ttl_seconds: int = 3600       # 1 hour cache for API results
    cache_backend: str = "memory"       # "memory" for MVP; "redis" toggle preserved for production

    # Rate Limiting
    max_requests_per_minute: int = 20   # For the OverBuild API itself

    model_config = {"env_file": ".env", "env_prefix": "OVERBUILD_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

---

## 11. Docker & CI/CD

### Dockerfile (Multi-Stage)

```dockerfile
# Dockerfile
# Multi-stage build for minimal production image

# --- Build stage ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache .

# --- Production stage ---
FROM python:3.12-slim AS production

# Security: non-root user
RUN groupadd -r overbuild && useradd -r -g overbuild overbuild

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/

# Switch to non-root
USER overbuild

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "overbuild.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml (Local Dev)

```yaml
# docker-compose.yml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - OVERBUILD_CACHE_BACKEND=memory
      - OVERBUILD_DEBUG=true
    volumes:
      - ./src:/app/src  # Hot reload in dev
```

### GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install --system ".[dev]"

      - name: Lint
        run: ruff check src/ tests/

      - name: Format check
        run: ruff format --check src/ tests/

      - name: Type check
        run: mypy src/overbuild/

      - name: Unit tests
        run: pytest tests/ -v --tb=short
        env:
          OVERBUILD_ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OVERBUILD_LIBRARIESIO_API_KEY: ${{ secrets.LIBRARIESIO_API_KEY }}
          OVERBUILD_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitHub Actions Deploy (Railway — auto-deploys from GitHub)

```yaml
# .github/workflows/deploy.yml
# Railway auto-deploys from main branch when connected to GitHub.
# This workflow just ensures CI passes before deploy is triggered.
# For Render: same pattern — connect repo, auto-deploy on push to main.

name: Deploy Gate

on:
  push:
    branches: [main]

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install --system ".[dev]"

      - name: Full test suite must pass before deploy
        run: pytest tests/ -v --tb=short
        env:
          OVERBUILD_ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OVERBUILD_LIBRARIESIO_API_KEY: ${{ secrets.LIBRARIESIO_API_KEY }}

      - name: Build Docker image (verify it builds)
        run: docker build -t overbuild-detector:${{ github.sha }} .
```

> **Note:** Keep the `infra/terraform/` folder with AWS ECS Fargate configs in the repo.
> This shows IaC skills even though personal deployment uses Railway/Render.
> Add a note in README: *"Terraform configs target AWS ECS for production scale.
> Currently deployed on Railway for cost efficiency."*

---

## 12. Evaluation Harness

```python
# eval/run_eval.py

"""
Evaluation harness for OverBuild Detector.
Runs predefined scenarios and measures accuracy.

Usage:
    python eval/run_eval.py
    python eval/run_eval.py --output eval/results/run_$(date +%Y%m%d).json
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from overbuild.core.pipeline import analyze
from overbuild.api.models import AnalyzeRequest


def load_scenarios() -> list[dict]:
    scenarios_path = Path(__file__).parent / "scenarios.json"
    return json.loads(scenarios_path.read_text())


async def run_evaluation(output_path: str | None = None):
    scenarios = load_scenarios()
    results = []
    correct = 0
    total = len(scenarios)

    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{total}] {scenario['name']}...")

        request = AnalyzeRequest(
            problem=scenario["problem"],
            language=scenario.get("language"),
            context=scenario.get("context"),
        )

        try:
            result = await analyze(request)
            is_correct = result.verdict.value == scenario["expected_verdict"]
            if is_correct:
                correct += 1

            results.append({
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
            })

            status = "PASS" if is_correct else "MISS"
            print(f"  [{status}] Expected: {scenario['expected_verdict']}, "
                  f"Got: {result.verdict.value}, Score: {result.overbuild_score.score}")

        except Exception as e:
            results.append({
                "scenario": scenario["name"],
                "error": str(e),
                "correct": False,
            })
            print(f"  [ERROR] {e}")

    # Summary
    accuracy = correct / total * 100
    total_cost = sum(r.get("llm_cost_usd", 0) for r in results)
    avg_time = sum(r.get("search_time_ms", 0) for r in results) / total

    summary = {
        "run_date": datetime.now().isoformat(),
        "total_scenarios": total,
        "correct": correct,
        "accuracy_pct": round(accuracy, 1),
        "total_llm_cost_usd": round(total_cost, 4),
        "avg_search_time_ms": round(avg_time),
        "results": results,
    }

    print(f"\n{'='*40}")
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    print(f"Total LLM Cost: ${total_cost:.4f}")
    print(f"Avg Search Time: {avg_time:.0f}ms")

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(summary, indent=2))
        print(f"Results saved to {output_path}")

    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", help="Output JSON path")
    args = parser.parse_args()
    asyncio.run(run_evaluation(args.output))
```

### Evaluation Scenarios

```json
// eval/scenarios.json
[
    {
        "name": "The 82K-line cleanup daemon",
        "problem": "I need a tool that watches my Rust project directories and deletes build artifacts (target/ folders) older than 7 days to free disk space",
        "language": "rust",
        "expected_verdict": "JUST_USE_A_ONE_LINER",
        "notes": "cargo-sweep exists. find + cron solves it. ext4 reserves 5%."
    },
    {
        "name": "Python rate limiter",
        "problem": "I need to add rate limiting to my FastAPI endpoints, 100 requests per minute per IP address",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
        "notes": "slowapi, fastapi-limiter, etc. Well-solved problem."
    },
    {
        "name": "File watcher for tests",
        "problem": "Create a tool that watches a directory for file changes and automatically runs my test suite when Python files change",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
        "notes": "watchdog, pytest-watch, entr, inotifywait all solve this."
    },
    {
        "name": "Custom JSON logger",
        "problem": "Build a structured JSON logging library for Python with log levels, timestamps, and context fields",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
        "notes": "structlog, python-json-logger, loguru all exist."
    },
    {
        "name": "Git hooks manager",
        "problem": "Build a tool to manage and share git hooks across a team, with support for running linters and tests before commit",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
        "notes": "pre-commit is the dominant solution here."
    },
    {
        "name": "Environment variable loader",
        "problem": "I need a library that loads environment variables from .env files with type validation and default values",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
        "notes": "python-dotenv + pydantic-settings. Extremely well-solved."
    },
    {
        "name": "CSV to JSON converter",
        "problem": "Convert CSV files to JSON format with custom column mapping and data type inference",
        "language": "python",
        "expected_verdict": "JUST_USE_A_ONE_LINER",
        "notes": "pandas one-liner or jq/csvkit CLI tools."
    },
    {
        "name": "Retry with backoff",
        "problem": "Implement retry logic with exponential backoff for HTTP requests that fail with transient errors",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
        "notes": "tenacity, backoff, urllib3 Retry, httpx built-in."
    },
    {
        "name": "Healthcare rule engine (genuinely custom)",
        "problem": "Build a domain-specific rule engine that evaluates healthcare prior authorization requests against insurance policy criteria with full audit trails, explainability, and regulatory compliance logging",
        "language": "python",
        "expected_verdict": "BUILD_CUSTOM",
        "notes": "Genuinely domain-specific. No off-the-shelf solution."
    },
    {
        "name": "Custom ML training pipeline (genuinely custom)",
        "problem": "Build a training pipeline for a proprietary medical document classification model that handles PHI data with differential privacy, custom tokenization for medical terminology, and HIPAA-compliant logging",
        "language": "python",
        "expected_verdict": "BUILD_CUSTOM",
        "notes": "While frameworks exist (PyTorch, HF), the domain constraints make this custom."
    },
    {
        "name": "Markdown to HTML",
        "problem": "Convert markdown files to styled HTML with syntax highlighting, table of contents, and custom themes",
        "language": "python",
        "expected_verdict": "USE_EXISTING",
        "notes": "markdown, mistune, pandoc, mkdocs all solve this."
    },
    {
        "name": "Docker container cleanup",
        "problem": "Automatically remove stopped Docker containers and dangling images older than 48 hours",
        "language": "bash",
        "expected_verdict": "JUST_USE_A_ONE_LINER",
        "notes": "docker system prune --filter 'until=48h' is literally the answer."
    }
]
```

---

## 13. Observability

```python
# src/overbuild/observability/metrics.py

"""
Lightweight cost and performance tracking.
Logs structured metrics for every request.
In production, these feed into CloudWatch/Grafana.
"""

import structlog
from datetime import datetime

logger = structlog.get_logger()


async def track_request(
    request_id: str,
    elapsed_ms: int,
    llm_cost_usd: float,
    verdict: str,
):
    """Log structured metrics for every analysis request."""
    logger.info(
        "analysis_complete",
        request_id=request_id,
        elapsed_ms=elapsed_ms,
        llm_cost_usd=round(llm_cost_usd, 6),
        verdict=verdict,
        timestamp=datetime.utcnow().isoformat(),
    )


# Cumulative metrics (in-memory for MVP, Redis/Prometheus for production)
_metrics = {
    "total_requests": 0,
    "total_llm_cost_usd": 0.0,
    "verdicts": {"USE_EXISTING": 0, "ADAPT_EXISTING": 0, "BUILD_CUSTOM": 0, "JUST_USE_A_ONE_LINER": 0},
}


def record_metric(verdict: str, cost: float):
    _metrics["total_requests"] += 1
    _metrics["total_llm_cost_usd"] += cost
    _metrics["verdicts"][verdict] = _metrics["verdicts"].get(verdict, 0) + 1


def get_metrics() -> dict:
    return {**_metrics, "avg_cost_per_request": _metrics["total_llm_cost_usd"] / max(_metrics["total_requests"], 1)}
```

---

## 14. API Routes

```python
# src/overbuild/api/routes.py

from fastapi import APIRouter, HTTPException
from overbuild.api.models import AnalyzeRequest, AnalyzeResponse
from overbuild.core.pipeline import analyze
from overbuild.observability.metrics import get_metrics

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_problem(request: AnalyzeRequest):
    """Analyze a problem description and recommend build vs. reuse."""
    try:
        return await analyze(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "overbuild-detector"}


@router.get("/metrics")
async def metrics():
    """Basic usage metrics (cost tracking, verdict distribution)."""
    return get_metrics()
```

```python
# src/overbuild/main.py

from fastapi import FastAPI
from overbuild.api.routes import router
from overbuild.observability.middleware import add_observability


def create_app() -> FastAPI:
    app = FastAPI(
        title="OverBuild Detector",
        description="Before you build, check if it already exists.",
        version="0.1.0",
    )
    app.include_router(router)
    add_observability(app)
    return app

app = create_app()
```

---

## 15. Build Plan (3 Weeks)

### Week 1: Core Pipeline + CLI (The "It Works" Week)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Project scaffolding: pyproject.toml, folder structure, config, .env.example | Skeleton project that runs |
| 2 | LLM Call #1 (parser.py): prompt engineering, Pydantic structured output, unit tests with mock | `parse_intent()` works with 3 test inputs |
| 3 | Search providers: Libraries.io + GitHub (with fixtures for testing) | Two searches work, return normalized results |
| 4 | Search providers: StackOverflow + npm + Ecosyste.ms + aggregator with parallel execution | `search_all_sources()` fires all 5 in parallel |
| 5 | LLM Call #2 (synthesizer.py) + OverBuild Score calculator + full pipeline integration | End-to-end pipeline works for 1 scenario |
| 6-7 | CLI interface + run all 5 demo scenarios + fix prompt issues | `overbuild --demo` runs successfully |

**Milestone:** Terminal demo that takes a problem description and returns a recommendation.

### Week 2: API + MCP + Docker (The "It Ships" Week)

| Day | Task | Deliverable |
|-----|------|-------------|
| 8 | FastAPI routes + request/response models + health check + error handling | `POST /analyze` works via curl |
| 9 | MCP server implementation + test with Claude Desktop or Cursor | MCP tool callable by AI coding agents |
| 10 | Dockerfile (multi-stage) + docker-compose for local dev | `docker-compose up` runs the full app |
| 11 | Observability: structured logging, cost tracking middleware, /metrics endpoint | Every request logs cost + latency as JSON |
| 12 | TTL caching for search results (in-memory, respect API rate limits) | Repeated queries hit cache, not external APIs |
| 13-14 | Evaluation harness: all 12 scenarios + accuracy report | `python eval/run_eval.py` produces accuracy report |

**Milestone:** Dockerized API + MCP server + evaluation suite.

### Week 3: Polish + Deploy + Document (The "It Impresses" Week)

| Day | Task | Deliverable |
|-----|------|-------------|
| 15 | GitHub Actions CI: lint + test on every PR | Green CI badge on repo |
| 16 | Deploy to Railway (connect GitHub repo, auto-deploy) | Live URL serving the API |
| 17 | README: architecture diagram, demo GIF/video, setup instructions, evaluation results | Professional README |
| 18 | Write Terraform files for AWS ECS (in `infra/terraform/`) — demonstrates IaC skill | Terraform configs in repo |
| 19 | Edge cases, error handling, prompt refinement based on eval results | Accuracy improvements |
| 20-21 | Blog post draft: "I Built a Tool That Questions Whether You Should Build" | Shareable content for visibility |

**Milestone:** Live on Railway, documented, with CI and eval results in README. Terraform IaC for AWS ECS in repo.

---

## 16. Environment Setup

### Required API Keys

```bash
# .env.example

# Required
OVERBUILD_ANTHROPIC_API_KEY=sk-ant-...       # https://console.anthropic.com
OVERBUILD_LIBRARIESIO_API_KEY=...            # https://libraries.io/api (free)

# Recommended (higher rate limits)
OVERBUILD_GITHUB_TOKEN=ghp_...               # https://github.com/settings/tokens (public_repo scope)
OVERBUILD_STACKOVERFLOW_API_KEY=...           # https://stackapps.com/apps/oauth/register (free)

# Optional
OVERBUILD_LLM_MODEL=claude-sonnet-4-20250514
OVERBUILD_CACHE_BACKEND=memory               # "memory" for dev/personal, "redis" for production
OVERBUILD_DEBUG=true
```

### pyproject.toml

```toml
[project]
name = "overbuild-detector"
version = "0.1.0"
description = "Before you build, check if it already exists."
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "httpx>=0.27.0",
    "anthropic>=0.40.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "click>=8.1.0",
    "structlog>=24.4.0",
    "mcp>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
    "respx>=0.21.0",      # Mock httpx requests in tests
]
redis = [
    "redis>=5.2.0",
]

[project.scripts]
overbuild = "overbuild.cli:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.11"
strict = true
```

---

## 17. Key Design Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| No LangGraph | Lean pipeline | This is a 2-step pipeline, not a complex agent. Using LangGraph here would be ironic over-engineering for a tool that detects over-engineering. Save LangGraph for Failure Archaeology. |
| Claude Sonnet (not Opus) | Cost-efficiency | Two LLM calls per request. Sonnet is sufficient for parsing + synthesis. Keeps per-request cost under $0.01. |
| Pydantic structured output | Reliability | No regex parsing of LLM text. Both LLM calls return validated JSON via Pydantic. |
| Libraries.io as primary | Coverage | Single API searches 30+ package managers. More efficient than querying PyPI, npm, Cargo individually. |
| asyncio.gather not sequential | Speed | 5 API calls taking 500ms each = 500ms parallel vs 2500ms sequential. User-perceptible difference. |
| MCP server as Day 1 feature | Career signal | Not originally in MVP plan. Added because 5/10 target JDs mention MCP. Differentiating portfolio signal. |
| Multi-stage Docker | Best practice | Smaller image, non-root user, health check. Shows production Docker knowledge. |
| Eval harness from Week 2 | Quality culture | Not afterthought. Shows systematic approach to AI system quality that JDs emphasize. |
| Railway/Render not AWS ECS | Personal budget | AWS ECS costs $15-30/month for low-traffic. Railway free tier is $0. Terraform IaC files for AWS ECS kept in repo to demonstrate cloud skills. No interviewer faults cost-awareness. |
| In-memory cache not Redis | Simplicity | Redis adds infrastructure cost + complexity for a single-instance portfolio project. Config toggle preserved so switching to Redis is a one-line env var change. |

---

## 18. Realistic Cost Breakdown (Personal Account)

| Item | Cost | Notes |
|------|------|-------|
| **Anthropic API** | ~$3-5/month during dev | ~$0.005-0.01 per analysis (2 Sonnet calls). 10-20 analyses/day during dev. Near-zero once stable. |
| **Libraries.io API** | Free | 60 req/min. Free API key at libraries.io/api |
| **GitHub Search API** | Free | 30 req/min with free PAT (public_repo scope) |
| **StackOverflow API** | Free | 300 req/day unauth, 10K/day with free key |
| **npm Registry API** | Free | No auth needed, generous limits |
| **Ecosyste.ms API** | Free | Open API, no auth |
| **Railway deployment** | Free ($5 credit/month) | Enough for low-traffic portfolio project. Spins down on inactivity. |
| **GitHub Actions CI** | Free | Unlimited for public repos |
| **Domain (optional)** | ~$10/year | Optional. Railway gives you a `.up.railway.app` subdomain free. |
| **TOTAL** | **~$5-10/month during active dev, ~$0-5/month after** | |

### Free Tier Strategy

1. **Railway** (recommended): Connect GitHub repo → auto-deploy on push. Free tier = 500 hours/month + $5 credit. Perfect for portfolio projects. Supports Docker natively.
2. **Render** (alternative): Free web services with spin-down. Slightly slower cold starts but $0 cost.
3. **Cheapest cloud VM** (if you want always-on): Hetzner CX22 at €4.5/month or DigitalOcean $4/month. Run Docker directly.

### What to Tell Interviewers

*"I built and deployed the OverBuild Detector on Railway for cost efficiency. The repo includes Terraform configs targeting AWS ECS Fargate for production-scale deployment. In my current organization, I deploy similar containerized services to [your actual cloud platform]."*

This is honest, shows cost-awareness (a skill JDs mention!), and your professional cloud experience fills the gap.

---

## 19. Success Criteria

Before calling this project "done," verify:

- [ ] `overbuild --demo` runs 5 scenarios successfully
- [ ] `POST /analyze` returns structured JSON with verdict + score
- [ ] MCP server works in Claude Desktop or Cursor
- [ ] Docker build completes, container runs, health check passes
- [ ] `docker-compose up` starts app locally
- [ ] GitHub Actions CI runs lint + tests on PR (green badge)
- [ ] Deployed to Railway/Render with live URL
- [ ] Evaluation harness: >80% accuracy on 12 scenarios
- [ ] README has: architecture diagram, demo output, setup instructions, eval results
- [ ] Every request logs: cost, latency, verdict as structured JSON
- [ ] In-memory cache prevents repeated API calls for identical queries within TTL
- [ ] `infra/terraform/` contains AWS ECS Fargate IaC files (demonstrates cloud skill even if not actively deployed there)
