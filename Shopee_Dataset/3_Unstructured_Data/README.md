# Review Shopee đã thu thập

15 review có văn bản từ 3 shop, tại thời điểm 2026-09-24. Mỗi review liên kết đến một sản phẩm trong file JSON nguồn. Các trang đã quan sát: 2 sản phẩm Maison Online, 1 sản phẩm AstroMazing, 1 sản phẩm Camelia Brand. Các sản phẩm còn lại chưa có review được thu thập; xem `review_collection_manifest.csv`.

`review_id` là mã nội bộ của bộ dữ liệu, không phải mã review do Shopee cung cấp. `rating` và `has_image` là null vì chưa xác minh trực tiếp cho từng review. Video hiển thị trên trang không tự động đồng nghĩa `has_image=1`. Review có văn bản được chép từ trang sản phẩm; không đưa phản hồi của người bán vào `review_text`. Một số listing có nhiều biến thể, review có thể đề cập biến thể khác cùng listing.
