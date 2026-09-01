"""Tek bir kaynağı uçtan uca çalıştıran akış: fetch -> parse -> türet -> yaz -> kaydet."""

import logging
import sqlite3

from crawler import db, rss
from crawler.cve import extract_cves
from crawler.errors import CrawlerError
from crawler.http_client import fetch_text
from crawler.sources import Source

logger = logging.getLogger(__name__)


def build_records(source: Source, xml: str) -> list[dict]:
    records = []
    for item in rss.parse_feed(xml):
        category, advisory_code = (
            source.derive_category(item["link"]) if source.derive_category else (None, None)
        )
        records.append({**item, "category": category, "advisory_code": advisory_code})
    return records


def run_source(conn: sqlite3.Connection, source: Source) -> tuple[int, int]:
    """Kaynağı çeker ve yazar; (yeni advisory, yeni CVE bağı) döner.

    Hata durumunda `crawl_runs`'a kaydeder ve `CrawlerError`'ı yeniden yükseltir —
    çağıran tarafın (CLI) diğer kaynaklara devam edip etmeyeceğine karar vermesi için.
    """
    source_id = db.get_or_create_source(conn, source.slug, source.name, source.feed_url)
    run_id = db.start_run(conn, source_id)

    try:
        records = build_records(source, fetch_text(source.feed_url))
        new_count = db.upsert_advisories(conn, source_id, records)

        ids = db.link_to_id(conn, source_id)
        cve_links = 0
        for record in records:
            advisory_id = ids.get(record["link"])
            if advisory_id is None:
                continue
            # MSRC gibi kaynaklar CVE'yi başlıkta taşıyor, CISA ise açıklamada.
            text = f"{record.get('title') or ''} {record.get('summary') or ''}"
            cve_links += db.link_cves(conn, advisory_id, extract_cves(text))

        db.finish_run(conn, run_id, "success", new_count)
        return new_count, cve_links
    except CrawlerError as exc:
        db.finish_run(conn, run_id, "error", error_message=str(exc))
        raise
