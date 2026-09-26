# Shopee DIKW Analytics

Reproducible validation and analytics pipeline for Shop, Product, and Review data. It never overwrites raw inputs or fabricates missing business fields, cluster meanings, or class labels.

The seven submission notebooks are stored in `src/` and are self-contained. They implement loading, validation, cleaning, sentiment, EDA, clustering, classification, regression, and final DIKW analysis. `tools/build_notebooks.py` is development tooling only; the submitted analysis does not import it.

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

Upload the project to Drive, open a notebook, mount Drive if needed, set only `PROJECT_ROOT = Path('.')` (or the project folder), install requirements, and Run All. All project paths are relative/config-based.

## Known submission blockers

Real data for at least 15 shops, complete rating/image metadata, authorized conversion metrics, a verified three-page `.pbix`, human mapping/labels, verified Colab/Drive links, and a data-backed 10+ page PDF are required before submission. The current seed has 3 shops, 30 products, and 15 reviews, so it is not submission-ready.

Run the strict gate with `python tools/submission_check.py --write`. Complete `powerbi/verification.json` from its example and `submission/submission_metadata.yaml` only after manual verification, using the current `input_fingerprint` written by the checker so stale model/dashboard evidence cannot pass. Once every gate passes, create the sanitized ZIP with `python tools/package_submission.py`; private Seller Centre rows, cookies, browser profiles, logs, model binaries, and caches are excluded.
