# ------------------------------------------------------------------------------
# HealthOps Studio - Backend Dockerfile
# ------------------------------------------------------------------------------
# This Dockerfile builds the FastAPI application and the Celery worker.
# It uses a multi-stage approach to keep the final image clean.

# --- Stage 1: Build ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies for compiling certain Python packages (like psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# --- Stage 2: Runtime ---
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (require for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install them
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Create a non-root user for security
RUN useradd -m appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create data directory and set permissions
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

USER appuser

# Ensure the /app path is in PYTHONPATH so absolute imports work
ENV PYTHONPATH=/app

# Expose FastAPI port
EXPOSE 8000

# Default command (can be overridden in docker-compose for celery workers)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
