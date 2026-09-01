"""CISA Cybersecurity Advisories: RSS feed ve HTML sayfası çekme."""

import logging
import sys
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.errors import CrawlerError, ParseError
from crawler.http_client import fetch_text
from crawler.storage import load_records, merge_records, save_records

FEED_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
BASE_URL = "https://www.cisa.gov"
HTML_LIST_URL = f"{BASE_URL}/news-events/cybersecurity-advisories"
DATA_PATH = Path("data/cisa.json")

logger = logging.getLogger(__name__)


def fetch_feed() -> str:
    return fetch_text(FEED_URL)


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
            logger.warning("Başlık/link çıkarılamayan kart atlandı: %.120s", container.get_text(" ", strip=True))
            continue

        date_el = container.select_one("div.c-teaser__date time")
        meta_el = container.select_one("div.c-teaser__meta")
        advisories.append(
            {
                "title": link_el.get_text(strip=True),
                "link": urljoin(BASE_URL, link_el["href"]),
                "date": date_el.get("datetime") if date_el else None,
                "type": meta_el.get_text(strip=True) if meta_el else None,
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

    try:
        scraped = scrape_advisories()
        records, new_count = merge_records(load_records(DATA_PATH), scraped)
        save_records(DATA_PATH, records)
    except CrawlerError as exc:
        logger.error("%s", exc)
        return 1

    for advisory in records:
        print(f"{advisory['title']} -> {advisory['link']}")
    logger.info("%d yeni kayıt, toplam %d — %s", new_count, len(records), DATA_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
