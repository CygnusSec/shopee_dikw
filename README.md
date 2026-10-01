# Shopee DIKW Analytics

Reproducible validation and analytics pipeline for Shop, Product, and Review data. It never overwrites raw inputs or fabricates missing business fields, cluster meanings, or class labels.

The seven stage notebooks are stored in `src/` and are self-contained. They implement loading, validation, cleaning, sentiment, EDA, clustering, classification, regression, and final DIKW analysis. `src/Shopee_DIKW_Colab.ipynb` combines those seven stages into one Colab-ready notebook. Development builders are not imported by submitted notebooks.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows activation: `.venv\Scripts\activate`.

## Run notebooks

Open Jupyter and run the notebooks in `src/` sequentially from `00_data_validation.ipynb` through `06_final_analysis.ipynb`. The first notebook writes both human-readable and JSON submission checks; a valid schema alone is not treated as a populated dataset.

Dữ liệu Shop/Product/Review được thu thập local bằng notebook từng bước `src/crawl_data/collect_shopee_data.ipynb` hoặc CLI tương đương `./run_crawler_local.sh`; xem `src/crawl_data/README.md` trước khi chạy.

Add at least 15 genuine shops, 5–10 products per shop, five text reviews per product, and an authorized Seller Centre export at `Shopee_Dataset/1_Structured_Data/seller_center_metrics.csv`. The private raw export is gitignored. After clustering, inspect its profile and samples, then enter a human-confirmed mapping in config. Classification requires the manually reviewed `output/labeling/Data_Labeled.csv`.

## Google Colab

1. Upload the **entire project folder** to `MyDrive/shopee_dikw`; uploading only the notebook is insufficient because datasets and configuration remain external files.
2. Open `src/Shopee_DIKW_Colab.ipynb` in Colab.
3. If the Drive folder differs, edit only `COLAB_PROJECT_ROOT` in the first code cell.
4. Run All. The notebook mounts Drive, installs only missing analysis dependencies, and executes stages `00 → 06`.

Clustering interpretation and shop labeling remain human gates: inspect the generated files, update the mapping/labels in Drive, then rerun from the relevant stage. Crawling is excluded from the combined Colab notebook because it requires a local interactive Chromium session; the original crawler notebooks remain under `src/crawl_data/`.

The `output/` tree contains generated run artifacts and is intentionally excluded from Git. Recreate it by running the notebooks; do not commit stale model results.

## Known submission blockers

Real data for at least 15 shops, complete rating/image metadata, authorized conversion metrics, a verified three-page `.pbix`, human mapping/labels, verified Colab/Drive links, and a data-backed 10+ page PDF are required before submission. The current seed has 3 shops, 30 products, and 15 reviews, so it is not submission-ready.

Run the strict gate with `python tools/submission_check.py --write`. Complete `powerbi/verification.json` from its example and `submission/submission_metadata.yaml` only after manual verification, using the current `input_fingerprint` written by the checker so stale model/dashboard evidence cannot pass. Once every gate passes, create the sanitized ZIP with `python tools/package_submission.py`; private Seller Centre rows, cookies, browser profiles, logs, model binaries, and caches are excluded.
