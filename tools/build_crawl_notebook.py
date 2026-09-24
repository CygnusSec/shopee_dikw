"""Generate the interactive Shopee collection notebook."""
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]

def cell(kind, source):
    value={"cell_type":kind,"metadata":{},"source":dedent(source).strip().splitlines(True)}
    if kind=="code": value.update({"execution_count":None,"outputs":[]})
    return value

cells=[
cell("markdown",'''# Shopee Data Collector

Thu thập dữ liệu thật theo manifest, có health check, retry, checkpoint và merge không phá dữ liệu cũ. Notebook không lưu mật khẩu/cookie và không vượt CAPTCHA hoặc cơ chế bảo vệ của Shopee.'''),
cell("markdown","""## 1. Cài đặt lần đầu

Bỏ comment nếu cần, sau đó restart kernel."""),
cell("code","""# %pip install -r ../../requirements.txt
# !python -m playwright install chromium"""),
cell("markdown","## 2. Đọc cấu hình và kiểm tra manifest"),
cell("code",'''from pathlib import Path
import sys

current=Path.cwd().resolve()
PROJECT_ROOT=next((p for p in (current,*current.parents) if (p/"Shopee_Dataset").is_dir() and (p/"src").is_dir()),None)
if PROJECT_ROOT is None: raise FileNotFoundError("Không tìm thấy project root")
CRAWL_ROOT=PROJECT_ROOT/"src"/"crawl_data"
sys.path.insert(0,str(CRAWL_ROOT))

from crawler import ShopeeCrawler, load_manifest, load_settings

settings=load_settings(CRAWL_ROOT/"crawl_config.yaml")
manifest=load_manifest(CRAWL_ROOT/"product_review_mapping.json")
shop_ids=sorted({row["Shop_ID"] for row in manifest})
print({"shops":len(shop_ids),"products":len(manifest),"settings":settings})
if len(shop_ids)<15: print(f"WARNING: mới có {len(shop_ids)}/15 shop")'''),
cell("markdown","""## 3. Mở Chromium và đăng nhập

Đăng nhập trực tiếp trong cửa sổ Chromium. Không nhập credential vào notebook."""),
cell("code",'''import os
from playwright.async_api import async_playwright

has_display=bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
effective_headless=settings.headless or not has_display
if effective_headless and not settings.headless:
    print("WARNING: Không tìm thấy XServer/$DISPLAY; tự chuyển sang headless=True.")
    print("Nếu Shopee yêu cầu đăng nhập/CAPTCHA, hãy chạy notebook trên máy local có giao diện, đăng nhập vào persistent profile rồi chạy lại.")
runtime=await async_playwright().start()
context=await runtime.chromium.launch_persistent_context(
    user_data_dir=str(CRAWL_ROOT/".shopee_browser_profile"),
    headless=effective_headless,
    viewport={"width":1440,"height":1000},
)
page=context.pages[0] if context.pages else await context.new_page()
await page.goto("https://shopee.vn/",wait_until="domcontentloaded",timeout=settings.timeout_ms)
print("Browser started:", {"headless":effective_headless,"has_display":has_display})
print("Nếu đang chạy headed, đăng nhập xong rồi chạy health check.")'''),
cell("markdown","## 4. Health check một sản phẩm"),
cell("code",'''crawler=ShopeeCrawler(page,settings,manifest,PROJECT_ROOT/"Shopee_Dataset",PROJECT_ROOT/"output")
await crawler.health_check()
print("Health check PASS")'''),
cell("markdown","""## 5. Thu thập

Kết quả được checkpoint sau từng product. Chạy lại sẽ bỏ qua product đã hoàn tất nếu `resume: true`."""),
cell("code",'''status=await crawler.run()
status'''),
cell("markdown","## 6. Kiểm tra output"),
cell("code",'''import json
from crawler.storage import read_json_list
from crawler.validation import validate_collection

products=[]; reviews=[]
for shop_id in shop_ids:
    products += read_json_list(PROJECT_ROOT/"Shopee_Dataset"/"2_Semi_Structured_Data"/f"shop_{shop_id}_products.json")
    reviews += read_json_list(PROJECT_ROOT/"Shopee_Dataset"/"3_Unstructured_Data"/f"shop_{shop_id}_reviews.json")
result=validate_collection(manifest,products,reviews)
print(json.dumps(result,ensure_ascii=False,indent=2))
if not result["valid"]: raise ValueError("Output validation failed")'''),
cell("markdown","## 7. Đóng trình duyệt"),
cell("code",'''await context.close()
await runtime.stop()
print("Browser closed")'''),
]
nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3"}},"nbformat":4,"nbformat_minor":5}
path=ROOT/"src"/"crawl_data"/"collect_shopee_data.ipynb"
path.write_text(json.dumps(nb,ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
print("wrote",path)
