FROM python:3.11-slim as builder

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY ek_scraper ./ek_scraper

# Install dependencies
RUN uv sync --frozen --no-dev

FROM python:3.11-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /app /app

# Create non-root user
RUN useradd -m scraper && chown -R scraper:scraper /app
USER scraper

# Environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "-m", "ek_scraper.cli", "run", "config.json"]
