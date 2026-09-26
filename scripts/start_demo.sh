#!/usr/bin/env bash
set -e

echo "========================================="
echo " SIH 26059 - FINAL DEMO STARTUP SCRIPT"
echo "========================================="

# 1. Start Database
echo "Starting PostgreSQL/PostGIS database..."
cd database
docker-compose up -d
cd ..

# 2. Wait for DB
echo "Waiting for database to accept connections..."
sleep 5

# 3. Start Backend
echo "Starting FastAPI Backend..."
cd backend
source venv_mac/bin/activate || echo "Warning: Virtual environment not found. Assuming dependencies are globally installed."
export PYTHONPATH=$(pwd)
# Run in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 4. Start Frontend
echo "Starting React Frontend..."
cd frontend
# Run in background
npm run dev &
FRONTEND_PID=$!
cd ..

echo "========================================="
echo " SYSTEM STARTED"
echo "========================================="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000 (Check Vite/Next port if different)"
echo ""
echo "Press Ctrl+C to stop all services."

# Trap Ctrl+C and kill background processes
trap "echo 'Shutting down services...'; kill $BACKEND_PID; kill $FRONTEND_PID; cd database && docker-compose down; exit" INT

# Keep script running to maintain processes
wait
