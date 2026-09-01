"""CISA Cybersecurity Advisories: RSS feed ve HTML sayfası çekme."""

import logging
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler import db
from crawler.errors import CrawlerError, ParseError
from crawler.http_client import fetch_text

FEED_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
BASE_URL = "https://www.cisa.gov"
HTML_LIST_URL = f"{BASE_URL}/news-events/cybersecurity-advisories"
DB_PATH = Path("data/advisories.db")

SOURCE_SLUG = "cisa"
SOURCE_NAME = "CISA (ABD)"

# 'AA26-237A' gibi advisory kodları; 'resource' gibi içerik etiketlerini dışarıda bırakır.
ADVISORY_CODE_RE = re.compile(r"[A-Za-z]{1,5}\d{2}-\d+[A-Za-z]?")

logger = logging.getLogger(__name__)


def fetch_feed() -> str:
    return fetch_text(FEED_URL)


def split_meta(meta: str | None) -> tuple[str | None, str | None]:
    """'Cybersecurity Advisory | AA26-237A' -> ('Cybersecurity Advisory', 'AA26-237A')."""
    if not meta:
        return None, None

    category, _, rest = meta.partition("|")
    rest = rest.strip()
    code = rest if ADVISORY_CODE_RE.fullmatch(rest) else None
    return category.strip() or None, code


def scrape_advisories() -> list[dict[str, str | None]]:
    soup = BeautifulSoup(fetch_text(HTML_LIST_URL), "html.parser")

    containers = soup.select("article.c-teaser")
    if not containers:
        raise ParseError(
            f"{HTML_LIST_URL} sayfasında 'article.c-teaser' seçicisiyle hiç kart bulunamadı — "
            "sayfa yapısı değişmiş olabilir."
        )

    advisories = []
    for container in containers:
        link_el = container.select_one("h3.c-teaser__title a")
        if link_el is None or not link_el.get("href"):
            logger.warning(
                "Başlık/link çıkarılamayan kart atlandı: %.120s",
                container.get_text(" ", strip=True),
            )
            continue

        date_el = container.select_one("div.c-teaser__date time")
        meta_el = container.select_one("div.c-teaser__meta")
        category, advisory_code = split_meta(meta_el.get_text(strip=True) if meta_el else None)
        advisories.append(
            {
                "title": link_el.get_text(strip=True),
                "link": urljoin(BASE_URL, link_el["href"]),
                "published_at": date_el.get("datetime") if date_el else None,
                "category": category,
                "advisory_code": advisory_code,
            }
        )

    if not advisories:
        raise ParseError(
            f"{len(containers)} kart bulundu ama hiçbirinden başlık/link çıkarılamadı — "
            "kart içi seçiciler değişmiş olabilir."
        )
    return advisories


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # httpx her istek için INFO log basıyor; sadece sorun olduğunda duyalım.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    conn = None
    run_id = None
    try:
        conn = db.connect(DB_PATH)
        source_id = db.get_or_create_source(conn, SOURCE_SLUG, SOURCE_NAME, HTML_LIST_URL)
        run_id = db.start_run(conn, source_id)

        scraped = scrape_advisories()
        new_count = db.upsert_advisories(conn, source_id, scraped)
        db.finish_run(conn, run_id, "success", new_count)

        for advisory in db.list_advisories(conn, source_id):
            print(f"{advisory['title']} -> {advisory['link']}")
        logger.info("%d yeni kayıt — %s", new_count, DB_PATH)
        return 0
    except CrawlerError as exc:
        logger.error("%s", exc)
        if conn is not None and run_id is not None:
            db.finish_run(conn, run_id, "error", error_message=str(exc))
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
