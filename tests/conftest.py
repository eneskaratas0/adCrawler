from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cisa_list_html() -> str:
    """CISA advisories listeleme sayfasının gerçek bir kopyası (10 kart)."""
    return (FIXTURES / "cisa_list.html").read_text(encoding="utf-8")


@pytest.fixture
def cisa_feed_xml() -> str:
    """CISA all.xml RSS feed'inin gerçek bir kopyası (30 item)."""
    return (FIXTURES / "cisa_all.xml").read_text(encoding="utf-8")
