#!/bin/bash

# ===========================================
#  AIVIUE Frontend Startup Script
# ===========================================
#
#  This script starts the Next.js frontend.
#
#  Prerequisites:
#  - Node.js installed
#  - npm install completed
#  - Backend server running (./server.sh) 
#
#  Usage: ./frontend.sh
# ===========================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=========================================="
echo "  🎨 AIVIUE Frontend (Next.js)"
echo "=========================================="
echo ""

# Navigate to client directory
cd "$SCRIPT_DIR" || exit
echo "📂 Working directory: $(pwd)"
echo ""

# ===========================================
# Step 1: Check Node.js
# ===========================================
echo "🔄 [1/3] Checking Node.js..."

if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION"
else
    echo "❌ Node.js not found!"
    echo "   Please install Node.js from https://nodejs.org"
    exit 1
fi
echo ""

# ===========================================
# Step 2: Install Dependencies
# ===========================================
echo "🔄 [2/3] Checking dependencies..."

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "✅ Dependencies already installed!"
fi
echo ""

# ===========================================
# Step 3: Start Frontend
# ===========================================
echo "🔄 [3/3] Starting Next.js development server..."
echo ""
echo "------------------------------------------"
echo "🌐 Frontend:  http://localhost:3000"
echo "🔗 API:       http://localhost:8000"
echo "------------------------------------------"
echo ""
echo "⚠️  Make sure backend is running:"
echo "    cd ../server && ./server.sh"
echo ""
echo "=========================================="
echo "  Press Ctrl+C to stop the frontend"
echo "=========================================="
echo ""

# Run Next.js development server
npm run dev
