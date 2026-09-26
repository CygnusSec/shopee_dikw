import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    path = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_current_repository_is_truthfully_not_ready():
    checker = load_tool("submission_check")
    result = checker.evaluate(ROOT)
    assert not result["overall_ready"]
    assert result["evidence"]["shops"] == 3
    assert result["evidence"]["products"] == 30
    assert result["evidence"]["reviews"] == 15
    assert not result["checks"]["MINIMUM_REAL_SHOPS"]
    assert not result["checks"]["REVIEW_RATING_COMPLETE"]
    assert not result["checks"]["REVIEW_IMAGE_COMPLETE"]
    assert "OVERALL: NOT READY FOR SUBMISSION" in checker.render(result)


def test_review_schema_allows_explicit_unverified_nulls():
    schema = json.loads((ROOT / "docs/review_schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    row = {
        "Shop_ID": "01_001", "product_id": "sp_1", "review_id": "rv_1",
        "user_name": "buyer", "rating": None, "review_time": None,
        "review_text": "real text", "has_image": None,
        "Data_Source": "manual public-page transcription",
    }
    Draft202012Validator(schema).validate([row])


def test_package_list_excludes_private_and_runtime_artifacts():
    package = load_tool("package_submission")
    names = {str(path.relative_to(ROOT)) for path in package.files_to_package(ROOT)}
    assert "Shopee_Dataset/1_Structured_Data/seller_center_metrics.csv" not in names
    assert all(".shopee_browser_profile" not in name for name in names)
    assert all(not name.endswith(".joblib") for name in names)
    assert "src/00_data_validation.ipynb" in names
