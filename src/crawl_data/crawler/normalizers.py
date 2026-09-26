from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .errors import SchemaChanged


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def safe_date(value):
    if value in (None, ""):
        return None
    try:
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        return datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone(VN_TZ).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def stable_review_id(raw, shop_id, product_id):
    source_id = raw.get("cmtid") or raw.get("comment_id")
    if source_id not in (None, ""):
        return f"rv_{shop_id}_{source_id}"
    identity = "|".join(str(value or "") for value in (
        shop_id, product_id, raw.get("author_username") or raw.get("username"),
        raw.get("ctime") or raw.get("create_time"),
        (raw.get("comment") or raw.get("comment_text") or "").strip().lower(),
    ))
    return f"rv_{shop_id}_{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]}"


def normalize_review(raw, manifest_row):
    if not isinstance(raw, dict):
        raise SchemaChanged("Review record is not an object")
    images = raw.get("images") or raw.get("image") or []
    if not isinstance(images, list): images = [images] if images else []
    rating = raw.get("rating_star") or raw.get("rating")
    try: rating = int(rating)
    except (TypeError, ValueError): raise SchemaChanged("Review rating is absent or invalid")
    text = (raw.get("comment") or raw.get("comment_text") or "").strip()
    shop_id, product_id = manifest_row["Shop_ID"], manifest_row["product_id"]
    collected_at = datetime.now(VN_TZ).date().isoformat()
    return {
        "Shop_ID": shop_id,
        "product_id": product_id,
        "review_id": stable_review_id(raw, shop_id, product_id),
        "user_name": raw.get("author_username") or raw.get("username") or "unknown",
        "rating": rating,
        "review_time": safe_date(raw.get("ctime") or raw.get("create_time")),
        "review_text": text,
        "has_image": int(bool(images)),
        "source_comment_id": raw.get("cmtid") or raw.get("comment_id"),
        "source_url": manifest_row["product_url"],
        "Time_Collected": collected_at,
        "Data_Source": "Shopee public product review endpoint",
        "Verification_Status": "collected_from_endpoint",
    }


def normalize_product(payload, manifest_row, collected_at):
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise SchemaChanged("Product response has no data object")
    rating = data.get("item_rating", {}).get("rating_star", data.get("rating_star"))
    sold = data.get("historical_sold", data.get("sold"))
    details = {}
    for item in data.get("attributes") or []:
        if isinstance(item, dict):
            name = item.get("name") or item.get("display_name")
            value = item.get("value") or item.get("display_value")
            if name: details[str(name)] = value
    return {
        "Shop_ID": manifest_row["Shop_ID"],
        "product_id": manifest_row["product_id"],
        "product_name": data.get("name") or manifest_row.get("product_name") or "",
        "product_details": details,
        "description_text": data.get("description") or "",
        "Review_stars": float(rating) if rating is not None else None,
        "units_sold": int(sold) if sold is not None else None,
        "product_url": manifest_row["product_url"],
        "Time_Collected": collected_at,
        "Data_Source": "Shopee public product detail endpoint",
    }


def normalize_shop(payload, manifest_row, collected_at):
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise SchemaChanged("Shop response has no data object")
    created = data.get("ctime") or data.get("create_time")
    years = None
    if created:
        created_date = datetime.fromtimestamp(int(created), tz=timezone.utc).date()
        years = max(0, (datetime.now(timezone.utc).date() - created_date).days // 365)
    return {
        "Shop_ID": manifest_row["Shop_ID"],
        "Shop_Name": data.get("name") or manifest_row.get("Shop_Name") or "",
        "Shop_type": data.get("shop_type") or "unknown",
        "Years_Active": years,
        "Is_Online_Now": int(bool(data.get("is_online"))),
        "Total_Products": data.get("item_count"),
        "Follower_Count_k": (data.get("follower_count") / 1000) if data.get("follower_count") is not None else None,
        "Rating_Average": data.get("rating_star"),
        "Total_Ratings_k": (data.get("rating_count") / 1000) if data.get("rating_count") is not None else None,
        "Chat_Response_Rate_pct": data.get("response_rate"),
        "Has_Voucher": None,
        "Target_Label": None,
        "Time_Collected": collected_at,
        "Data_Source": "Shopee public shop detail endpoint",
    }


def sanitize_raw(value):
    blocked = {"cookie", "cookies", "token", "access_token", "refresh_token", "authorization", "phone", "email"}
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in blocked else sanitize_raw(item) for key, item in value.items()}
    if isinstance(value, list): return [sanitize_raw(item) for item in value]
    return value


def canonical_hash(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
