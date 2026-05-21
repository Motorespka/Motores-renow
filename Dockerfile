# Gêmeo Digital — imagem production-ready (multi-stage)
# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-saas.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels \
        -r requirements.txt \
        -r requirements-saas.txt

FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="gemeo-digital-moto-renow" \
      org.opencontainers.image.description="Streamlit SaaS — Gêmeo Digital"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# libheif — conversão HEIC (pillow-heif)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libheif1 \
    libde265-0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
COPY requirements.txt requirements-saas.txt ./
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

COPY . .
COPY docker/entrypoint.sh /entrypoint.sh
RUN mkdir -p data logs \
    && adduser --disabled-password --gecos "" appuser \
    && chmod +x /entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')" || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["streamlit", "run", "App.py", "--server.headless=true"]
