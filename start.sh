#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  echo "No .env found. Copy .env.example to .env and add your API keys." >&2
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -q -r backend/requirements.txt

# Build the vector store, then serve.
python -m backend.app.cli index
exec uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
