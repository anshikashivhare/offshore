#!/bin/bash
# SIH 26059 - Antarctic Navigation Demo Startup Script

echo "========================================="
echo " Starting SIH 26059 Demo Infrastructure"
echo "========================================="

# 1. Preflight Check
echo "Running Preflight checks..."
PYTHONPATH=backend backend/.venv/bin/python scripts/training/preflight_demo.py
if [ $? -ne 0 ]; then
    echo "ERROR: Preflight failed. Please fix configuration before starting."
    exit 1
fi

echo "Starting Backend (FastAPI)..."
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

echo "Starting Frontend (React)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "========================================="
echo "DEMO INFRASTRUCTURE RUNNING"
echo "Backend URL:  http://localhost:8000"
echo "Frontend URL: http://localhost:5173 (usually)"
echo "DEMO_MODE is Active if DB is unavailable."
echo "Press Ctrl+C to stop all services."
echo "========================================="

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
