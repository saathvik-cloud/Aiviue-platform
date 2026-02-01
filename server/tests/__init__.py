"""
AIVIUE Backend Test Suite

Test Modules:
- test_employer.py: Employer CRUD operations
- test_job.py: Job CRUD and lifecycle operations
- test_extraction.py: JD extraction tests
- test_health.py: Health check endpoints

Run all tests:
    pytest tests/ -v

Run specific module:
    pytest tests/test_employer.py -v

Run with coverage:
    pytest tests/ -v --cov=app --cov-report=html

Skip integration tests:
    pytest tests/ -v -k "not integration"

Skip slow tests:
    pytest tests/ -v -k "not slow"
"""
