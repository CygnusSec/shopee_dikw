#!/usr/bin/env python3
"""Build one Google Colab notebook from the seven analysis notebooks."""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = SRC / "Shopee_DIKW_Colab.ipynb"
SOURCES = [
    SRC / "00_data_validation.ipynb",
    SRC / "01_data_cleaning.ipynb",
    SRC / "02_eda.ipynb",
    SRC / "03_clustering_reviews.ipynb",
    SRC / "04_shop_classification.ipynb",
    SRC / "05_regression.ipynb",
    SRC / "06_final_analysis.ipynb",
]
def markdown(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": dedent(source).strip().splitlines(True),
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip().splitlines(True),
    }


INTRODUCTION = markdown(
    """
    # Shopee DIKW - Google Colab Pipeline

    Notebook duy nhất chạy pipeline phân tích theo thứ tự:

    `Validation → Cleaning → EDA → Clustering → Classification → Regression → Wisdom`

    **Dữ liệu không được nhúng vào notebook.** Hãy tải toàn bộ project lên Google Drive để giữ
    đúng cấu trúc `Shopee_Dataset/`, `config/`, `output/`, `powerbi/`, `report/` và `submission/`.

    Notebook này chỉ chứa pipeline phân tích. Phần crawler không được đưa vào notebook Colab vì
    cần Chromium có giao diện và đăng nhập thủ công. Hãy thu thập dữ liệu thật ở máy local trước,
    sau đó đồng bộ project lên Drive.

    Pipeline sẽ dừng tại các human gate nếu chưa có mapping cụm, nhãn shop được duyệt,
    Seller Centre metrics hoặc các artifact bắt buộc. Không chỉnh code để tự tạo các dữ liệu này.
    """
)


COLAB_LOCATION = code(
    r'''
    from pathlib import Path

    IN_COLAB = False
    try:
        from google.colab import drive
        IN_COLAB = True
    except ImportError:
        drive = None

    # Chỉ sửa giá trị này nếu thư mục project trên Google Drive có tên/vị trí khác.
    COLAB_PROJECT_ROOT = Path("/content/drive/MyDrive/shopee_dikw")

    if IN_COLAB:
        drive.mount("/content/drive")
        PROJECT_ROOT = COLAB_PROJECT_ROOT.resolve()
    else:
        current = Path.cwd().resolve()
        PROJECT_ROOT = next(
            (path for path in (current, *current.parents) if (path / "config" / "config.yaml").exists()),
            current,
        )

    config_path = PROJECT_ROOT / "config" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {config_path}. Hãy upload toàn bộ project lên Drive và sửa "
            "COLAB_PROJECT_ROOT ở cell này; không chỉ upload riêng file notebook."
        )
    print({"IN_COLAB": IN_COLAB, "PROJECT_ROOT": str(PROJECT_ROOT)})
    '''
)


DEPENDENCIES = code(
    r'''
    import importlib.util
    import subprocess
    import sys

    ANALYSIS_PACKAGES = {
        "pandas": "pandas>=2.0,<3",
        "numpy": "numpy>=1.24,<3",
        "openpyxl": "openpyxl>=3.1,<4",
        "sklearn": "scikit-learn>=1.3,<2",
        "matplotlib": "matplotlib>=3.7,<4",
        "seaborn": "seaborn>=0.13,<1",
        "wordcloud": "wordcloud>=1.9,<2",
        "yaml": "PyYAML>=6.0,<7",
        "joblib": "joblib>=1.3,<2",
    }
    missing = [requirement for module, requirement in ANALYSIS_PACKAGES.items() if importlib.util.find_spec(module) is None]
    if missing:
        print("Installing missing analysis dependencies:", missing)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])
    else:
        print("All analysis dependencies are available.")
    '''
)


SHARED_SETUP = code(
    r'''
    from pathlib import Path
    import hashlib
    import json
    import warnings
    import numpy as np
    import pandas as pd
    import yaml

    warnings.filterwarnings("ignore")
    PROJECT_ROOT = Path(PROJECT_ROOT).resolve()
    with (PROJECT_ROOT / "config" / "config.yaml").open(encoding="utf-8") as handle:
        CONFIG = yaml.safe_load(handle)

    def project_path(key):
        return PROJECT_ROOT / CONFIG["paths"][key]

    OUTPUT = project_path("output")
    PROCESSED = project_path("processed")
    for folder in [OUTPUT / "reports", OUTPUT / "figures", OUTPUT / "models", OUTPUT / "labeling", OUTPUT / "logs", OUTPUT / "powerbi", PROCESSED]:
        folder.mkdir(parents=True, exist_ok=True)

    fingerprint_paths = [PROJECT_ROOT / "config" / "config.yaml", project_path("shops")]
    for key in ("products", "reviews"):
        fingerprint_paths.extend(sorted(project_path(key).glob("shop_*.json")))
    seller_candidate = project_path("seller_metrics")
    for candidate in (seller_candidate, seller_candidate.with_suffix(".xlsx")):
        if candidate.exists():
            fingerprint_paths.append(candidate)
    digest = hashlib.sha256()
    for path in fingerprint_paths:
        digest.update(str(path.relative_to(PROJECT_ROOT)).encode("utf-8"))
        digest.update(path.read_bytes())
    INPUT_FINGERPRINT = digest.hexdigest()
    print("PROJECT_ROOT:", PROJECT_ROOT)
    print("INPUT_FINGERPRINT:", INPUT_FINGERPRINT)
    '''
)


def is_generated_setup(cell: dict) -> bool:
    source = "".join(cell.get("source", []))
    return cell.get("cell_type") == "code" and "Cannot locate project root containing config/config.yaml" in source


def load_analysis_cells() -> list[dict]:
    cells: list[dict] = []
    for stage, path in enumerate(SOURCES):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        cells.append(markdown(f"---\n\n## Pipeline stage {stage:02d}: `{path.name}`"))
        for original in notebook["cells"]:
            if is_generated_setup(original):
                continue
            copied = {
                "cell_type": original["cell_type"],
                "metadata": {},
                "source": list(original.get("source", [])),
            }
            if copied["cell_type"] == "code":
                copied.update({"execution_count": None, "outputs": []})
            cells.append(copied)
    return cells


def add_cell_ids(cells: list[dict]) -> None:
    for index, cell in enumerate(cells, start=1):
        cell["id"] = f"shopee-{index:03d}"


def build() -> Path:
    cells = [
        INTRODUCTION,
        COLAB_LOCATION,
        DEPENDENCIES,
        SHARED_SETUP,
        *load_analysis_cells(),
    ]
    add_cell_ids(cells)
    notebook = {
        "cells": cells,
        "metadata": {
            "colab": {"name": OUTPUT.name, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return OUTPUT


if __name__ == "__main__":
    print("wrote", build())
