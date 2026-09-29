# Bộ dữ liệu 15 shop — bản tiến độ 28/09/2026

shops_master.xlsx có đúng 15 shop: 5 shop gốc và đúng 10 shop do người dùng chỉ định theo URL. Sources ghi URL shop và trang sản phẩm đã quan sát. Trong 10 shop mới, đã xác minh 50 sản phẩm có mô tả và 500 review thực; mỗi sản phẩm mới đã chọn có đúng 10 review riêng biệt.

10 shop mới (01_006–01_015) đã đạt đúng 5 sản phẩm × 10 review có nội dung cho mỗi shop: 50 sản phẩm và 500 review duy nhất. 5 shop gốc (01_001–01_005) vẫn giữ dữ liệu cũ 10 sản phẩm × 5 review, chưa đáp ứng dạng 5 sản phẩm × 10 review; riêng Maison (01_001) chỉ 31/50 review cũ có nội dung. Một sản phẩm Maison được kiểm tra lại trên trang Shopee chỉ có một review có chữ, nên cần chọn sản phẩm khác khi hoàn thiện shop này. collection_status.csv ghi số lượng thật theo từng shop. Tổng hiện lưu: 100 sản phẩm và 750 review; không coi 15 dòng shop là 15 shop đã hoàn chỉnh cùng một chuẩn.

Sales/Conversion của Seller Center chưa có nguồn truy cập nên vẫn rỗng. Không tự tạo dữ liệu thiếu hoặc nhãn phân loại. Chỉ số shop quan sát ngày 28/09/2026 từ trang Shopee công khai; số đếm dạng k/m được quy đổi và có thể đã làm tròn tại nguồn.

Đối với 10 shop mới, username được đối chiếu lại từ phần hiển thị của từng review: tên đã bị Shopee che được giữ nguyên dạng như n*****9, không suy đoán tên đầy đủ. Các review không có username hiển thị được lưu null.
