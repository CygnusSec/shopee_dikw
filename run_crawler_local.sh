#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Chưa có .venv. Chạy các lệnh sau trước:"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -r requirements.txt"
  echo "  python -m playwright install chromium"
  exit 1
fi

exec "$PYTHON_BIN" "$PROJECT_DIR/src/crawl_data/run_local.py" "$@"
