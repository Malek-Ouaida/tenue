#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python -m venv .venv
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
