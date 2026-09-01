"""Tüm kaynak fetcher'larının paylaştığı, kimliğini belirten bir User-Agent gönderen HTTP client."""

import httpx

USER_AGENT = "AdvCrawler/0.1 (Security Advisory Aggregator; contact: set via ADVCRAWLER_CONTACT env var)"


def get_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=15.0,
    )
