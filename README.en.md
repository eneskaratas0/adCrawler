# AdvCrawler

*[Türkçe](README.md)*

A crawler that collects security advisory reports from various sources (national CERTs, vendor PSIRTs).

## Status

The project is at an early stage. Added so far:

- `crawler/http_client.py` — a shared `httpx` client, used by all source fetchers, that sends a descriptive `User-Agent`.
- `crawler/cisa.py` — two ways to pull CISA (US) Cybersecurity Advisories:
  - `fetch_feed()`: fetches the official RSS feed (`all.xml`).
  - `scrape_advisories()`: parses `https://www.cisa.gov/news-events/cybersecurity-advisories` with BeautifulSoup and extracts the title and link from each advisory card.

See [`docs/sources.md`](docs/sources.md) for researched/planned sources.

## Setup

Dependencies are managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
# Scrape the CISA advisories page and list title + link pairs
uv run python -m crawler.cisa
```

## Structure

```
crawler/
  http_client.py   # shared HTTP client (User-Agent)
  cisa.py          # CISA RSS + HTML scraper
docs/
  sources.md       # source research (RSS/API/scraping status)
```
