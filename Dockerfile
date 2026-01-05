# Production Dockerfile for ApexFlow Prediction Service
# Optimized multi-stage build

# Stage 1: Build dependencies
FROM python:3.10-slim as builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:${PATH}"

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to a local directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime image
FROM python:3.10-slim

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/apexflow/.local/bin:${PATH}" \
    PYTHONPATH="/app/src"

WORKDIR /app

# Create a non-root user
RUN useradd -m apexflow && chown -R apexflow:apexflow /app
USER apexflow

# Copy installed packages from builder stage
COPY --from=builder --chown=apexflow:apexflow /root/.local /home/apexflow/.local

# Copy application source code
COPY --chown=apexflow:apexflow src /app/src
COPY --chown=apexflow:apexflow config /app/config
COPY --chown=apexflow:apexflow main.py /app/

# Expose API port
EXPOSE 8000

# Health check to verify service and model readiness
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch the FastAPI service
CMD ["uvicorn", "apex_flow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
