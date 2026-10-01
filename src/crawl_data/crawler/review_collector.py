from __future__ import annotations

from .errors import SchemaChanged
from .normalizers import normalize_review


class ReviewCollector:
    def __init__(self, client, settings): self.client = client; self.settings = settings

    async def collect(self, manifest_row):
        collected, seen = [], set()
        rejected_without_text = 0
        for page_number in range(self.settings.max_pages):
            offset = page_number * self.settings.page_size
            base = (
                "https://shopee.vn/api/v2/item/get_ratings"
                f"?flag=1&itemid={manifest_row['shopee_item_id']}&limit={self.settings.page_size}"
                f"&offset={offset}&shopid={manifest_row['shopee_shop_id']}&type=0"
            )
            body = await self.client.get_json(base + "&filter=1")
            ratings = ((body.get("data") or {}).get("ratings") or [])
            if not ratings:
                body = await self.client.get_json(base + "&filter=0")
                ratings = ((body.get("data") or {}).get("ratings") or [])
            if not isinstance(ratings, list): raise SchemaChanged("ratings is not a list")
            if not ratings: break
            for raw in ratings:
                row = normalize_review(raw, manifest_row)
                if not row["review_text"]:
                    rejected_without_text += 1; continue
                if not 1 <= row["rating"] <= 5: continue
                if row["review_id"] in seen: continue
                seen.add(row["review_id"]); collected.append(row)
                if len(collected) >= self.settings.reviews_per_product:
                    return collected, {"rejected_without_text": rejected_without_text, "pages": page_number+1}
        return collected, {"rejected_without_text": rejected_without_text, "pages": min(self.settings.max_pages, page_number+1)}
