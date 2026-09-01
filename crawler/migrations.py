"""`PRAGMA user_version` tabanlı şema migrasyonları.

`schema.sql` yalnızca eksik tabloları oluşturur (CREATE TABLE IF NOT EXISTS); mevcut bir
veritabanına kolon eklemez veya kısıt değiştirmez. Bu modül o farkı kapatır.

Yeni migrasyon eklerken: MIGRATIONS listesinin SONUNA ekle, mevcutları değiştirme.
"""

import logging
import sqlite3

from crawler.errors import StorageError

logger = logging.getLogger(__name__)


def _add_summary_column(conn: sqlite3.Connection) -> None:
    """RSS description'ı saklamak için advisories.summary."""
    conn.execute("ALTER TABLE advisories ADD COLUMN summary TEXT")


def _allow_interrupted_status(conn: sqlite3.Connection) -> None:
    """crawl_runs.status CHECK kısıtına 'interrupted' ekler.

    SQLite CHECK kısıtını ALTER ile değiştiremez; tabloyu yeniden oluşturup veriyi taşırız.
    """
    conn.executescript(
        """
        CREATE TABLE crawl_runs_new (
            id            INTEGER PRIMARY KEY,
            source_id     INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            started_at    TEXT NOT NULL,
            finished_at   TEXT,
            status        TEXT NOT NULL
                          CHECK (status IN ('running', 'success', 'error', 'interrupted')),
            new_count     INTEGER,
            error_message TEXT
        );

        INSERT INTO crawl_runs_new
            SELECT id, source_id, started_at, finished_at, status, new_count, error_message
            FROM crawl_runs;

        DROP TABLE crawl_runs;
        ALTER TABLE crawl_runs_new RENAME TO crawl_runs;

        CREATE INDEX IF NOT EXISTS idx_crawl_runs_source ON crawl_runs(source_id, started_at DESC);
        """
    )


# Sıra önemli: indeks = uygulanacak user_version. Asla araya ekleme yapma.
MIGRATIONS = [
    _add_summary_column,
    _allow_interrupted_status,
]


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Eksik migrasyonları sırayla uygular; uygulanan sayıyı döner."""
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        pending = MIGRATIONS[version:]

        for offset, migration in enumerate(pending, start=version):
            logger.info("Migrasyon uygulanıyor: %s", migration.__name__)
            with conn:
                migration(conn)
                # PRAGMA parametre bağlamayı desteklemiyor; değer koddan geliyor.
                conn.execute(f"PRAGMA user_version = {offset + 1}")

        return len(pending)
    except sqlite3.Error as exc:
        raise StorageError(f"Şema migrasyonu başarısız: {exc}") from exc
