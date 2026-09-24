from __future__ import annotations

import asyncio
import random

from .errors import AntiAutomation, AuthRequired, NetworkError, RateLimited, RecordNotFound, SchemaChanged


class BrowserClient:
    def __init__(self, page, settings): self.page = page; self.settings = settings

    async def delay(self):
        await asyncio.sleep(random.uniform(self.settings.request_delay_min_seconds, self.settings.request_delay_max_seconds))

    async def get_json(self, url):
        last_error = None
        for attempt in range(1, self.settings.retry_attempts + 1):
            try:
                result = await self.page.evaluate("""async (url) => {
                    const response = await fetch(url, {credentials: 'include', headers: {'accept':'application/json, text/plain, */*'}});
                    const text = await response.text();
                    let body; try { body = JSON.parse(text); } catch (_) { body = {__raw_text:text}; }
                    return {status:response.status, body};
                }""", url)
                status, body = result.get("status"), result.get("body") or {}
                if status in (401, 403): raise AuthRequired(f"HTTP {status}")
                if status == 404: raise RecordNotFound(f"HTTP {status}")
                if status == 429: raise RateLimited("HTTP 429")
                if status in (500, 502, 503, 504): raise NetworkError(f"HTTP {status}")
                if status != 200: raise NetworkError(f"Unexpected HTTP {status}")
                error = body.get("error") if isinstance(body, dict) else None
                if error in (90309999, 90309998): raise AntiAutomation(f"Shopee error {error}")
                if error not in (None, 0): raise SchemaChanged(f"Shopee API error {error}")
                await self.delay()
                return body
            except (AuthRequired, RecordNotFound, AntiAutomation, SchemaChanged):
                raise
            except Exception as error:
                last_error = error
                if attempt < self.settings.retry_attempts:
                    await asyncio.sleep(self.settings.backoff_seconds * (2 ** (attempt-1)) + random.random())
        if isinstance(last_error, RateLimited): raise last_error
        raise NetworkError(f"Request failed after {self.settings.retry_attempts} attempts: {last_error}")

    async def health_check(self, manifest_row):
        url = f"https://shopee.vn/api/v2/item/get_ratings?flag=1&itemid={manifest_row['shopee_item_id']}&limit=1&offset=0&shopid={manifest_row['shopee_shop_id']}&type=0&filter=0"
        body = await self.get_json(url)
        if not isinstance(body.get("data"), dict): raise SchemaChanged("Health check response has no data object")
        return True
