from enum import StrEnum

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """User request payload."""

    problem: str = Field(
        ...,
        description="Natural language description of what you want to build",
        min_length=10,
        max_length=2000,
        examples=[
            "I need to clean up old Rust build artifacts older than 7 days",
            "Build a rate limiter for my FastAPI endpoints",
            "Create a tool that watches a directory for file changes and runs tests",
        ],
    )
    language: str | None = Field(
        None,
        description="Target programming language (auto-detected if not provided)",
        examples=["python", "rust", "javascript", "go"],
    )
    context: str | None = Field(
        None,
        description="Additional context: OS, constraints, existing stack",
        max_length=500,
    )


class ParsedIntent(BaseModel):
    """Structured output from LLM call #1."""

    problem_summary: str = Field(description="One-line summary of what the user wants")
    target_language: str = Field(description="Primary language/ecosystem")
    domain: str = Field(description="Problem domain")
    keywords: list[str] = Field(description="3-6 search keywords for package/tool discovery")
    os_relevant: bool = Field(description="Could OS-level tools solve this?")
    expected_complexity: int = Field(
        ge=1,
        le=10,
        description="How complex SHOULD the solution be? 1=one-liner, 10=complex system",
    )
    search_queries: list[str] = Field(
        description="3-5 source-specific search queries",
        min_length=2,
        max_length=6,
    )
    potential_one_liner: str | None = Field(
        None,
        description="Possible one-liner solution if applicable",
    )
    is_ambiguous: bool = Field(
        default=False,
        description="True if the problem is too vague to analyze reliably",
    )
    clarifying_questions: list[str] = Field(
        default_factory=list,
        description="Questions to ask the user when is_ambiguous is True",
    )


class SearchSource(StrEnum):
    LIBRARIES_IO = "libraries_io"
    GITHUB = "github"
    NPM = "npm"
    STACKOVERFLOW = "stackoverflow"
    ECOSYSTEMS = "ecosystems"


class SearchResult(BaseModel):
    """Normalized search result across providers."""

    source: SearchSource
    name: str
    description: str
    url: str
    relevance_score: float = Field(ge=0.0, le=1.0, description="Computed relevance score")

    stars: int | None = None
    downloads_monthly: int | None = None
    dependents_count: int | None = None

    last_updated: str | None = None
    is_maintained: bool | None = None
    license: str | None = None

    language: str | None = None
    package_manager: str | None = None
    stackoverflow_score: int | None = None
    answer_count: int | None = None


class OverBuildScore(BaseModel):
    """Quantified comparison: problem complexity vs minimum viable complexity."""

    problem_complexity: int = Field(ge=1, le=10)
    best_existing_complexity: int = Field(ge=0, le=10)
    custom_build_complexity: int = Field(ge=1, le=10)
    score: float = Field(
        description="OverBuild Score = custom_build_complexity / max(problem_complexity, 1)"
    )
    explanation: str = Field(description="One-line explanation of score meaning")


class Verdict(StrEnum):
    USE_EXISTING = "USE_EXISTING"
    ADAPT_EXISTING = "ADAPT_EXISTING"
    BUILD_CUSTOM = "BUILD_CUSTOM"
    JUST_USE_A_ONE_LINER = "JUST_USE_A_ONE_LINER"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class ExistingSolution(BaseModel):
    """Top candidate solution in final response."""

    name: str
    description: str
    url: str
    install_command: str | None = None
    usage_example: str | None = None
    pros: list[str]
    cons: list[str]
    source: SearchSource
    stars: int | None = None
    last_updated: str | None = None


class SynthesisResult(BaseModel):
    """Structured output from LLM call #2."""

    verdict: Verdict
    summary: str
    existing_solutions: list[ExistingSolution] = Field(default_factory=list)
    one_liner: str | None = None
    if_you_must_build: str | None = None


class AnalyzeResponse(BaseModel):
    """Full response payload for API/CLI/MCP."""

    verdict: Verdict
    overbuild_score: OverBuildScore | None = None
    summary: str
    existing_solutions: list[ExistingSolution] = Field(default_factory=list)
    one_liner: str | None = None
    if_you_must_build: str | None = None
    clarifying_questions: list[str] = Field(
        default_factory=list,
        description="Returned when verdict is NEEDS_CLARIFICATION",
    )

    sources_searched: list[SearchSource] = Field(default_factory=list)
    total_results_found: int = 0
    search_time_ms: int
    llm_cost_usd: float
    request_id: str
