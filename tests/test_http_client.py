from crawler.http_client import build_user_agent


class TestBuildUserAgent:
    def test_env_var_yoksa_contact_hic_gecmez(self, monkeypatch):
        monkeypatch.delenv("ADVCRAWLER_CONTACT", raising=False)

        ua = build_user_agent()

        assert ua == "AdvCrawler/0.1 (Security Advisory Aggregator)"
        assert "ADVCRAWLER_CONTACT" not in ua

    def test_env_var_varsa_eklenir(self, monkeypatch):
        monkeypatch.setenv("ADVCRAWLER_CONTACT", "enes@example.com")

        assert build_user_agent() == (
            "AdvCrawler/0.1 (Security Advisory Aggregator; +enes@example.com)"
        )

    def test_bosluktan_ibaret_deger_yok_sayilir(self, monkeypatch):
        monkeypatch.setenv("ADVCRAWLER_CONTACT", "   ")

        assert build_user_agent() == "AdvCrawler/0.1 (Security Advisory Aggregator)"
