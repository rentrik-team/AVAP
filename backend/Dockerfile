# AVAP Backend — FastAPI + Nmap
#
# Python 3.12 (documented stack floor). Nmap is installed in the image
# because the scanner engine invokes it as a subprocess (unprivileged
# -sT/-sn scans only, so no extra capabilities or root are required).
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# nmap: invoked by the scanner adapter (NMAP_EXECUTABLE=/usr/bin/nmap).
# curl: used by the container healthcheck against GET /health.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nmap curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user. Nmap's connect/ping scans need no privileges.
RUN groupadd --system avap && useradd --system --gid avap --create-home avap

WORKDIR /app

# Install runtime dependencies first so source edits don't bust the pip
# layer. Dependencies are read straight from pyproject.toml (the single
# source of truth) — the app package itself is not installed; it is run
# from /app via PYTHONPATH.
COPY pyproject.toml ./
RUN python -c "import tomllib, pathlib; \
    deps = tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['dependencies']; \
    pathlib.Path('requirements.txt').write_text('\n'.join(deps))" \
    && pip install -r requirements.txt

# Application source + migrations. The runtime .env file is deliberately
# NOT copied (see .dockerignore) — all configuration comes from container
# environment variables (docker-compose.yml / your orchestrator).
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Writable data directories (scan output, generated reports, logs).
# Named volumes mounted here inherit this ownership on first use.
RUN mkdir -p /data/scan_output /data/generated_reports /data/logs \
    && chown -R avap:avap /data /app

ENV PYTHONPATH=/app \
    SCANNER_OUTPUT_DIRECTORY=/data/scan_output \
    REPORT_OUTPUT_DIRECTORY=/data/generated_reports \
    LOG_DIRECTORY=/data/logs \
    NMAP_EXECUTABLE=/usr/bin/nmap

USER avap

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
