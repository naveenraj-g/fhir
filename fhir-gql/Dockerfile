# ── Stage: runtime ────────────────────────────────────────────────────────────
# Single-stage build — uv handles dependency resolution and installation
# entirely inside the final image. python:3.14-slim matches pyproject.toml.
FROM python:3.14-slim

# Prevent .pyc files and enable unbuffered stdout/stderr so uvicorn logs
# appear immediately in `docker logs` without buffering delays.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Install into the system Python — no isolated .venv needed in containers.
    UV_SYSTEM_PYTHON=1 \
    # Fail the build if uv.lock is out of sync with pyproject.toml.
    UV_FROZEN=1

# Install uv via pip — avoids needing ghcr.io registry access during the build.
RUN pip install --no-cache-dir uv

WORKDIR /app

# ── Dependency layer (cached separately from app code) ────────────────────────
# Copy only the manifests first — Docker re-uses this layer until pyproject.toml
# or uv.lock changes, so routine app-code edits won't trigger a full reinstall.
COPY pyproject.toml uv.lock ./

# Install production dependencies from the lockfile.
# --no-dev skips linters, test runners, and other dev-only packages.
RUN uv sync --no-dev

# ── Application code ──────────────────────────────────────────────────────────
COPY app/ ./app/

# ── Non-root user (security hardening) ───────────────────────────────────────
# Running as root grants the process unnecessary host privileges if the
# container is compromised. A dedicated user limits the blast radius.
RUN adduser --disabled-password --gecos "" --home /app appuser \
    && chown -R appuser:appuser /app
USER appuser

# ── Network ───────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Entry point ───────────────────────────────────────────────────────────────
# Adjust --workers to match VPS vCPU count (2 × vCPUs is a common starting point).
# All secrets and URLs must be supplied at runtime via .env file or
# docker-compose environment: — never bake them into the image.
#
# Required env vars:
#   FHIR_SERVER_URL       — downstream FHIR server base URL
#   TERMINOLOGY_SERVER_URL — terminology service base URL
#   IAM_JWKS_URL          — JWT public key endpoint
#   IAM_ISSUER            — expected JWT issuer claim
#   REDIS_URL             — Redis connection string (rate limiting)
#   ENVIRONMENT           — development | staging | production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
