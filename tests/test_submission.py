import importlib.util
from pathlib import Path


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
    assert result["evidence"]["shops"] >= 1
    assert result["evidence"]["products"] >= 1
    assert result["evidence"]["reviews"] >= result["evidence"]["text_reviews"]
    assert result["checks"]["MINIMUM_REAL_SHOPS"]
    assert "OVERALL: NOT READY FOR SUBMISSION" in checker.render(result)


def test_package_list_excludes_private_and_runtime_artifacts():
    package = load_tool("package_submission")
    names = {str(path.relative_to(ROOT)) for path in package.files_to_package(ROOT)}
    assert "Shopee_Dataset/1_Structured_Data/seller_center_metrics.csv" not in names
    assert all(".shopee_browser_profile" not in name for name in names)
    assert all(not name.endswith(".joblib") for name in names)
    assert "src/00_data_validation.ipynb" in names
