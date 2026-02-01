#!/bin/bash

# ===========================================
#  AIVIUE Backend Test Runner
# ===========================================
#
#  Usage:
#    ./run_tests.sh              # Run all tests
#    ./run_tests.sh employer     # Run employer tests only
#    ./run_tests.sh job          # Run job tests only
#    ./run_tests.sh extraction   # Run extraction tests only
#    ./run_tests.sh health       # Run health tests only
#    ./run_tests.sh quick        # Skip slow/integration tests
#    ./run_tests.sh coverage     # Run with coverage report
#
# ===========================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=========================================="
echo "  🧪 AIVIUE Backend Test Runner"
echo "=========================================="
echo ""

# Navigate to server directory
cd "$SCRIPT_DIR" || exit
echo "📂 Working directory: $(pwd)"
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    exit 1
fi
echo "✅ Virtual environment activated!"
echo ""

# Determine test command based on argument
TEST_CMD="pytest tests/ -v"

case "$1" in
    "employer")
        echo "🎯 Running Employer tests..."
        TEST_CMD="pytest tests/test_employer.py -v"
        ;;
    "job")
        echo "🎯 Running Job tests..."
        TEST_CMD="pytest tests/test_job.py -v"
        ;;
    "extraction")
        echo "🎯 Running Extraction tests..."
        TEST_CMD="pytest tests/test_extraction.py -v"
        ;;
    "health")
        echo "🎯 Running Health tests..."
        TEST_CMD="pytest tests/test_health.py -v"
        ;;
    "quick")
        echo "🎯 Running quick tests (skipping slow/integration)..."
        TEST_CMD="pytest tests/ -v -k 'not slow and not integration'"
        ;;
    "coverage")
        echo "🎯 Running tests with coverage..."
        TEST_CMD="pytest tests/ -v --cov=app --cov-report=html --cov-report=term"
        ;;
    "")
        echo "🎯 Running all tests..."
        ;;
    *)
        echo "❌ Unknown option: $1"
        echo ""
        echo "Usage:"
        echo "  ./run_tests.sh              # Run all tests"
        echo "  ./run_tests.sh employer     # Run employer tests"
        echo "  ./run_tests.sh job          # Run job tests"
        echo "  ./run_tests.sh extraction   # Run extraction tests"
        echo "  ./run_tests.sh health       # Run health tests"
        echo "  ./run_tests.sh quick        # Skip slow tests"
        echo "  ./run_tests.sh coverage     # With coverage report"
        exit 1
        ;;
esac

echo ""
echo "------------------------------------------"
echo "Running: $TEST_CMD"
echo "------------------------------------------"
echo ""

# Run tests
$TEST_CMD

# Capture exit code
EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✅ All tests passed!"
else
    echo "  ❌ Some tests failed (exit code: $EXIT_CODE)"
fi
echo "=========================================="
echo ""

exit $EXIT_CODE
