# OverBuild Detector — Enterprise Enhancements

> This document outlines possibilities for evolving OverBuild Detector into an enterprise-grade tool.
> The current open-source version searches public registries (Libraries.io, GitHub, npm, StackOverflow, Ecosyste.ms).
> Enterprise deployments can go significantly further by connecting to internal systems and organizational data.
>
> Original concept and architecture by **Akshay Dhotre** ([@akshayDhotre](https://github.com/akshayDhotre)).
> If you build on this idea, please credit the original work per the [LICENSE](../LICENSE).

---

## Why Enterprise?

AI coding agents systematically over-engineer because they respond to prompt complexity, not problem complexity.
At enterprise scale, the problem compounds — developers don't just duplicate open-source solutions, they duplicate
each other's internal work. A shared utility written by Team A gets independently rebuilt by Teams B and C because
there's no discovery mechanism at the moment a developer starts building.

OverBuild Detector is designed to intervene at that critical moment. An enterprise deployment extends that
intervention to the full internal codebase.

---

## Enhancement 1 — Internal Codebase Search (Core Enterprise Capability)

**What the DevOps suggestion unlocks:** The current pipeline's search providers are pluggable (see [search/](../src/overbuild/search/)). An `internal_codebase.py` provider would fit naturally alongside existing providers.

### 1a. Private Repository Indexing
- Connect to internal GitHub Enterprise, GitLab Self-Managed, or Bitbucket Data Center.
- Crawl repos and extract module names, function signatures, READMEs, and package manifests.
- Build a searchable index (Elasticsearch or PostgreSQL full-text) of what exists internally.
- Surface results in the same ranked format as public search providers.

### 1b. Semantic / Embedding-Based Code Search
- Use vector embeddings (e.g. `text-embedding-3-small`) to find *functionally similar* code, not just keyword matches.
- "Send email with retry" surfaces `notification_relay.py` even without keyword overlap.
- Internal code that solves the problem but is named differently gets discovered.
- Embedding index can be pre-built nightly and served from a vector store (pgvector, Qdrant, Weaviate).

### 1c. Internal Package Registry Search
- Pull from JFrog Artifactory, Sonatype Nexus, AWS CodeArtifact, or Azure Artifacts.
- The private equivalents of npm/PyPI that the current public providers miss entirely.
- Treat internal packages as first-class candidates, ranked above public alternatives when available.

**Architecture note:** Each of these maps to a new provider class in `src/overbuild/search/`. The aggregator and pipeline require no changes — just register the new providers.

---

## Enhancement 2 — CI/CD Pipeline Gate

Shift left from *before building* to *before merging*.

- **PR analysis**: A GitHub Actions / GitLab CI job scans new files added in a PR, detects potentially over-built components, and comments on the PR with alternatives.
- **Pre-commit hook**: Run heuristic-only analysis locally (no LLM call, hence fast) before code is committed.
- **Pass/fail gate**: Configurable to block PRs with overbuild scores above a threshold (e.g. `> 2.60`) unless the author adds an explicit justification comment.
- **Low cost**: CI integration can use heuristic fallback mode — no LLM call needed for a fast gate check.

---

## Enhancement 3 — IDE Plugin / Real-Time Suggestions

Detect over-engineering *as developers code*, not after.

- **VS Code / JetBrains extension**: Detect when a developer writes a new class or function matching known overbuild patterns (rate limiter, retry decorator, file watcher, distributed lock) and surface a pre-emptive suggestion.
- **Context-aware intent**: The plugin knows the current file's language and imports — higher accuracy than plain-text input.
- **Inline verdict**: Lightbulb action or inline hint, no context switch required.
- **MCP surface**: The existing MCP server (`src/overbuild/mcp/`) already exposes the core as an AI tool — IDE AI assistants can call it natively.

---

## Enhancement 4 — Policy & Compliance Layer

Enterprise procurement and legal constraints often override pure technical recommendations.

- **License policy enforcement**: If the best existing solution is GPL-licensed, flag it as incompatible for a commercial product. Recommendation shifts to a permissively-licensed alternative or `BUILD_CUSTOM`.
- **Approved package allowlist**: Cross-reference recommendations against the org's approved package list (maintained via FOSSA, Snyk, or Mend). Never recommend a package the org hasn't vetted.
- **CVE / Security check**: Before returning `USE_EXISTING`, run the candidate package against OSV or NVD. Do not recommend packages with unpatched critical CVEs.
- **Industry compliance**: HIPAA-aware mode for healthcare (flag packages that process data without audit trails), PCI-DSS mode for fintech.

**Integration point:** Plugs into the synthesizer (`src/overbuild/core/synthesizer.py`) as a post-processing filter that can downgrade or veto candidates before the final verdict is assembled.

---

## Enhancement 5 — Organizational Knowledge Graph

Map what exists *within* the org, not just in the open-source world.

- **Service catalog integration**: Connect to Backstage or an internal service registry. "Team Platform already built a distributed lock service — contact @platform-team."
- **ADR (Architecture Decision Records) search**: Before recommending `BUILD_CUSTOM`, check if the org already made a decision about this pattern. Surface the ADR link directly in the response.
- **"Who built what" routing**: Identify the owning team of an internal solution and suggest direct contact, not just a repo link.
- **Duplicate detection across teams**: Track when the same problem has been independently solved multiple times and surface it as a candidate for a shared internal library.

---

## Enhancement 6 — Multi-Tenant SaaS Architecture

To go from a personal/team tool to an org-wide product:

- **Org-level configuration**: Each org gets its own strictness profile, domain packs, internal registry connections, and approved package lists.
- **SSO / OIDC**: Enterprise auth via Okta, Azure AD, Google Workspace.
- **RBAC**: Admins configure policy; developers just query. Separate roles for policy management vs. analysis consumption.
- **Audit log**: Every analysis recorded — who ran it, verdict, whether accepted — for compliance and retrospectives.
- **Tenant isolation**: Internal codebase indexes are per-tenant; no cross-org data leakage.

---

## Enhancement 7 — Team Analytics Dashboard

Turn individual verdicts into organizational intelligence.

- **Overbuild trend per team**: Which teams over-engineer most? Which domains (DevOps, Data, Frontend) have the highest reuse rates?
- **ROI metrics**: "This week, 12 developers accepted `USE_EXISTING` verdicts. Estimated dev-hours saved: ~47."
- **Repeat pattern detection**: "Rate limiting has been independently built 6 times across 4 teams in the last year." → Candidate for a shared internal library.
- **Verdict acceptance rate**: How often are `BUILD_CUSTOM` verdicts overridden? Signals either over-strictness in policy or cultural resistance to reuse.

---

## Enhancement 8 — Chat & Collaboration Tool Integration

Bring the tool to where developers already communicate.

- **Slack / Microsoft Teams bot**: `@overbuild I need a distributed cache warming service` — returns verdict inline in the channel.
- **GitHub Discussions / Issue comments**: Mention the bot in an issue describing a planned feature; it analyzes and responds with alternatives.
- **Weekly digest**: Automated team report showing overbuild patterns from the past week, surfaced in an engineering channel.
- **Integration surface**: The existing REST API (`POST /analyze`) is the only dependency. Slack/Teams bots are thin wrappers.

---

## Enhancement 9 — Batch Analysis for Planning Sessions

Sprint planning and architecture reviews benefit from bulk analysis.

- **Batch endpoint** (`POST /analyze/batch`): Submit an array of planned work items (from Jira or Linear tickets) and get verdicts on all before the sprint starts.
- **Planning session input**: "Of these 20 planned tasks, 8 have high overbuild risk. Reclaim ~3 sprint points by reusing existing solutions."
- **Confluence / Notion integration**: Analyze a technical design doc, flag sections that propose rebuilding something that already exists internally or publicly.

---

## Enhancement 10 — Confidence Scoring & Abstain Mode

The current synthesizer always forces a verdict. At enterprise scale, uncertain verdicts carry real cost.

- **Confidence score**: Return a confidence value alongside the verdict (e.g. `0.87`). Low-confidence analyses prompt for more context rather than forcing a potentially wrong decision.
- **Abstain mode**: When evidence is thin or contradictory, return `NEEDS_MORE_CONTEXT` with specific clarifying questions.
- **Evidence breakdown**: Show *why* each candidate ranked high — keyword match percentage, stars, language alignment, recency. Critical for enterprise trust and auditability.
- **Integration point:** Changes are scoped to `src/overbuild/core/synthesizer.py` and `src/overbuild/api/models.py`.

---

## Prioritization Guide

| Enhancement | Enterprise Value | Implementation Effort | Natural Starting Point |
|---|---|---|---|
| Internal codebase search | Very High | High | New search provider + embedding index |
| Policy / compliance layer | Very High | Medium | Synthesizer post-filter |
| CI/CD gate | High | Low | GitHub Action wrapping existing API |
| IDE plugin | High | Medium | Thin client over existing MCP server |
| Multi-tenant SaaS | High | High | Auth + config infra |
| Org knowledge graph | High | High | Service catalog API integration |
| Analytics dashboard | Medium | Medium | Persistent storage + metrics endpoint |
| Slack / Teams bot | Medium | Low | Thin wrapper over existing REST API |
| Batch analysis | Medium | Low | Extend existing pipeline |
| Confidence / abstain | Medium | Medium | Synthesizer + model changes |

**Recommended enterprise entry path:**
1. **CI/CD gate** — lowest effort, immediate value, no new infrastructure.
2. **Policy / compliance layer** — high value for regulated industries, scoped to synthesizer.
3. **Internal codebase search** — the core differentiator; plan embedding infrastructure early.

---

## Attribution

OverBuild Detector was conceived and built by **Akshay Dhotre**.
If you adapt, extend, or deploy this system, please include attribution per the project [LICENSE](../LICENSE).

- GitHub: [@akshayDhotre](https://github.com/akshayDhotre)
- Contact: akshaydhotre.work@gmail.com
