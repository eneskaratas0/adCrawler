"""RSS/RDF feed ayrıştırma. stdlib ile yeterli — feedparser bağımlılığına gerek yok.

Kaynaklar tek bir formatta anlaşmıyor: CISA/Cisco RSS 2.0 (`pubDate`, RFC 822), JVN ise
RSS 1.0/RDF (namespace'li etiketler, `dc:date`, ISO 8601). Bu yüzden etiketler namespace'ten
bağımsız, tarihler iki formatta da okunur.
"""

import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

from crawler.errors import ParseError

logger = logging.getLogger(__name__)

# Tarih için sırayla denenecek etiketler (yerel ad).
DATE_TAGS = ("pubDate", "date", "issued", "published", "updated")


def local_name(tag: str) -> str:
    """'{http://purl.org/rss/1.0/}item' -> 'item'"""
    return tag.rsplit("}", 1)[-1]


def child_text(element: ElementTree.Element, name: str) -> str | None:
    """Namespace'i yok sayarak çocuk etiketin metnini döner."""
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip() or None
    return None


def parse_date(raw: str | None) -> str | None:
    """RFC 822 ('Mon, 31 Aug 26 12:00:00 +0000') veya ISO 8601 tarihini ISO'ya çevirir."""
    if not raw:
        return None

    try:
        return parsedate_to_datetime(raw).isoformat()
    except (TypeError, ValueError):
        pass

    try:
        return datetime.fromisoformat(raw).isoformat()
    except ValueError:
        logger.warning("Tarih ayrıştırılamadı: %r", raw)
        return None


def parse_feed(xml: str) -> list[dict[str, str | None]]:
    """Feed'deki item'ları döner. Boş feed `ParseError` sayılır — kaynak hep dolu olmalı."""
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise ParseError(f"Feed geçerli XML değil: {exc}") from exc

    items = []
    for element in root.iter():
        if local_name(element.tag) != "item":
            continue

        link = child_text(element, "link")
        title = child_text(element, "title")
        if not link or not title:
            logger.warning("Başlık/link'i olmayan feed item'ı atlandı: %r", link or title)
            continue

        published_at = None
        for tag in DATE_TAGS:
            published_at = parse_date(child_text(element, tag))
            if published_at:
                break

        items.append(
            {
                "title": title,
                "link": link,
                "summary": child_text(element, "description"),
                "published_at": published_at,
            }
        )

    if not items:
        raise ParseError("Feed'de hiç geçerli item bulunamadı — format değişmiş olabilir.")
    return items
