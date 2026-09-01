"""AdvCrawler komut satırı arayüzü."""

import argparse
import logging
import sys
from pathlib import Path

from crawler import db, pipeline, sources
from crawler.errors import CrawlerError

DB_PATH = Path("data/advisories.db")

logger = logging.getLogger("advcrawler")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="advcrawler", description="Güvenlik advisory raporlarını toplar."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", metavar="SLUG", help="Tek bir kaynağı çalıştır")
    group.add_argument("--all", action="store_true", help="Tüm kaynakları çalıştır")
    group.add_argument("--list-sources", action="store_true", help="Kaynakları listele")
    parser.add_argument(
        "--db", type=Path, default=DB_PATH, help=f"Veritabanı yolu (varsayılan: {DB_PATH})"
    )
    return parser


def list_sources() -> int:
    for source in sources.SOURCES:
        print(f"  {source.slug:16} {source.name:30} {source.feed_url}")
    return 0


def run(selected: list[sources.Source], db_path: Path) -> int:
    conn = None
    try:
        conn = db.connect(db_path)
        db.close_stale_runs(conn)
    except CrawlerError as exc:
        logger.error("%s", exc)
        if conn is not None:
            conn.close()
        return 1

    failed = []
    try:
        for source in selected:
            try:
                new_count, cve_links = pipeline.run_source(conn, source)
                logger.info(
                    "%-16s %d yeni advisory, %d yeni CVE bağı", source.slug, new_count, cve_links
                )
            except CrawlerError as exc:
                # Bir kaynağın hatası diğerlerini düşürmemeli.
                logger.error("%-16s %s", source.slug, exc)
                failed.append(source.slug)
    finally:
        conn.close()

    if failed:
        logger.error("%d/%d kaynak başarısız: %s", len(failed), len(selected), ", ".join(failed))
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # httpx her istek için INFO log basıyor; sadece sorun olduğunda duyalım.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    args = build_parser().parse_args(argv)

    if args.list_sources:
        return list_sources()

    if args.all:
        selected = sources.SOURCES
    else:
        source = sources.BY_SLUG.get(args.source)
        if source is None:
            logger.error(
                "Bilinmeyen kaynak: %s. Seçenekler: %s",
                args.source,
                ", ".join(sources.BY_SLUG),
            )
            return 2
        selected = [source]

    return run(selected, args.db)


if __name__ == "__main__":
    sys.exit(main())
