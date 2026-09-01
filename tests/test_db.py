import pytest

from crawler import db


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "test.db")
    yield connection
    connection.close()


@pytest.fixture
def source_id(conn):
    return db.get_or_create_source(conn, "test", "Test Kaynağı", "https://example.com")


def make_record(link="https://example.com/a1", title="Advisory 1"):
    return {
        "link": link,
        "title": title,
        "published_at": "2026-08-31T12:00:00Z",
        "category": "Alert",
        "advisory_code": None,
    }


class TestGetOrCreateSource:
    def test_ayni_slug_ayni_id_doner(self, conn):
        first = db.get_or_create_source(conn, "cisa", "CISA", "https://cisa.gov")
        second = db.get_or_create_source(conn, "cisa", "CISA", "https://cisa.gov")

        assert first == second

    def test_ad_ve_url_guncellenir(self, conn):
        db.get_or_create_source(conn, "cisa", "Eski Ad", "https://eski.example")
        db.get_or_create_source(conn, "cisa", "Yeni Ad", "https://yeni.example")

        row = conn.execute("SELECT name, url FROM sources WHERE slug = 'cisa'").fetchone()
        assert row["name"] == "Yeni Ad"
        assert row["url"] == "https://yeni.example"


class TestUpsertAdvisories:
    def test_yeni_kayitlari_ekler(self, conn, source_id):
        records = [make_record("https://example.com/a1"), make_record("https://example.com/a2")]

        new_count = db.upsert_advisories(conn, source_id, records)

        assert new_count == 2
        assert conn.execute("SELECT COUNT(*) FROM advisories").fetchone()[0] == 2

    def test_ikinci_calistirmada_mukerrer_eklemez(self, conn, source_id):
        records = [make_record()]
        db.upsert_advisories(conn, source_id, records)

        new_count = db.upsert_advisories(conn, source_id, records)

        assert new_count == 0
        assert conn.execute("SELECT COUNT(*) FROM advisories").fetchone()[0] == 1

    def test_first_seen_korunur_last_seen_guncellenir(self, conn, source_id):
        records = [make_record()]
        db.upsert_advisories(conn, source_id, records)
        before = conn.execute("SELECT first_seen, last_seen FROM advisories").fetchone()

        db.upsert_advisories(conn, source_id, records)
        after = conn.execute("SELECT first_seen, last_seen FROM advisories").fetchone()

        assert after["first_seen"] == before["first_seen"]
        assert after["last_seen"] > before["last_seen"]

    def test_baslik_degisirse_guncellenir(self, conn, source_id):
        db.upsert_advisories(conn, source_id, [make_record(title="Eski Başlık")])

        db.upsert_advisories(conn, source_id, [make_record(title="Düzeltilmiş Başlık")])

        title = conn.execute("SELECT title FROM advisories").fetchone()["title"]
        assert title == "Düzeltilmiş Başlık"


class TestCrawlRuns:
    def test_basarili_calistirma_kaydedilir(self, conn, source_id):
        run_id = db.start_run(conn, source_id)
        db.finish_run(conn, run_id, "success", new_count=5)

        row = conn.execute("SELECT * FROM crawl_runs WHERE id = ?", (run_id,)).fetchone()
        assert row["status"] == "success"
        assert row["new_count"] == 5
        assert row["error_message"] is None
        assert row["finished_at"] is not None

    def test_hata_mesaji_kaydedilir(self, conn, source_id):
        run_id = db.start_run(conn, source_id)
        db.finish_run(conn, run_id, "error", error_message="seçici bozuldu")

        row = conn.execute("SELECT * FROM crawl_runs WHERE id = ?", (run_id,)).fetchone()
        assert row["status"] == "error"
        assert row["error_message"] == "seçici bozuldu"
        assert row["new_count"] is None

    def test_yeni_calistirma_running_durumunda_baslar(self, conn, source_id):
        run_id = db.start_run(conn, source_id)

        row = conn.execute("SELECT * FROM crawl_runs WHERE id = ?", (run_id,)).fetchone()
        assert row["status"] == "running"
        assert row["finished_at"] is None
