# Cognitive Value Studio: one container serving the built web app and the API on port 8876.
# Synthetic data, shadow mode, no credentials. See docker-compose.yml for the hardened run settings.

FROM node:22.14-bookworm-slim AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY apps/api/requirements.lock.txt apps/api/requirements.lock.txt
RUN pip install -r apps/api/requirements.lock.txt \
    && pip uninstall -y pip setuptools wheel || true

COPY apps/api apps/api
COPY data data
COPY packages packages
COPY fixtures fixtures
COPY reference_projects/value_studio reference_projects/value_studio
COPY reference_projects/agent_runtime reference_projects/agent_runtime
COPY --from=web /web/dist apps/web/dist

RUN useradd --system --uid 10001 --home-dir /nonexistent --shell /usr/sbin/nologin twin \
    && mkdir -p /state && chown twin /state

ENV BIND_HOST=0.0.0.0 \
    PORT=8876 \
    STUDIO_WEB_DIST=/app/apps/web/dist \
    STUDIO_DB=/state/studio.sqlite3 \
    STUDIO_LG_DB=/state/langgraph.sqlite3

USER twin
EXPOSE 8876
VOLUME ["/state"]
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8876/api/health', timeout=2)"]

WORKDIR /app/apps/api
CMD ["python", "main.py"]
