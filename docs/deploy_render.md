# Deploying OverBuild Detector on Render

Render is the recommended hosting platform for personal and portfolio deployment of OverBuild Detector.
It supports Docker-based deploys with a free tier, zero infrastructure management, and automatic HTTPS.

---

## Prerequisites

- A [Render](https://render.com) account (free tier is sufficient to start)
- This repository pushed to GitHub (public or private)
- Your API keys ready (LLM provider key at minimum)

---

## Option A: Docker Deploy (Recommended)

OverBuild Detector ships with a production-ready multi-stage `Dockerfile`. Render can build and run it directly.

### Step 1 — Create a new Web Service

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**
2. Connect your GitHub account and select the `overbuild-detector` repository
3. Choose a **region** closest to your users

### Step 2 — Configure Build Settings

| Field | Value |
| --- | --- |
| **Environment** | Docker |
| **Dockerfile path** | `./Dockerfile` |
| **Docker context** | `.` (root of repo) |
| **Branch** | `main` |

Render will automatically detect the `Dockerfile` if you leave the path as default.

### Step 3 — Configure Instance

| Field | Value |
| --- | --- |
| **Instance type** | Free (for personal/portfolio) or Starter ($7/mo for always-on) |
| **Port** | `8000` (matches `EXPOSE 8000` in Dockerfile) |

> **Note:** Free tier instances spin down after 15 minutes of inactivity and take ~30 seconds to cold-start on the next request. Upgrade to Starter for always-on hosting.

### Step 4 — Set Environment Variables

In the **Environment** tab, add the following variables:

**Required (for full LLM quality):**

| Key | Example Value |
| --- | --- |
| `OVERBUILD_LLM_PROVIDER` | `anthropic` |
| `OVERBUILD_LLM_MODEL` | `claude-sonnet-4-20250514` |
| `OVERBUILD_LLM_API_KEY` | `sk-ant-...` |

**Recommended (for better search coverage):**

| Key | Notes |
| --- | --- |
| `OVERBUILD_GITHUB_TOKEN` | GitHub personal access token — raises rate limits significantly |
| `OVERBUILD_LIBRARIESIO_API_KEY` | From libraries.io/api |
| `OVERBUILD_STACKOVERFLOW_API_KEY` | From stackapps.com |

**Optional (alternative provider keys):**

| Key | Notes |
| --- | --- |
| `OVERBUILD_OPENAI_API_KEY` | If using OpenAI provider |
| `OVERBUILD_GOOGLE_API_KEY` | If using Google provider |

> Set all secrets using Render's **Secret** type (not Plain Text) to prevent them from appearing in logs.

### Step 5 — Deploy

Click **Create Web Service**. Render will:

1. Clone your repository
2. Build the Docker image using your `Dockerfile`
3. Run the container with the environment variables you configured
4. Assign a public HTTPS URL like `https://overbuild-detector.onrender.com`

### Step 6 — Verify

Once the deploy shows **Live**, verify the service:

```bash
curl https://your-service.onrender.com/health
```

Expected response:

```json
{"status": "ok"}
```

Test an analysis:

```bash
curl -X POST https://your-service.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "I need to add rate limiting to my FastAPI endpoints",
    "language": "python"
  }'
```

---

## Option B: Python (Native) Deploy

If you prefer not to use Docker, Render can run the app directly with a start command.

### Build Command

```bash
pip install uv && uv pip install --system .
```

### Start Command

```bash
uvicorn overbuild.main:app --host 0.0.0.0 --port $PORT
```

> Render injects `$PORT` automatically. The app binds to it instead of hardcoded `8000`.

### Environment

Set `PYTHON_VERSION` to `3.12` in the environment variables tab.

Set all the same API keys as listed in Option A.

---

## Auto-Deploy on Push

Render auto-deploys whenever you push to the configured branch (`main` by default).
To disable this and deploy manually, go to **Settings** → **Build & Deploy** → toggle off **Auto-Deploy**.

---

## Health Check Configuration

Render uses health checks to determine when a deploy is ready and to restart unhealthy instances.

The app exposes `GET /health` which returns `{"status": "ok"}`. Configure this in Render:

- **Health Check Path:** `/health`
- **Health Check Timeout:** `30s`

This matches the `HEALTHCHECK` defined in the `Dockerfile`.

---

## Custom Domain

1. Go to **Settings** → **Custom Domains**
2. Add your domain (e.g. `overbuild.yourdomain.com`)
3. Follow Render's DNS instructions (CNAME record pointing to your Render service)
4. Render provisions a TLS certificate automatically via Let's Encrypt

---

## Render vs Other Platforms

| Feature | Render (Free) | Render (Starter) | Railway | AWS ECS |
| --- | --- | --- | --- | --- |
| Cost | Free | $7/mo | ~$5/mo | ~$15–30/mo |
| Cold starts | Yes (30s) | No | No | No |
| Docker support | Yes | Yes | Yes | Yes |
| Auto HTTPS | Yes | Yes | Yes | Yes (ALB) |
| Auto-deploy from Git | Yes | Yes | Yes | Via CI/CD |
| Custom domains | Yes | Yes | Yes | Yes |
| Best for | Portfolio / demos | Always-on personal | Hobby projects | Production scale |

---

## Troubleshooting

**Deploy fails at build step:**
- Check that `pyproject.toml` and `README.md` are committed (the `Dockerfile` copies both)
- Verify `uv` can resolve all dependencies: run `uv pip install .` locally first

**Health check fails after deploy:**
- Ensure the `OVERBUILD_LLM_API_KEY` is set; the app starts without it (heuristic mode) but confirm with `/health`
- Check Render logs under **Logs** tab for startup errors

**Slow cold starts on free tier:**
- Expected — free instances sleep after inactivity
- Use [UptimeRobot](https://uptimerobot.com) (free) to ping `/health` every 14 minutes to prevent sleep
- Or upgrade to Starter tier ($7/mo) for always-on

**Rate limit errors from search APIs:**
- Add `OVERBUILD_GITHUB_TOKEN` — unauthenticated GitHub API is limited to 60 req/hour
- Add `OVERBUILD_LIBRARIESIO_API_KEY` for higher Libraries.io limits

---

## Attribution

OverBuild Detector — original concept and architecture by **Akshay Dhotre**
GitHub: [@akshayDhotre](https://github.com/akshayDhotre) | akshaydhotre.work@gmail.com
