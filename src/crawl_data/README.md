# Thu thập Review thật từ Shopee

Notebook `collect_shopee_reviews.ipynb` điền trực tiếp 3 file:

```text
Shopee_Dataset/3_Unstructured_Data/
├── shop_01_001_reviews.json
├── shop_01_002_reviews.json
└── shop_01_003_reviews.json
```

Mỗi Shop đã được ánh xạ tới 10 sản phẩm Shopee thật trong `product_review_mapping.json`.

## Chạy bằng notebook

Mở `src/crawl_data/collect_shopee_reviews.ipynb` bằng Jupyter và chạy lần lượt từng cell.

Nếu mở Jupyter ngay trong `src/crawl_data`, có thể cài dependency bằng:

```bash
pip install -r requirements.txt
playwright install chromium
```

Notebook chia riêng bước mở trình duyệt và bước crawl. Sau khi cell mở Chromium chạy xong, đăng nhập trực tiếp trong Chromium rồi quay lại notebook chạy cell **Thu thập và ghi Review JSON**.

Trình duyệt sẽ mở Shopee. Nếu Shopee yêu cầu đăng nhập, hãy đăng nhập **trực tiếp trong trình duyệt**.
Không nhập mật khẩu vào script hoặc terminal.

Không nhập mật khẩu vào notebook hoặc terminal.

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
Shopee_Dataset/review_collection_report.md
```

để biết số review, số review có ảnh, review thiếu ngày và sản phẩm bị lỗi.
