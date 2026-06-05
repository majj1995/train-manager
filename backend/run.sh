#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"
exec "$PROJECT_ROOT/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload