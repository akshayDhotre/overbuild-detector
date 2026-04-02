import json
import re
from collections import Counter

from overbuild.api.models import ParsedIntent
from overbuild.core.llm import call_llm_json, extract_json_payload, has_llm_config

PARSE_SYSTEM_PROMPT = """You are an expert software engineer analyzing a problem description.

First, assess whether the problem is too vague to analyze reliably. A problem is ambiguous when:
- It is a single generic word or phrase with no specific action (e.g. "authentication", "data management")
- It lacks any indication of what inputs, outputs, or behavior are expected
- It is impossible to determine what a solution would actually do

If ambiguous, set "is_ambiguous" to true and populate "clarifying_questions" with 2-4 specific questions
that would give you enough detail to proceed. Keep questions short and concrete.

If the problem is clear enough to analyze, set "is_ambiguous" to false and leave "clarifying_questions" empty.

Return ONLY valid JSON matching this schema:
{
  "problem_summary": "string",
  "target_language": "string",
  "domain": "string",
  "keywords": ["string"],
  "os_relevant": true,
  "expected_complexity": 1,
  "search_queries": ["string"],
  "potential_one_liner": "string or null",
  "is_ambiguous": false,
  "clarifying_questions": []
}
Be aggressive about low complexity for common utility tasks.
"""

_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "build",
    "create",
    "for",
    "i",
    "in",
    "is",
    "it",
    "my",
    "need",
    "of",
    "that",
    "the",
    "to",
    "tool",
    "with",
}


def _detect_language(problem: str, language: str | None) -> str:
    if language:
        return language.lower()
    text = problem.lower()
    mapping = {
        "python": ["python", "fastapi", "pytest"],
        "rust": ["rust", "cargo"],
        "javascript": ["javascript", "node", "npm", "react"],
        "typescript": ["typescript", "ts"],
        "go": ["golang", " go ", "go "],
        "bash": ["bash", "shell", "cron", "find "],
    }
    for candidate, hints in mapping.items():
        for hint in hints:
            if hint.strip() in text:
                return candidate
    return "python"


def _extract_keywords(problem: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9_+-]+", problem.lower())
    filtered = [token for token in tokens if token not in _STOPWORDS and len(token) > 2]
    most_common = [word for word, _ in Counter(filtered).most_common(6)]
    return most_common[:6] if most_common else ["automation", "tool", "library"]


def _heuristic_complexity(problem: str) -> int:
    text = problem.lower()
    if any(
        phrase in text
        for phrase in [
            "one-liner",
            "cleanup",
            "clean up",
            "remove stopped docker",
            "csv to json",
        ]
    ):
        return 1
    if any(
        phrase in text for phrase in ["rate limiting", "file watcher", "retry", "markdown to html"]
    ):
        return 3
    if any(
        phrase in text
        for phrase in [
            "healthcare",
            "hipaa",
            "proprietary",
            "domain-specific rule engine",
            "differential privacy",
            "regulatory compliance",
        ]
    ):
        return 8
    return 5


def _detect_domain(problem: str) -> str:
    text = problem.lower()
    if any(v in text for v in ["fastapi", "api", "endpoint"]):
        return "web-backend"
    if any(v in text for v in ["docker", "cron", "cleanup", "artifact"]):
        return "devops"
    if any(v in text for v in ["csv", "json", "markdown", "converter"]):
        return "data-processing"
    return "cli-tool"


def _one_liner(problem: str) -> str | None:
    text = problem.lower()
    if "rust" in text and "target" in text and "older than" in text:
        return "find . -type d -name target -mtime +7 -prune -exec rm -rf {} +"
    if "docker" in text and (
        "cleanup" in text
        or "remove stopped" in text
        or "dangling images" in text
        or "older than 48" in text
    ):
        return "docker system prune --filter 'until=48h' -f"
    if "csv" in text and "json" in text:
        return "python -c \"import pandas as pd; print(pd.read_csv('in.csv').to_json(orient='records'))\""
    return None


_AMBIGUOUS_SINGLE_TERMS = {
    "authentication",
    "authorization",
    "caching",
    "database",
    "deployment",
    "logging",
    "messaging",
    "monitoring",
    "networking",
    "security",
    "storage",
    "system",
    "testing",
    "validation",
}

_VAGUE_PHRASES = [
    "build something",
    "manage data",
    "managing data",
    "handle data",
    "some kind of",
    "a thing that",
    "a tool",
    "an app",
    "a system",
    "a service",
]


def _check_ambiguity(problem: str) -> tuple[bool, list[str]]:
    """Return (is_ambiguous, clarifying_questions) using heuristics."""
    text = problem.strip().lower()
    meaningful_tokens = [
        t for t in re.findall(r"[a-zA-Z0-9_+-]+", text) if t not in _STOPWORDS and len(t) > 2
    ]

    is_single_generic = text in _AMBIGUOUS_SINGLE_TERMS or (
        len(meaningful_tokens) == 1 and meaningful_tokens[0] in _AMBIGUOUS_SINGLE_TERMS
    )
    is_vague_phrase = any(phrase in text for phrase in _VAGUE_PHRASES)
    is_too_short = len(meaningful_tokens) < 2

    if not (is_single_generic or is_vague_phrase or is_too_short):
        return False, []

    questions = [
        "What specific behavior or outcome do you need? (e.g. what goes in, what comes out)",
        "What language or tech stack are you working in?",
        "What have you already tried or ruled out?",
        "Are there any constraints? (performance, licensing, no external dependencies, etc.)",
    ]
    return True, questions


def _build_queries(problem: str, keywords: list[str], language: str) -> list[str]:
    base = " ".join(keywords[:3])
    return [
        f"{base} {language} package",
        f"{problem[:120]} existing library",
        f"{base} github",
    ]


def _heuristic_parse(problem: str, language: str | None = None) -> ParsedIntent:
    resolved_language = _detect_language(problem, language)
    keywords = _extract_keywords(problem)
    is_ambiguous, clarifying_questions = _check_ambiguity(problem)
    return ParsedIntent(
        problem_summary=problem[:160],
        target_language=resolved_language,
        domain=_detect_domain(problem),
        keywords=keywords,
        os_relevant=any(
            key in problem.lower()
            for key in ["cleanup", "cron", "shell", "bash", "docker", "filesystem", "artifact"]
        ),
        expected_complexity=_heuristic_complexity(problem),
        search_queries=_build_queries(problem, keywords, resolved_language),
        potential_one_liner=_one_liner(problem),
        is_ambiguous=is_ambiguous,
        clarifying_questions=clarifying_questions,
    )


async def parse_intent(
    problem: str,
    language: str | None = None,
    context: str | None = None,
) -> tuple[ParsedIntent, float]:
    """Parse user intent into structured search directives."""
    if not has_llm_config():
        return _heuristic_parse(problem, language), 0.0

    user_message = f"Problem: {problem}"
    if language:
        user_message += f"\nLanguage: {language}"
    if context:
        user_message += f"\nContext: {context}"

    try:
        text_payload, cost = await call_llm_json(
            system_prompt=PARSE_SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=1000,
        )
        parsed = ParsedIntent.model_validate(json.loads(extract_json_payload(text_payload)))
        return parsed, cost
    except Exception:
        return _heuristic_parse(problem, language), 0.0
