-- AdvCrawler şeması. Idempotent: her açılışta güvenle çalıştırılabilir.

CREATE TABLE IF NOT EXISTS sources (
    id         INTEGER PRIMARY KEY,
    slug       TEXT NOT NULL UNIQUE,          -- 'cisa', 'cert-eu', 'msrc'
    name       TEXT NOT NULL,                 -- 'CISA (ABD)'
    url        TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS advisories (
    id            INTEGER PRIMARY KEY,
    source_id     INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    link          TEXT NOT NULL UNIQUE,       -- tekilleştirme anahtarı
    title         TEXT NOT NULL,
    published_at  TEXT,                       -- ISO 8601, kaynağın bildirdiği tarih
    category      TEXT,                       -- 'Alert', 'Cybersecurity Advisory'
    advisory_code TEXT,                       -- 'AA26-237A' (varsa)
    summary       TEXT,                       -- feed description'ı (CVE'ler buradan çıkarılır)
    first_seen    TEXT NOT NULL,              -- crawler'ın ilk gördüğü an
    last_seen     TEXT NOT NULL               -- listede en son görüldüğü an
);

CREATE INDEX IF NOT EXISTS idx_advisories_source    ON advisories(source_id);
CREATE INDEX IF NOT EXISTS idx_advisories_published ON advisories(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_advisories_code      ON advisories(advisory_code);

-- CVE ilişkisi: şu an boş kalır, advisory detay sayfaları parse edilince doldurulacak.
CREATE TABLE IF NOT EXISTS cves (
    id     INTEGER PRIMARY KEY,
    cve_id TEXT NOT NULL UNIQUE                -- 'CVE-2026-1234'
);

CREATE TABLE IF NOT EXISTS advisory_cves (
    advisory_id INTEGER NOT NULL REFERENCES advisories(id) ON DELETE CASCADE,
    cve_id      INTEGER NOT NULL REFERENCES cves(id) ON DELETE CASCADE,
    PRIMARY KEY (advisory_id, cve_id)
);

-- Ters yön sorgu için: 'şu CVE hangi advisory'lerde geçiyor'
CREATE INDEX IF NOT EXISTS idx_advisory_cves_cve ON advisory_cves(cve_id);

-- Her çalıştırmanın kaydı: zamanlanmış çalışmada "ne zaman bozuldu" sorusunu cevaplar.
CREATE TABLE IF NOT EXISTS crawl_runs (
    id            INTEGER PRIMARY KEY,
    source_id     INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    started_at    TEXT NOT NULL,
    finished_at   TEXT,
    status        TEXT NOT NULL
                  CHECK (status IN ('running', 'success', 'error', 'interrupted')),
    new_count     INTEGER,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_source ON crawl_runs(source_id, started_at DESC);
