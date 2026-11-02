# ---- build stage: compile/install deps, none of this ships ----
FROM python:3.13-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage: only what the app needs to run ----
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Never run as root inside the container
RUN useradd --create-home --uid 10001 appuser

COPY --from=builder /install /usr/local
WORKDIR /app
COPY app/ ./app/

USER appuser
EXPOSE 8000

# Docker-level check. Kubernetes will use its own probes instead (step 3).
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
