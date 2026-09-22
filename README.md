# Shopee DIKW Analytics

Reproducible validation and analytics pipeline for Shop, Product, and Review data. It never overwrites raw inputs or fabricates missing business fields, cluster meanings, or class labels.

The seven submission notebooks are stored in `src/` and are self-contained: their code cells implement loading, validation, cleaning, sentiment, EDA, clustering, classification, regression, and final DIKW analysis directly. The submitted source code is notebook-only and does not depend on separate Python modules or scripts.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows activation: `.venv\Scripts\activate`.

## Run notebooks

Open Jupyter and run the notebooks in `src/` sequentially from `00_data_validation.ipynb` through `06_final_analysis.ipynb`.

The raw workbook initially contains headers only. Add genuine records plus matching Product and Review JSON files. After clustering, inspect the profile and enter a human-confirmed mapping in config. Classification requires the manually reviewed `output/labeling/Data_Labeled.csv`.

## Google Colab

Upload the project to Drive, open a notebook, mount Drive if needed, set only `PROJECT_ROOT = Path('.')` (or the project folder), install requirements, and Run All. All project paths are relative/config-based.

## Known submission blockers

Real data for at least five shops, a verified `.pbix` with at least three pages, human mapping/labels, and a data-backed 10+ page report are still required before submission.
