#!/bin/bash
# Start only the React frontend development server
# Requires backend to be running on port 6001

set -e

echo "⚛️  Starting GeminiRAG React Frontend"
echo "====================================="
echo ""

# Check if we're in the right directory
if [ ! -d "web/ui" ]; then
    echo "❌ Error: Please run this script from the GeminiRAG directory"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "web/ui/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd web/ui
    npm install
    cd ../..
fi

echo "⚛️  React Frontend Starting..."
echo "   - Production UI: http://localhost:5173"
echo "   - Make sure backend is running on port 6001"
echo ""

# Start frontend
cd web/ui
npm run dev
