# Advisory Kaynakları

Bu dosya, crawler'ın izleyeceği kaynakları ve her birine nasıl erişileceğini (RSS/API/HTML scraping) belgeler. Araştırma tarihi: 2026-08-26.

## Ulusal CERT'ler

### USOM / Siber Güvenlik Başkanlığı (Türkiye)
- Durum: USOM hizmetleri `usom.gov.tr`'den `siberguvenlik.gov.tr`'ye taşınıyor. `.txt` formatı ile paylaşım 2026-06-01'de sona erecek, kurum API kullanımına yönlendiriyor.
- Güvenlik bildirimleri listesi: `https://siberguvenlik.gov.tr/guvenlik-bildirimleri` (ör. detay sayfası: `/guvenlik-bildirimleri/detay/tr-26-0210`)
- Sorun: Sayfa JS ile render ediliyor (SPA) — düz HTTP fetch içerik döndürmüyor, muhtemelen headless browser (Playwright/Puppeteer) gerekecek. Kurumun `siberguvenlik.gov.tr/api/` altında bir API'si olduğu belirtiliyor ama genel dokümantasyona bu araştırmada ulaşılamadı.
- Eski RSS (`usom.gov.tr/en/rss`) artık aktif görünmüyor, sayfa yönlendirme/duyuru içeriyor.
- **Aksiyon gerekiyor:** API dokümantasyonuna ulaşılıp ulaşılamayacağı netleşene kadar bu kaynak headless-browser scraping ile planlanacak.

### CISA (ABD)
- Durum: RSS akışları aktif ve çalışıyor (2026-09-01'de doğrulandı). Sayfa üzerinde görünür bir `<link>` reklamı yok ama Drupal `.xml` view endpoint'leri `application/rss+xml` ile 200 dönüyor; eski `/uscert/ncas/...` yolları bunlara 301 ile yönleniyor.
- Genel advisory listesi (HTML): `https://www.cisa.gov/news-events/cybersecurity-advisories`
- RSS feed'ler:
  - `https://www.cisa.gov/cybersecurity-advisories/all.xml` — Tüm CISA Advisories (en kapsamlı)
  - `https://www.cisa.gov/cybersecurity-advisories/cybersecurity-advisories.xml` — sadece Cybersecurity Advisories
  - `https://www.cisa.gov/cybersecurity-advisories/alerts.xml` — Alerts
  - `https://www.cisa.gov/rss.xml` — site geneli feed
- robots.txt'te bu yollara özel bir `Disallow` yok; User-Agent zorunlu değil ama iyi pratik olarak gönderiliyor (bkz. `crawler/http_client.py`).
- Known Exploited Vulnerabilities (KEV) katalogu: JSON/CSV olarak yayınlanıyor (makine-okunur, güvenilir).
- ICS/OT/Medical Device advisory'leri: OASIS CSAF 2.0 formatında (JSON, makine-okunur) yayınlanıyor.
- **Aksiyon gerekiyor:** Genel advisory'ler için `all.xml` RSS kullanılabilir; ayrıca KEV ve ICS/CSAF makine-okunur formatları öncelikli kaynak olarak değerlendirilebilir.

### CERT-EU (AB)
- RSS: `https://cert.europa.eu/publications/security-advisories-rss`
- Doğrudan kullanılabilir.

### CERT-FR / ANSSI (Fransa)
- Avis (advisory) RSS: `https://www.cert.ssi.gouv.fr/avis/feed/`
- Alerte (alert) RSS: `https://www.cert.ssi.gouv.fr/alerte/feed/`
- CTI RSS: `https://www.cert.ssi.gouv.fr/cti/feed/`
- IOC RSS: `https://www.cert.ssi.gouv.fr/ioc/feed/`
- Tüm içerik: `https://www.cert.ssi.gouv.fr/feed/`
- Doğrudan kullanılabilir.

### JPCERT/CC & JVN (Japonya)
- JVN RSS (İngilizce): `https://jvn.jp/en/rss/`
- JPCERT/CC advisory ve alert'leri de RSS ile yayınlıyor; İngilizce sayfa üzerinden doğrulanacak.

## Vendor Blog / PSIRT Kaynakları

### Microsoft MSRC
- RSS: `https://api.msrc.microsoft.com/update-guide/rss`
- Doğrudan kullanılabilir.

### Cisco PSIRT
- RSS feed'leri mevcut (kayıt gerektirmiyor): `https://sec.cloudapps.cisco.com/security/center/rss.x?i=44`
- Ayrıca openVuln API (programatik, daha zengin veri) mevcut — OAuth ile kimlik doğrulama gerekiyor.

### Diğer vendor'lar (Fortinet, Palo Alto, VMware, Oracle, Adobe, vb.)
- Henüz araştırılmadı — kullanıcı hangi vendor'ların öncelikli olduğunu belirledikçe eklenecek.

## Açık Sorular
1. USOM/Siber Güvenlik Başkanlığı için headless browser mı kullanılacak, yoksa API dokümantasyonu bulununca ona mı geçilecek?
2. CISA için genel advisory'ler (AA-xxxx) HTML scraping ile mi takip edilecek, yoksa sadece KEV + ICS/CSAF (makine-okunur olanlar) ile mi yetinilecek?
3. Vendor blogları için öncelikli liste ne olacak (Microsoft ve Cisco doğrulandı; başka hangileri eklenecek)?
