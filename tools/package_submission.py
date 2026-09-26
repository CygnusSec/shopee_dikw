#!/usr/bin/env python3
"""Create a clean submission ZIP only after every readiness gate passes."""
from __future__ import annotations

import argparse
import importlib.util
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ("Shopee_Dataset", "src", "config", "docs", "output/reports", "output/powerbi", "powerbi", "report", "submission", "README.md", "requirements.txt")
EXCLUDED_PARTS = {".venv", "__pycache__", ".pytest_cache", ".shopee_browser_profile", ".auth", "crawl", "logs", "models"}
EXCLUDED_NAMES = {".DS_Store", "seller_center_metrics.csv", "seller_center_metrics.xlsx", "verification.example.json", "submission_metadata.example.yaml"}
EXCLUDED_SUFFIXES = {".pyc", ".cookies.json", ".cookies.txt", ".zip"}


def _checker_module():
    spec = importlib.util.spec_from_file_location("submission_check", ROOT / "tools/submission_check.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def should_include(path: Path, root: Path = ROOT) -> bool:
    relative = path.relative_to(root)
    if EXCLUDED_PARTS & set(relative.parts):
        return False
    if path.name in EXCLUDED_NAMES or path.name.startswith(".~lock"):
        return False
    return not any(path.name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def files_to_package(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for item in INCLUDE:
        path = root / item
        candidates = path.rglob("*") if path.is_dir() else [path]
        files.extend(candidate for candidate in candidates if candidate.is_file() and should_include(candidate, root))
    return sorted(set(files))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "Shopee_DIKW_Submission.zip")
    parser.add_argument("--list", action="store_true", help="List safe package contents without creating a ZIP")
    args = parser.parse_args()
    files = files_to_package(ROOT)
    if args.list:
        print("\n".join(str(path.relative_to(ROOT)) for path in files))
        return 0
    result = _checker_module().evaluate(ROOT)
    if not result["overall_ready"]:
        failed = [name for name, passed in result["checks"].items() if not passed]
        raise SystemExit("Refusing to package an incomplete submission. Failed: " + ", ".join(failed))
    output = args.output.resolve()
    if ROOT not in output.parents:
        raise SystemExit("Output ZIP must be inside the project directory")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
    print(f"Created {output} with {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
