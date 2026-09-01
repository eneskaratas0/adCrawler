"""CISA Cybersecurity Advisories: RSS feed ve HTML sayfası çekme."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.http_client import get_client

FEED_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
BASE_URL = "https://www.cisa.gov"
HTML_LIST_URL = f"{BASE_URL}/news-events/cybersecurity-advisories"


def fetch_feed() -> str:
    with get_client() as client:
        response = client.get(FEED_URL)
        response.raise_for_status()
        return response.text


def scrape_advisories() -> list[dict[str, str]]:
    with get_client() as client:
        response = client.get(HTML_LIST_URL)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    advisories = []
    for container in soup.select("article.c-teaser"):
        link_el = container.select_one("h3.c-teaser__title a")
        if link_el is None:
            continue
        advisories.append(
            {
                "title": link_el.get_text(strip=True),
                "link": urljoin(BASE_URL, link_el["href"]),
            }
        )
    return advisories


if __name__ == "__main__":
    for advisory in scrape_advisories():
        print(f"{advisory['title']} -> {advisory['link']}")
