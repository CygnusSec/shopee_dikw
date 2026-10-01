from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def read_json_list(path: Path):
    if not path.exists(): return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list): raise ValueError(f"{path} must contain a JSON list")
    return payload


def atomic_write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush(); os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def merge_records(existing, incoming, key):
    merged = {str(row[key]): row for row in existing}
    inserted = updated = 0
    for row in incoming:
        identity = str(row[key])
        if identity in merged:
            updated += int(merged[identity] != row)
        else:
            inserted += 1
        merged[identity] = row
    return sorted(merged.values(), key=lambda row: str(row[key])), {"inserted": inserted, "updated": updated, "unchanged_or_duplicate": len(incoming)-inserted-updated}


def merge_shop_file(path: Path, records, replace_product_id=None):
    existing = read_json_list(path)
    if replace_product_id is not None:
        existing = [row for row in existing if row.get("product_id") != replace_product_id]
    merged, stats = merge_records(existing, records, "review_id")
    atomic_write_json(path, merged)
    return stats


class CheckpointStore:
    def __init__(self, path: Path): self.path = path; self.state = self._load()
    def _load(self):
        if not self.path.exists(): return {"completed_products": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))
    def is_complete(self, product_id): return product_id in self.state.get("completed_products", {})
    def mark_complete(self, product_id, details):
        self.state.setdefault("completed_products", {})[product_id] = details
        atomic_write_json(self.path, self.state)
