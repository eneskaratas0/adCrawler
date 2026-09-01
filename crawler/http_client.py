"""Tüm kaynak fetcher'larının paylaştığı, kimliğini belirten bir User-Agent gönderen HTTP client."""

import os

import httpx

from crawler.errors import FetchError

VERSION = "0.1"


def build_user_agent() -> str:
    """ADVCRAWLER_CONTACT tanımlıysa iletişim bilgisini ekler, yoksa hiç bahsetmez."""
    contact = os.environ.get("ADVCRAWLER_CONTACT", "").strip()
    contact_part = f"; +{contact}" if contact else ""
    return f"AdvCrawler/{VERSION} (Security Advisory Aggregator{contact_part})"


def get_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": build_user_agent()},
        follow_redirects=True,
        timeout=15.0,
    )


def fetch_text(url: str) -> str:
    """URL'yi çeker; ağ ve HTTP hatalarını `FetchError`'a çevirir."""
    try:
        with get_client() as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as exc:
        raise FetchError(
            f"{url} beklenmeyen HTTP durumu döndürdü: {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        raise FetchError(f"{url} çekilemedi: {exc}") from exc
