FROM python:3.11-slim as builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# System deps (falls lxml etc. bauen muss)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./
COPY ek_scraper ./ek_scraper

# Lock neu prüfen + sync
RUN uv lock && uv sync --frozen --no-dev --no-install-project

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app /app

RUN useradd -m scraper && chown -R scraper:scraper /app
USER scraper

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "ek_scraper.cli", "run", "config.json"]
