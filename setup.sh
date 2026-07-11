#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  echo "Note: venv is active — using system Python, not .venv/bin"
  PATH=$(echo "$PATH" | tr ':' '\n' | grep -v "^${VIRTUAL_ENV}/bin$" | tr '\n' ':' | sed 's/:$//')
  export PATH
  hash -r 2>/dev/null || true
fi

# Resolve full path so deleting .venv mid-script doesn't break us
PY=""
for candidate in python3.12 python3.11; do
  if path=$(command -v "$candidate" 2>/dev/null); then
    # Skip interpreters inside this project's .venv
    if [[ "$path" != "$(pwd)/.venv/"* ]]; then
      PY=$path
      break
    fi
  fi
done

if [[ -z "$PY" ]]; then
  echo "ERROR: Need Python 3.11 or 3.12 outside this venv."
  echo "Install via: brew install python@3.12"
  exit 1
fi

echo "Using $($PY --version) at $PY"

rm -rf .venv
"$PY" -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Done. Activate with: source .venv/bin/activate"
echo "Then add FISH_API_KEY to .env"
echo "Then run:           python web.py"
