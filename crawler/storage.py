"""Kaynak-bağımsız JSON kalıcılık katmanı: kayıtları okur, tekilleştirip birleştirir, atomik yazar."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from crawler.errors import StorageError

logger = logging.getLogger(__name__)


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []

    try:
        with path.open(encoding="utf-8") as f:
            records = json.load(f)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"{path} geçerli JSON değil: {exc}. Veri kaybını önlemek için dosyaya "
            "dokunulmadı; elle düzeltin veya silin."
        ) from exc
    except OSError as exc:
        raise StorageError(f"{path} okunamadı: {exc}") from exc

    if not isinstance(records, list):
        raise StorageError(
            f"{path} bir JSON listesi içermeli, {type(records).__name__} bulundu."
        )
    return records


def merge_records(
    existing: list[dict], scraped: list[dict], key: str = "link"
) -> tuple[list[dict], int]:
    """Yeni kayıtları `key` ile tekilleştirerek ekler; mevcutların `first_seen`'ini korur."""
    by_key = {}
    unkeyed = []
    for record in existing:
        if isinstance(record, dict) and key in record:
            by_key[record[key]] = record
        else:
            # Elle düzenlenmiş olabilir; tekilleştiremeyiz ama veriyi de atmayalım.
            logger.warning("Mevcut kayıtta '%s' alanı yok, olduğu gibi korunuyor: %r", key, record)
            unkeyed.append(record)

    now = datetime.now(timezone.utc).isoformat()

    new_count = 0
    for record in scraped:
        if key not in record:
            logger.warning("Çekilen kayıtta '%s' alanı yok, atlanıyor: %r", key, record)
            continue

        previous = by_key.get(record[key])
        if previous is None:
            by_key[record[key]] = {**record, "first_seen": now}
            new_count += 1
        else:
            # Kaynakta düzeltme olursa yansısın, ama ilk görülme zamanı korunsun.
            by_key[record[key]] = {**previous, **record}

    merged = sorted(by_key.values(), key=lambda r: r.get("date") or "", reverse=True)
    return merged + unkeyed, new_count


def save_records(path: Path, records: list[dict]) -> None:
    # Çalıştırma yarıda kesilirse JSON bozulmasın diye önce geçici dosyaya yazılır.
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        raise StorageError(f"{path} yazılamadı: {exc}") from exc
