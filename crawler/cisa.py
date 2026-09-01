"""CISA Cybersecurity Advisories: RSS feed ve HTML sayfası çekme."""

from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.http_client import get_client
from crawler.storage import load_records, merge_records, save_records

FEED_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
BASE_URL = "https://www.cisa.gov"
HTML_LIST_URL = f"{BASE_URL}/news-events/cybersecurity-advisories"
DATA_PATH = Path("data/cisa.json")


def fetch_feed() -> str:
    with get_client() as client:
        response = client.get(FEED_URL)
        response.raise_for_status()
        return response.text


def scrape_advisories() -> list[dict[str, str | None]]:
    with get_client() as client:
        response = client.get(HTML_LIST_URL)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    advisories = []
    for container in soup.select("article.c-teaser"):
        link_el = container.select_one("h3.c-teaser__title a")
        if link_el is None:
            continue

        date_el = container.select_one("div.c-teaser__date time")
        meta_el = container.select_one("div.c-teaser__meta")
        advisories.append(
            {
                "title": link_el.get_text(strip=True),
                "link": urljoin(BASE_URL, link_el["href"]),
                "date": date_el["datetime"] if date_el else None,
                "type": meta_el.get_text(strip=True) if meta_el else None,
            }
        )
    return advisories


if __name__ == "__main__":
    scraped = scrape_advisories()
    records, new_count = merge_records(load_records(DATA_PATH), scraped)
    save_records(DATA_PATH, records)

    for advisory in records:
        print(f"{advisory['title']} -> {advisory['link']}")
    print(f"\n{new_count} yeni kayıt, toplam {len(records)} — {DATA_PATH}")
