# Use a lightweight Python base image
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# --- Stage 1: Build Core Environment ---
FROM base AS core-builder
COPY pyproject.toml uv.lock ./
RUN uv venv envs/core && \
    uv sync --frozen --no-dev --venv envs/core

# --- Stage 2: Build Docling Environment ---
FROM base AS docling-builder
# Note: Docling is heavy; we use a separate venv to isolate ML deps
RUN uv venv envs/docling && \
    uv pip install docling --venv envs/docling

# --- Stage 3: Final Production Image ---
FROM base AS runtime

# Install system dependencies (git for RepoInvestigator,
# and libraries required by docling/pyMuPDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy environments from builders
COPY --from=core-builder /app/envs/core /app/envs/core
COPY --from=docling-builder /app/envs/docling /app/envs/docling

# Copy source code and rubric
COPY src/ /app/src/
COPY runners/ /app/runners/
COPY rubric/ /app/rubric/
COPY main.py /app/

# Set environment variables
ENV PATH="/app/envs/core/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Application entrypoint
ENTRYPOINT ["python", "main.py"]
