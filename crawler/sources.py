"""Kaynak tanımları.

`docs/sources.md`'de araştırılan kaynakların hepsi RSS yayınlıyor, bu yüzden yeni kaynak
eklemek buraya bir satır eklemek demek — kod yazmak değil. Kaynağa özgü davranış gerekirse
`derive_category` ile verilir.
"""

from collections.abc import Callable
from dataclasses import dataclass

from crawler import cisa


@dataclass(frozen=True)
class Source:
    slug: str
    name: str
    feed_url: str
    # Advisory URL'inden (kategori, advisory_kodu) türetir. Yoksa ikisi de None kalır.
    derive_category: Callable[[str], tuple[str | None, str | None]] | None = None


SOURCES = [
    Source(
        slug=cisa.SOURCE_SLUG,
        name=cisa.SOURCE_NAME,
        feed_url=cisa.FEED_URL,
        derive_category=cisa.derive_category,
    ),
    Source(
        slug="cert-eu",
        name="CERT-EU (AB)",
        feed_url="https://cert.europa.eu/publications/security-advisories-rss",
    ),
    Source(
        slug="cert-fr-avis",
        name="CERT-FR / ANSSI — Avis",
        feed_url="https://www.cert.ssi.gouv.fr/avis/feed/",
    ),
    Source(
        slug="cert-fr-alerte",
        name="CERT-FR / ANSSI — Alerte",
        feed_url="https://www.cert.ssi.gouv.fr/alerte/feed/",
    ),
    Source(
        slug="jvn",
        name="JVN / JPCERT/CC (Japonya)",
        # RSS 1.0/RDF formatında. /en/rss/ (sondaki slash) HTML sayfası döndürür.
        feed_url="https://jvn.jp/en/rss/jvn.rdf",
    ),
    Source(
        slug="msrc",
        name="Microsoft MSRC",
        feed_url="https://api.msrc.microsoft.com/update-guide/rss",
    ),
    Source(
        slug="cisco",
        name="Cisco PSIRT",
        # rss.x?i=44 artık HTML sayfası döndürüyor; gerçek feed bu adreste.
        feed_url="https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml",
    ),
]

BY_SLUG = {source.slug: source for source in SOURCES}
