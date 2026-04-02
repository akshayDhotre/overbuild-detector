# Multi-stage build for minimal runtime image.
FROM python:3.12-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir --root-user-action=ignore uv
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system --no-cache .

FROM python:3.12-slim AS production

RUN groupadd -r overbuild && useradd -r -g overbuild overbuild
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src ./src
COPY pyproject.toml README.md ./

USER overbuild

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=2.0)" || exit 1

EXPOSE 8000
CMD ["uvicorn", "overbuild.main:app", "--host", "0.0.0.0", "--port", "8000"]

