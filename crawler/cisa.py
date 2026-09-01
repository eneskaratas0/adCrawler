"""CISA Cybersecurity Advisories.

Birincil yol RSS (`all.xml`): HTML listeleme sayfasından 3 kat fazla kayıt veriyor, ICS
advisory'lerini de kapsıyor ve CSS seçicilerine bağımlı değil. HTML scraper ikincil yol
olarak duruyor — tarihsel backfill (506 sayfa) onun üzerinden yapılacak.
"""

import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from crawler.errors import ParseError
from crawler.http_client import fetch_text

FEED_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
BASE_URL = "https://www.cisa.gov"
HTML_LIST_URL = f"{BASE_URL}/news-events/cybersecurity-advisories"

SOURCE_SLUG = "cisa"
SOURCE_NAME = "CISA (ABD)"

# İki kod biçimi: 'AA26-237A' (advisory) ve 'ICSA-26-239-05' (ICS).
# 'resource' gibi rakamsız içerik etiketlerini dışarıda bırakır.
ADVISORY_CODE_RE = re.compile(r"[A-Za-z]{1,5}-?\d{2}-\d+(?:-\d+)?[A-Za-z]?")

# URL yolundan kategori: /news-events/<segment>/... eşlemesi.
PATH_CATEGORIES = {
    "alerts": "Alert",
    "ics-advisories": "ICS Advisory",
    "cybersecurity-advisories": "Cybersecurity Advisory",
    "ics-medical-advisories": "ICS Medical Advisory",
}

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


def derive_category(link: str) -> tuple[str | None, str | None]:
    """URL yolundan kategori ve advisory kodunu türetir.

    /news-events/alerts/2026/08/31/<slug>      -> ('Alert', None)
    /news-events/ics-advisories/icsa-26-239-05 -> ('ICS Advisory', 'ICSA-26-239-05')
    /news-events/cybersecurity-advisories/aa26-237a -> ('Cybersecurity Advisory', 'AA26-237A')
    /resources-tools/resources/<slug>          -> ('Resource', None)
    """
    parts = [p for p in urlparse(link).path.split("/") if p]
    if not parts:
        return None, None

    if parts[0] == "resources-tools":
        return "Resource", None

    if parts[0] != "news-events" or len(parts) < 2:
        return None, None

    category = PATH_CATEGORIES.get(parts[1])
    last = parts[-1]
    code = last.upper() if ADVISORY_CODE_RE.fullmatch(last) else None
    return category, code



def scrape_advisories() -> list[dict[str, str | None]]:
    """HTML listeleme sayfasını scrape eder (ikincil yol; backfill için korunuyor)."""
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
