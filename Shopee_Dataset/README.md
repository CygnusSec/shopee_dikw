# Bộ dữ liệu Shopee

3 shop, 10 sản phẩm/shop, 5 review/sản phẩm. Dữ liệu được xem trên trang Shopee ngày 26/09/2026. Mỗi review có 8 trường theo mẫu PDF; review_id là mã review Shopee. URL nguồn nằm ở product_details.source_product_url của sản phẩm liên kết.

Maison Online: 31/50 review có văn bản, 19 review chỉ có sao hoặc ảnh nên review_text được giữ rỗng. AstroMazing và Camelia: 50/50 review có văn bản mỗi shop. Không tự tạo nội dung cho review rỗng. 5 sản phẩm cuối của Maison trong JSON ban đầu thiếu số đánh giá và đã được thay bằng sản phẩm khác cùng shop; product_id nội bộ được giữ, URL và item ID được cập nhật. description_text trong dữ liệu sản phẩm nguồn vẫn là null.
