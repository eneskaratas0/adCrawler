# AdvCrawler

*[Türkçe](README.md)*

A crawler that collects security advisory reports from national CERTs and vendor PSIRTs. Records are stored in SQLite, and CVEs mentioned in advisories are extracted and linked.

## Sources

Seven sources are tracked over RSS/RDF:

| Slug | Source |
|---|---|
| `cisa` | CISA (US) — Alert, ICS Advisory, Cybersecurity Advisory |
| `cert-eu` | CERT-EU (EU) |
| `cert-fr-avis` / `cert-fr-alerte` | CERT-FR / ANSSI (France) |
| `jvn` | JVN / JPCERT/CC (Japan) |
| `msrc` | Microsoft MSRC |
| `cisco` | Cisco PSIRT |

Adding a source means adding one line to [`crawler/sources.py`](crawler/sources.py). Source research: [`docs/sources.md`](docs/sources.md).

## Setup

Dependencies are managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

```bash
uv run advcrawler --list-sources     # list sources
uv run advcrawler --source cisa      # a single source
uv run advcrawler --all              # every source
```

Data is written to `data/advisories.db` (SQLite), not tracked in git. A successful run exits 0 and a failure exits 1, so scheduled runs (cron/CI) can catch problems. Under `--all`, one source failing does not stop the others.

Optional: if `ADVCRAWLER_CONTACT` is set, a contact address is added to the User-Agent.

## Schema

| Table | Purpose |
|---|---|
| `sources` | Sources (`cisa`, `cert-eu`, …) |
| `advisories` | Advisory records; `link` is unique (the dedupe key), `first_seen`/`last_seen` are tracked |
| `cves` + `advisory_cves` | CVEs extracted from advisory titles and summaries (many-to-many) |
| `crawl_runs` | One row per run: status, new record count, error message |

Full DDL: [`crawler/schema.sql`](crawler/schema.sql). Schema changes ship as `PRAGMA user_version` migrations ([`crawler/migrations.py`](crawler/migrations.py)) — existing databases are upgraded automatically.

## Roadmap

Next up, in priority order:

- **Historical backfill** — CISA's HTML listing spans 506 pages (~5060 advisories), an archive the RSS feed does not reach. Prerequisites: a delay between requests, resumability, progress tracking.
- **Conditional GET** (ETag / If-Modified-Since) — avoids a full download on every run; a clear win for the MSRC feed at ~4500 items.
- **Retry/backoff** — a transient network error currently fails the whole source.
- **CISA KEV (JSON/CSV) and ICS CSAF 2.0** — official machine-readable sources, far richer than RSS.
- **USOM / Turkish Cybersecurity Directorate** — an SPA, so it needs a headless browser.
- Widening the vendor list (Fortinet, Palo Alto, VMware, Oracle, Adobe …).

Details and open questions: [`docs/sources.md`](docs/sources.md).

## Development

```bash
uv run --group dev pytest      # tests (no network needed, they run on fixtures)
uv run --group dev ruff check .
```

## Structure

```
crawler/
  cli.py           # command-line interface
  pipeline.py      # per-source run flow (fetch -> parse -> derive -> store)
  sources.py       # source definitions
  rss.py           # RSS 2.0 / RDF parsing (namespace-agnostic)
  cve.py           # CVE id extraction
  cisa.py          # CISA-specific: category derivation + HTML scraper (for backfill)
  db.py            # SQLite persistence
  migrations.py    # schema migrations
  schema.sql       # table definitions
  http_client.py   # shared HTTP client (User-Agent)
  errors.py        # CrawlerError hierarchy
tests/             # fixtures are real feed/HTML snapshots
data/              # SQLite file (not tracked in git)
docs/sources.md    # source research
```
