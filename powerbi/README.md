# Power BI handoff

Import the clean CSV files from `Shopee_Dataset/4_Processed_Data` and reports from `output/reports`. Create one-to-many relationships Shop → Product on `Shop_ID` and Product → Review on `product_id`.

Required pages are Shop Analysis, Review Keyword Analysis (positive/negative WordCloud using `Sentiment_Label`), and Response Rate vs Conversion. The exact sales and conversion visuals remain blocked until genuine source fields exist; see `output/reports/data_gap_report.md`. A `.pbix` cannot be generated or verified outside Power BI Desktop.
