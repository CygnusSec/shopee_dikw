#!/usr/bin/env python3
"""
Collect REAL Shopee reviews into the exact JSON structure required by the project.

The script does NOT ask for or store Shopee credentials.
It opens a real browser. Log in manually if Shopee asks, then return to the terminal.

Usage:
    pip install -r requirements-collector.txt
    playwright install chromium
    python scripts/collect_shopee_reviews.py --reviews-per-product 5

Output:
    3_Unstructured_Data/shop_01_001_reviews.json
    3_Unstructured_Data/shop_01_002_reviews.json
    3_Unstructured_Data/shop_01_003_reviews.json
    review_collection_report.md
"""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.async_api import async_playwright, Page

ROOT = Path(__file__).resolve().parents[1]
MAPPING_FILE = ROOT / "product_review_mapping.json"
OUTPUT_DIR = ROOT / "3_Unstructured_Data"
PROFILE_DIR = ROOT / ".shopee_browser_profile"

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def safe_date(value):
    if not value:
        return None
    try:
        # Shopee ctime is Unix seconds.
        return datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone(VN_TZ).date().isoformat()
    except Exception:
        return None


def normalize_rating(raw: dict, shop_id: str, product_id: str, review_id: str) -> dict:
    images = raw.get("images") or raw.get("image") or []
    if not isinstance(images, list):
        images = [images] if images else []

    comment = (raw.get("comment") or raw.get("comment_text") or "").strip()

    return {
        "Shop_ID": shop_id,
        "product_id": product_id,
        "review_id": review_id,
        "user_name": raw.get("author_username") or raw.get("username") or None,
        "rating": raw.get("rating_star") or raw.get("rating") or None,
        "review_time": safe_date(raw.get("ctime") or raw.get("create_time")),
        "review_text": comment,
        "has_image": 1 if images else 0,
        "source_comment_id": raw.get("cmtid") or raw.get("comment_id"),
    }


async def fetch_json_in_page(page: Page, url: str):
    return await page.evaluate(
        """async (url) => {
            const r = await fetch(url, {
                credentials: 'include',
                headers: {
                    'accept': 'application/json, text/plain, */*'
                }
            });
            const text = await r.text();
            let body;
            try { body = JSON.parse(text); }
            catch (_) { body = {__raw_text: text}; }
            return {status: r.status, body};
        }""",
        url,
    )


async def fetch_reviews(page: Page, shop_id: int, item_id: int, needed: int) -> list[dict]:
    collected = []
    seen = set()
    offset = 0
    page_size = 20

    # filter=1 is commonly used for reviews containing text.
    while len(collected) < needed and offset <= 300:
        api = (
            "https://shopee.vn/api/v2/item/get_ratings"
            f"?filter=1&flag=1&itemid={item_id}"
            f"&limit={page_size}&offset={offset}&shopid={shop_id}&type=0"
        )
        result = await fetch_json_in_page(page, api)
        body = result.get("body") or {}

        if result.get("status") != 200:
            raise RuntimeError(f"HTTP {result.get('status')} from ratings endpoint")

        ratings = ((body.get("data") or {}).get("ratings") or [])
        if not ratings:
            # Retry once with filter=0 because Shopee occasionally changes filter behaviour.
            api = (
                "https://shopee.vn/api/v2/item/get_ratings"
                f"?filter=0&flag=1&itemid={item_id}"
                f"&limit={page_size}&offset={offset}&shopid={shop_id}&type=0"
            )
            result = await fetch_json_in_page(page, api)
            body = result.get("body") or {}
            ratings = ((body.get("data") or {}).get("ratings") or [])

        if not ratings:
            break

        for r in ratings:
            comment = (r.get("comment") or "").strip()
            if not comment:
                continue
            key = r.get("cmtid") or (
                r.get("author_username"),
                r.get("ctime"),
                comment,
            )
            key = repr(key)
            if key in seen:
                continue
            seen.add(key)
            collected.append(r)
            if len(collected) >= needed:
                break

        offset += page_size

    return collected[:needed]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviews-per-product", type=int, default=5)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()

    mapping = json.loads(MAPPING_FILE.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    by_shop = defaultdict(list)
    report = defaultdict(lambda: {
        "products": 0,
        "reviews": 0,
        "with_image": 0,
        "without_image": 0,
        "missing_date": 0,
        "failed_products": [],
        "urls": [],
    })

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=args.headless,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("\nOpening Shopee...")
        await page.goto("https://shopee.vn/", wait_until="domcontentloaded", timeout=90000)

        if not args.headless:
            print(
                "\nIf Shopee asks you to sign in, complete the login in the browser.\n"
                "Do NOT enter your password in this terminal.\n"
                "When the Shopee page is ready, press ENTER here to start collection."
            )
            input()

        shop_counters = defaultdict(int)

        for item in mapping:
            shop_id = item["Shop_ID"]
            report[shop_id]["products"] += 1
            report[shop_id]["urls"].append(item["product_url"])

            print(f"\n[{shop_id}] {item['product_id']} — {item['product_name']}")
            try:
                await page.goto(
                    item["product_url"],
                    wait_until="domcontentloaded",
                    timeout=90000,
                )
                await page.wait_for_timeout(1800)

                ratings = await fetch_reviews(
                    page,
                    int(item["shopee_shop_id"]),
                    int(item["shopee_item_id"]),
                    args.reviews_per_product,
                )

                if len(ratings) < args.reviews_per_product:
                    print(
                        f"  WARNING: only {len(ratings)} text reviews retrieved "
                        f"(target {args.reviews_per_product})"
                    )

                for raw in ratings:
                    shop_counters[shop_id] += 1
                    rid = f"rv_{shop_id}_{shop_counters[shop_id]:06d}"
                    row = normalize_rating(raw, shop_id, item["product_id"], rid)

                    # Basic validation.
                    rating = row["rating"]
                    if rating is not None:
                        rating = int(rating)
                        if not 1 <= rating <= 5:
                            continue
                        row["rating"] = rating

                    by_shop[shop_id].append(row)
                    report[shop_id]["reviews"] += 1
                    report[shop_id]["with_image"] += row["has_image"]
                    report[shop_id]["without_image"] += 1 - row["has_image"]
                    if row["review_time"] is None:
                        report[shop_id]["missing_date"] += 1

                print(f"  collected: {len(ratings)}")

            except Exception as e:
                print(f"  ERROR: {e}")
                report[shop_id]["failed_products"].append(
                    f"{item['product_id']}: {type(e).__name__}: {e}"
                )

        await context.close()

    # Persist exactly one JSON file per shop.
    for shop_id in ("01_001", "01_002", "01_003"):
        outfile = OUTPUT_DIR / f"shop_{shop_id}_reviews.json"
        outfile.write_text(
            json.dumps(by_shop[shop_id], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {len(by_shop[shop_id])} reviews -> {outfile}")

    lines = ["# Shopee Review Collection Report", ""]
    for shop_id in ("01_001", "01_002", "01_003"):
        r = report[shop_id]
        lines += [
            f"## {shop_id}",
            "",
            f"- Products attempted: {r['products']}",
            f"- Reviews collected: {r['reviews']}",
            f"- Reviews with image: {r['with_image']}",
            f"- Reviews without image: {r['without_image']}",
            f"- Reviews missing date: {r['missing_date']}",
            f"- Failed products: {len(r['failed_products'])}",
            "",
            "### Product URLs",
            *[f"- {u}" for u in r["urls"]],
            "",
        ]
        if r["failed_products"]:
            lines += ["### Errors", *[f"- {e}" for e in r["failed_products"]], ""]

    report_path = ROOT / "review_collection_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report -> {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
