# AdvCrawler

*[English](README.en.md)*

Güvenlik danışmanlığı (advisory) raporlarını çeşitli kaynaklardan (ulusal CERT'ler, vendor PSIRT'ler) toplayan bir crawler.

## Durum

Proje erken aşamada. Şu ana kadar eklenenler:

- `crawler/http_client.py` — tüm kaynak fetcher'larının paylaştığı, tanımlayıcı bir `User-Agent` gönderen ortak `httpx` client.
- `crawler/cisa.py` — CISA (ABD) Cybersecurity Advisories için iki erişim yolu:
  - `fetch_feed()`: resmi RSS feed'i (`all.xml`) çeker.
  - `scrape_advisories()`: `https://www.cisa.gov/news-events/cybersecurity-advisories` sayfasını BeautifulSoup ile parse edip her advisory kartından başlık, link, tarih ve tip çıkarır.
- `crawler/db.py` + `crawler/schema.sql` — SQLite kalıcılık katmanı (stdlib `sqlite3`, ORM yok). Kayıtlar `link` alanına göre upsert edilir: her çalıştırma üstüne yazmak yerine arşivi büyütür, `first_seen` korunur, `last_seen` güncellenir.
- `crawler/errors.py` — `CrawlerError` hiyerarşisi (`FetchError`, `ParseError`, `StorageError`). Beklenen hatalar net mesaja ve çıkış kodu 1'e dönüşür; beklenmeyenler traceback verir.

Araştırılan/planlanan kaynaklar için bkz. [`docs/sources.md`](docs/sources.md).

## Kurulum

Bağımlılık yönetimi [`uv`](https://docs.astral.sh/uv/) ile yapılıyor.

```bash
uv sync
```

## Kullanım

```bash
# CISA advisories sayfasını scrape et, data/advisories.db'ye yaz ve listele
uv run python -m crawler.cisa
```

Veri `data/advisories.db` (SQLite) dosyasına yazılır, git'e dahil edilmez. Başarılı çalıştırma 0, hata durumunda 1 çıkış kodu döner — zamanlanmış çalıştırmada (cron/CI) hata bu şekilde yakalanabilir.

Eski `data/cisa.json` verisini taşımak için (tek seferlik):

```bash
uv run python -m scripts.migrate_json_to_sqlite
```

## Şema

| Tablo | Amaç |
|---|---|
| `sources` | Kaynaklar (`cisa`, `cert-eu`, …) — çok kaynaklı yapı için |
| `advisories` | Advisory kayıtları; `link` benzersiz (tekilleştirme anahtarı), `first_seen`/`last_seen` izlenir |
| `cves` + `advisory_cves` | CVE'ler ve advisory ilişkisi (çoka-çok). Şema hazır, doldurma detay sayfası parse edilince yapılacak |
| `crawl_runs` | Her çalıştırmanın kaydı: durum, yeni kayıt sayısı, hata mesajı |

Tam DDL: [`crawler/schema.sql`](crawler/schema.sql)

## Yapı

```
crawler/
  http_client.py   # ortak HTTP client (User-Agent) + fetch_text
  cisa.py          # CISA RSS + HTML scraper
  db.py            # SQLite kalıcılık (upsert, çalıştırma kaydı)
  schema.sql       # tablo tanımları
  errors.py        # CrawlerError hiyerarşisi
scripts/
  migrate_json_to_sqlite.py
data/              # crawler çıktısı, SQLite dosyası (git'e dahil değil)
docs/
  sources.md       # kaynak araştırması (RSS/API/scraping durumları)
```
