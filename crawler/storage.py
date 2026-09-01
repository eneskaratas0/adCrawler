"""Kaynak-bağımsız JSON kalıcılık katmanı: kayıtları okur, tekilleştirip birleştirir, atomik yazar."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def merge_records(
    existing: list[dict], scraped: list[dict], key: str = "link"
) -> tuple[list[dict], int]:
    """Yeni kayıtları `key` ile tekilleştirerek ekler; mevcutların `first_seen`'ini korur."""
    by_key = {record[key]: record for record in existing}
    now = datetime.now(timezone.utc).isoformat()

    new_count = 0
    for record in scraped:
        previous = by_key.get(record[key])
        if previous is None:
            by_key[record[key]] = {**record, "first_seen": now}
            new_count += 1
        else:
            # Kaynakta düzeltme olursa yansısın, ama ilk görülme zamanı korunsun.
            by_key[record[key]] = {**previous, **record}

    merged = sorted(by_key.values(), key=lambda r: r.get("date") or "", reverse=True)
    return merged, new_count


def save_records(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Çalıştırma yarıda kesilirse JSON bozulmasın diye önce geçici dosyaya yazılır.
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)
