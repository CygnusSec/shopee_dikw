#!/usr/bin/env python3
"""Run the Shopee crawler locally with a visible Chromium window."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import sys
from dataclasses import replace
from pathlib import Path


CRAWL_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = CRAWL_ROOT.parents[1]
sys.path.insert(0, str(CRAWL_ROOT))

from crawler import ShopeeCrawler, load_manifest, load_settings
from crawler.auth import load_playwright_cookies
from crawler.storage import read_json_list
from crawler.validation import validate_collection


def parse_args():
    parser = argparse.ArgumentParser(description="Crawl Shopee locally with visible Chromium and manual login")
    parser.add_argument("--manifest", type=Path, default=CRAWL_ROOT / "product_review_mapping.json")
    parser.add_argument("--config", type=Path, default=CRAWL_ROOT / "crawl_config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Validate and open browser without writing collected records")
    parser.add_argument("--restart", action="store_true", help="Ignore completion checkpoints; merge still prevents duplicates")
    parser.add_argument("--skip-login-wait", action="store_true", help="Use an existing browser profile without waiting for Enter")
    parser.add_argument("--cookie-file", type=Path, help="Load Shopee session cookies from a private curl/JSON/Netscape file")
    return parser.parse_args()


def ensure_local_gui():
    system = platform.system()
    has_gui = system in {"Darwin", "Windows"} or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if not has_gui:
        raise RuntimeError(
            "Không tìm thấy giao diện desktop. Hãy chạy script trong Terminal trên macOS/Windows "
            "hoặc Linux desktop, không chạy trong Colab/Docker/SSH server không có DISPLAY."
        )
    return system


async def ensure_not_verification_page(page):
    url = page.url.lower()
    title = (await page.title()).lower()
    body = (await page.locator("body").inner_text(timeout=5_000)).lower()
    markers = ("/verify/captcha", "anti_bot_tracking_id", "please try again later", "verification can't be completed")
    if any(marker in url or marker in title or marker in body for marker in markers):
        raise RuntimeError(
            "Shopee đang chặn phiên bằng trang verification/captcha. Crawler đã dừng và sẽ không retry. "
            "Đóng Chromium, chờ cooldown, kiểm tra truy cập bằng trình duyệt thông thường; nếu vẫn bị chặn, "
            "hãy dùng export/API được cấp quyền hoặc nhập dữ liệu thủ công."
        )


def load_outputs(manifest):
    products, reviews = [], []
    for shop_id in sorted({row["Shop_ID"] for row in manifest}):
        products += read_json_list(PROJECT_ROOT / "Shopee_Dataset" / "2_Semi_Structured_Data" / f"shop_{shop_id}_products.json")
        reviews += read_json_list(PROJECT_ROOT / "Shopee_Dataset" / "3_Unstructured_Data" / f"shop_{shop_id}_reviews.json")
    return products, reviews


async def run(args):
    host = ensure_local_gui()
    settings = load_settings(args.config)
    settings = replace(settings, headless=False, dry_run=args.dry_run, resume=not args.restart)
    manifest = load_manifest(args.manifest)
    shops = sorted({row["Shop_ID"] for row in manifest})
    print("Shopee local crawler")
    print(json.dumps({"host": host, "shops": len(shops), "products": len(manifest), "resume": settings.resume, "dry_run": settings.dry_run}, ensure_ascii=False, indent=2))
    if len(shops) < 15:
        print(f"WARNING: manifest mới có {len(shops)}/15 shop.")

    try:
        from playwright.async_api import async_playwright
    except ImportError as error:
        raise RuntimeError("Playwright chưa được cài. Chạy: pip install -r requirements.txt") from error

    runtime = await async_playwright().start()
    context = None
    try:
        context = await runtime.chromium.launch_persistent_context(
            user_data_dir=str(CRAWL_ROOT / ".shopee_browser_profile"),
            headless=False,
            viewport={"width": 1440, "height": 1000},
        )
        if args.cookie_file:
            cookies = load_playwright_cookies(args.cookie_file.expanduser().resolve())
            await context.add_cookies(cookies)
            print(f"Đã nạp {len(cookies)} session cookies từ file riêng (giá trị đã ẩn).")
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://shopee.vn/", wait_until="domcontentloaded", timeout=settings.timeout_ms)
        print("\nChromium đã mở. Đăng nhập Shopee trực tiếp trong cửa sổ đó.")
        if not args.skip_login_wait:
            await asyncio.to_thread(input, "Sau khi đăng nhập và trang chủ đã ổn định, nhấn Enter tại Terminal để tiếp tục... ")

        await ensure_not_verification_page(page)
        crawler = ShopeeCrawler(page, settings, manifest, PROJECT_ROOT / "Shopee_Dataset", PROJECT_ROOT / "output")
        print("Đang health-check sản phẩm đầu tiên...")
        await crawler.health_check()
        print("Health check PASS. Bắt đầu crawl.")
        status = await crawler.run()

        products, reviews = load_outputs(manifest)
        validation = validate_collection(manifest, products, reviews)
        validation_path = PROJECT_ROOT / "output" / "crawl" / "validation.json"
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        success = sum(row.get("status") == "SUCCESS" for row in status)
        failed = sum(row.get("status") == "FAILED" for row in status)
        skipped = sum(row.get("status") == "SKIPPED_CHECKPOINT" for row in status)
        print(json.dumps({"success": success, "failed": failed, "skipped": skipped, "validation": validation}, ensure_ascii=False, indent=2))
        if not validation["valid"]:
            raise RuntimeError("Crawl hoàn tất nhưng output validation có lỗi")
    finally:
        if context is not None:
            await context.close()
        await runtime.stop()
        print("Đã đóng Chromium.")


def main():
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("\nĐã dừng theo yêu cầu người dùng.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        print(f"\nERROR: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
