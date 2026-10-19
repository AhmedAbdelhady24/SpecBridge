# Multi-stage Dockerfile for SpecBridge
# Stage 1: Build static web assets
FROM node:22-bookworm-slim AS frontend-build

WORKDIR /build

# Copy frontend manifests
COPY apps/web/package.json apps/web/package-lock.json ./apps/web/
COPY packages/contracts ./packages/contracts

# Install dependencies locked
RUN cd apps/web && npm ci --no-fund

# Copy frontend source code
COPY apps/web ./apps/web

# Build static assets (outputs to /build/apps/web/dist)
RUN cd apps/web && npm run build

# Stage 2: Python runtime with uv and FastAPI
FROM python:3.12-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official binary
COPY --from=ghcr.io/astral-sh/uv:0.5.26 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/api \
    UV_LINK_MODE=copy \
    SPECBRIDGE_DATA_DIR=/data \
    SPECBRIDGE_UI_ORIGIN=http://127.0.0.1:8000

# Create unprivileged system user
RUN useradd -u 10001 -m -s /bin/bash specbridge && \
    mkdir -p /data && \
    chown -R specbridge:specbridge /data

WORKDIR /app

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Install production dependencies
RUN uv sync --locked --no-dev

# Copy application source
COPY services ./services
COPY skills ./skills
COPY packages ./packages

# Copy built frontend assets from builder stage
COPY --from=frontend-build /build/apps/web/dist ./apps/web/dist

# Set ownership
RUN chown -R specbridge:specbridge /app

USER specbridge

VOLUME ["/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/ || exit 1

ENTRYPOINT ["uv", "run", "uvicorn", "specbridge.main:create_default_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
