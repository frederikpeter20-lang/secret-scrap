# ek-scraper - Kleinanzeigen.de Scraper

Production-ready scraper for monitoring apartments and items on kleinanzeigen.de with robust error handling, rate limiting, and multi-channel notifications.

## Features

- ✅ **Rate limiting & delays** - Random delays to avoid blocking
- ✅ **Robust HTML parsing** - Multiple selectors with fallbacks
- ✅ **Retry logic** - Automatic retry with exponential backoff
- ✅ **Multi-channel notifications** - Pushover, ntfy.sh, Telegram
- ✅ **Persistent data store** - JSON-based tracking of seen items
- ✅ **CLI interface** - Simple command-line tools
- ✅ **Docker support** - Container-ready with multi-stage builds
- ✅ **Environment variables** - `.env` file support via pydantic

## Quick Start

```bash
# Clone repository
git clone https://github.com/frederikpeter20-lang/secret-scrap.git
cd secret-scrap

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS or .venv\Scripts\activate on Windows

# Install dependencies
uv sync

# Create and edit config
cp docs/example-config.json config.json
# nano config.json

# Run scraper
ek-scraper run config.json
