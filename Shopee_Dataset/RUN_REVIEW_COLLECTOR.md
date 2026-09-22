# Thu thập Review thật từ Shopee

Script này điền trực tiếp 3 file:

```text
3_Unstructured_Data/
├── shop_01_001_reviews.json
├── shop_01_002_reviews.json
└── shop_01_003_reviews.json
```

Mỗi Shop đã được ánh xạ tới 10 sản phẩm Shopee thật trong `product_review_mapping.json`.

## Chạy

```bash
cd Shopee_Dataset

python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows

pip install -r requirements-collector.txt
playwright install chromium

python scripts/collect_shopee_reviews.py --reviews-per-product 5
```

Trình duyệt sẽ mở Shopee. Nếu Shopee yêu cầu đăng nhập, hãy đăng nhập **trực tiếp trong trình duyệt**.
Không nhập mật khẩu vào script hoặc terminal.

Sau khi đăng nhập xong, quay lại terminal và nhấn ENTER.

## Kết quả mong đợi

```text
Maison:      10 x 5 = 50 review
AstroMazing: 10 x 5 = 50 review
Camelia:     10 x 5 = 50 review
Total:       >= 150 review
```

Script chỉ lấy review có nội dung text thật từ response Shopee và không tạo review giả.

Nếu một sản phẩm không đủ 5 review text, report sẽ ghi rõ số lượng thực lấy được thay vì tự sinh thêm.

## Kiểm tra

Sau khi chạy, xem:

```text
review_collection_report.md
```

để biết số review, số review có ảnh, review thiếu ngày và sản phẩm bị lỗi.
