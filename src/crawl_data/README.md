# Thu thập Review thật từ Shopee

Notebook chính là `collect_shopee_data.ipynb`. Nó đọc manifest `product_review_mapping.json`, thu thập Shop/Product/Review, checkpoint sau từng sản phẩm và merge vào dữ liệu cũ. `collect_shopee_reviews.ipynb` chỉ được giữ lại để tham khảo lịch sử.

```text
Shopee_Dataset/3_Unstructured_Data/
├── shop_01_001_reviews.json
├── shop_01_002_reviews.json
└── ...
```

Trước khi chạy, mở rộng manifest lên ít nhất 15 shop, mỗi shop 5–10 sản phẩm. Mỗi dòng phải có `Shop_ID`, `Shop_Name`, `product_id`, `product_name`, `shopee_shop_id`, `shopee_item_id` và `product_url`. Notebook không chứa danh sách shop hard-code.

## Chạy bằng notebook

Mở `src/crawl_data/collect_shopee_data.ipynb` bằng Jupyter và chạy lần lượt từng cell. Tùy chỉnh timeout, retry, delay, headless, dry-run và resume trong `crawl_config.yaml`.

Nếu mở Jupyter ngay trong `src/crawl_data`, có thể cài dependency bằng:

```bash
pip install -r requirements.txt
playwright install chromium
```

Notebook chia riêng bước mở trình duyệt và bước crawl. Sau khi cell mở Chromium chạy xong, đăng nhập trực tiếp trong Chromium rồi quay lại notebook chạy cell thu thập.

Notebook tự kiểm tra `DISPLAY`/`WAYLAND_DISPLAY`. Trên Colab, Docker hoặc server không có XServer, nó tự chuyển sang `headless=True` để tránh `TargetClosedError`. Nếu Shopee yêu cầu đăng nhập hoặc CAPTCHA, headless không thể cho người dùng thao tác; khi đó cần chạy notebook trên máy local có giao diện hoặc dùng XServer/Xvfb do môi trường cung cấp. Tool không tự vượt bước xác minh.

Trình duyệt sẽ mở Shopee. Nếu Shopee yêu cầu đăng nhập, hãy đăng nhập **trực tiếp trong trình duyệt**.
Không nhập mật khẩu vào script hoặc terminal.

Không nhập mật khẩu vào notebook hoặc terminal.

## Kết quả mong đợi

```text
Mỗi sản phẩm: >= 5 review có text
Mỗi shop:     5–10 sản phẩm
Toàn bộ:      >= 15 shop
```

Tool dùng ID review ổn định từ comment ID hoặc hash nội dung, ghi file atomically và không xóa dữ liệu cũ khi lượt crawl mới trả ít kết quả hơn. Session hết hạn hoặc anti-automation sẽ dừng an toàn sau khi ghi checkpoint. Tool không vượt CAPTCHA, không né cơ chế bảo vệ và không tạo dữ liệu giả.

Nếu một sản phẩm không đủ 5 review text, report sẽ ghi rõ số lượng thực lấy được thay vì tự sinh thêm.

## Kiểm tra

Sau khi chạy, xem:

```text
output/crawl/product_status.csv
output/crawl/checkpoint.json
output/crawl/shops_collected.json
```

để biết trạng thái từng product, số review mới/trùng/bị loại, số trang đã đọc và loại lỗi. `shops_collected.json` là handoff để nhóm duyệt trước khi cập nhật workbook Excel; crawler không tự ghi đè file master dùng chung.

Raw response đã được loại các khóa nhạy cảm có thể được lưu trong `output/crawl/schema_change_samples/` để chẩn đoán parser. Toàn bộ `output/crawl/` và browser profile đều bị Git bỏ qua.
