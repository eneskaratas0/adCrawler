import pytest

from crawler import rss
from crawler.errors import ParseError


class TestParseDate:
    def test_iki_haneli_yil_dogru_cozulur(self):
        # CISA feed'i RFC 822'yi 2 haneli yılla yayınlıyor.
        assert rss.parse_date("Mon, 31 Aug 26 12:00:00 +0000") == "2026-08-31T12:00:00+00:00"

    def test_dort_haneli_yil(self):
        assert rss.parse_date("Mon, 31 Aug 2026 12:00:00 +0000") == "2026-08-31T12:00:00+00:00"

    def test_bos_ve_bozuk_deger_none_doner(self):
        assert rss.parse_date(None) is None
        assert rss.parse_date("") is None
        assert rss.parse_date("bu bir tarih değil") is None


class TestParseFeed:
    def test_gercek_feed_item_sayisi(self, cisa_feed_xml):
        items = rss.parse_feed(cisa_feed_xml)

        assert len(items) == 30

    def test_item_alanlari(self, cisa_feed_xml):
        first = rss.parse_feed(cisa_feed_xml)[0]

        assert first["title"] == "CISA Adds Two Known Exploited Vulnerabilities to Catalog"
        assert first["link"].startswith("https://www.cisa.gov/")
        assert first["published_at"] == "2026-08-31T12:00:00+00:00"
        assert first["summary"]

    def test_bozuk_xml_parse_error(self):
        with pytest.raises(ParseError, match="geçerli XML değil"):
            rss.parse_feed("<rss><channel><item>kapanmamış")

    def test_bos_feed_parse_error(self):
        with pytest.raises(ParseError, match="hiç geçerli item bulunamadı"):
            rss.parse_feed("<rss><channel></channel></rss>")

    def test_baslik_veya_linki_olmayan_item_atlanir(self):
        xml = """
        <rss><channel>
          <item><title>Geçerli</title><link>https://example.com/a</link></item>
          <item><title>Linksiz</title></item>
          <item><link>https://example.com/b</link></item>
        </channel></rss>
        """
        items = rss.parse_feed(xml)

        assert len(items) == 1
        assert items[0]["title"] == "Geçerli"
