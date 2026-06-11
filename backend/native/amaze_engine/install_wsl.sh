#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  rawtherapee

python3 -m venv .venv-amaze-service
source .venv-amaze-service/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install PiDNG

echo
echo "AMaZE service venv is ready:"
echo "  $ROOT_DIR/.venv-amaze-service"
echo
echo "Run:"
echo "  source $ROOT_DIR/.venv-amaze-service/bin/activate"
echo "  export AMAZE_ENGINE_COMMAND=\"python $ROOT_DIR/native/amaze_engine/rawtherapee_amaze_engine.py {input} {output}\""
echo "  uvicorn amaze_service.main:app --host 0.0.0.0 --port 8077"
