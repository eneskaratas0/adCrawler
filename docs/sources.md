# Advisory Kaynakları

Crawler'ın izlediği kaynaklar ve her birine nasıl erişildiği. İlk araştırma: 2026-08-26, canlı doğrulama: 2026-09-01.

Kod tarafındaki tanımlar: [`crawler/sources.py`](../crawler/sources.py).

## Uygulanan Kaynaklar

Hepsi RSS/RDF üzerinden, `pipeline.run_source()` ile aynı akıştan geçer.

| Slug | Kaynak | Feed | Item |
|---|---|---|---|
| `cisa` | CISA (ABD) | `https://www.cisa.gov/cybersecurity-advisories/all.xml` | 30 |
| `cert-eu` | CERT-EU (AB) | `https://cert.europa.eu/publications/security-advisories-rss` | 10 |
| `cert-fr-avis` | CERT-FR / ANSSI — Avis | `https://www.cert.ssi.gouv.fr/avis/feed/` | 40 |
| `cert-fr-alerte` | CERT-FR / ANSSI — Alerte | `https://www.cert.ssi.gouv.fr/alerte/feed/` | 40 |
| `jvn` | JVN / JPCERT/CC (Japonya) | `https://jvn.jp/en/rss/jvn.rdf` | 20 |
| `msrc` | Microsoft MSRC | `https://api.msrc.microsoft.com/update-guide/rss` | ~4500 |
| `cisco` | Cisco PSIRT | `https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml` | 50 |

### Format ve içerik notları
- **JVN, RSS 2.0 değil RSS 1.0/RDF** yayınlıyor: namespace'li etiketler ve `pubDate` yerine `dc:date` (ISO 8601). `rss.parse_feed()` bu yüzden namespace'ten bağımsız çalışır ve iki tarih formatını da okur.
- **CISA `pubDate`'i 2 haneli yıl** kullanıyor (`Mon, 31 Aug 26 12:00:00 +0000`); stdlib `email.utils.parsedate_to_datetime` doğru çözüyor.
- **MSRC CVE'yi başlıkta taşıyor**, açıklamada değil (`CVE-2026-64899 Microsoft Office …`). CVE çıkarımı bu yüzden başlık + özet üzerinden yapılır.
- **JVN feed'inde CVE geçmiyor** (JVN# kimlikleri kullanılıyor); bu kaynak için CVE bağı kurulamıyor.
- CISA'da kategori ve advisory kodu URL yolundan türetiliyor (`cisa.derive_category`): `/alerts/…` → Alert, `/ics-advisories/icsa-26-239-05` → ICS Advisory + `ICSA-26-239-05`, `/cybersecurity-advisories/aa26-237a` → Cybersecurity Advisory + `AA26-237A`.

### Düzeltilen ölü URL'ler
İlk araştırmada kaydedilen iki adres artık RSS değil HTML sayfası döndürüyor (2026-09-01'de tespit edildi):

| Eski (ölü) | Yeni |
|---|---|
| `https://jvn.jp/en/rss/` | `https://jvn.jp/en/rss/jvn.rdf` |
| `https://sec.cloudapps.cisco.com/security/center/rss.x?i=44` | `https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml` |

### CISA — ek erişim yolları
- HTML listeleme sayfası: `https://www.cisa.gov/news-events/cybersecurity-advisories`. **506 sayfa** (~5060 advisory) ile tarihsel arşivi kapsıyor ama RSS'te olan ICS advisory'lerini göstermiyor. `cisa.scrape_advisories()` bu yolu backfill için koruyor.
- Diğer feed'ler: `cybersecurity-advisories.xml` (yalnız CSA), `alerts.xml` (yalnız Alert), `rss.xml` (site geneli). `all.xml` bunların hepsini kapsadığı için o seçildi.
- robots.txt'te bu yollara özel `Disallow` yok. User-Agent zorunlu değil ama gönderiliyor (`crawler/http_client.py`; `ADVCRAWLER_CONTACT` ile iletişim adresi eklenebilir).

## Araştırılmış, Henüz Uygulanmamış

### USOM / Siber Güvenlik Başkanlığı (Türkiye)
- USOM hizmetleri `usom.gov.tr`'den `siberguvenlik.gov.tr`'ye taşınıyor; `.txt` paylaşımı 2026-06-01'de sona eriyor, kurum API'ye yönlendiriyor.
- Bildirim listesi: `https://siberguvenlik.gov.tr/guvenlik-bildirimleri` (detay: `/guvenlik-bildirimleri/detay/tr-26-0210`)
- **Engel:** Sayfa SPA — düz HTTP fetch içerik döndürmüyor, headless browser (Playwright/Puppeteer) gerekiyor. `siberguvenlik.gov.tr/api/` altında bir API olduğu belirtiliyor ama dokümantasyona ulaşılamadı.
- Eski RSS (`usom.gov.tr/en/rss`) aktif değil.

### CISA makine-okunur kaynaklar
- **KEV katalogu** (Known Exploited Vulnerabilities): JSON/CSV. Aktif istismar edilen zafiyetler için birincil kaynak olabilir.
- **ICS/OT/Medical Device CSAF 2.0**: JSON, RSS'e göre çok daha zengin (etkilenen ürünler, sürümler, CVSS).

### CERT-FR ek feed'leri
`cti/feed/` (tehdit istihbaratı), `ioc/feed/` (IOC), `feed/` (tüm içerik) — advisory dışı içerik oldukları için şimdilik alınmadı.

### Cisco openVuln API
RSS'ten zengin veri veriyor (CVSS, etkilenen sürümler) ama OAuth kimlik doğrulaması gerekiyor.

### Diğer vendor'lar
Fortinet, Palo Alto, VMware, Oracle, Adobe vb. henüz araştırılmadı — öncelik belirlendikçe eklenecek.

## Açık Sorular
1. USOM için headless browser mı kurulacak, yoksa API dokümantasyonu bulunana kadar beklenecek mi?
2. ~~CISA advisory'leri HTML scraping ile mi takip edilecek?~~ **Cevaplandı (2026-09-01):** `all.xml` RSS birincil yol oldu — HTML'den 3 kat fazla kayıt veriyor, ICS advisory'lerini de kapsıyor ve CSS seçicilerine bağımlı değil. HTML scraper yalnızca tarihsel backfill için duruyor.
3. Vendor listesi ne kadar genişletilecek (Microsoft ve Cisco uygulandı)?
4. Tarihsel backfill (CISA'nın 506 sayfası) yapılacak mı? Önkoşul: istekler arası gecikme, kaldığı yerden devam, ilerleme takibi.
