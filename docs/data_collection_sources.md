# Data collection sources

Collection date: 2026-09-21 (Asia/Ho_Chi_Minh).

| Shop_ID | Shopee username | Source URL | Shopee shop ID |
|---|---|---|---:|
| 01_001 | maisononline | https://shopee.vn/maisononline | 364616598 |
| 01_002 | astromazing | https://shopee.vn/astromazing | 320823232 |
| 01_003 | camelia_vn | https://shopee.vn/camelia_vn | 233235070 |

Shop metadata was collected from Shopee's public shop-detail response. Product names and displayed ratings were transcribed from public Shopee shop/listing pages. Local IDs follow the deterministic project convention and are not claimed to be Shopee's internal item IDs.

The user-provided URLs contained Shopee item IDs `22323464989` and `7618653327`, but the item-detail endpoint was blocked, so those IDs were not assigned to any local product record without verification.

## Collection limitation

Shopee returned anti-automation error `90309999` for product-detail, item-list and rating endpoints. The interactive browser was unavailable. Therefore the three Review JSON files are valid empty arrays: no review text was fabricated. Product `description_text` contains only the observed listing title/summary, not an inaccessible full product description. `Has_Voucher` is left blank where it could not be verified.

These three shops satisfy the user's requested scope but do not satisfy the course minimum of 5-10 shops. Real Review records must be collected manually from Shopee or supplied through an authorized export before clustering, authenticity scoring and classification can run.
