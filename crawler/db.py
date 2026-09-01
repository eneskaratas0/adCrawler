"""SQLite kalıcılık katmanı: şema kurulumu, advisory upsert'i ve çalıştırma kaydı."""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from crawler.errors import StorageError

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    """Veritabanını açar, şemayı kurar (idempotent) ve bağlantıyı döner."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return conn
    except (sqlite3.Error, OSError) as exc:
        raise StorageError(f"{path} veritabanı açılamadı: {exc}") from exc


def get_or_create_source(conn: sqlite3.Connection, slug: str, name: str, url: str) -> int:
    try:
        with conn:
            conn.execute(
                "INSERT INTO sources (slug, name, url, created_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(slug) DO UPDATE SET name = excluded.name, url = excluded.url",
                (slug, name, url, now_iso()),
            )
        row = conn.execute("SELECT id FROM sources WHERE slug = ?", (slug,)).fetchone()
        return row["id"]
    except sqlite3.Error as exc:
        raise StorageError(f"'{slug}' kaynağı kaydedilemedi: {exc}") from exc


def upsert_advisories(
    conn: sqlite3.Connection, source_id: int, records: list[dict]
) -> int:
    """Kayıtları `link`'e göre ekler/günceller. `first_seen` korunur; yeni kayıt sayısını döner."""
    seen_at = now_iso()
    try:
        existing = {
            row["link"]
            for row in conn.execute(
                "SELECT link FROM advisories WHERE source_id = ?", (source_id,)
            )
        }
        new_count = sum(1 for r in records if r["link"] not in existing)

        with conn:
            conn.executemany(
                """
                INSERT INTO advisories
                    (source_id, link, title, published_at, category, advisory_code,
                     first_seen, last_seen)
                VALUES
                    (:source_id, :link, :title, :published_at, :category, :advisory_code,
                     :seen_at, :seen_at)
                ON CONFLICT(link) DO UPDATE SET
                    title         = excluded.title,
                    published_at  = excluded.published_at,
                    category      = excluded.category,
                    advisory_code = excluded.advisory_code,
                    last_seen     = excluded.last_seen
                """,
                [{**r, "source_id": source_id, "seen_at": seen_at} for r in records],
            )
        return new_count
    except sqlite3.Error as exc:
        raise StorageError(f"Advisory kayıtları yazılamadı: {exc}") from exc


def start_run(conn: sqlite3.Connection, source_id: int) -> int:
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO crawl_runs (source_id, started_at, status) VALUES (?, ?, 'running')",
                (source_id, now_iso()),
            )
        return cursor.lastrowid
    except sqlite3.Error as exc:
        raise StorageError(f"Çalıştırma kaydı açılamadı: {exc}") from exc


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    new_count: int | None = None,
    error_message: str | None = None,
) -> None:
    try:
        with conn:
            conn.execute(
                "UPDATE crawl_runs SET finished_at = ?, status = ?, new_count = ?, "
                "error_message = ? WHERE id = ?",
                (now_iso(), status, new_count, error_message, run_id),
            )
    except sqlite3.Error as exc:
        # Asıl hatanın üstünü örtmemek için burada yükseltmiyoruz.
        logger.warning("Çalıştırma kaydı (%d) kapatılamadı: %s", run_id, exc)


def list_advisories(conn: sqlite3.Connection, source_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT title, link, published_at, category, advisory_code FROM advisories "
        "WHERE source_id = ? ORDER BY published_at DESC",
        (source_id,),
    ).fetchall()
