#!/usr/bin/env python3
"""Evaluate the evidence required for a Shopee DIKW submission.

The checker is deliberately strict: missing real data or human approvals are
reported as blockers and are never replaced with generated values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _json_rows(folder: Path, pattern: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(folder.glob(pattern)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"{path}: top-level JSON must be a list")
        rows.extend(payload)
    return rows


def _report_pages(path: Path) -> int:
    """Count PDF pages without making pypdf a runtime requirement."""
    try:
        from pypdf import PdfReader

        return len(PdfReader(path).pages)
    except ImportError:
        data = path.read_bytes()
        return len(re.findall(rb"/Type\s*/Page(?!s)\b", data))
    except Exception:
        return 0


def _https_url(value: object, host: str) -> bool:
    text = str(value or "").strip()
    return text.startswith("https://") and host in text


def _input_fingerprint(root: Path, config: dict) -> str:
    paths = [root / "config/config.yaml", root / config["paths"]["shops"]]
    for key in ("products", "reviews"):
        paths.extend(sorted((root / config["paths"][key]).glob("shop_*.json")))
    seller = root / config["paths"]["seller_metrics"]
    paths.extend(path for path in (seller, seller.with_suffix(".xlsx")) if path.exists())
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(root)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def evaluate(root: Path = ROOT) -> dict:
    config = yaml.safe_load((root / "config/config.yaml").read_text(encoding="utf-8"))
    dq = config["data_quality"]
    input_fingerprint = _input_fingerprint(root, config)
    shops = pd.read_excel(root / config["paths"]["shops"], dtype={"Shop_ID": str})
    products = _json_rows(root / config["paths"]["products"], "shop_*_products.json")
    reviews = _json_rows(root / config["paths"]["reviews"], "shop_*_reviews.json")
    product_frame = pd.DataFrame(products)
    review_frame = pd.DataFrame(reviews)

    shop_ids = set(shops.get("Shop_ID", pd.Series(dtype=str)).dropna())
    product_ids = set(product_frame.get("product_id", pd.Series(dtype=str)).dropna())
    product_counts = product_frame.groupby("Shop_ID").size() if not product_frame.empty and "Shop_ID" in product_frame else pd.Series(dtype=int)
    text_mask = review_frame.get("review_text", pd.Series(index=review_frame.index, dtype=object)).fillna("").astype(str).str.strip().ne("")
    text_reviews = review_frame.loc[text_mask]
    review_counts = text_reviews.groupby("product_id").size() if not text_reviews.empty and "product_id" in text_reviews else pd.Series(dtype=int)
    review_product_ids = set(review_frame.get("product_id", pd.Series(dtype=str)).dropna())

    def complete_column(frame: pd.DataFrame, name: str) -> bool:
        return name in frame and frame[name].notna().all()

    product_provenance = bool(products) and all(
        (
            row.get("product_url")
            or (row.get("product_details") or {}).get("source_product_url")
        )
        and (
            row.get("Time_Collected")
            or (row.get("product_details") or {}).get("collection_date")
        )
        and (
            row.get("Data_Source")
            or row.get("product_url")
            or (row.get("product_details") or {}).get("source_product_url")
        )
        for row in products
    )
    product_provenance_by_id = {
        row.get("product_id"): {
            "source_url": row.get("product_url") or (row.get("product_details") or {}).get("source_product_url"),
            "collected_at": row.get("Time_Collected") or (row.get("product_details") or {}).get("collection_date"),
        }
        for row in products
    }
    review_provenance = bool(reviews) and all(
        (
            row.get("source_url")
            or row.get("Data_Source")
            or product_provenance_by_id.get(row.get("product_id"), {}).get("source_url")
        )
        and (
            row.get("collection_date")
            or row.get("Time_Collected")
            or product_provenance_by_id.get(row.get("product_id"), {}).get("collected_at")
        )
        for row in reviews
    )

    seller = root / config["paths"]["seller_metrics"]
    seller_source = next((path for path in (seller, seller.with_suffix(".xlsx")) if path.exists()), None)
    seller_valid = False
    if seller_source:
        seller_frame = pd.read_excel(seller_source) if seller_source.suffix == ".xlsx" else pd.read_csv(seller_source)
        required = {"Shop_ID", "Conversion_Rate_pct", "Source", "Collection_Status"}
        conversion = pd.to_numeric(seller_frame.get("Conversion_Rate_pct"), errors="coerce")
        seller_keys = ["Shop_ID", "product_id"] if "product_id" in seller_frame else ["Shop_ID"]
        seller_valid = bool(not seller_frame.empty and required <= set(seller_frame) and conversion.notna().all() and conversion.between(0, 100).all() and not seller_frame.duplicated(seller_keys).any())
    mapping = config["clustering"].get("authenticity_mapping") or {}
    auth_metadata_path = root / "output/reports/authenticity_metadata.json"
    auth_metadata = json.loads(auth_metadata_path.read_text(encoding="utf-8")) if auth_metadata_path.exists() else {}
    expected_mapping = {str(key): float(value) for key, value in mapping.items()}
    authenticity_ready = bool(
        mapping
        and (root / "output/reports/Shop_Authenticity_Report.csv").exists()
        and auth_metadata.get("input_fingerprint") == input_fingerprint
        and auth_metadata.get("authenticity_mapping") == expected_mapping
    )
    metrics_path = root / "output/reports/classification_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    regression_metrics_path = root / "output/reports/regression_metrics.json"
    regression_metrics = json.loads(regression_metrics_path.read_text(encoding="utf-8")) if regression_metrics_path.exists() else {}
    wisdom_path = root / "output/reports/wisdom_facts.json"
    wisdom = json.loads(wisdom_path.read_text(encoding="utf-8")) if wisdom_path.exists() else {}

    powerbi_path = next((p for p in (root / "powerbi").glob("*.pbix")), None)
    powerbi_evidence_path = root / "powerbi/verification.json"
    powerbi_evidence = json.loads(powerbi_evidence_path.read_text(encoding="utf-8")) if powerbi_evidence_path.exists() else {}
    required_pages = {"Tổng quan shop", "Sản phẩm và review", "Uy tín và chuyển đổi"}
    powerbi_verified = bool(
        powerbi_path
        and required_pages <= set(powerbi_evidence.get("pages", []))
        and powerbi_evidence.get("refresh_passed") is True
        and powerbi_evidence.get("cross_filter_passed") is True
        and str(powerbi_evidence.get("verified_by", "")).strip()
        and str(powerbi_evidence.get("verified_at", "")).strip()
        and powerbi_evidence.get("input_fingerprint") == input_fingerprint
    )

    metadata_path = root / "submission/submission_metadata.yaml"
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    links_verified = bool(
        _https_url(metadata.get("colab_url"), "colab.research.google.com")
        and _https_url(metadata.get("drive_url"), "drive.google.com")
        and metadata.get("access_verified") is True
        and str(metadata.get("verified_by", "")).strip()
        and str(metadata.get("verified_at", "")).strip()
        and metadata.get("input_fingerprint") == input_fingerprint
    )

    report_path = root / "report/Final_Report.pdf"
    report_pages = _report_pages(report_path) if report_path.exists() else 0

    checks = {
        "THREE_DATA_TYPES": bool(len(shops) and products and reviews),
        "MINIMUM_REAL_SHOPS": len(shop_ids) >= dq["minimum_shops"],
        "PRODUCTS_PER_SHOP": bool(shop_ids) and all(
            dq["minimum_products_per_shop"] <= int(product_counts.get(shop_id, 0)) <= dq["maximum_products_per_shop"]
            for shop_id in shop_ids
        ),
        "REVIEWS_PER_PRODUCT": bool(product_ids) and all(
            int(review_counts.get(product_id, 0)) >= dq["minimum_text_reviews_per_product"] for product_id in product_ids
        ),
        "REFERENTIAL_INTEGRITY": bool(product_ids) and review_product_ids <= product_ids and set(product_frame["Shop_ID"]) <= shop_ids,
        "PRODUCT_PROVENANCE": product_provenance,
        "REVIEW_PROVENANCE": review_provenance,
        "REVIEW_RATING_COMPLETE": complete_column(review_frame, "rating"),
        "REVIEW_IMAGE_COMPLETE": complete_column(review_frame, "has_image"),
        "SELLER_METRICS": seller_valid,
        "AUTHENTICITY_MAPPING": bool(mapping) and set(map(float, mapping.values())) == {0.0, 0.5, 1.0},
        "AUTHENTICITY_REPORT": authenticity_ready,
        "CLASSIFICATION_RESULT": (root / "output/reports/Classification_Result.csv").exists() and metrics.get("input_fingerprint") == input_fingerprint and metrics.get("valid_ground_truth_evaluation") is True,
        "CLASSIFICATION_ACCURACY": metrics.get("input_fingerprint") == input_fingerprint and metrics.get("valid_ground_truth_evaluation") is True and float(metrics.get("accuracy", 0)) > float(config["classification"]["accuracy_target"]),
        "CLASSIFICATION_MACRO_F1": metrics.get("input_fingerprint") == input_fingerprint and metrics.get("valid_ground_truth_evaluation") is True and pd.notna(metrics.get("macro_f1")),
        "REGRESSION_RESULT": (root / "output/reports/Regression_Result.csv").exists() and regression_metrics.get("input_fingerprint") == input_fingerprint,
        "WISDOM_FACTS": wisdom.get("input_fingerprint") == input_fingerprint,
        "POWER_BI_VERIFIED": powerbi_verified,
        "FINAL_REPORT_10_PAGES": report_pages >= 10,
        "COLAB_DRIVE_ACCESS": links_verified,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    return {
        "checks": checks,
        "overall_ready": all(checks.values()),
        "evidence": {
            "shops": len(shop_ids),
            "products": len(product_ids),
            "reviews": len(reviews),
            "text_reviews": len(text_reviews),
            "report_pages": report_pages,
            "powerbi_file": powerbi_path.name if powerbi_path else None,
            "input_fingerprint": input_fingerprint,
        },
    }


def render(result: dict) -> str:
    lines = [f"{name:<32} {'PASS' if passed else 'FAIL'}" for name, passed in result["checks"].items()]
    evidence = result["evidence"]
    lines.extend([
        "",
        f"COUNTS: shops={evidence['shops']}, products={evidence['products']}, reviews={evidence['reviews']}, text_reviews={evidence['text_reviews']}",
        f"FINAL_REPORT_PAGES: {evidence['report_pages']}",
        "",
        f"OVERALL: {'READY FOR SUBMISSION' if result['overall_ready'] else 'NOT READY FOR SUBMISSION'}",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true", help="Write output/reports/submission_check.txt and JSON evidence")
    args = parser.parse_args()
    result = evaluate(args.root.resolve())
    text = render(result)
    print(text, end="")
    if args.write:
        folder = args.root.resolve() / "output/reports"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "submission_check.txt").write_text(text, encoding="utf-8")
        (folder / "submission_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result["overall_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
