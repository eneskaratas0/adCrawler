# AdvCrawler

*[Türkçe](README.md)*

A crawler that collects security advisory reports from various sources (national CERTs, vendor PSIRTs).

## Status

The project is at an early stage. Added so far:

- `crawler/http_client.py` — a shared `httpx` client, used by all source fetchers, that sends a descriptive `User-Agent`.
- `crawler/cisa.py` — two ways to pull CISA (US) Cybersecurity Advisories:
  - `fetch_feed()`: fetches the official RSS feed (`all.xml`).
  - `scrape_advisories()`: parses `https://www.cisa.gov/news-events/cybersecurity-advisories` with BeautifulSoup and extracts the title, link, date and type from each advisory card.
- `crawler/db.py` + `crawler/schema.sql` — SQLite persistence layer (stdlib `sqlite3`, no ORM). Records are upserted by `link`: each run grows the archive instead of overwriting it, `first_seen` is preserved and `last_seen` is updated.
- `crawler/errors.py` — the `CrawlerError` hierarchy (`FetchError`, `ParseError`, `StorageError`). Expected failures turn into a clear message and exit code 1; unexpected ones still raise a traceback.

See [`docs/sources.md`](docs/sources.md) for researched/planned sources.

## Setup

Dependencies are managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
# Scrape the CISA advisories page, persist to data/advisories.db and list them
uv run python -m crawler.cisa
```

Data is written to `data/advisories.db` (SQLite), not tracked in git. A successful run exits 0 and a failure exits 1, so scheduled runs (cron/CI) can catch problems.

To migrate legacy `data/cisa.json` data (one-off):

```bash
uv run python -m scripts.migrate_json_to_sqlite
```

## Schema

| Table | Purpose |
|---|---|
| `sources` | Sources (`cisa`, `cert-eu`, …) — for the multi-source design |
| `advisories` | Advisory records; `link` is unique (the dedupe key), `first_seen`/`last_seen` are tracked |
| `cves` + `advisory_cves` | CVEs and their many-to-many link to advisories. Schema is ready; population comes once detail pages are parsed |
| `crawl_runs` | One row per run: status, new record count, error message |

Full DDL: [`crawler/schema.sql`](crawler/schema.sql)

## Structure

```
crawler/
  http_client.py   # shared HTTP client (User-Agent) + fetch_text
  cisa.py          # CISA RSS + HTML scraper
  db.py            # SQLite persistence (upsert, run logging)
  schema.sql       # table definitions
  errors.py        # CrawlerError hierarchy
scripts/
  migrate_json_to_sqlite.py
data/              # crawler output, SQLite file (not tracked in git)
docs/
  sources.md       # source research (RSS/API/scraping status)
```
