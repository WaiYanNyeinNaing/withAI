#!/bin/bash
# Start both backend and frontend for development
# This script starts the FastAPI backend and React frontend in parallel

set -e

echo "🚀 Starting GeminiRAG Development Environment"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "web/server.py" ]; then
    echo "❌ Error: Please run this script from the GeminiRAG directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please copy .env.example to .env and add your GOOGLE_API_KEY"
    exit 1
fi

echo "📦 Starting Backend Server (Port 6001)..."
echo "   - Test UI: http://localhost:6001"
echo "   - API Endpoints: http://localhost:6001/docs"
echo ""

# Start backend in background
python web/server.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

echo "⚛️  Starting React Frontend (Port 5173)..."
echo "   - Production UI: http://localhost:5173"
echo ""

# Start frontend
cd web/ui
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
