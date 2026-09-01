# AdvCrawler

## Amaç
Güvenlik danışmanlığı (advisory) raporlarını ulusal CERT'ler ve vendor PSIRT'lerinden toplayan bir crawler. Kayıtlar SQLite'a yazılır, advisory'lerde geçen CVE'ler çıkarılıp ilişkilendirilir.

## Teknoloji Yığını
- Python ≥3.11, bağımlılık yönetimi `uv`
- `httpx` (HTTP), `beautifulsoup4` (yalnızca CISA HTML scraper'ı için)
- Kalıcılık: stdlib `sqlite3` — **ORM kullanılmıyor**
- RSS/RDF ayrıştırma: stdlib `xml.etree` — `feedparser` bağımlılığı bilinçli olarak eklenmedi
- Test: `pytest`, lint: `ruff` (satır uzunluğu 100)

## Mimari
Akış: `cli.py` → `pipeline.run_source()` → `http_client.fetch_text()` → `rss.parse_feed()` → kategori/CVE türetme → `db` upsert → `crawl_runs` kaydı.

- **Yeni kaynak eklemek** = `crawler/sources.py`'a bir `Source` satırı. Kaynağa özgü davranış gerekiyorsa `derive_category` fonksiyonu verilir (bkz. `cisa.derive_category`).
- **Kaynak modülleri saf olmalı** — `cisa.py` yalnızca CISA'ya özgü ayrıştırma içerir; fetch/persist/CLI sorumluluğu almaz.
- **Tekilleştirme anahtarı `link`** (UNIQUE). Upsert'te `first_seen` korunur, `last_seen` güncellenir.
- **Şema değişikliği** `schema.sql` + `migrations.py`'a birlikte yazılır: yeni DB `schema.sql`'den kurulur, mevcut DB `PRAGMA user_version` migrasyonuyla yükseltilir. `MIGRATIONS` listesine yalnızca **sona** ekleme yapılır.

## Konvansiyonlar
- Kod içi yorumlar, log mesajları ve docstring'ler Türkçe.
- Beklenen hatalar `CrawlerError` alt tiplerine (`FetchError`, `ParseError`, `StorageError`) sarılır; beklenmeyenler traceback vermeli.
- **Boş sonuç hatadır.** Feed/sayfa parse edilip 0 kayıt çıkıyorsa `ParseError` fırlatılır — sessiz veri kaybı, "yeni advisory yok" gibi görünen en tehlikeli hata.
- Çıkış kodu: başarı 0, hata 1 (cron/CI yakalayabilsin). `--all`'da bir kaynağın hatası diğerlerini durdurmaz.
- Testler ağ erişimi gerektirmez; `tests/fixtures/` altındaki gerçek feed/HTML snapshot'ları kullanılır.

## Komutlar
```bash
uv run advcrawler --all              # tüm kaynakları çalıştır
uv run advcrawler --source cisa      # tek kaynak
uv run advcrawler --list-sources
uv run --group dev pytest
uv run --group dev ruff check .
```

## Geliştirme Süreci
Geliştirme adımları kullanıcı tarafından sırayla bildirilir. Yol haritası ve bilinen eksikler için `docs/sources.md` ve README'lerin backlog bölümlerine bakılır.
