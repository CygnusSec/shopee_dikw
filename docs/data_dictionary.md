# Data dictionary

## Shop (structured Excel)

Primary key: `Shop_ID`. Required fields: `Shop_Name`, `Shop_type`, `Years_Active`, `Is_Online_Now`, `Total_Products`, `Follower_Count_k`, `Rating_Average`, `Total_Ratings_k`, `Chat_Response_Rate_pct`, `Has_Voucher`, nullable `Target_Label`, and `Time_Collected`.

`Target_Label` uses 0 = Kem, 1 = Binh_thuong, 2 = Uy_tin. Optional future source fields are `Sales`/`Revenue` and `Conversion_Rate_pct`; they must contain observed values, never inferred placeholders.

## Product (semi-structured JSON)

Primary key: `product_id`; foreign key: `Shop_ID`. Required fields: `product_name`, object-valued `product_details`, `description_text`, and `Review_stars` in [0,5]. Each file is a JSON list named `shop_<SHOP_ID>_products.json`.

## Review (unstructured JSON)

Primary key: `review_id`; foreign keys: `Shop_ID`, `product_id`. Required fields: `user_name`, `rating` in [1,5], `review_time`, `review_text`, and binary `has_image`. Each file is named `shop_<SHOP_ID>_reviews.json`.

Processed columns preserve raw text and add `description_clean`, `review_clean`, `Comment_Length`, `Word_Count`, `Sentiment_Score`, and `Sentiment_Label`.
