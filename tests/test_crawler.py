import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "crawl_data"))

from crawler.normalizers import normalize_review, stable_review_id
from crawler.storage import atomic_write_json, merge_records, merge_shop_file, read_json_list
from crawler.validation import validate_collection
from crawler.config import CrawlSettings
from crawler.runner import ShopeeCrawler
from crawler.errors import AntiAutomation
from crawler.browser import BrowserClient

import asyncio


MANIFEST_ROW = {
    "Shop_ID": "01_001", "product_id": "sp_01_001_001",
    "shopee_shop_id": 10, "shopee_item_id": 20,
    "product_url": "https://shopee.vn/product/10/20",
}


def test_review_id_is_stable_with_and_without_source_id():
    assert stable_review_id({"cmtid": 123}, "01_001", "sp_1") == "rv_01_001_123"
    raw = {"username": "a", "ctime": 100, "comment": "Tốt"}
    assert stable_review_id(raw, "01_001", "sp_1") == stable_review_id(dict(raw), "01_001", "sp_1")


def test_normalize_review():
    row = normalize_review({"cmtid": 1, "username": "buyer", "rating_star": 5, "ctime": 1_700_000_000, "comment": "Hàng tốt", "images": ["x"]}, MANIFEST_ROW)
    assert row["review_id"] == "rv_01_001_1"
    assert row["has_image"] == 1
    assert row["rating"] == 5
    assert row["Data_Source"]
    assert row["source_url"] == MANIFEST_ROW["product_url"]
    assert row["Time_Collected"]
    assert row["Verification_Status"] == "collected_from_endpoint"


def test_merge_records_is_idempotent():
    rows = [{"review_id": "a", "value": 1}]
    merged, stats = merge_records(rows, list(rows), "review_id")
    assert merged == rows
    assert stats == {"inserted": 0, "updated": 0, "unchanged_or_duplicate": 1}


def test_atomic_merge_preserves_existing(tmp_path):
    path = tmp_path / "reviews.json"
    atomic_write_json(path, [{"review_id": "old", "value": 1}])
    stats = merge_shop_file(path, [{"review_id": "new", "value": 2}])
    assert {row["review_id"] for row in read_json_list(path)} == {"old", "new"}
    assert stats["inserted"] == 1


def test_collection_validation_detects_duplicate_review():
    product = {"Shop_ID":"01_001","product_id":"sp_01_001_001","product_name":"x","product_details":{},"description_text":"x","Review_stars":5,"units_sold":1,"product_url":MANIFEST_ROW["product_url"],"Time_Collected":"2026-01-01","Data_Source":"source"}
    review = normalize_review({"cmtid":1,"username":"a","rating_star":5,"comment":"ok"}, MANIFEST_ROW)
    result = validate_collection([MANIFEST_ROW], [product], [review, dict(review)], minimum_shops=1, minimum_products=1, maximum_products=10, minimum_reviews=1)
    assert not result["valid"]
    assert any("duplicate review_id" in error for error in result["errors"])


def test_collection_validation_preserves_missing_review_metadata_as_warning():
    product = {"Shop_ID":"01_001","product_id":"sp_01_001_001","product_name":"x","product_details":{},"description_text":"x","Review_stars":5,"units_sold":1,"product_url":MANIFEST_ROW["product_url"],"Time_Collected":"2026-01-01","Data_Source":"source"}
    review = {"Shop_ID":"01_001","product_id":"sp_01_001_001","review_id":"rv_1","user_name":"a","rating":None,"review_time":None,"review_text":"review thật","has_image":None,"source_url":MANIFEST_ROW["product_url"],"collection_date":"2026-01-01"}
    result = validate_collection([MANIFEST_ROW], [product], [review], minimum_shops=1, minimum_products=1, maximum_products=10, minimum_reviews=1)
    assert result["valid"]
    assert any("rating is unverified" in warning for warning in result["warnings"])
    assert any("has_image is unverified" in warning for warning in result["warnings"])


def test_collection_validation_rejects_cross_shop_review():
    review = {"Shop_ID":"01_999","product_id":"sp_01_001_001","review_id":"rv_1","user_name":"a","rating":5,"review_time":"2026-01-01","review_text":"ok","has_image":0,"Data_Source":"source","Time_Collected":"2026-01-01"}
    result = validate_collection([MANIFEST_ROW], [], [review], minimum_shops=1, minimum_products=1, maximum_products=10, minimum_reviews=1)
    assert not result["valid"]
    assert any("Shop_ID does not match product" in error for error in result["errors"])


def test_browser_stops_on_shopee_anti_automation_error():
    class Page:
        async def evaluate(self, *_):
            return {"status": 200, "body": {"error": 90309999}}

    client = BrowserClient(Page(), CrawlSettings(request_delay_min_seconds=0, request_delay_max_seconds=0))
    try:
        asyncio.run(client.get_json("https://shopee.vn/api/test"))
    except AntiAutomation:
        pass
    else:
        raise AssertionError("anti-automation response must stop the crawler")


def test_runner_wires_settings_into_review_collector(tmp_path):
    crawler = ShopeeCrawler(object(), CrawlSettings(), [MANIFEST_ROW], tmp_path / "dataset", tmp_path / "output")
    assert crawler.reviews.settings.reviews_per_product == 5
