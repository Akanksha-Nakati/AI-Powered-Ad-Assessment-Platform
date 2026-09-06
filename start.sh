#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env and add your API keys." >&2
  exit 1
fi

# Pinned to 3.13: several pinned wheels (pydantic-core, Pillow) have no 3.14
# builds yet and fall back to compiling from source, which fails without a Rust
# toolchain. See .python-version.
PYTHON="${PYTHON:-python3.13}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "$PYTHON not found. Install Python 3.13 or set PYTHON=/path/to/python3.13." >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -q -r backend/requirements.txt

# Build the vector store, then serve.
python -m backend.app.cli index
exec uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
