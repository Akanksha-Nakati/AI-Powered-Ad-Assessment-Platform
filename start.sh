#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r backend/requirements.txt

# Build vector store and start API
python -m backend.setup_vectorstore
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

