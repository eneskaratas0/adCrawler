# AdvCrawler

*[English](README.en.md)*

Güvenlik danışmanlığı (advisory) raporlarını çeşitli kaynaklardan (ulusal CERT'ler, vendor PSIRT'ler) toplayan bir crawler.

## Durum

Proje erken aşamada. Şu ana kadar eklenenler:

- `crawler/http_client.py` — tüm kaynak fetcher'larının paylaştığı, tanımlayıcı bir `User-Agent` gönderen ortak `httpx` client.
- `crawler/cisa.py` — CISA (ABD) Cybersecurity Advisories için iki erişim yolu:
  - `fetch_feed()`: resmi RSS feed'i (`all.xml`) çeker.
  - `scrape_advisories()`: `https://www.cisa.gov/news-events/cybersecurity-advisories` sayfasını BeautifulSoup ile parse edip her advisory kartından başlık ve link çıkarır.

Araştırılan/planlanan kaynaklar için bkz. [`docs/sources.md`](docs/sources.md).

## Kurulum

Bağımlılık yönetimi [`uv`](https://docs.astral.sh/uv/) ile yapılıyor.

```bash
uv sync
```

## Kullanım

```bash
# CISA advisories sayfasını scrape edip başlık + link listele
uv run python -m crawler.cisa
```

## Yapı

```
crawler/
  http_client.py   # ortak HTTP client (User-Agent)
  cisa.py          # CISA RSS + HTML scraper
docs/
  sources.md       # kaynak araştırması (RSS/API/scraping durumları)
```
