"""
Background Workers for Aiviue Platform.

Workers process jobs from Redis queues asynchronously.

Available Workers:
- ExtractionWorker: Processes JD extraction jobs

Usage:
    # Run as module
    python -m app.workers.extraction_worker
    
    # Or in code
    from app.workers import run_extraction_worker
    await run_extraction_worker()
"""

from app.workers.extraction_worker import (
    ExtractionWorker,
    run_extraction_worker,
)

__all__ = [
    "ExtractionWorker",
    "run_extraction_worker",
]
