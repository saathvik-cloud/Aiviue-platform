"""
Background Workers for Aiviue Platform.

Workers process jobs from Redis queues asynchronously.

Available Workers:
- ExtractionWorker: Processes JD extraction jobs

Usage:
    # Run as module (recommended)
    python -m app.workers.extraction_worker
    
    # Or import directly when needed
    from app.workers.extraction_worker import ExtractionWorker, run_extraction_worker
    await run_extraction_worker()

Note: Imports are lazy to avoid circular import warnings when running workers as modules.
"""


def __getattr__(name: str):
    """Lazy import to avoid RuntimeWarning when running workers as modules."""
    if name == "ExtractionWorker":
        from app.workers.extraction_worker import ExtractionWorker
        return ExtractionWorker
    if name == "run_extraction_worker":
        from app.workers.extraction_worker import run_extraction_worker
        return run_extraction_worker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ExtractionWorker",
    "run_extraction_worker",
]
