import pytest

from crawler import cisa
from crawler.errors import ParseError


class TestSplitMeta:
    def test_kategori_ve_kod_ayrilir(self):
        assert cisa.split_meta("Cybersecurity Advisory | AA26-237A") == (
            "Cybersecurity Advisory",
            "AA26-237A",
        )

    def test_ayirac_yoksa_sadece_kategori(self):
        assert cisa.split_meta("Alert") == ("Alert", None)

    def test_advisory_kodu_olmayan_ikinci_parca_elenir(self):
        # 'resource' bir içerik etiketi, advisory kodu değil.
        assert cisa.split_meta("Publication | resource") == ("Publication", None)

    def test_bos_deger(self):
        assert cisa.split_meta(None) == (None, None)
        assert cisa.split_meta("") == (None, None)


class TestScrapeAdvisories:
    def test_fixture_uzerinden_kayitlari_cikarir(self, monkeypatch, cisa_list_html):
        monkeypatch.setattr(cisa, "fetch_text", lambda url: cisa_list_html)

        records = cisa.scrape_advisories()

        assert len(records) == 10
        assert all(r["link"].startswith("https://www.cisa.gov/") for r in records)
        assert all(r["title"] for r in records)

    def test_alanlar_dogru_doldurulur(self, monkeypatch, cisa_list_html):
        monkeypatch.setattr(cisa, "fetch_text", lambda url: cisa_list_html)

        first = cisa.scrape_advisories()[0]

        assert first["title"] == "CISA Adds Two Known Exploited Vulnerabilities to Catalog"
        assert first["published_at"] == "2026-08-31T12:00:00Z"
        assert first["category"] == "Alert"
        assert first["advisory_code"] is None

    def test_advisory_kodu_olan_kayit(self, monkeypatch, cisa_list_html):
        monkeypatch.setattr(cisa, "fetch_text", lambda url: cisa_list_html)

        records = cisa.scrape_advisories()
        coded = [r for r in records if r["advisory_code"]]

        assert len(coded) == 1
        assert coded[0]["advisory_code"] == "AA26-237A"
        assert coded[0]["category"] == "Cybersecurity Advisory"

    def test_kart_bulunamazsa_parse_error(self, monkeypatch):
        monkeypatch.setattr(
            cisa, "fetch_text", lambda url: "<html><body>yeni tasarım</body></html>"
        )

        with pytest.raises(ParseError, match="hiç kart bulunamadı"):
            cisa.scrape_advisories()

    def test_kart_var_ama_baslik_secicisi_bozuksa_parse_error(self, monkeypatch):
        monkeypatch.setattr(
            cisa, "fetch_text", lambda url: "<article class='c-teaser'><div>boş</div></article>"
        )

        with pytest.raises(ParseError, match="hiçbirinden başlık/link çıkarılamadı"):
            cisa.scrape_advisories()
