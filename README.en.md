# AdvCrawler

*[Türkçe](README.md)*

A crawler that collects security advisory reports from various sources (national CERTs, vendor PSIRTs).

## Status

The project is at an early stage. Added so far:

- `crawler/http_client.py` — a shared `httpx` client, used by all source fetchers, that sends a descriptive `User-Agent`.
- `crawler/cisa.py` — two ways to pull CISA (US) Cybersecurity Advisories:
  - `fetch_feed()`: fetches the official RSS feed (`all.xml`).
  - `scrape_advisories()`: parses `https://www.cisa.gov/news-events/cybersecurity-advisories` with BeautifulSoup and extracts the title, link, date and type from each advisory card.
- `crawler/storage.py` — a source-agnostic JSON persistence layer. Records are merged and deduplicated by `link`, so each run grows the archive instead of overwriting it, and `first_seen` (when the crawler first saw a record) is preserved. Writes are atomic.

See [`docs/sources.md`](docs/sources.md) for researched/planned sources.

## Setup

Dependencies are managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
# Scrape the CISA advisories page, persist results to data/cisa.json and list them
uv run python -m crawler.cisa
```

Output is written to `data/cisa.json` (not tracked in git). Each record contains:

```json
{
  "title": "CISA Adds Two Known Exploited Vulnerabilities to Catalog",
  "link": "https://www.cisa.gov/news-events/alerts/2026/08/31/...",
  "date": "2026-08-31T12:00:00Z",
  "type": "Alert",
  "first_seen": "2026-09-01T09:20:08.906575+00:00"
}
```

## Structure

```
crawler/
  http_client.py   # shared HTTP client (User-Agent)
  cisa.py          # CISA RSS + HTML scraper
  storage.py       # JSON persistence (merge + dedupe)
data/              # crawler output (not tracked in git)
docs/
  sources.md       # source research (RSS/API/scraping status)
```
