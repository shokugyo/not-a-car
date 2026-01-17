#!/bin/bash

# NOT A CAR - Startup Script

echo "================================================"
echo "  NOT A CAR - Your car works while you sleep"
echo "================================================"
echo ""

# Check if we're using Docker
if command -v docker-compose &> /dev/null && [ "$1" = "docker" ]; then
    echo "Starting with Docker Compose..."
    docker-compose up --build
    exit 0
fi

# Start Backend
echo "Starting Backend (FastAPI)..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start Frontend
echo "Starting Frontend (React/Vite)..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================================"
echo "  NOT A CAR is running!"
echo "================================================"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
