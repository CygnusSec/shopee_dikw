from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # Allows dependency-free tests of storage/normalizers.
    yaml = None


@dataclass(frozen=True)
class CrawlSettings:
    reviews_per_product: int = 5
    page_size: int = 20
    max_pages: int = 20
    timeout_ms: int = 90_000
    retry_attempts: int = 3
    backoff_seconds: float = 2.0
    request_delay_min_seconds: float = 1.2
    request_delay_max_seconds: float = 2.5
    headless: bool = False
    resume: bool = True
    dry_run: bool = False
    save_sanitized_raw: bool = True


def load_settings(path: Path) -> CrawlSettings:
    if not path.exists():
        return CrawlSettings()
    if yaml is None:
        raise RuntimeError("PyYAML is required to read crawl_config.yaml; install requirements.txt")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    unknown = set(payload) - set(CrawlSettings.__dataclass_fields__)
    if unknown:
        raise ValueError(f"Unknown crawler settings: {sorted(unknown)}")
    settings = CrawlSettings(**payload)
    if settings.reviews_per_product < 1 or settings.page_size < 1 or settings.max_pages < 1:
        raise ValueError("reviews_per_product, page_size and max_pages must be positive")
    if settings.retry_attempts < 1 or settings.request_delay_min_seconds < 0:
        raise ValueError("Invalid retry or delay configuration")
    if settings.request_delay_max_seconds < settings.request_delay_min_seconds:
        raise ValueError("Maximum request delay must be >= minimum delay")
    return settings


def _flatten_manifest(payload):
    if not isinstance(payload, list):
        raise ValueError("Manifest must be a JSON list")
    flattened = []
    for entry in payload:
        if "products" not in entry:
            flattened.append(dict(entry))
            continue
        shop = {key: value for key, value in entry.items() if key != "products"}
        for product in entry["products"]:
            flattened.append({**shop, **product})
    return flattened


def load_manifest(path: Path):
    rows = _flatten_manifest(json.loads(path.read_text(encoding="utf-8")))
    required = {"Shop_ID", "product_id", "shopee_shop_id", "shopee_item_id", "product_url"}
    errors = []
    seen_products, seen_sources, seen_urls = set(), set(), set()
    for index, row in enumerate(rows):
        missing = required - set(row)
        if missing:
            errors.append(f"row {index}: missing {sorted(missing)}")
            continue
        parsed = urlparse(str(row["product_url"]))
        if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith("shopee.vn"):
            errors.append(f"row {index}: invalid Shopee URL")
        product_id = str(row["product_id"])
        source_key = (str(row["shopee_shop_id"]), str(row["shopee_item_id"]))
        if product_id in seen_products: errors.append(f"row {index}: duplicate product_id {product_id}")
        if source_key in seen_sources: errors.append(f"row {index}: duplicate Shopee shop/item pair {source_key}")
        if row["product_url"] in seen_urls: errors.append(f"row {index}: duplicate product_url")
        seen_products.add(product_id); seen_sources.add(source_key); seen_urls.add(row["product_url"])
        prohibited = {"password", "cookie", "token", "authorization", "session"}
        if prohibited & set(map(str.lower, row)):
            errors.append(f"row {index}: contains prohibited credential field")
    if errors:
        raise ValueError("Invalid manifest:\n- " + "\n- ".join(errors))
    return rows
