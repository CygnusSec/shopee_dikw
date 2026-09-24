from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .browser import BrowserClient
from .errors import AntiAutomation, AuthRequired, CrawlError
from .normalizers import sanitize_raw
from .product_collector import ProductCollector
from .review_collector import ReviewCollector
from .shop_collector import ShopCollector
from .storage import CheckpointStore, atomic_write_json, merge_records, merge_shop_file, read_json_list


class ShopeeCrawler:
    def __init__(self, page, settings, manifest, dataset_root: Path, output_root: Path):
        self.settings, self.manifest = settings, manifest
        self.dataset_root, self.output_root = dataset_root, output_root
        self.client = BrowserClient(page, settings)
        self.products = ProductCollector(self.client); self.reviews = ReviewCollector(self.client); self.shops = ShopCollector(self.client)
        self.crawl_root = output_root / "crawl"; self.raw_root = self.crawl_root / "schema_change_samples"
        self.crawl_root.mkdir(parents=True, exist_ok=True)
        self.checkpoints = CheckpointStore(self.crawl_root / "checkpoint.json")
        self.status = []

    async def health_check(self): return await self.client.health_check(self.manifest[0])

    def _save_raw(self, product_id, kind, payload):
        if not self.settings.save_sanitized_raw: return
        self.raw_root.mkdir(parents=True, exist_ok=True)
        (self.raw_root/f"{product_id}_{kind}.json").write_text(json.dumps(sanitize_raw(payload),ensure_ascii=False,indent=2),encoding="utf-8")

    async def run(self):
        shop_records = {}
        for item in self.manifest:
            product_id, started = item["product_id"], datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
            if self.settings.resume and self.checkpoints.is_complete(product_id):
                self.status.append({"product_id":product_id,"Shop_ID":item["Shop_ID"],"status":"SKIPPED_CHECKPOINT"}); continue
            row = {"product_id":product_id,"Shop_ID":item["Shop_ID"],"started_at":started.isoformat()}
            fatal_error = None
            try:
                if self.settings.dry_run:
                    row["status"]="DRY_RUN"; self.status.append(row); continue
                if item["Shop_ID"] not in shop_records:
                    shop, shop_raw = await self.shops.collect(item); shop_records[item["Shop_ID"]]=shop; self._save_raw(product_id,"shop",shop_raw); self._write_shops(shop_records)
                product, product_raw = await self.products.collect(item); self._save_raw(product_id,"product",product_raw); self._merge_product(item["Shop_ID"],product)
                reviews, meta = await self.reviews.collect(item)
                review_path=self.dataset_root/"3_Unstructured_Data"/f"shop_{item['Shop_ID']}_reviews.json"
                stats=merge_shop_file(review_path,reviews)
                row.update({"status":"SUCCESS","reviews_collected":len(reviews),**meta,**stats})
                self.checkpoints.mark_complete(product_id,{"completed_at":datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(),"review_count":len(reviews)})
            except Exception as error:
                row.update({"status":"FAILED","error_category":getattr(error,"category","UNEXPECTED_ERROR"),"error":f"{type(error).__name__}: {error}"})
                if row["error_category"] in {AuthRequired.category, AntiAutomation.category}: fatal_error = error
            row["finished_at"]=datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).isoformat(); self.status.append(row); self._write_status()
            if fatal_error is not None: raise fatal_error
        self._write_status(); return self.status

    def _merge_product(self, shop_id, product):
        path=self.dataset_root/"2_Semi_Structured_Data"/f"shop_{shop_id}_products.json"
        merged,_=merge_records(read_json_list(path),[product],"product_id"); atomic_write_json(path,merged)

    def _write_shops(self, records):
        if not records: return
        # JSON handoff avoids rewriting the shared Excel workbook automatically.
        atomic_write_json(self.crawl_root/"shops_collected.json",sorted(records.values(),key=lambda r:r["Shop_ID"]))

    def _write_status(self):
        if not self.status: return
        fields=sorted({key for row in self.status for key in row})
        path=self.crawl_root/"product_status.csv"
        with path.open("w",encoding="utf-8-sig",newline="") as handle:
            writer=csv.DictWriter(handle,fieldnames=fields); writer.writeheader(); writer.writerows(self.status)
