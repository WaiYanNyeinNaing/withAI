#!/bin/bash

# GeminiRAG Startup Script
# This script starts both the document service and API server

set -e

echo "🚀 Starting GeminiRAG Services..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your GOOGLE_API_KEY"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_api_key_here" ]; then
    echo "❌ GOOGLE_API_KEY not set in .env file"
    echo "📝 Please edit .env and add your Google API key"
    exit 1
fi

# Kill any existing processes on the ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

# Start document service
echo "📚 Starting Document Service (port 8000)..."
uvicorn services.api:app --port 8000 --reload &
DOC_PID=$!

# Wait for document service to be ready
sleep 2

# Start API server
echo "🌐 Starting API Server (port 5001)..."
python backend/api_server.py &
API_PID=$!

# Wait for API server to be ready
sleep 2

echo ""
# Start Frontend Server
echo "🌐 Starting Frontend Server..."
cd react_frontend
python3 -m http.server 8080 > /dev/null 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ All services started!"
echo "   - Document Service: http://localhost:8000"
echo "   - API Server: http://localhost:5001"
echo "   - Frontend: http://localhost:8080"
echo ""
echo "Opening frontend in browser..."
sleep 2
open http://localhost:8080

# Trap cleanup
trap "kill $DOC_PID $API_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '🛑 Stopping services...'; exit" INT TERM

# Keep script running
wait
