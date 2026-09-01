"""Crawler'a özgü hata tipleri. Beklenen hatalar bunlara sarılır, beklenmeyenler olduğu gibi yükselir."""


class CrawlerError(Exception):
    """Tüm crawler hatalarının ortak atası."""


class FetchError(CrawlerError):
    """Ağ hatası veya beklenmeyen HTTP durumu."""


class ParseError(CrawlerError):
    """Sayfa çekildi ama beklenen yapı bulunamadı (muhtemelen kaynak sitede değişiklik)."""


class StorageError(CrawlerError):
    """JSON dosyası okunamadı, bozuk, veya yazılamadı."""
