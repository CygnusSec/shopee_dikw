from datetime import datetime
from zoneinfo import ZoneInfo

from .normalizers import normalize_shop


class ShopCollector:
    def __init__(self, client): self.client = client
    async def collect(self, manifest_row):
        url = f"https://shopee.vn/api/v4/shop/get_shop_detail?shopid={manifest_row['shopee_shop_id']}"
        payload = await self.client.get_json(url)
        return normalize_shop(payload, manifest_row, datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()), payload
