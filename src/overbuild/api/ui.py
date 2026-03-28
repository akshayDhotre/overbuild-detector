"""HTML UI for interactive OverBuild analysis demos."""

HOME_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OverBuild Detector</title>
  <style>
    :root {
      --bg: #f5f4ef;
      --panel: #fffef9;
      --ink: #1f2a24;
      --muted: #5d6a62;
      --line: #d7ddd8;
      --brand: #0f766e;
      --brand-2: #f59e0b;
      --danger: #b91c1c;
      --shadow: 0 10px 30px rgba(16, 24, 40, 0.08);
      --radius: 18px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Satoshi", "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 8%, rgba(15, 118, 110, 0.15), transparent 38%),
        radial-gradient(circle at 84% 20%, rgba(245, 158, 11, 0.18), transparent 34%),
        var(--bg);
      min-height: 100vh;
    }

    .shell {
      max-width: 1120px;
      margin: 0 auto;
      padding: 2.5rem 1rem 3.25rem;
    }

    .hero {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 1.4rem 1.4rem 1.1rem;
      margin-bottom: 1rem;
      animation: rise 400ms ease-out both;
    }

    .eyebrow {
      margin: 0 0 0.35rem;
      color: var(--brand);
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      font-size: 0.75rem;
    }

    h1 {
      margin: 0;
      font-size: clamp(1.55rem, 2.6vw, 2.35rem);
      line-height: 1.12;
      letter-spacing: -0.02em;
    }

    .sub {
      margin: 0.55rem 0 0;
      color: var(--muted);
      max-width: 72ch;
    }

    .grid {
      display: grid;
      grid-template-columns: minmax(320px, 360px) minmax(0, 1fr);
      gap: 1rem;
      align-items: start;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 1rem;
      animation: rise 500ms ease-out both;
    }

    .card-form {
      position: sticky;
      top: 1rem;
      max-height: calc(100vh - 2rem);
      overflow-y: auto;
      scrollbar-gutter: stable;
    }

    .card-results {
      min-width: 0;
    }

    .label {
      display: block;
      margin-bottom: 0.34rem;
      font-size: 0.82rem;
      font-weight: 700;
      color: #44524b;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    textarea,
    input,
    select {
      width: 100%;
      border: 1px solid #bcc7bf;
      background: #ffffff;
      color: var(--ink);
      border-radius: 12px;
      padding: 0.72rem 0.78rem;
      font: inherit;
      line-height: 1.35;
    }

    textarea { min-height: 120px; resize: vertical; }

    #problem { min-height: 170px; }
    #context { min-height: 110px; }

    .row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 0.7rem;
      margin-top: 0.75rem;
    }

    .presets {
      display: flex;
      gap: 0.45rem;
      flex-wrap: wrap;
      margin-bottom: 0.8rem;
    }

    .chip {
      border: 1px solid #bfd4d0;
      background: #ecf8f6;
      color: #0f5550;
      border-radius: 999px;
      padding: 0.34rem 0.7rem;
      font-size: 0.82rem;
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease;
    }

    .chip:hover {
      transform: translateY(-1px);
      background: #dff3f0;
    }

    .actions {
      margin-top: 0.9rem;
      display: flex;
      align-items: center;
      gap: 0.7rem;
      flex-wrap: wrap;
    }

    .btn {
      border: 0;
      border-radius: 12px;
      padding: 0.7rem 0.95rem;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease;
    }

    .btn:disabled { opacity: 0.7; cursor: wait; }
    .btn:hover:not(:disabled) { transform: translateY(-1px); }
    .btn-primary { background: var(--brand); color: white; }
    .btn-secondary { background: #e8ece9; color: #263630; }
    .btn-secondary:disabled { opacity: 0.55; }

    .hint { margin: 0; color: var(--muted); font-size: 0.86rem; }

    .status {
      margin: 0 0 0.7rem;
      font-size: 0.92rem;
      color: #355046;
    }

    .error {
      color: var(--danger);
      margin: 0.35rem 0 0;
      font-size: 0.9rem;
      white-space: pre-wrap;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      border-radius: 999px;
      padding: 0.3rem 0.65rem;
      border: 1px solid transparent;
      margin-bottom: 0.55rem;
    }

    .badge-one-liner { background: #e8f8f3; color: #065f46; border-color: #8bd8bf; }
    .badge-existing { background: #edf7ff; color: #075985; border-color: #9bd0f5; }
    .badge-adapt { background: #fff7e8; color: #9a5f00; border-color: #f6cd80; }
    .badge-custom { background: #fff0f0; color: #991b1b; border-color: #f1b0b0; }
    .badge-default { background: #edf2f7; color: #334155; border-color: #c6d3e0; }

    .kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 0.6rem;
      margin: 0.7rem 0;
    }

    .kpi {
      border: 1px solid #dbe4dd;
      border-radius: 12px;
      padding: 0.62rem 0.68rem;
      background: #fcfefc;
    }

    .kpi small { color: var(--muted); display: block; font-size: 0.77rem; }
    .kpi strong { display: block; margin-top: 0.2rem; font-size: 0.97rem; }

    .score-guide {
      margin-top: 0.35rem;
      padding: 0.75rem;
      border: 1px solid #dbe4dd;
      border-radius: 12px;
      background: #fbfdfb;
    }

    .score-guide p {
      margin: 0 0 0.35rem;
      color: #37463f;
      font-size: 0.86rem;
    }

    .score-guide ul {
      margin: 0;
      padding-left: 1rem;
      color: #4a5a52;
      font-size: 0.82rem;
      line-height: 1.35;
    }

    .export-actions {
      display: flex;
      gap: 0.55rem;
      flex-wrap: wrap;
      margin: 0.25rem 0 0.35rem;
    }

    .section-title {
      margin: 1rem 0 0.35rem;
      font-size: 0.84rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #45544d;
    }

    .summary {
      margin: 0.4rem 0 0;
      line-height: 1.45;
      color: #283730;
    }

    .mono {
      margin: 0.25rem 0 0;
      border: 1px solid #d5e0d8;
      background: #f7fbf8;
      border-radius: 12px;
      padding: 0.75rem;
      font-family: "SF Mono", "Consolas", monospace;
      overflow-x: auto;
      font-size: 0.86rem;
    }

    .solutions {
      width: 100%;
      border-collapse: collapse;
      margin-top: 0.45rem;
      font-size: 0.9rem;
    }

    .table-wrap {
      width: 100%;
      overflow-x: auto;
    }

    .solutions th,
    .solutions td {
      border-bottom: 1px solid #dee6e0;
      text-align: left;
      padding: 0.55rem 0.3rem;
      vertical-align: top;
    }

    .solutions th {
      color: #4a5b53;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .solutions a { color: #0f5f92; text-decoration: none; }
    .solutions a:hover { text-decoration: underline; }
    .muted { color: var(--muted); font-size: 0.86rem; margin: 0.3rem 0 0; }

    @keyframes rise {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 920px) {
      .grid { grid-template-columns: 1fr; }
      .row { grid-template-columns: 1fr; }
      .shell { padding-top: 1.1rem; }
      .card-form {
        position: static;
        max-height: none;
        overflow: visible;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Build Less, Ship More</p>
      <h1>OverBuild Detector</h1>
      <p class="sub">Describe what you want to build. This tool checks for existing solutions and helps you avoid over-engineering before implementation starts.</p>
    </section>

    <section class="grid">
      <article class="card card-form">
        <div class="presets">
          <button class="chip" data-problem="I need to add rate limiting to my FastAPI endpoints, 100 requests per minute per IP" data-language="python">Rate Limiter</button>
          <button class="chip" data-problem="Build a script to clean up dangling Docker images older than 48h" data-language="bash">Docker Cleanup</button>
          <button class="chip" data-problem="Create a tool that watches a directory for file changes and reruns tests" data-language="python">File Watcher</button>
          <button class="chip" data-problem="Build a domain-specific healthcare prior authorization rule engine with audit trails" data-language="python">Domain Engine</button>
        </div>

        <label class="label" for="problem">Problem statement</label>
        <textarea id="problem" placeholder="Describe what you are about to build..."></textarea>

        <div class="row">
          <div>
            <label class="label" for="language">Language</label>
            <select id="language">
              <option value="">Auto-detect</option>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="rust">Rust</option>
              <option value="go">Go</option>
              <option value="bash">Bash</option>
            </select>
          </div>
        </div>

        <label class="label" for="context">Context</label>
        <textarea id="context" placeholder="Environment, constraints, team preferences, compliance needs, scale expectations..."></textarea>

        <div class="actions">
          <button id="analyze" class="btn btn-primary">Analyze</button>
          <button id="reset" class="btn btn-secondary">Reset</button>
          <p class="hint">Tip: Start with a concrete problem statement for better recommendations.</p>
        </div>
      </article>

      <article class="card card-results">
        <p id="status" class="status">Ready. Run an analysis to see verdict, score, and alternatives.</p>
        <div id="results" hidden style="max-height:72vh;overflow-y:auto;scrollbar-gutter:stable;padding-right:0.2rem;">
          <span id="badge" class="badge badge-default">Verdict</span>
          <p id="summary" class="summary"></p>

          <div class="kpis">
            <div class="kpi">
              <small>OverBuild Score</small>
              <strong id="score">-</strong>
            </div>
            <div class="kpi">
              <small>Score Meaning</small>
              <strong id="scoreNote">-</strong>
            </div>
            <div class="kpi">
              <small>Search Time</small>
              <strong id="searchTime">-</strong>
            </div>
            <div class="kpi">
              <small>Sources / Results</small>
              <strong id="sources">-</strong>
            </div>
          </div>

          <div class="score-guide">
            <p><strong>How to read OverBuild Score (ratio, not /10)</strong></p>
            <ul>
              <li>1.30 to 1.45: low overbuild risk</li>
              <li>1.46 to 1.90: moderate risk, adapt existing tools first</li>
              <li>1.91 to 2.60: high risk, prefer existing solutions</li>
              <li>>2.60: very high risk, package or one-liner is usually enough</li>
            </ul>
          </div>

          <h3 class="section-title">Export</h3>
          <div class="export-actions">
            <button id="exportJson" class="btn btn-secondary" disabled>Export JSON</button>
            <button id="exportMd" class="btn btn-secondary" disabled>Export Markdown</button>
          </div>
          <p class="hint">Downloads include your input and the latest completed analysis.</p>

          <h3 class="section-title">One-liner</h3>
          <pre id="oneLiner" class="mono">No one-liner recommendation</pre>

          <h3 class="section-title">Top Existing Solutions</h3>
          <div class="table-wrap">
            <table class="solutions">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Source</th>
                  <th>Install</th>
                </tr>
              </thead>
              <tbody id="solutionRows"></tbody>
            </table>
          </div>
          <p id="mustBuild" class="muted"></p>
        </div>
        <p id="error" class="error"></p>
      </article>
    </section>
  </main>

  <script>
    const verdictClassMap = {
      JUST_USE_A_ONE_LINER: "badge-one-liner",
      USE_EXISTING: "badge-existing",
      ADAPT_EXISTING: "badge-adapt",
      BUILD_CUSTOM: "badge-custom"
    };

    const problemEl = document.getElementById("problem");
    const languageEl = document.getElementById("language");
    const contextEl = document.getElementById("context");
    const analyzeBtn = document.getElementById("analyze");
    const resetBtn = document.getElementById("reset");
    const statusEl = document.getElementById("status");
    const resultsEl = document.getElementById("results");
    const errorEl = document.getElementById("error");
    const badgeEl = document.getElementById("badge");
    const summaryEl = document.getElementById("summary");
    const scoreEl = document.getElementById("score");
    const scoreNoteEl = document.getElementById("scoreNote");
    const searchTimeEl = document.getElementById("searchTime");
    const sourcesEl = document.getElementById("sources");
    const oneLinerEl = document.getElementById("oneLiner");
    const solutionRowsEl = document.getElementById("solutionRows");
    const mustBuildEl = document.getElementById("mustBuild");
    const exportJsonBtn = document.getElementById("exportJson");
    const exportMdBtn = document.getElementById("exportMd");

    let latestPayload = null;
    let latestAnalysis = null;

    document.querySelectorAll(".chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        problemEl.value = chip.dataset.problem || "";
        languageEl.value = chip.dataset.language || "";
        contextEl.value = "";
        errorEl.textContent = "";
      });
    });

    resetBtn.addEventListener("click", () => {
      problemEl.value = "";
      languageEl.value = "";
      contextEl.value = "";
      errorEl.textContent = "";
      statusEl.textContent = "Ready. Run an analysis to see verdict, score, and alternatives.";
      resultsEl.hidden = true;
      latestPayload = null;
      latestAnalysis = null;
      exportJsonBtn.disabled = true;
      exportMdBtn.disabled = true;
    });

    function renderSolutions(solutions) {
      solutionRowsEl.innerHTML = "";
      if (!solutions || solutions.length === 0) {
        solutionRowsEl.innerHTML = "<tr><td colspan='3' class='muted'>No existing solutions were ranked for this input.</td></tr>";
        return;
      }
      solutions.slice(0, 5).forEach((solution) => {
        const row = document.createElement("tr");
        const link = solution.url ? `<a href="${solution.url}" target="_blank" rel="noreferrer">${solution.name || "Unnamed"}</a>` : (solution.name || "Unnamed");
        const install = solution.install_command ? `<code>${solution.install_command}</code>` : "-";
        row.innerHTML = `<td>${link}</td><td>${solution.source || "-"}</td><td>${install}</td>`;
        solutionRowsEl.appendChild(row);
      });
    }

    function setVerdict(verdict) {
      badgeEl.className = "badge";
      badgeEl.classList.add(verdictClassMap[verdict] || "badge-default");
      badgeEl.textContent = verdict || "UNKNOWN";
    }

    function scoreInterpretation(score) {
      if (score <= 1.45) return "Low overbuild risk";
      if (score <= 1.9) return "Moderate overbuild risk";
      if (score <= 2.6) return "High overbuild risk";
      return "Very high overbuild risk";
    }

    function slugify(value) {
      const fallback = "analysis";
      if (!value || typeof value !== "string") return fallback;
      const cleaned = value.toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
      return cleaned || fallback;
    }

    function downloadText(filename, content, contentType) {
      const blob = new Blob([content], { type: contentType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }

    function analysisToMarkdown(payload, analysis) {
      const sourceList = Array.isArray(analysis.sources_searched) ? analysis.sources_searched : [];
      const score = Number(analysis.overbuild_score?.score);
      const lines = [];
      lines.push("# OverBuild Detector Analysis");
      lines.push("");
      lines.push(`- Generated: ${new Date().toISOString()}`);
      lines.push(`- Request ID: ${analysis.request_id || "n/a"}`);
      lines.push(`- Problem: ${payload.problem}`);
      if (payload.language) lines.push(`- Language: ${payload.language}`);
      if (payload.context) lines.push(`- Context: ${payload.context}`);
      lines.push("");
      lines.push("## Verdict");
      lines.push("");
      lines.push(`**${analysis.verdict || "UNKNOWN"}**`);
      lines.push("");
      lines.push("## OverBuild Score");
      lines.push("");
      lines.push(`- Score: ${analysis.overbuild_score?.score ?? "-"}`);
      lines.push(`- Meaning: ${analysis.overbuild_score?.explanation || "-"}`);
      if (!Number.isNaN(score)) {
        lines.push(`- Interpretation: ${scoreInterpretation(score)}`);
      }
      lines.push("");
      lines.push("## Summary");
      lines.push("");
      lines.push(analysis.summary || "No summary available.");
      lines.push("");

      if (analysis.one_liner) {
        lines.push("## One-Liner");
        lines.push("");
        lines.push("```");
        lines.push(analysis.one_liner);
        lines.push("```");
        lines.push("");
      }

      lines.push("## Existing Solutions");
      lines.push("");
      const solutions = Array.isArray(analysis.existing_solutions) ? analysis.existing_solutions : [];
      if (solutions.length === 0) {
        lines.push("No ranked solutions returned.");
      } else {
        solutions.slice(0, 5).forEach((solution, index) => {
          lines.push(`${index + 1}. **${solution.name || "Unnamed"}** (${solution.source || "-"})`);
          if (solution.description) lines.push(`   - ${solution.description}`);
          if (solution.url) lines.push(`   - URL: ${solution.url}`);
          if (solution.install_command) lines.push(`   - Install: \\`${solution.install_command}\\``);
        });
      }
      lines.push("");

      if (analysis.if_you_must_build) {
        lines.push("## If You Must Build");
        lines.push("");
        lines.push(analysis.if_you_must_build);
        lines.push("");
      }

      lines.push("## Runtime Stats");
      lines.push("");
      lines.push(`- Search time (ms): ${analysis.search_time_ms ?? "-"}`);
      lines.push(`- Sources searched: ${sourceList.join(", ") || "-"}`);
      lines.push(`- Results found: ${analysis.total_results_found ?? "-"}`);
      lines.push(`- LLM cost (USD): ${analysis.llm_cost_usd ?? "-"}`);
      return lines.join("\\n");
    }

    exportJsonBtn.addEventListener("click", () => {
      if (!latestAnalysis || !latestPayload) return;
      const requestId = slugify(latestAnalysis.request_id || String(Date.now()));
      const exportPayload = {
        exported_at: new Date().toISOString(),
        input: latestPayload,
        analysis: latestAnalysis
      };
      downloadText(
        `overbuild-analysis-${requestId}.json`,
        JSON.stringify(exportPayload, null, 2),
        "application/json"
      );
    });

    exportMdBtn.addEventListener("click", () => {
      if (!latestAnalysis || !latestPayload) return;
      const requestId = slugify(latestAnalysis.request_id || String(Date.now()));
      const markdown = analysisToMarkdown(latestPayload, latestAnalysis);
      downloadText(`overbuild-analysis-${requestId}.md`, markdown, "text/markdown");
    });

    async function runAnalysis() {
      const problem = problemEl.value.trim();
      if (problem.length < 10) {
        errorEl.textContent = "Please enter at least 10 characters in the problem statement.";
        return;
      }

      const payload = { problem };
      if (languageEl.value) payload.language = languageEl.value;
      if (contextEl.value.trim()) payload.context = contextEl.value.trim();

      analyzeBtn.disabled = true;
      errorEl.textContent = "";
      statusEl.textContent = "Analyzing... searching ecosystems and scoring alternatives.";

      try {
        const response = await fetch("/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!response.ok) {
          const details = await response.text();
          throw new Error(`Request failed (${response.status}): ${details}`);
        }
        const data = await response.json();
        const scoreValue = Number(data.overbuild_score?.score);
        setVerdict(data.verdict);
        summaryEl.textContent = data.summary || "No summary available.";
        scoreEl.textContent = Number.isNaN(scoreValue) ? "-" : scoreValue.toFixed(2);
        const interpretation = Number.isNaN(scoreValue) ? "" : ` (${scoreInterpretation(scoreValue)})`;
        scoreNoteEl.textContent = `${data.overbuild_score?.explanation || "-"}${interpretation}`;
        searchTimeEl.textContent = `${data.search_time_ms ?? "-"} ms`;
        const sourceCount = Array.isArray(data.sources_searched) ? data.sources_searched.length : 0;
        const resultCount = data.total_results_found ?? "-";
        sourcesEl.textContent = `${sourceCount} / ${resultCount}`;
        oneLinerEl.textContent = data.one_liner || "No one-liner recommendation";
        renderSolutions(data.existing_solutions || []);
        mustBuildEl.textContent = data.if_you_must_build ? `If you must build: ${data.if_you_must_build}` : "";
        resultsEl.hidden = false;
        statusEl.textContent = `Analysis complete. Request ID: ${data.request_id || "n/a"}.`;
        latestPayload = payload;
        latestAnalysis = data;
        exportJsonBtn.disabled = false;
        exportMdBtn.disabled = false;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unexpected error";
        errorEl.textContent = message;
        statusEl.textContent = "Analysis failed. Check your config/API keys and try again.";
      } finally {
        analyzeBtn.disabled = false;
      }
    }

    analyzeBtn.addEventListener("click", runAnalysis);
    problemEl.value = "I need to add rate limiting to my FastAPI endpoints, 100 requests per minute per IP";
    languageEl.value = "python";
  </script>
</body>
</html>
"""


def get_home_html() -> str:
    """Return the static HTML page for browser-based demos."""
    return HOME_HTML
