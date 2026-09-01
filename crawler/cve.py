"""CVE kimliği çıkarma. Kaynaktan bağımsız — her feed'in özet metninde kullanılır."""

import html
import re

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


def extract_cves(summary: str | None) -> list[str]:
    """Özet metninden benzersiz CVE kimliklerini çıkarır (görülme sırasını korur)."""
    if not summary:
        return []

    seen = {}
    for match in CVE_RE.findall(html.unescape(summary)):
        seen.setdefault(match.upper(), None)
    return list(seen)
