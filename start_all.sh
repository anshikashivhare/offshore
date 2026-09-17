#!/bin/bash
echo "Starting Integrated FastAPI & Frontend Server..."
# Use the virtual environment python
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --app-dir backend

