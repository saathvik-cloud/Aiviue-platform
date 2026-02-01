#!/bin/bash

# ===========================================
#  AIVIUE Extraction Worker Startup Script
# ===========================================
#
#  This script starts the background worker
#  that processes JD extraction jobs using LLM.
#
#  Prerequisites:
#  - Redis must be running (started by server.sh)
#  - Run this in a SEPARATE terminal from server.sh
#
#  Usage: ./worker.sh
# ===========================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=========================================="
echo "  🤖 AIVIUE Extraction Worker"
echo "=========================================="
echo ""

# Navigate to server directory
cd "$SCRIPT_DIR" || exit
echo "📂 Working directory: $(pwd)"
echo ""

# ===========================================
# Step 1: Check Redis
# ===========================================
echo "🔄 [1/3] Checking Redis connection..."

if docker ps | grep -q "aiviue-redis"; then
    echo "✅ Redis is running!"
else
    echo "❌ Redis is NOT running!"
    echo "   Please run ./server.sh first to start Redis."
    exit 1
fi
echo ""

# ===========================================
# Step 2: Activate Virtual Environment
# ===========================================
echo "🔄 [2/3] Activating virtual environment..."

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
# Step 3: Start Worker
# ===========================================
echo "🔄 [3/3] Starting extraction worker..."
echo ""
echo "------------------------------------------"
echo "📋 Queue:     queue:extraction"
echo "🔴 Redis:     localhost:6379"
echo "🤖 LLM:       Google Gemini"
echo "------------------------------------------"
echo ""
echo "👂 Listening for extraction jobs..."
echo "   When you submit a JD for extraction,"
echo "   this worker will process it using AI."
echo ""
echo "=========================================="
echo "  Press Ctrl+C to stop the worker"
echo "=========================================="
echo ""

# Run the extraction worker
python -m app.workers.extraction_worker
