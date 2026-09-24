# Data Gap Report

## Sales / Revenue

Status: Existing product records predate the required `units_sold` field. Recollect public product data with the updated schema. The pipeline aggregates only observed `units_sold` into shop-level `Sales`; it never substitutes ratings, followers, or product counts.

## Conversion_Rate_pct

Status: Authorized Seller Centre export has not been supplied. Copy `docs/seller_center_metrics_template.csv`, populate verified values, and save it as `Shopee_Dataset/1_Structured_Data/seller_center_metrics.csv`. The raw private file is gitignored. Dashboard 3 and downstream models remain blocked until this input exists.

## Collection coverage

Status: 3 shops, 30 products, and 0 reviews are currently present. Required target: at least 15 shops, 5–10 products per shop, and five text reviews per product.
