# AdvCrawler

*[English](README.en.md)*

Güvenlik danışmanlığı (advisory) raporlarını ulusal CERT'ler ve vendor PSIRT'lerinden toplayan bir crawler. Kayıtlar SQLite'a yazılır, advisory'lerde geçen CVE'ler çıkarılıp ilişkilendirilir.

## Kaynaklar

7 kaynak RSS/RDF üzerinden takip ediliyor:

| Slug | Kaynak |
|---|---|
| `cisa` | CISA (ABD) — Alert, ICS Advisory, Cybersecurity Advisory |
| `cert-eu` | CERT-EU (AB) |
| `cert-fr-avis` / `cert-fr-alerte` | CERT-FR / ANSSI (Fransa) |
| `jvn` | JVN / JPCERT/CC (Japonya) |
| `msrc` | Microsoft MSRC |
| `cisco` | Cisco PSIRT |

Yeni kaynak eklemek [`crawler/sources.py`](crawler/sources.py)'a bir satır eklemektir. Kaynak araştırması: [`docs/sources.md`](docs/sources.md).

## Kurulum

Bağımlılık yönetimi [`uv`](https://docs.astral.sh/uv/) ile yapılıyor.

```bash
uv sync
```

## Kullanım

```bash
uv run advcrawler --list-sources     # kaynakları listele
uv run advcrawler --source cisa      # tek kaynak
uv run advcrawler --all              # tüm kaynaklar
```

Veri `data/advisories.db` (SQLite) dosyasına yazılır, git'e dahil edilmez. Başarılı çalıştırma 0, hata durumunda 1 çıkış kodu döner — zamanlanmış çalıştırmada (cron/CI) hata bu şekilde yakalanır. `--all` çalışırken bir kaynağın hatası diğerlerini durdurmaz.

İsteğe bağlı: `ADVCRAWLER_CONTACT` tanımlıysa User-Agent'a iletişim adresi eklenir.

## Şema

| Tablo | Amaç |
|---|---|
| `sources` | Kaynaklar (`cisa`, `cert-eu`, …) |
| `advisories` | Advisory kayıtları; `link` benzersiz (tekilleştirme anahtarı), `first_seen`/`last_seen` izlenir |
| `cves` + `advisory_cves` | Advisory başlık ve özetlerinden çıkarılan CVE'ler (çoka-çok) |
| `crawl_runs` | Her çalıştırmanın kaydı: durum, yeni kayıt sayısı, hata mesajı |

Tam DDL: [`crawler/schema.sql`](crawler/schema.sql). Şema değişiklikleri `PRAGMA user_version` tabanlı migrasyonlarla uygulanır ([`crawler/migrations.py`](crawler/migrations.py)) — mevcut veritabanları otomatik yükseltilir.

## Yol Haritası

Sıradaki işler, öncelik sırasıyla:

- **Tarihsel backfill** — CISA'nın HTML listesi 506 sayfa (~5060 advisory) ile RSS'in kapsamadığı arşivi taşıyor. Önkoşul: istekler arası gecikme, kaldığı yerden devam, ilerleme takibi.
- **Conditional GET** (ETag / If-Modified-Since) — her çalıştırmada tam indirmeyi önler; MSRC feed'i ~4500 item olduğu için belirgin kazanç.
- **Retry/backoff** — geçici ağ hataları şu an tüm kaynağı düşürüyor.
- **CISA KEV (JSON/CSV) ve ICS CSAF 2.0** — RSS'ten çok daha zengin, resmî makine-okunur kaynaklar.
- **USOM / Siber Güvenlik Başkanlığı** — SPA olduğu için headless browser gerekiyor.
- Vendor listesinin genişletilmesi (Fortinet, Palo Alto, VMware, Oracle, Adobe …).

Ayrıntı ve açık sorular: [`docs/sources.md`](docs/sources.md).

## Geliştirme

```bash
uv run --group dev pytest      # testler (ağ erişimi gerekmez, fixture'larla çalışır)
uv run --group dev ruff check .
```

## Yapı

```
crawler/
  cli.py           # komut satırı arayüzü
  pipeline.py      # kaynak çalıştırma akışı (fetch -> parse -> türet -> yaz)
  sources.py       # kaynak tanımları
  rss.py           # RSS 2.0 / RDF ayrıştırma (namespace'ten bağımsız)
  cve.py           # CVE kimliği çıkarma
  cisa.py          # CISA'ya özgü: kategori türetme + HTML scraper (backfill için)
  db.py            # SQLite kalıcılık
  migrations.py    # şema migrasyonları
  schema.sql       # tablo tanımları
  http_client.py   # ortak HTTP client (User-Agent)
  errors.py        # CrawlerError hiyerarşisi
tests/             # fixture'lar gerçek feed/HTML snapshot'ları
data/              # SQLite dosyası (git'e dahil değil)
docs/sources.md    # kaynak araştırması
```
