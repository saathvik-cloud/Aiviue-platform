#!/bin/bash

# ===========================================
#  AIVIUE Backend Server Startup Script
# ===========================================
#
#  This script:
#  1. Starts Redis (Docker)
#  2. Activates virtual environment
#  3. Runs database migrations
#  4. Starts FastAPI server
#
#  Usage: ./server.sh
# ===========================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=========================================="
echo "  🚀 AIVIUE Backend Server"
echo "=========================================="
echo ""

# Navigate to server directory
cd "$SCRIPT_DIR" || exit
echo "📂 Working directory: $(pwd)"
echo ""

# ===========================================
# Step 1: Start Redis
# ===========================================
echo "🔄 [1/4] Checking Redis..."

if docker ps | grep -q "aiviue-redis"; then
    echo "✅ Redis already running!"
else
    echo "🐳 Starting Redis container..."
    
    # Remove old container if exists
    docker rm -f aiviue-redis 2>/dev/null
    
    # Start Redis
    docker run -d \
        --name aiviue-redis \
        -p 6379:6379 \
        redis:7-alpine \
        redis-server --appendonly yes
    
    # Wait for Redis to be ready
    sleep 2
    
    if docker ps | grep -q "aiviue-redis"; then
        echo "✅ Redis started successfully!"
    else
        echo "❌ Failed to start Redis. Check Docker."
        exit 1
    fi
fi
echo ""

# ===========================================
# Step 2: Activate Virtual Environment
# ===========================================
echo "🔄 [2/4] Activating virtual environment..."

if [ -f "venv/Scripts/activate" ]; then
    # Windows Git Bash
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    # Linux/Mac
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "   Run: python -m venv venv"
    exit 1
fi

echo "✅ Virtual environment activated!"
echo ""

# ===========================================
# Step 3: Run Migrations (optional)
# ===========================================
echo "🔄 [3/4] Checking database migrations..."

# Check if alembic is available and run migrations
if command -v alembic &> /dev/null; then
    echo "   Running: alembic upgrade head"
    alembic upgrade head 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Migrations up to date!"
    else
        echo "⚠️  Migration check skipped (might need DB connection)"
    fi
else
    echo "⚠️  Alembic not found, skipping migrations"
fi
echo ""

# ===========================================
# Step 4: Start Server
# ===========================================
echo "🔄 [4/4] Starting FastAPI server..."
echo ""
echo "------------------------------------------"
echo "🌐 Server:    http://localhost:8000"
echo "📋 API Docs:  http://localhost:8000/docs"
echo "❤️  Health:   http://localhost:8000/health"
echo "🔴 Redis:     localhost:6379"
echo "------------------------------------------"
echo ""
echo "⚠️  NOTE: Run ./worker.sh in another terminal"
echo "         for AI extraction to work!"
echo ""
echo "=========================================="
echo "  Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Run the FastAPI server
# --reload-dir app: Only watch app/ folder for changes (prevents watching stray folders)
uvicorn app.main:app --reload  --host 0.0.0.0 --port 8000
