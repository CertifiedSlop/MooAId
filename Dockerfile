# MooAId - My Opinion AI Daemon
# Multi-stage Dockerfile for production deployment

# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 mooaid && \
    useradd --uid 1000 --gid mooaid --shell /bin/bash --create-home mooaid

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=mooaid:mooaid mooaid/ ./mooaid/
COPY --chown=mooaid:mooaid config.yaml ./config.yaml

# Create data directory for database
RUN mkdir -p /app/data && chown mooaid:mooaid /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MOOAID_CONFIG_PATH=/app/config.yaml
ENV MOOAID_DB_PATH=/app/data/mooaid.db

# Switch to non-root user
USER mooaid

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Default command - run the API server
CMD ["uvicorn", "mooaid.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
