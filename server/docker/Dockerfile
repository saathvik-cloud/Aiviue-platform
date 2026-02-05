# =============================================================================
# AIVIUE API - DOCKERFILE
# =============================================================================
# Multi-stage build for production-ready FastAPI application.
#
# LOCAL DEVELOPMENT:
#   Build: docker build -t aiviue-api -f docker/Dockerfile .
#   Run:   docker run -p 8000:8000 --env-file .env aiviue-api
#
# RAILWAY DEPLOYMENT:
#   - Set Root Directory: server
#   - Set Dockerfile Path: docker/Dockerfile
#   - Railway automatically injects PORT env variable
#   - No custom start command needed (uses CMD below)
#
# =============================================================================

# ===================== BUILD STAGE =====================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ===================== PRODUCTION STAGE =====================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Default port (Railway overrides via PORT env variable)
ENV PORT=8000

# Expose port (documentation only, Railway ignores this)
EXPOSE 8000

# Health check (uses default port for local, Railway handles health differently)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run application with dynamic port support
# Uses shell form to allow $PORT environment variable expansion
# Railway injects PORT, locally defaults to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
