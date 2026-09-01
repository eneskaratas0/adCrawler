# AdvCrawler

*[English](README.en.md)*

Güvenlik danışmanlığı (advisory) raporlarını çeşitli kaynaklardan (ulusal CERT'ler, vendor PSIRT'ler) toplayan bir crawler.

## Durum

Proje erken aşamada. Şu ana kadar eklenenler:

- `crawler/http_client.py` — tüm kaynak fetcher'larının paylaştığı, tanımlayıcı bir `User-Agent` gönderen ortak `httpx` client.
- `crawler/cisa.py` — CISA (ABD) Cybersecurity Advisories için iki erişim yolu:
  - `fetch_feed()`: resmi RSS feed'i (`all.xml`) çeker.
  - `scrape_advisories()`: `https://www.cisa.gov/news-events/cybersecurity-advisories` sayfasını BeautifulSoup ile parse edip her advisory kartından başlık, link, tarih ve tip çıkarır.
- `crawler/storage.py` — kaynak-bağımsız JSON kalıcılık katmanı. Kayıtlar `link` alanına göre tekilleştirilerek birleştirilir, yani her çalıştırma üstüne yazmak yerine arşivi büyütür; `first_seen` (ilk görülme zamanı) korunur. Yazma işlemi atomiktir.

Araştırılan/planlanan kaynaklar için bkz. [`docs/sources.md`](docs/sources.md).

## Kurulum

Bağımlılık yönetimi [`uv`](https://docs.astral.sh/uv/) ile yapılıyor.

```bash
uv sync
```

## Kullanım

```bash
# CISA advisories sayfasını scrape et, sonuçları data/cisa.json'a yaz ve listele
uv run python -m crawler.cisa
```

Çıktı `data/cisa.json` dosyasına yazılır (git'e dahil edilmez). Her kayıt şu alanları içerir:

```json
{
  "title": "CISA Adds Two Known Exploited Vulnerabilities to Catalog",
  "link": "https://www.cisa.gov/news-events/alerts/2026/08/31/...",
  "date": "2026-08-31T12:00:00Z",
  "type": "Alert",
  "first_seen": "2026-09-01T09:20:08.906575+00:00"
}
```

## Yapı

```
crawler/
  http_client.py   # ortak HTTP client (User-Agent)
  cisa.py          # CISA RSS + HTML scraper
  storage.py       # JSON kalıcılık (merge + dedupe)
data/              # crawler çıktısı (git'e dahil değil)
docs/
  sources.md       # kaynak araştırması (RSS/API/scraping durumları)
```
