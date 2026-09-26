# Thu thập Review thật từ Shopee

Entrypoint tương tác là `collect_shopee_data.ipynb`, tách riêng các bước kiểm tra manifest, mở Chromium, đăng nhập, health check, crawl, validation và đóng trình duyệt. CLI `run_local.py`, gọi qua `run_crawler_local.sh`, thực hiện cùng luồng cho người dùng muốn chạy từ Terminal. `collect_shopee_reviews.ipynb` chỉ là tài liệu lịch sử và không còn là entrypoint.

```text
Shopee_Dataset/3_Unstructured_Data/
├── shop_01_001_reviews.json
├── shop_01_002_reviews.json
└── ...
```

Trước khi chạy, mở rộng manifest lên ít nhất 15 shop, mỗi shop 5–10 sản phẩm. Mỗi dòng phải có `Shop_ID`, `Shop_Name`, `product_id`, `product_name`, `shopee_shop_id`, `shopee_item_id` và `product_url`. Notebook không chứa danh sách shop hard-code.

## Cài đặt trên máy local

Từ Terminal tại thư mục dự án:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Chạy crawler

```bash
./run_crawler_local.sh
```

Chromium sẽ mở trên máy local. Đăng nhập trực tiếp trong cửa sổ đó, quay lại Terminal và nhấn Enter. Script health-check trước rồi mới crawl.

Các tùy chọn:

```bash
./run_crawler_local.sh --dry-run
./run_crawler_local.sh --restart
./run_crawler_local.sh --skip-login-wait
./run_crawler_local.sh --cookie-file /duong/dan/private-curl.txt --skip-login-wait
```

- `--dry-run`: mở browser và kiểm tra luồng nhưng không ghi record crawl.
- `--restart`: bỏ qua checkpoint hoàn tất; merge vẫn chống duplicate.
- `--skip-login-wait`: dùng profile đã đăng nhập mà không chờ Enter.
- `--cookie-file`: nạp session cookie từ file cURL/JSON/Netscape riêng. Tool chỉ nhập allowlist cookie phiên Shopee, không chép giá trị vào source hoặc log.

Cookie file phải nằm ngoài Git hoặc trong `src/crawl_data/.auth/` đã được gitignore. Giới hạn quyền đọc bằng `chmod 600 <file>`. Không gửi file này cho thành viên khác; đăng xuất/thu hồi phiên sau khi thu thập xong. Cookie có thể hết hạn hoặc bị ràng buộc với thiết bị/IP, và không bảo đảm vượt qua verification.

Script từ chối chạy trên Colab, Docker hoặc SSH server không có desktop. Tool không tự vượt đăng nhập, CAPTCHA hoặc cơ chế bảo vệ của Shopee.

Nếu Chromium chuyển tới `/verify/captcha`, hiển thị “Please Try Again Later” hoặc có `anti_bot_tracking_id`, không tiếp tục bấm/retry liên tục. CLI sẽ nhận diện và dừng trước health check. Đóng phiên, chờ cooldown và kiểm tra Shopee bằng trình duyệt thông thường. Nếu vẫn bị chặn, dùng Seller Centre export/API được cấp quyền hoặc thu thập thủ công; không chỉnh crawler để vượt xác minh.

Nếu Shopee yêu cầu đăng nhập, hãy đăng nhập **trực tiếp trong Chromium**. Không nhập mật khẩu vào script hoặc Terminal.

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
