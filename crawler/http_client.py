"""Tüm kaynak fetcher'larının paylaştığı, kimliğini belirten bir User-Agent gönderen HTTP client."""

import httpx

from crawler.errors import FetchError

USER_AGENT = "AdvCrawler/0.1 (Security Advisory Aggregator; contact: set via ADVCRAWLER_CONTACT env var)"


def get_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
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
