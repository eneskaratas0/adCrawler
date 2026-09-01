"""Tek seferlik: data/cisa.json içeriğini SQLite'a taşır, `first_seen` değerlerini korur.

Kullanım:  uv run python -m scripts.migrate_json_to_sqlite  (proje kökünden)
JSON dosyası silinmez; yedek olarak yerinde kalır.
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path

from crawler import db
from crawler.cisa import split_meta
from crawler.cli import DB_PATH
from crawler.errors import CrawlerError
from crawler.sources import BY_SLUG

CISA = BY_SLUG["cisa"]

JSON_PATH = Path("data/cisa.json")

logger = logging.getLogger("migrate")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not JSON_PATH.exists():
        logger.error("%s bulunamadı, taşınacak veri yok.", JSON_PATH)
        return 1

    records = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    logger.info("%s içinde %d kayıt bulundu.", JSON_PATH, len(records))

    try:
        conn = db.connect(DB_PATH)
    except CrawlerError as exc:
        logger.error("%s", exc)
        return 1

    try:
        source_id = db.get_or_create_source(conn, CISA.slug, CISA.name, CISA.feed_url)

        migrated = 0
        with conn:
            for record in records:
                category, advisory_code = split_meta(record.get("type"))
                seen = record.get("first_seen") or db.now_iso()
                cursor = conn.execute(
                    """
                    INSERT INTO advisories
                        (source_id, link, title, published_at, category, advisory_code,
                         first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(link) DO NOTHING
                    """,
                    (
                        source_id,
                        record["link"],
                        record["title"],
                        record.get("date"),
                        category,
                        advisory_code,
                        seen,
                        seen,
                    ),
                )
                migrated += cursor.rowcount

        total = conn.execute(
            "SELECT COUNT(*) AS n FROM advisories WHERE source_id = ?", (source_id,)
        ).fetchone()["n"]
        logger.info("%d kayıt taşındı, veritabanında toplam %d kayıt.", migrated, total)
        logger.info("%s dosyası yedek olarak korundu.", JSON_PATH)
        return 0
    except (sqlite3.Error, KeyError) as exc:
        logger.error("Taşıma başarısız: %s", exc)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
