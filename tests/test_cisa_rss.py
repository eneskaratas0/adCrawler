"""Faz 2: RSS yolu, kategori türetme ve CVE çıkarımı."""

import pytest

from crawler import cisa, db, pipeline, sources
from crawler.cve import extract_cves
from crawler.errors import ParseError


class TestDeriveCategory:
    def test_alert(self):
        link = "https://www.cisa.gov/news-events/alerts/2026/08/31/cisa-adds-two-kev"
        assert cisa.derive_category(link) == ("Alert", None)

    def test_ics_advisory_kodu_buyuk_harfe_cevrilir(self):
        link = "https://www.cisa.gov/news-events/ics-advisories/icsa-26-239-05"
        assert cisa.derive_category(link) == ("ICS Advisory", "ICSA-26-239-05")

    def test_cybersecurity_advisory(self):
        link = "https://www.cisa.gov/news-events/cybersecurity-advisories/aa26-237a"
        assert cisa.derive_category(link) == ("Cybersecurity Advisory", "AA26-237A")

    def test_resource(self):
        link = "https://www.cisa.gov/resources-tools/resources/cisa-vulnerability-review"
        assert cisa.derive_category(link) == ("Resource", None)

    def test_taninmayan_yol(self):
        assert cisa.derive_category("https://www.cisa.gov/") == (None, None)


class TestExtractCves:
    def test_html_kacisli_metinden_cikarir(self):
        summary = 'href=&quot;...id=CVE-2026-81578&quot;&gt;&lt;u&gt;CVE-2026-81578&lt;/u&gt;'
        assert extract_cves(summary) == ["CVE-2026-81578"]

    def test_birden_fazla_ve_mukerrersiz(self):
        summary = "CVE-2026-1111 ve CVE-2026-2222, tekrar CVE-2026-1111"
        assert extract_cves(summary) == ["CVE-2026-1111", "CVE-2026-2222"]

    def test_kucuk_harf_buyuge_cevrilir(self):
        assert extract_cves("cve-2026-1234") == ["CVE-2026-1234"]

    def test_cve_yoksa_bos_liste(self):
        assert extract_cves("hiç CVE yok") == []
        assert extract_cves(None) == []


class TestFetchAdvisories:
    def test_feed_uzerinden_kayitlari_uretir(self, monkeypatch, cisa_feed_xml):
        records = pipeline.build_records(sources.BY_SLUG["cisa"], cisa_feed_xml)

        assert len(records) == 30
        assert all(r["title"] and r["link"] for r in records)

    def test_ics_advisoryleri_kapsar(self, monkeypatch, cisa_feed_xml):
        """HTML listeleme sayfasında hiç ICS advisory'si yok; RSS'te çoğunluk onlar."""
        records = pipeline.build_records(sources.BY_SLUG["cisa"], cisa_feed_xml)
        ics = [r for r in records if r["category"] == "ICS Advisory"]

        assert len(ics) == 17
        assert all(r["advisory_code"] for r in ics)

    def test_feed_cve_iceriyor(self, monkeypatch, cisa_feed_xml):
        records = pipeline.build_records(sources.BY_SLUG["cisa"], cisa_feed_xml)
        all_cves = {cve for r in records for cve in extract_cves(r["summary"])}

        assert len(all_cves) == 65


class TestRunSource:
    """`pipeline.run_source` uçtan uca: fetch -> parse -> türet -> yaz."""

    @pytest.fixture
    def conn(self, tmp_path):
        connection = db.connect(tmp_path / "t.db")
        yield connection
        connection.close()

    @pytest.fixture
    def cisa_source(self, monkeypatch, cisa_feed_xml):
        monkeypatch.setattr(pipeline, "fetch_text", lambda url: cisa_feed_xml)
        return sources.BY_SLUG["cisa"]

    def test_advisory_ve_cve_baglantilari_yazilir(self, conn, cisa_source):
        new_count, cve_links = pipeline.run_source(conn, cisa_source)

        assert new_count == 30
        assert cve_links > 0
        assert conn.execute("SELECT COUNT(*) FROM cves").fetchone()[0] == 65

    def test_ikinci_calistirmada_mukerrer_kayit_ve_bag_olusmaz(self, conn, cisa_source):
        pipeline.run_source(conn, cisa_source)

        new_count, cve_links = pipeline.run_source(conn, cisa_source)

        assert new_count == 0
        assert cve_links == 0

    def test_basarili_calistirma_kaydedilir(self, conn, cisa_source):
        pipeline.run_source(conn, cisa_source)

        row = conn.execute("SELECT status, new_count FROM crawl_runs").fetchone()
        assert row["status"] == "success"
        assert row["new_count"] == 30

    def test_hata_crawl_runs_a_yazilir_ve_yukseltilir(self, conn, monkeypatch):
        monkeypatch.setattr(pipeline, "fetch_text", lambda url: "<html>yeni tasarım</html>")

        with pytest.raises(ParseError):
            pipeline.run_source(conn, sources.BY_SLUG["cisa"])

        row = conn.execute("SELECT status, error_message FROM crawl_runs").fetchone()
        assert row["status"] == "error"
        assert row["error_message"]
