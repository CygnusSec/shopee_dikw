from __future__ import annotations

from collections import Counter


REVIEW_FIELDS = {"Shop_ID","product_id","review_id","user_name","rating","review_time","review_text","has_image","Data_Source"}
PRODUCT_FIELDS = {"Shop_ID","product_id","product_name","product_details","description_text","Review_stars","units_sold","product_url","Time_Collected","Data_Source"}


def validate_collection(manifest, products, reviews, minimum_shops=15, minimum_products=5, maximum_products=10, minimum_reviews=5):
    errors, warnings = [], []
    shops = {row["Shop_ID"] for row in manifest}
    if len(shops) < minimum_shops: warnings.append(f"Only {len(shops)}/{minimum_shops} shops configured")
    counts = Counter(row["Shop_ID"] for row in manifest)
    for shop_id, count in counts.items():
        if not minimum_products <= count <= maximum_products: warnings.append(f"{shop_id}: {count} products, expected {minimum_products}-{maximum_products}")
    valid_product_ids = {row["product_id"] for row in manifest}
    seen_reviews = set()
    for row in products:
        missing = PRODUCT_FIELDS-set(row)
        if missing: errors.append(f"product {row.get('product_id')}: missing {sorted(missing)}")
    review_counts = Counter()
    for row in reviews:
        missing = REVIEW_FIELDS-set(row)
        if missing: errors.append(f"review {row.get('review_id')}: missing {sorted(missing)}")
        if row.get("product_id") not in valid_product_ids: errors.append(f"review {row.get('review_id')}: unknown product")
        if row.get("review_id") in seen_reviews: errors.append(f"duplicate review_id {row.get('review_id')}")
        seen_reviews.add(row.get("review_id")); review_counts[row.get("product_id")] += 1
    for product_id in valid_product_ids:
        if review_counts[product_id] < minimum_reviews: warnings.append(f"{product_id}: {review_counts[product_id]}/{minimum_reviews} text reviews")
    return {"errors": errors, "warnings": warnings, "valid": not errors}
