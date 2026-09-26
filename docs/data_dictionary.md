# Data dictionary

## Shop (structured Excel)

Primary key: `Shop_ID`. Required fields: `Shop_Name`, `Shop_type`, `Years_Active`, `Is_Online_Now`, `Total_Products`, `Follower_Count_k`, `Rating_Average`, `Total_Ratings_k`, `Chat_Response_Rate_pct`, `Has_Voucher`, nullable `Target_Label`, and `Time_Collected`.

`Target_Label` uses 0 = Kem, 1 = Binh_thuong, 2 = Uy_tin. `Sales`/`Units_Sold` must be observed values. `Conversion_Rate_pct` comes only from an authorized Seller Centre export; neither field may be inferred from ratings or reviews. `Data_Source` and `Time_Collected` provide provenance.

## Product (semi-structured JSON)

Primary key: `product_id`; foreign key: `Shop_ID`. Required keys include `product_name`, object-valued `product_details`, `description_text`, `Review_stars`, `units_sold`, `product_url`, `Time_Collected`, and `Data_Source`. Values that could not be observed remain JSON `null`; a required key is not permission to invent its value.

## Review (unstructured JSON)

Primary key: `review_id`; foreign keys: `Shop_ID`, `product_id`. Required keys include `user_name`, `rating`, `review_time`, `review_text`, binary `has_image`, source URL, collection date, `Data_Source`, and `Verification_Status`. Unverified `rating`, `review_time`, and `has_image` remain JSON `null` and block submission readiness.

## Seller Centre metrics

Private, authorized input keyed by `Shop_ID` and `product_id`: `Conversion_Rate_pct`, optional `Units_Sold`, `Time_Collected`, and `Data_Source`. Raw exports are gitignored; only approved aggregates belong in the submission.

Processed columns preserve raw text and add `description_clean`, `review_clean`, `Comment_Length`, `Word_Count`, `Sentiment_Score`, and `Sentiment_Label`.
