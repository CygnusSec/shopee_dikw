# Checklist crawl bổ sung review

## Shop cần crawl

- **Shop ID nội bộ:** `01_001`
- **Tên shop:** Maison Online
- **Shopee Shop ID:** `364616598`
- **Số sản phẩm cần bổ sung:** 9
- **Tổng số review có nội dung còn thiếu:** 19

Chỉ tính review có `review_text` không rỗng. Crawler có thể lấy nhiều hơn số lượng tối thiểu; dữ liệu được chống trùng bằng `review_id`.

## Danh sách sản phẩm

| STT | Product ID nội bộ | Tên sản phẩm | Review có nội dung hiện tại | Cần thêm tối thiểu |
|---:|---|---|---:|---:|
| 1 | `sp_01_001_001` | SKECHERS - Giày sneakers bé gái cổ thấp Dynamatic_303552L-BBK | 1 | 4 |
| 2 | `sp_01_001_002` | CONVERSE - Giày sneakers unisex cổ thấp Chuck Taylor All Star Original_M9697C-0000 | 4 | 1 |
| 3 | `sp_01_001_003` | SKECHERS - Dép nam quai ngang Foamies Arch Fit Horizon_243336-BBK | 4 | 1 |
| 4 | `sp_01_001_004` | CONVERSE - Giày sneakers unisex cổ cao Chuck Taylor All Star 1970s_162050C-0000 | 0 | 5 |
| 5 | `sp_01_001_006` | CONVERSE - Giày sneakers unisex cổ thấp Chuck Taylor All Star 1970s_162058C-0000 | 4 | 1 |
| 6 | `sp_01_001_007` | CONVERSE - Giày sneakers unisex cổ thấp Chuck Taylor All Star Original_M9166C-0000 | 4 | 1 |
| 7 | `sp_01_001_008` | CONVERSE - Giày sneakers unisex cổ thấp Chuck Taylor All Star Classic_M7652C-00W0 | 4 | 1 |
| 8 | `sp_01_001_009` | SKECHERS - Dép nam quai ngang Foamies Arch Fit Horizon_243336-KHK | 2 | 3 |
| 9 | `sp_01_001_010` | SKECHERS - Giày clog nam Foamies GO WALK 5 Key Choice_243032-CHAR | 3 | 2 |

## URL crawl

### 1. `sp_01_001_001` — cần thêm 4 review

https://shopee.vn/product/364616598/26425712721

### 2. `sp_01_001_002` — cần thêm 1 review

https://shopee.vn/product/364616598/26076118065

### 3. `sp_01_001_003` — cần thêm 1 review

https://shopee.vn/product/364616598/27825706326

### 4. `sp_01_001_004` — cần thêm 5 review

https://shopee.vn/product/364616598/27876031796

### 5. `sp_01_001_006` — cần thêm 1 review

https://shopee.vn/product/364616598/26076118067

### 6. `sp_01_001_007` — cần thêm 1 review

https://shopee.vn/product/364616598/26376031406

### 7. `sp_01_001_008` — cần thêm 1 review

https://shopee.vn/product/364616598/28226035281

### 8. `sp_01_001_009` — cần thêm 3 review

https://shopee.vn/product/364616598/27675678658

### 9. `sp_01_001_010` — cần thêm 2 review

https://shopee.vn/product/364616598/28025703993

## Thứ tự thực hiện

1. Ưu tiên `sp_01_001_004` vì hiện chưa có review văn bản.
2. Crawl lần lượt tám sản phẩm còn lại.
3. Không tạo nội dung giả cho review bị thiếu.
4. Không sửa hoặc ghi đè các review raw đã có.
5. Merge review mới vào `Shopee_Dataset/3_Unstructured_Data/shop_01_001_reviews.json` và chống trùng bằng `review_id`.
6. Chạy lại các notebook `00_data_validation.ipynb` đến `03_clustering_reviews.ipynb`.
7. Xác nhận `REVIEWS_PER_PRODUCT = PASS` trong `output/reports/submission_check.txt`.

## Lệnh chạy crawler local

```bash
cd /Users/bglobal-jsc/Documents/shopee_dikw
source .venv/bin/activate
./run_crawler_local.sh --restart
```

Đăng nhập trực tiếp trong Chromium. Nếu Shopee chuyển sang CAPTCHA hoặc báo `Please Try Again Later`, dừng phiên và chờ cooldown; không tự động vượt CAPTCHA hoặc retry liên tục.

