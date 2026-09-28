"""Build the seven self-contained submission notebooks.

Run this file only when notebook sources need to be regenerated.  Runtime
analysis does not import this module; every generated notebook is self-contained.
"""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(text).strip().splitlines(True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": dedent(text).strip().splitlines(True)}


SETUP = r'''
from pathlib import Path
import hashlib
import json
import warnings
import numpy as np
import pandas as pd
import yaml

warnings.filterwarnings("ignore")
current = Path.cwd().resolve()
PROJECT_ROOT = next((p for p in (current, *current.parents) if (p / "config" / "config.yaml").exists()), None)
if PROJECT_ROOT is None:
    raise FileNotFoundError("Cannot locate project root containing config/config.yaml")
with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
    CONFIG = yaml.safe_load(handle)

def project_path(key):
    return PROJECT_ROOT / CONFIG["paths"][key]

OUTPUT = project_path("output")
PROCESSED = project_path("processed")
for folder in [OUTPUT / "reports", OUTPUT / "figures", OUTPUT / "models", OUTPUT / "labeling", OUTPUT / "logs", OUTPUT / "powerbi", PROCESSED]:
    folder.mkdir(parents=True, exist_ok=True)
fingerprint_paths = [PROJECT_ROOT / "config" / "config.yaml", project_path("shops")]
for key in ("products", "reviews"):
    fingerprint_paths.extend(sorted(project_path(key).glob("shop_*.json")))
seller_candidate = project_path("seller_metrics")
for candidate in (seller_candidate, seller_candidate.with_suffix(".xlsx")):
    if candidate.exists(): fingerprint_paths.append(candidate)
digest = hashlib.sha256()
for path in fingerprint_paths:
    digest.update(str(path.relative_to(PROJECT_ROOT)).encode("utf-8")); digest.update(path.read_bytes())
INPUT_FINGERPRINT = digest.hexdigest()
print("PROJECT_ROOT:", PROJECT_ROOT)
print("INPUT_FINGERPRINT:", INPUT_FINGERPRINT)
'''


LOADERS = r'''
SHOP_REQUIRED = ["Shop_ID", "Shop_Name", "Shop_type", "Years_Active", "Is_Online_Now", "Total_Products", "Follower_Count_k", "Rating_Average", "Total_Ratings_k", "Chat_Response_Rate_pct", "Has_Voucher", "Target_Label", "Time_Collected"]
PRODUCT_REQUIRED = ["Shop_ID", "product_id", "product_name", "product_details", "description_text", "Review_stars", "units_sold", "product_url", "Time_Collected", "Data_Source"]
REVIEW_REQUIRED = ["Shop_ID", "product_id", "review_id", "user_name", "rating", "review_time", "review_text", "has_image", "source_url", "Time_Collected", "Data_Source", "Verification_Status"]
SELLER_REQUIRED = ["Shop_ID", "product_id", "Conversion_Rate_pct", "Time_Collected", "Data_Source"]

def load_json_folder(folder, pattern, columns):
    records = []
    for path in sorted(folder.glob(pattern)):
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            raise ValueError(f"{path}: top-level JSON must be a list")
        records.extend(payload)
    return pd.DataFrame(records) if records else pd.DataFrame(columns=columns)

def load_seller_metrics(path):
    candidates = [path, path.with_suffix(".xlsx")]
    source = next((p for p in candidates if p.exists()), None)
    if source is None:
        return pd.DataFrame(columns=SELLER_REQUIRED), None
    frame = pd.read_excel(source, dtype={"Shop_ID": str, "product_id": str}) if source.suffix == ".xlsx" else pd.read_csv(source, dtype={"Shop_ID": str, "product_id": str})
    return frame, source

shops = pd.read_excel(project_path("shops"), dtype={"Shop_ID": str})
products = load_json_folder(project_path("products"), "shop_*_products.json", PRODUCT_REQUIRED)
reviews = load_json_folder(project_path("reviews"), "shop_*_reviews.json", REVIEW_REQUIRED)
seller_metrics, seller_source = load_seller_metrics(project_path("seller_metrics"))

# Canonicalize legacy/manual collection fields without inventing business values.
manifest_path = PROJECT_ROOT / "src" / "crawl_data" / "product_review_mapping.json"
if manifest_path.exists():
    manifest = pd.DataFrame(json.loads(manifest_path.read_text(encoding="utf-8")))
    if {"product_id", "product_url"} <= set(manifest):
        url_map = manifest.drop_duplicates("product_id").set_index("product_id")["product_url"]
        if "product_url" not in products: products["product_url"] = products["product_id"].map(url_map)
        else: products["product_url"] = products["product_url"].fillna(products["product_id"].map(url_map))
for column in PRODUCT_REQUIRED:
    if column not in products: products[column] = np.nan
if "product_details" in products:
    detail_url = products["product_details"].map(lambda value: value.get("source_product_url") if isinstance(value, dict) else None)
    detail_date = products["product_details"].map(lambda value: value.get("collection_date") if isinstance(value, dict) else None)
    products["product_url"] = products["product_url"].fillna(detail_url)
    products["Time_Collected"] = products["Time_Collected"].fillna(detail_date)
products["Data_Source"] = products["Data_Source"].fillna(products["product_url"])
for column in REVIEW_REQUIRED:
    if column not in reviews: reviews[column] = np.nan
if "collection_date" in reviews: reviews["Time_Collected"] = reviews["Time_Collected"].fillna(reviews["collection_date"])
if "source_url" in reviews: reviews["Data_Source"] = reviews["Data_Source"].fillna(reviews["source_url"])
reviews["Verification_Status"] = reviews["Verification_Status"].fillna("legacy_partial_metadata")
print({"shops": len(shops), "products": len(products), "reviews": len(reviews), "seller_metrics": len(seller_metrics)})
'''


NOTEBOOKS = {
"00_data_validation.ipynb": [
md('''# 00 — Data Validation

Validates schema, ranges, keys, provenance, collection coverage, and submission readiness. Raw inputs are never modified.'''),
code(SETUP), code(LOADERS),
code(r'''
checks = []
def check(name, severity, invalid_count, description):
    invalid_count = int(invalid_count)
    checks.append({"check_name": name, "severity": severity, "status": "PASS" if invalid_count == 0 else severity, "error_count": invalid_count, "description": description})

def missing_count(frame, required):
    return len(set(required) - set(frame.columns))

for name, frame, required in [("shops", shops, SHOP_REQUIRED), ("products", products, PRODUCT_REQUIRED), ("reviews", reviews, REVIEW_REQUIRED), ("seller_metrics", seller_metrics, SELLER_REQUIRED)]:
    check(f"{name}_required_columns", "FAIL", missing_count(frame, required), f"Required schema: {required}")

if not missing_count(shops, SHOP_REQUIRED):
    check("unique_Shop_ID", "FAIL", shops["Shop_ID"].duplicated().sum(), "Shop_ID must be unique")
    check("shop_rating_range", "FAIL", (~pd.to_numeric(shops["Rating_Average"], errors="coerce").between(0, 5)).sum(), "Rating_Average in [0,5]")
    check("response_rate_range", "FAIL", (~pd.to_numeric(shops["Chat_Response_Rate_pct"], errors="coerce").between(0, 100)).sum(), "Chat response in [0,100]")
    check("shop_dates", "FAIL", pd.to_datetime(shops["Time_Collected"], errors="coerce").isna().sum(), "Time_Collected must be a date")
if not missing_count(products, PRODUCT_REQUIRED):
    check("unique_product_id", "FAIL", products["product_id"].duplicated().sum(), "product_id must be globally unique")
    product_rating = pd.to_numeric(products["Review_stars"], errors="coerce")
    product_sales = pd.to_numeric(products["units_sold"], errors="coerce")
    check("product_rating_range", "FAIL", (product_rating.notna() & ~product_rating.between(0, 5)).sum(), "Observed Review_stars in [0,5]")
    check("product_rating_missing", "WARNING", product_rating.isna().sum(), "Missing rating remains null")
    check("product_units_sold_negative", "FAIL", (product_sales.notna() & (product_sales < 0)).sum(), "Observed units_sold must be non-negative")
    check("product_units_sold_missing", "WARNING", product_sales.isna().sum(), "Missing sales remains null; never substitute ratings")
    check("product_provenance", "WARNING", products[["product_url", "Time_Collected", "Data_Source"]].isna().any(axis=1).sum(), "Products should have URL, date and source")
if not missing_count(reviews, REVIEW_REQUIRED):
    check("unique_review_id", "FAIL", reviews["review_id"].duplicated().sum(), "review_id must be unique")
    review_rating = pd.to_numeric(reviews["rating"], errors="coerce")
    review_image = pd.to_numeric(reviews["has_image"], errors="coerce")
    check("review_rating_range", "FAIL", (review_rating.notna() & ~review_rating.between(1, 5)).sum(), "Observed rating in [1,5]")
    check("review_rating_missing", "WARNING", review_rating.isna().sum(), "Unverified rating remains null")
    check("review_has_image", "FAIL", (review_image.notna() & ~review_image.isin([0, 1])).sum(), "Observed has_image must be binary")
    check("review_has_image_missing", "WARNING", review_image.isna().sum(), "Unverified image flag remains null")
    check("review_text", "WARNING", reviews["review_text"].fillna("").astype(str).str.strip().eq("").sum(), "Rating-only reviews remain raw but are excluded from text analysis")
    check("review_provenance", "WARNING", reviews[["source_url", "Time_Collected", "Data_Source", "Verification_Status"]].isna().any(axis=1).sum(), "Reviews should have URL, collection date, source and verification status")
if not missing_count(seller_metrics, SELLER_REQUIRED):
    check("seller_key_unique", "FAIL", seller_metrics.duplicated(["Shop_ID", "product_id"]).sum(), "Seller export must have one row per shop/product")
    check("conversion_range", "FAIL", (~pd.to_numeric(seller_metrics["Conversion_Rate_pct"], errors="coerce").between(0,100)).sum(), "Conversion rate in [0,100]")

if {"Shop_ID"} <= set(shops) and {"Shop_ID", "product_id"} <= set(products) and {"Shop_ID", "product_id"} <= set(reviews):
    check("product_shop_fk", "FAIL", len(set(products["Shop_ID"]) - set(shops["Shop_ID"])), "Every product shop exists")
    check("review_shop_fk", "FAIL", len(set(reviews["Shop_ID"]) - set(shops["Shop_ID"])), "Every review shop exists")
    check("review_product_fk", "FAIL", len(set(reviews["product_id"]) - set(products["product_id"])), "Every review product exists")
    product_shop = products.set_index("product_id")["Shop_ID"].to_dict()
    check("review_product_shop_match", "FAIL", reviews.apply(lambda r: product_shop.get(r["product_id"]) not in (None, r["Shop_ID"]), axis=1).sum(), "Review Shop_ID agrees with its product")

dq = CONFIG["data_quality"]
check("minimum_shops", "WARNING", max(0, dq["minimum_shops"] - shops["Shop_ID"].nunique()), f"At least {dq['minimum_shops']} real shops")
product_counts = products.groupby("Shop_ID").size().reindex(shops["Shop_ID"], fill_value=0)
reviews_with_text = reviews.loc[reviews["review_text"].fillna("").astype(str).str.strip().ne("")]
review_counts = reviews_with_text.groupby(["Shop_ID", "product_id"]).size().reindex(pd.MultiIndex.from_frame(products[["Shop_ID", "product_id"]]), fill_value=0)
check("products_per_shop", "WARNING", ((product_counts < dq["minimum_products_per_shop"]) | (product_counts > dq["maximum_products_per_shop"])).sum(), "Each shop needs 5–10 products")
check("reviews_per_product", "WARNING", (review_counts < dq["minimum_text_reviews_per_product"]).sum(), "Each product needs at least five text reviews")
check("seller_metrics_present", "WARNING", int(seller_metrics.empty), "Authorized Seller Centre export is required")

coverage = pd.DataFrame({"Shop_ID": shops["Shop_ID"], "Product_Count": shops["Shop_ID"].map(product_counts).fillna(0).astype(int)})
coverage["Review_Count"] = coverage["Shop_ID"].map(reviews_with_text.groupby("Shop_ID").size()).fillna(0).astype(int)
coverage["Products_With_Conversion"] = coverage["Shop_ID"].map(seller_metrics.groupby("Shop_ID").size() if not seller_metrics.empty else {}).fillna(0).astype(int)
report = pd.DataFrame(checks)
report.to_csv(OUTPUT / "reports" / "data_validation_report.csv", index=False)
coverage.to_csv(OUTPUT / "reports" / "data_coverage_by_shop.csv", index=False)
display(report); display(coverage)
critical = report.query("status == 'FAIL'")
if not critical.empty:
    raise ValueError("Critical validation failed: " + ", ".join(critical["check_name"]))
'''),
code(r'''
import re
def exists(rel): return (PROJECT_ROOT / rel).exists()
metrics_path = OUTPUT / "reports" / "classification_metrics.json"
metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
regression_metrics_path = OUTPUT / "reports" / "regression_metrics.json"
regression_metrics = json.loads(regression_metrics_path.read_text(encoding="utf-8")) if regression_metrics_path.exists() else {}
wisdom_path = OUTPUT / "reports" / "wisdom_facts.json"
wisdom = json.loads(wisdom_path.read_text(encoding="utf-8")) if wisdom_path.exists() else {}
mapping = CONFIG["clustering"].get("authenticity_mapping") or {}
pbix = next((path for path in (PROJECT_ROOT / "powerbi").glob("*.pbix")), None)
pbix_evidence_path = PROJECT_ROOT / "powerbi" / "verification.json"
pbix_evidence = json.loads(pbix_evidence_path.read_text(encoding="utf-8")) if pbix_evidence_path.exists() else {}
required_pages = {"Tổng quan shop", "Sản phẩm và review", "Uy tín và chuyển đổi"}
powerbi_verified = bool(pbix and required_pages <= set(pbix_evidence.get("pages", [])) and pbix_evidence.get("refresh_passed") is True and pbix_evidence.get("cross_filter_passed") is True and str(pbix_evidence.get("verified_by", "")).strip() and str(pbix_evidence.get("verified_at", "")).strip() and pbix_evidence.get("input_fingerprint") == INPUT_FINGERPRINT)
metadata_path = PROJECT_ROOT / "submission" / "submission_metadata.yaml"
metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
links_verified = bool(str(metadata.get("colab_url", "")).startswith("https://colab.research.google.com") and str(metadata.get("drive_url", "")).startswith("https://drive.google.com") and metadata.get("access_verified") is True and str(metadata.get("verified_by", "")).strip() and str(metadata.get("verified_at", "")).strip() and metadata.get("input_fingerprint") == INPUT_FINGERPRINT)
report_path = PROJECT_ROOT / "report" / "Final_Report.pdf"
report_pages = len(re.findall(rb"/Type\s*/Page(?!s)\b", report_path.read_bytes())) if report_path.exists() else 0
coverage_ready = bool(len(shops) >= dq["minimum_shops"] and product_counts.between(dq["minimum_products_per_shop"], dq["maximum_products_per_shop"]).all() and (review_counts >= dq["minimum_text_reviews_per_product"]).all())
products_per_shop_ready = bool(len(product_counts) and product_counts.between(dq["minimum_products_per_shop"], dq["maximum_products_per_shop"]).all())
reviews_per_product_ready = bool(len(review_counts) and (review_counts >= dq["minimum_text_reviews_per_product"]).all())
auth_metadata_path = OUTPUT / "reports" / "authenticity_metadata.json"
auth_metadata = json.loads(auth_metadata_path.read_text(encoding="utf-8")) if auth_metadata_path.exists() else {}
authenticity_ready = bool(mapping and exists("output/reports/Shop_Authenticity_Report.csv") and auth_metadata.get("input_fingerprint") == INPUT_FINGERPRINT and auth_metadata.get("authenticity_mapping") == {str(k):float(v) for k,v in mapping.items()})
items = {
    "THREE_DATA_TYPES": bool(len(shops) and len(products) and len(reviews)),
    "MINIMUM_REAL_SHOPS": shops["Shop_ID"].nunique() >= dq["minimum_shops"],
    "PRODUCTS_PER_SHOP": products_per_shop_ready,
    "REVIEWS_PER_PRODUCT": reviews_per_product_ready,
    "REVIEW_METADATA_COMPLETE": bool(reviews["rating"].notna().all() and reviews["has_image"].notna().all()),
    "PROVENANCE_COMPLETE": bool(products[["product_url","Time_Collected","Data_Source"]].notna().all(axis=1).all() and reviews[["source_url","Time_Collected","Data_Source","Verification_Status"]].notna().all(axis=1).all()),
    "SELLER_METRICS": not seller_metrics.empty,
    "AUTHENTICITY_MAPPING": bool(mapping) and set(map(float,mapping.values())) <= {0.0,0.5,1.0},
    "AUTHENTICITY_REPORT": authenticity_ready,
    "CLASSIFICATION_RESULT": exists("output/reports/Classification_Result.csv") and metrics.get("input_fingerprint") == INPUT_FINGERPRINT,
    "CLASSIFICATION_ACCURACY": metrics.get("input_fingerprint") == INPUT_FINGERPRINT and float(metrics.get("accuracy",0)) > float(CONFIG["classification"]["accuracy_target"]),
    "CLASSIFICATION_MACRO_F1": metrics.get("input_fingerprint") == INPUT_FINGERPRINT and pd.notna(metrics.get("macro_f1")),
    "REGRESSION_RESULT": exists("output/reports/Regression_Result.csv") and regression_metrics.get("input_fingerprint") == INPUT_FINGERPRINT,
    "WISDOM_FACTS": wisdom.get("input_fingerprint") == INPUT_FINGERPRINT,
    "POWER_BI_VERIFIED": powerbi_verified,
    "FINAL_REPORT_10_PAGES": report_pages >= 10,
    "COLAB_DRIVE_ACCESS": links_verified,
}
items = {name:bool(value) for name,value in items.items()}
text = "\n".join(f"{name:<32} {'PASS' if value else 'FAIL'}" for name, value in items.items())
text += f"\n\nCOUNTS: shops={shops['Shop_ID'].nunique()}, products={products['product_id'].nunique()}, reviews={len(reviews)}, text_reviews={len(reviews_with_text)}\nFINAL_REPORT_PAGES: {report_pages}\n\nOVERALL: {'READY FOR SUBMISSION' if all(items.values()) else 'NOT READY FOR SUBMISSION'}\n"
(OUTPUT / "reports" / "submission_check.txt").write_text(text, encoding="utf-8")
(OUTPUT / "reports" / "submission_check.json").write_text(json.dumps({"checks":items,"overall_ready":all(items.values())},ensure_ascii=False,indent=2),encoding="utf-8")
print(text)
''')],

"01_data_cleaning.ipynb": [md('''# 01 — Cleaning, Sentiment & Features

Normalizes data non-destructively, documents row loss, and produces analysis-ready datasets.'''), code(SETUP), code(LOADERS),
code(r'''
import html, re, unicodedata

def clean_text(value):
    if value is None or pd.isna(value): return ""
    text = unicodedata.normalize("NFC", html.unescape(str(value))).lower()
    text = re.sub(r"<[^>]+>|https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"([!?.,])\1+", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([!?.,])", r"\1", text)

STOPWORDS = {"và","là","của","có","cho","một","những","các","được","với","thì","mà","ở","đã","này","đó","rất"}
def remove_stopwords(value):
    return " ".join(token for token in str(value).split() if token not in STOPWORDS)

shops_clean, products_clean, reviews_clean = shops.copy(), products.copy(), reviews.copy()
reviews_clean = reviews_clean.loc[reviews_clean["review_text"].fillna("").astype(str).str.strip().ne("")].copy()
numeric_shop = ["Years_Active", "Is_Online_Now", "Total_Products", "Follower_Count_k", "Rating_Average", "Total_Ratings_k", "Chat_Response_Rate_pct", "Has_Voucher"]
for col in numeric_shop: shops_clean[col] = pd.to_numeric(shops_clean[col], errors="coerce")
for col in ["Review_stars", "units_sold"]: products_clean[col] = pd.to_numeric(products_clean[col], errors="coerce")
reviews_clean["rating"] = pd.to_numeric(reviews_clean["rating"], errors="coerce")
reviews_clean["has_image"] = pd.to_numeric(reviews_clean["has_image"], errors="coerce")
shops_clean["Time_Collected"] = pd.to_datetime(shops_clean["Time_Collected"], errors="coerce").dt.date.astype("string")
products_clean["Time_Collected"] = pd.to_datetime(products_clean["Time_Collected"], errors="coerce").dt.date.astype("string")
reviews_clean["review_time"] = pd.to_datetime(reviews_clean["review_time"], errors="coerce").dt.date.astype("string")
products_clean["description_normalized"] = products_clean["description_text"].map(clean_text)
reviews_clean["review_normalized"] = reviews_clean["review_text"].map(clean_text)
products_clean["description_clean"] = products_clean["description_normalized"].map(remove_stopwords)
reviews_clean["review_clean"] = reviews_clean["review_normalized"].map(remove_stopwords)
reviews_clean["Comment_Length"] = reviews_clean["review_text"].fillna("").astype(str).str.len()
reviews_clean["Word_Count"] = reviews_clean["review_clean"].str.split().str.len()
reviews_clean["Suspicious_Username"] = reviews_clean["user_name"].fillna("").astype(str).str.match(r"^(user\d{5,}|[a-z]\*{3,}[a-z])$", case=False).astype(int)
products_clean["Description_Length"] = products_clean["description_clean"].str.len()
products_clean["Detail_Field_Count"] = products_clean["product_details"].map(lambda x: len(x) if isinstance(x, dict) else 0)
products_clean["Transparency_Score"] = ((products_clean["Description_Length"].clip(upper=1000) / 1000) * .5 + (products_clean["Detail_Field_Count"].clip(upper=10) / 10) * .5)
observed_sales = products_clean.groupby("Shop_ID", as_index=False)["units_sold"].sum(min_count=1).rename(columns={"units_sold":"Sales"})
shops_clean = shops_clean.drop(columns=["Sales"], errors="ignore").merge(observed_sales, on="Shop_ID", how="left", validate="one_to_one")
'''),
code(r'''
POSITIVE = {"tốt", "đẹp", "ưng", "ok", "ổn", "nhanh", "chuẩn", "tuyệt", "hài lòng", "chất lượng"}
NEGATIVE = {"tệ", "xấu", "chậm", "lỗi", "hỏng", "kém", "thất vọng", "giả", "không tốt", "không hài lòng"}
def sentiment_score(text):
    value = "" if text is None or pd.isna(text) else str(text).lower()
    tokens = set(re.findall(r"\w+", value, flags=re.UNICODE))
    positive = sum(term in value if " " in term else term in tokens for term in POSITIVE)
    negative = sum(term in value if " " in term else term in tokens for term in NEGATIVE)
    return float((positive-negative) / max(positive+negative, 1))
reviews_clean["Sentiment_Score"] = reviews_clean["review_clean"].map(sentiment_score)
reviews_clean["Sentiment_Label"] = pd.cut(reviews_clean["Sentiment_Score"], [-1.01,-0.01,0.01,1.01], labels=["negative","neutral","positive"])

if not seller_metrics.empty:
    seller = seller_metrics.copy()
    seller["Conversion_Rate_pct"] = pd.to_numeric(seller["Conversion_Rate_pct"], errors="coerce")
    shop_seller = seller.groupby("Shop_ID", as_index=False).agg(Conversion_Rate_pct=("Conversion_Rate_pct","mean"))
    shops_clean = shops_clean.drop(columns=["Conversion_Rate_pct"], errors="ignore").merge(shop_seller, on="Shop_ID", how="left", validate="one_to_one")
    products_clean = products_clean.merge(seller[["Shop_ID","product_id","Conversion_Rate_pct"]], on=["Shop_ID","product_id"], how="left", validate="one_to_one")

audit = pd.DataFrame([
    {"dataset":"shops","raw_rows":len(shops),"clean_rows":len(shops_clean),"dropped_rows":len(shops)-len(shops_clean)},
    {"dataset":"products","raw_rows":len(products),"clean_rows":len(products_clean),"dropped_rows":len(products)-len(products_clean)},
    {"dataset":"reviews","raw_rows":len(reviews),"clean_rows":len(reviews_clean),"dropped_rows":len(reviews)-len(reviews_clean)},
])
merged = reviews_clean.merge(products_clean, on=["Shop_ID","product_id"], how="left", validate="many_to_one", suffixes=("_review","_product")).merge(shops_clean, on="Shop_ID", how="left", validate="many_to_one", suffixes=("","_shop"))
if len(merged) != len(reviews_clean): raise AssertionError("Join duplicated or lost review rows")
shops_clean.to_csv(PROCESSED / "shops_clean.csv", index=False)
products_clean.to_csv(PROCESSED / "products_clean.csv", index=False)
reviews_clean.to_csv(PROCESSED / "reviews_clean.csv", index=False)
merged.to_csv(PROCESSED / "merged_dataset.csv", index=False)
audit.to_csv(OUTPUT / "reports" / "cleaning_audit.csv", index=False)
display(audit); display(reviews_clean.head())
''')],

"02_eda.ipynb": [md('''# 02 — Exploratory Data Analysis

Produces reproducible figures and Power BI-ready summary tables. Every insight must cite an artifact generated here.'''), code(SETUP),
code(r'''
import os
os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT / ".matplotlib"))
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

shops = pd.read_csv(PROCESSED / "shops_clean.csv")
products = pd.read_csv(PROCESSED / "products_clean.csv")
reviews = pd.read_csv(PROCESSED / "reviews_clean.csv")
sns.set_theme(style="whitegrid")

def save(fig, name):
    fig.tight_layout(); fig.savefig(OUTPUT / "figures" / name, dpi=160, bbox_inches="tight"); plt.show(); plt.close(fig)
def histogram(frame, column, name):
    values = frame[column].dropna()
    if values.empty: print(f"SKIP {column}: no observed values"); return
    fig, ax = plt.subplots(); sns.histplot(values, bins=min(25,max(5,len(values))), ax=ax); ax.set_title(column); save(fig,name)

for frame, column, name in [(shops,"Follower_Count_k","followers.png"),(shops,"Rating_Average","shop_rating.png"),(shops,"Chat_Response_Rate_pct","response_rate.png"),(products,"Review_stars","product_rating.png"),(reviews,"rating","review_rating.png"),(reviews,"Comment_Length","comment_length.png")]: histogram(frame,column,name)
if not reviews["has_image"].dropna().empty:
    fig, ax = plt.subplots(); reviews["has_image"].value_counts().sort_index().plot.pie(autopct="%1.1f%%", ax=ax); ax.set_ylabel(""); ax.set_title("Review image rate"); save(fig,"has_image.png")
'''),
code(r'''
def scatter(x, y, name, title):
    if x not in shops or y not in shops or shops[[x,y]].dropna().empty: return
    fig, ax = plt.subplots(); sns.regplot(data=shops, x=x, y=y, ci=None, ax=ax); ax.set_title(title); save(fig,name)
scatter("Rating_Average","Sales","rating_sales.png","Rating vs observed sales")
scatter("Chat_Response_Rate_pct","Conversion_Rate_pct","response_conversion.png","Response rate vs conversion")
scatter("Follower_Count_k","Rating_Average","follower_rating.png","Followers vs rating")

for label in ["positive","negative"]:
    text = " ".join(reviews.loc[reviews["Sentiment_Label"] == label, "review_clean"].dropna().astype(str))
    if text.strip():
        cloud = WordCloud(width=1200,height=600,background_color="white",collocations=False).generate(text)
        fig, ax = plt.subplots(figsize=(12,6)); ax.imshow(cloud); ax.axis("off"); ax.set_title(f"{label.title()} review keywords"); save(fig,f"wordcloud_{label}.png")

observed_units = products["units_sold"].sum(min_count=1) if "units_sold" in products else np.nan
summary = pd.DataFrame({"Metric":["Total Shops","Total Products","Total Reviews","Average Review Rating","Image Rate","Observed Units Sold"],"Value":[len(shops),len(products),len(reviews),reviews["rating"].mean(),reviews["has_image"].mean(),observed_units]})
shop_eda = shops.copy()
shop_eda["Product_Count"] = shop_eda["Shop_ID"].map(products.groupby("Shop_ID").size()).fillna(0)
shop_eda["Review_Count"] = shop_eda["Shop_ID"].map(reviews.groupby("Shop_ID").size()).fillna(0)
shop_eda["Review_Image_Rate"] = shop_eda["Shop_ID"].map(reviews.groupby("Shop_ID")["has_image"].mean())
summary.to_csv(OUTPUT / "powerbi" / "kpi_summary.csv", index=False)
shop_eda.to_csv(OUTPUT / "powerbi" / "shop_eda_summary.csv", index=False)
reviews.groupby(["Shop_ID","Sentiment_Label"], observed=True).size().rename("Review_Count").reset_index().to_csv(OUTPUT / "powerbi" / "sentiment_summary.csv", index=False)
display(summary); display(shop_eda)
''')],

"03_clustering_reviews.ipynb": [md('''# 03 — Review Clustering / Truth Discovery

K-Means detects behavioral patterns, not proof of fake reviews. Cluster meaning is assigned only after human review.'''), code(SETUP),
code(r'''
import os
os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT / ".matplotlib"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
import joblib, matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

reviews = pd.read_csv(PROCESSED / "reviews_clean.csv")
features = CONFIG["clustering"]["features"]
numeric_features = reviews[features].apply(pd.to_numeric, errors="coerce")
feature_coverage = pd.DataFrame({
    "Feature": features,
    "Observed_Count": [numeric_features[c].notna().sum() for c in features],
    "Observed_Rate": [numeric_features[c].notna().mean() for c in features],
    "Unique_Observed_Values": [numeric_features[c].nunique(dropna=True) for c in features],
})
feature_coverage["Usable"] = (feature_coverage["Observed_Count"] >= 3) & (feature_coverage["Unique_Observed_Values"] >= 2)
feature_coverage.to_csv(OUTPUT / "reports" / "cluster_feature_coverage.csv", index=False)
active_features = feature_coverage.loc[feature_coverage["Usable"], "Feature"].tolist()
missing_required = [c for c in features if c not in active_features]
if missing_required:
    print("EXPLORATORY FALLBACK: unavailable/non-varying required features were excluded:", missing_required)
    print("This run is not submission-ready until all four required features are observed.")
if not active_features:
    raise ValueError("No observed clustering feature has enough coverage and variation")
complete = numeric_features[active_features].notna().all(axis=1)
if (~complete).any(): print(f"Excluded {(~complete).sum()} reviews with missing active features; values were not imputed.")
reviews = reviews.loc[complete].copy()
X = numeric_features.loc[complete, active_features]
if len(X) < 3: raise ValueError("Insufficient reviews for exploratory clustering")
distinct_rows = len(X.drop_duplicates())
if distinct_rows < 2: raise ValueError("Observed clustering features contain fewer than two distinct patterns")
scaled = StandardScaler().fit_transform(X)
rows = []
for k in CONFIG["clustering"]["k_candidates"]:
    if 2 <= k < len(X) and k <= distinct_rows:
        model = KMeans(n_clusters=k, random_state=CONFIG["project"]["random_state"], n_init=20).fit(scaled)
        rows.append({"k":k,"inertia":model.inertia_,"silhouette":silhouette_score(scaled,model.labels_)})
evaluation = pd.DataFrame(rows)
evaluation.to_csv(OUTPUT / "reports" / "cluster_k_evaluation.csv", index=False)
fig, axes = plt.subplots(1,2,figsize=(10,4)); axes[0].plot(evaluation["k"],evaluation["inertia"],marker="o"); axes[0].set_title("Elbow"); axes[1].plot(evaluation["k"],evaluation["silhouette"],marker="o"); axes[1].set_title("Silhouette"); fig.tight_layout(); fig.savefig(OUTPUT / "figures" / "cluster_selection.png",dpi=160); plt.show(); plt.close(fig)

selected_k = min(CONFIG["clustering"]["n_clusters"], distinct_rows, len(X)-1)
selected_k = max(2, selected_k)
print({"mode":"FULL" if not missing_required else "EXPLORATORY_PARTIAL_FEATURES", "active_features":active_features, "selected_k":selected_k})
pipeline = Pipeline([("scaler",StandardScaler()),("model",KMeans(n_clusters=selected_k,random_state=CONFIG["project"]["random_state"],n_init=20))])
reviews["Cluster_Label"] = pipeline.fit_predict(X)
joblib.dump(pipeline, OUTPUT / "models" / "kmeans_reviews.joblib")
'''),
code(r'''
profile = reviews.groupby("Cluster_Label").agg(Review_Count=("review_id","count"),Avg_Comment_Length=("Comment_Length","mean"),Avg_Rating=("rating","mean"),Image_Rate=("has_image","mean"),Avg_Sentiment_Score=("Sentiment_Score","mean"),Suspicious_Username_Rate=("Suspicious_Username","mean")).reset_index()
samples = reviews.sort_values(["Cluster_Label","Comment_Length"]).groupby("Cluster_Label",group_keys=False).head(5)[["Cluster_Label","Shop_ID","review_id","review_text","rating","has_image"]]
reviews.to_csv(PROCESSED / "reviews_clustered.csv", index=False)
profile.to_csv(OUTPUT / "reports" / "cluster_profile.csv", index=False)
samples.to_csv(OUTPUT / "reports" / "cluster_review_samples.csv", index=False)
display(profile); display(samples)

mapping = {int(k):float(v) for k,v in CONFIG["clustering"].get("authenticity_mapping",{}).items()}
if set(mapping) != set(reviews["Cluster_Label"].unique()):
    print("BLOCKED: team must map every cluster to 0.0, 0.5, or 1.0 in config.yaml after reviewing profiles and samples.")
else:
    if not set(mapping.values()) <= {0.0,0.5,1.0}: raise ValueError("Authenticity mapping values must be 0, 0.5 or 1")
    reviews["Is_Authentic"] = reviews["Cluster_Label"].map(mapping)
    report = reviews.groupby("Shop_ID").agg(Total_Reviews=("review_id","count"),Authentic_Review_Rate=("Is_Authentic","mean"),Suspicious_Review_Rate=("Is_Authentic",lambda s:(s==0).mean())).reset_index()
    reviews.to_csv(PROCESSED / "reviews_clustered.csv", index=False)
    report.to_csv(OUTPUT / "reports" / "Shop_Authenticity_Report.csv", index=False)
    auth_metadata = {"input_fingerprint":INPUT_FINGERPRINT,"authenticity_mapping":{str(k):float(v) for k,v in mapping.items()},"cluster_count":int(reviews["Cluster_Label"].nunique())}
    (OUTPUT / "reports" / "authenticity_metadata.json").write_text(json.dumps(auth_metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    display(report)
''')],

"04_shop_classification.ipynb": [md('''# 04 — Three-Class Shop Classification

Labels are 0 = Kém, 1 = Bình thường, 2 = Uy tín. Ground truth must be assigned and reviewed by people.'''), code(SETUP),
code(r'''
shops = pd.read_csv(PROCESSED / "shops_clean.csv")
auth_path = OUTPUT / "reports" / "Shop_Authenticity_Report.csv"
if not auth_path.exists(): raise FileNotFoundError("Run clustering and confirm authenticity mapping first")
auth = pd.read_csv(auth_path)
label_frame = shops.drop(columns=["Target_Label"], errors="ignore").merge(auth,on="Shop_ID",how="left",validate="one_to_one")
for column in ["Target_Label","Labeler","Label_Reason","Review_Status"]: label_frame[column] = ""
label_path = OUTPUT / "labeling" / "Data_To_Label.csv"
label_frame.to_csv(label_path,index=False,encoding="utf-8-sig")
print("Human-labeling template:",label_path)
display(label_frame.head())
'''),
code(r'''
import joblib, matplotlib.pyplot as plt, seaborn as sns
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

source = OUTPUT / "labeling" / "Data_Labeled.csv"
features = ["Years_Active","Total_Products","Follower_Count_k","Rating_Average","Chat_Response_Rate_pct","Authentic_Review_Rate","Conversion_Rate_pct"]
required_review = ["Labeler","Label_Reason","Review_Status"]
reasons = []
data = pd.DataFrame()
if not source.exists():
    reasons.append("Save the reviewed Data_To_Label.csv as output/labeling/Data_Labeled.csv")
else:
    data = pd.read_csv(source)
    required_columns = {"Shop_ID","Target_Label",*required_review,*features}
    missing_columns = required_columns - set(data)
    if missing_columns: reasons.append(f"Missing columns: {sorted(missing_columns)}")
    else:
        numeric_labels = pd.to_numeric(data["Target_Label"], errors="coerce")
        data = data.loc[numeric_labels.notna()].copy()
        if data.empty:
            reasons.append("Data_Labeled.csv has no labeled rows; assign Target_Label 0, 1 or 2")
        else:
            data["Target_Label"] = numeric_labels.loc[data.index].astype(int)
            if not set(data["Target_Label"]) <= {0,1,2}: reasons.append("Target_Label must contain only 0, 1 or 2")
            approved = data["Review_Status"].fillna("").astype(str).str.strip().str.lower().eq("approved")
            documented = data[["Labeler","Label_Reason"]].fillna("").astype(str).apply(lambda s:s.str.strip().ne("")).all(axis=1)
            if not (approved & documented).all(): reasons.append(f"{int((~(approved & documented)).sum())} labeled rows are not approved/documented")
            missing_feature_rows = data[features].isna().any(axis=1)
            if missing_feature_rows.any(): reasons.append(f"{int(missing_feature_rows.sum())} labeled rows have missing model features")
            counts = data["Target_Label"].value_counts().reindex([0,1,2],fill_value=0)
            minimum = CONFIG["classification"]["minimum_shops_per_class"]
            if (counts < minimum).any(): reasons.append(f"Need at least {minimum} shops per class; found {counts.to_dict()}")

readiness = pd.DataFrame([{"ready":not reasons,"labeled_rows":len(data),"blockers":" | ".join(reasons)}])
readiness.to_csv(OUTPUT/"reports"/"classification_readiness.csv",index=False)
display(readiness)

if reasons:
    print("CLASSIFICATION BLOCKED — no model or metrics were fabricated.")
    for reason in reasons: print("-",reason)
else:
    test_n = max(3,int(np.ceil(len(data)*CONFIG["classification"]["test_size"])))
    train,test = train_test_split(data,test_size=test_n,random_state=CONFIG["project"]["random_state"],stratify=data["Target_Label"])
    model = RandomForestClassifier(n_estimators=CONFIG["classification"]["n_estimators"],random_state=CONFIG["project"]["random_state"],class_weight="balanced").fit(train[features],train["Target_Label"])
    dummy = DummyClassifier(strategy="most_frequent").fit(train[features],train["Target_Label"])
    prediction = model.predict(test[features]); probability = model.predict_proba(test[features]).max(axis=1)
    macro = precision_recall_fscore_support(test["Target_Label"],prediction,average="macro",zero_division=0)
    metrics = {"input_fingerprint":INPUT_FINGERPRINT,"accuracy":accuracy_score(test["Target_Label"],prediction),"baseline_accuracy":accuracy_score(test["Target_Label"],dummy.predict(test[features])),"macro_precision":macro[0],"macro_recall":macro[1],"macro_f1":macro[2],"weighted_f1":precision_recall_fscore_support(test["Target_Label"],prediction,average="weighted",zero_division=0)[2],"target_accuracy":CONFIG["classification"]["accuracy_target"]}
    metrics["pass_accuracy_requirement"] = metrics["accuracy"] > metrics["target_accuracy"]
    cm = confusion_matrix(test["Target_Label"],prediction,labels=[0,1,2])
    fig,ax=plt.subplots(); sns.heatmap(cm,annot=True,fmt="d",xticklabels=[0,1,2],yticklabels=[0,1,2],ax=ax); ax.set(xlabel="Predicted",ylabel="Actual",title="Confusion matrix"); fig.tight_layout(); fig.savefig(OUTPUT/"figures"/"confusion_matrix.png",dpi=160); plt.show(); plt.close(fig)
    importance = pd.DataFrame({"Feature":features,"Importance":model.feature_importances_}).sort_values("Importance",ascending=False)
    fig,ax=plt.subplots(); sns.barplot(data=importance,x="Importance",y="Feature",ax=ax); fig.tight_layout(); fig.savefig(OUTPUT/"figures"/"classification_feature_importance.png",dpi=160); plt.show(); plt.close(fig)
    result = pd.DataFrame({"Shop_ID":test["Shop_ID"],"Actual_Label":test["Target_Label"],"Predicted_Label":prediction,"Predicted_Probability":probability})
    result.to_csv(OUTPUT/"reports"/"Classification_Result.csv",index=False); importance.to_csv(OUTPUT/"reports"/"Classification_Feature_Importance.csv",index=False)
    (OUTPUT/"reports"/"classification_metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    joblib.dump(model,OUTPUT/"models"/"random_forest_shop_reputation.joblib")
    print(classification_report(test["Target_Label"],prediction,labels=[0,1,2],zero_division=0)); display(pd.DataFrame([metrics])); display(importance)
''')],

"05_regression.ipynb": [md('''# 05 — Follower Count Regression

This cross-sectional model describes association, not future growth or causality.'''), code(SETUP),
code(r'''
import matplotlib.pyplot as plt, seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

shops = pd.read_csv(PROCESSED / "shops_clean.csv")
auth_path = OUTPUT / "reports" / "Shop_Authenticity_Report.csv"
if not auth_path.exists(): raise FileNotFoundError("Shop_Authenticity_Report.csv is required")
data = shops.merge(pd.read_csv(auth_path)[["Shop_ID","Authentic_Review_Rate"]],on="Shop_ID",how="left",validate="one_to_one")
features = CONFIG["regression"]["features"]; target = CONFIG["regression"]["target"]
data = data.dropna(subset=[target,*features]).copy()
if len(data) < 15: raise ValueError(f"Need at least 15 complete shops; found {len(data)}")
x_train,x_test,y_train,y_test=train_test_split(data[features],data[target],test_size=max(3,int(np.ceil(len(data)*.2))),random_state=CONFIG["project"]["random_state"])
model=LinearRegression().fit(x_train,y_train); prediction=model.predict(x_test)
x_scaler,y_scaler=StandardScaler(),StandardScaler(); standardized=LinearRegression().fit(x_scaler.fit_transform(data[features]),y_scaler.fit_transform(data[[target]]).ravel())
coefficients=pd.DataFrame({"Feature":features,"Coefficient":model.coef_,"Standardized_Coefficient":standardized.coef_}); coefficients["Direction"]=np.where(coefficients["Coefficient"]>=0,"positive","negative"); coefficients["Absolute_Standardized_Coefficient"]=coefficients["Standardized_Coefficient"].abs()
metrics={"input_fingerprint":INPUT_FINGERPRINT,"MAE":mean_absolute_error(y_test,prediction),"RMSE":mean_squared_error(y_test,prediction)**.5,"R2":r2_score(y_test,prediction)}
'''),
code(r'''
residuals=y_test-prediction
fig,axes=plt.subplots(1,2,figsize=(10,4)); sns.scatterplot(x=prediction,y=residuals,ax=axes[0]); axes[0].axhline(0,color="red"); axes[0].set(xlabel="Predicted",ylabel="Residual",title="Residuals"); sns.histplot(residuals,kde=True,ax=axes[1]); axes[1].set_title("Residual distribution"); fig.tight_layout(); fig.savefig(OUTPUT/"figures"/"regression_residuals.png",dpi=160); plt.show(); plt.close(fig)
corr=data[features].corr().abs(); high=[]
for i,a in enumerate(features):
    for b in features[i+1:]:
        if corr.loc[a,b]>=.8: high.append({"Feature_A":a,"Feature_B":b,"Absolute_Correlation":corr.loc[a,b]})
coefficients.to_csv(OUTPUT/"reports"/"Regression_Result.csv",index=False); pd.DataFrame(high).to_csv(OUTPUT/"reports"/"regression_multicollinearity_flags.csv",index=False)
(OUTPUT/"reports"/"regression_metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
display(coefficients.sort_values("Absolute_Standardized_Coefficient",ascending=False)); display(pd.DataFrame([metrics])); display(pd.DataFrame(high))
''')],

"06_final_analysis.ipynb": [md('''# 06 — Final DIKW Analysis

Builds traceable report facts. It refuses to invent Wisdom when required model artifacts are absent.'''), code(SETUP),
code(r'''
required = {"shops":PROCESSED/"shops_clean.csv","reviews":PROCESSED/"reviews_clustered.csv","profile":OUTPUT/"reports"/"cluster_profile.csv","authenticity":OUTPUT/"reports"/"Shop_Authenticity_Report.csv","classification":OUTPUT/"reports"/"Classification_Result.csv","regression":OUTPUT/"reports"/"Regression_Result.csv"}
missing=[name for name,path in required.items() if not path.exists()]
if missing: raise FileNotFoundError("Required final artifacts are missing: "+", ".join(missing))
frames={name:pd.read_csv(path) for name,path in required.items()}
class_metrics=json.loads((OUTPUT/"reports"/"classification_metrics.json").read_text(encoding="utf-8"))
reg_metrics=json.loads((OUTPUT/"reports"/"regression_metrics.json").read_text(encoding="utf-8"))
reviews=frames["reviews"]; shops=frames["shops"]; authenticity=frames["authenticity"]; regression=frames["regression"]
if "Is_Authentic" not in reviews: raise ValueError("Human-confirmed authenticity mapping has not been applied")
top_factor=regression.sort_values("Absolute_Standardized_Coefficient",ascending=False).iloc[0]
class_result=frames["classification"]
class_recall=class_result.assign(correct=lambda d:d["Actual_Label"]==d["Predicted_Label"]).groupby("Actual_Label")["correct"].mean()
weakest_class=int(class_recall.idxmin())
def finite_or_none(value):
    return float(value) if value is not None and np.isfinite(value) else None
facts={
 "input_fingerprint":INPUT_FINGERPRINT,
 "suspicious_review_pct":float((reviews["Is_Authentic"]==0).mean()*100),
 "lowest_authenticity_shop":authenticity.sort_values("Authentic_Review_Rate").iloc[0]["Shop_ID"],
 "highest_authenticity_shop":authenticity.sort_values("Authentic_Review_Rate").iloc[-1]["Shop_ID"],
 "classification_accuracy":class_metrics["accuracy"],"classification_macro_f1":class_metrics["macro_f1"],
 "classification_weakest_class":weakest_class,"classification_weakest_class_recall":float(class_recall.loc[weakest_class]),
 "regression_r2":reg_metrics["R2"],"strongest_standardized_factor":top_factor["Feature"],"strongest_standardized_coefficient":top_factor["Standardized_Coefficient"],
 "rating_sales_correlation":finite_or_none(shops[["Rating_Average","Sales"]].corr().iloc[0,1]) if "Sales" in shops else None,
 "response_conversion_correlation":finite_or_none(shops[["Chat_Response_Rate_pct","Conversion_Rate_pct"]].corr().iloc[0,1]) if "Conversion_Rate_pct" in shops else None,
 "interpretation_guardrail":"Clusters indicate suspicious patterns, and regression is association rather than causality."
}
(OUTPUT/"reports"/"wisdom_facts.json").write_text(json.dumps(facts,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
pd.DataFrame([facts]).to_csv(OUTPUT/"powerbi"/"wisdom_summary.csv",index=False)
display(pd.DataFrame([facts]))
'''),
code(r'''
lines=["# Computed Wisdom Facts","","> Auto-generated from model outputs. Review wording before publication.",""]
for key,value in facts.items(): lines.append(f"- **{key}**: {value}")
(OUTPUT/"reports"/"wisdom_facts.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("Final facts exported for the report and Power BI.")
''')],
}


for filename, cells in NOTEBOOKS.items():
    notebook = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (SRC / filename).write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", SRC / filename)
