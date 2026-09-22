# Shopee_Dataset — trạng thái thu thập

## Shop_ID
- `01_001`: Maison Online
- `01_002`: AstroMazing Official Store
- `01_003`: Camelia Brand

## Cấu trúc
- `1_Structured_Data/shops_master.xlsx`
- `2_Semi_Structured_Data/shop_<id>_products.json`
- `3_Unstructured_Data/shop_<id>_reviews.json`

Mỗi shop hiện có **10 sản phẩm** trong dữ liệu bán cấu trúc.

## Chất lượng dữ liệu
Dữ liệu được thu thập từ các trang Shopee công khai/indexed ngày 2026-09-21.

Các trường không xác minh được từ nội dung công khai đã truy xuất được để `null`:
- `Years_Active`
- `Total_Ratings_k`
- mô tả sản phẩm đầy đủ

## Review
Nội dung review/comment trên Shopee được tải động và không xuất hiện trong bản trang công khai/indexed
mà phiên này truy xuất được. Vì vậy các file `*_reviews.json` hiện là `[]` thay vì tạo review giả.

Để hoàn thiện đúng yêu cầu bài, bổ sung review thật theo schema:

```json
{
  "Shop_ID": "01_001",
  "product_id": "sp_01_001_001",
  "review_id": "rv_01_001_000001",
  "user_name": "...",
  "rating": 5,
  "review_time": "YYYY-MM-DD",
  "review_text": "...",
  "has_image": 1
}
```

Phải giữ nguyên `Shop_ID` và `product_id` để đảm bảo Data Linkage.
