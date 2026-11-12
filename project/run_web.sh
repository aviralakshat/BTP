#!/usr/bin/env bash
# Starts the model API (port 8000) and the web console (port 3000).
set -euo pipefail
cd "$(dirname "$0")"

./venv/bin/python -m uvicorn api.server:app --host 127.0.0.1 --port 8000 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null' EXIT

cd web
[ -d node_modules ] || npm install
npm run dev -- --port "${WEB_PORT:-3000}"
