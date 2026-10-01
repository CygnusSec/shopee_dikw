import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_submission_notebooks_exist_and_compile():
    expected = [
        "00_data_validation.ipynb", "01_data_cleaning.ipynb", "02_eda.ipynb",
        "03_clustering_reviews.ipynb", "04_shop_classification.ipynb",
        "05_regression.ipynb", "06_final_analysis.ipynb",
    ]
    for name in expected:
        path = ROOT / "src" / name
        notebook = json.loads(path.read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), f"{name}:cell{index}", "exec")


def test_combined_colab_notebook_contains_analysis_only():
    path = ROOT / "src" / "Shopee_DIKW_Colab.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    for stage in range(7):
        assert f"Pipeline stage {stage:02d}" in source
    assert "COLAB_PROJECT_ROOT" in source
    assert "drive.mount" in source
    assert "KMeans" in source
    assert "RandomForestClassifier" in source
    assert "LinearRegression" in source
    assert "collect_shopee_data.ipynb" not in source
    assert "collect_shopee_reviews.ipynb" not in source
    assert "RUN_LOCAL_CRAWL" not in source
    assert "async_playwright" not in source
    for index, cell in enumerate(notebook["cells"]):
        assert cell.get("id")
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"Shopee_DIKW_Colab.ipynb:cell{index}", "exec")


def test_config_contract():
    text = (ROOT / "config" / "config.yaml").read_text(encoding="utf-8")
    for contract in ["minimum_shops: 15", "minimum_shops_per_class: 5", "n_clusters: 3", "target: Follower_Count_k", "0: Kem", "1: Binh_thuong", "2: Uy_tin"]:
        assert contract in text


def test_no_credentials_are_tracked_in_collection_manifest():
    manifest = json.loads((ROOT / "src" / "crawl_data" / "product_review_mapping.json").read_text(encoding="utf-8"))
    prohibited = {"password", "cookie", "token", "authorization", "session"}
    assert manifest
    assert all(not (set(map(str.lower, row)) & prohibited) for row in manifest)
