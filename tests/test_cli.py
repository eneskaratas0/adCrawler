import pytest

from crawler import cli, pipeline, sources
from crawler.errors import FetchError


class TestListSources:
    def test_tum_kaynaklari_yazar(self, capsys):
        exit_code = cli.main(["--list-sources"])

        out = capsys.readouterr().out
        assert exit_code == 0
        for source in sources.SOURCES:
            assert source.slug in out


class TestArgumentValidation:
    def test_bilinmeyen_kaynak_2_doner(self, tmp_path):
        assert cli.main(["--source", "yok-boyle-bir-kaynak", "--db", str(tmp_path / "t.db")]) == 2

    def test_arguman_verilmezse_hata(self):
        with pytest.raises(SystemExit):
            cli.main([])


class TestCveFromTitle:
    def test_baslikta_gecen_cve_baglanir(self, tmp_path, monkeypatch):
        """MSRC advisory'leri CVE'yi başlıkta taşıyor, açıklamada değil."""
        feed = """
        <rss><channel><item>
          <title>CVE-2026-64899 Microsoft Office Information Disclosure Vulnerability</title>
          <link>https://msrc.microsoft.com/update-guide/vulnerability/CVE-2026-64899</link>
          <description>Out-of-bounds read in Microsoft Office.</description>
        </item></channel></rss>
        """
        monkeypatch.setattr(pipeline, "fetch_text", lambda url: feed)
        db_path = tmp_path / "t.db"

        cli.main(["--source", "msrc", "--db", str(db_path)])

        import sqlite3

        conn = sqlite3.connect(db_path)
        cves = [row[0] for row in conn.execute("SELECT cve_id FROM cves")]
        conn.close()

        assert cves == ["CVE-2026-64899"]


class TestRun:
    def test_tek_kaynak_basarili(self, tmp_path, monkeypatch, cisa_feed_xml):
        monkeypatch.setattr(pipeline, "fetch_text", lambda url: cisa_feed_xml)

        exit_code = cli.main(["--source", "cisa", "--db", str(tmp_path / "t.db")])

        assert exit_code == 0

    def test_kaynak_hatasi_1_doner(self, tmp_path, monkeypatch):
        def boom(url):
            raise FetchError("ağ yok")

        monkeypatch.setattr(pipeline, "fetch_text", boom)

        exit_code = cli.main(["--source", "cisa", "--db", str(tmp_path / "t.db")])

        assert exit_code == 1

    def test_bir_kaynak_patlasa_da_digerleri_calisir(
        self, tmp_path, monkeypatch, cisa_feed_xml, caplog
    ):
        """--all'da tek bir kaynağın hatası akışı durdurmamalı, ama çıkış kodu 1 olmalı."""

        def selective(url):
            if "cisa.gov" in url:
                raise FetchError("cisa erişilemiyor")
            return cisa_feed_xml

        monkeypatch.setattr(pipeline, "fetch_text", selective)
        db_path = tmp_path / "t.db"

        exit_code = cli.main(["--all", "--db", str(db_path)])

        assert exit_code == 1
        # Diğer kaynaklar yine de yazılmış olmalı.
        import sqlite3

        conn = sqlite3.connect(db_path)
        runs = conn.execute("SELECT COUNT(*) FROM crawl_runs").fetchone()[0]
        success = conn.execute(
            "SELECT COUNT(*) FROM crawl_runs WHERE status = 'success'"
        ).fetchone()[0]
        conn.close()

        assert runs == len(sources.SOURCES)
        assert success == len(sources.SOURCES) - 1
