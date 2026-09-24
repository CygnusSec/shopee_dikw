# Power BI handoff

The repository cannot generate or verify a binary `.pbix` outside Power BI Desktop. Build it from the outputs below and save it in this directory. Do not publish private Seller Centre row-level exports.

## Sources

Import `shops_clean.csv`, `products_clean.csv`, and `reviews_clean.csv` from `Shopee_Dataset/4_Processed_Data`, plus `Shop_Authenticity_Report.csv` and the tables in `output/powerbi`. Set identifiers to Text, rates to Decimal Number, counts to Whole Number, and collection fields to Date.

Use single-direction relationships:

- Shops `[Shop_ID]` 1 → * Products `[Shop_ID]`
- Products `[product_id]` 1 → * Reviews `[product_id]`
- Shops `[Shop_ID]` 1 → 1 Authenticity `[Shop_ID]`

Do not add a direct Shops → Reviews relationship because it creates an ambiguous filter path.

## Measures

```DAX
Total Shops = DISTINCTCOUNT(shops_clean[Shop_ID])
Total Products = DISTINCTCOUNT(products_clean[product_id])
Total Reviews = DISTINCTCOUNT(reviews_clean[review_id])
Average Rating = AVERAGE(reviews_clean[rating])
Observed Sales = SUM(products_clean[units_sold])
Image Review Rate = DIVIDE(CALCULATE([Total Reviews], reviews_clean[has_image] = 1), [Total Reviews])
Average Conversion Rate = AVERAGE(products_clean[Conversion_Rate_pct])
Average Authentic Review Rate = AVERAGE(Shop_Authenticity_Report[Authentic_Review_Rate])
```

## Required pages

1. **Tổng quan shop** — KPI cards, Rating–Observed Sales and Follower–Rating scatters, and Shop/Type/Date slicers.
2. **Sản phẩm và review** — positive/negative keywords, rating and comment-length distributions, image rate, and sentiment.
3. **Uy tín và chuyển đổi** — Response Rate–Conversion scatter and authenticity matrix. Color under 50% red, 50–80% amber, and over 80% green.

Selecting a shop must cross-filter product and review visuals. Refresh must complete without absolute-path errors, counts must match `output/powerbi/kpi_summary.csv`, and all interactions must work after reopening the file.
