#!/bin/bash
# Start only the FastAPI backend server
# Serves both the test UI and API endpoints on port 6001

set -e

echo "🚀 Starting GeminiRAG Backend Server"
echo "====================================="
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

echo "📦 Backend Server Starting..."
echo "   - Test UI: http://localhost:6001"
echo "   - API Docs: http://localhost:6001/docs"
echo ""

# Start backend
python web/server.py
