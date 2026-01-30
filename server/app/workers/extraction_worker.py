"""
JD Extraction Background Worker for Aiviue Platform.

Consumes jobs from the extraction queue and processes them using LLM.

Flow:
1. Poll queue for extraction jobs
2. Call LLM to extract fields from JD
3. Update database with results
4. Emit completion event

Usage:
    # Run as standalone script
    python -m app.workers.extraction_worker
    
    # Or in code
    from app.workers.extraction_worker import run_extraction_worker
    await run_extraction_worker()
"""

import asyncio
import signal
from typing import Optional
from uuid import UUID

from app.config import settings
from app.shared.cache import RedisClient, init_redis, close_redis
from app.shared.database import async_session_factory
from app.shared.events import EventPublisher, EventTypes
from app.shared.llm import extract_jd
from app.shared.logging import get_logger, setup_logging
from app.shared.queue import QueueConsumer, QueueNames, JobPayload


logger = get_logger(__name__)


class ExtractionWorker(QueueConsumer):
    """
    Worker that processes JD extraction jobs.
    
    Consumes from EXTRACTION queue, calls LLM, updates database.
    """
    
    def __init__(
        self,
        redis_client: RedisClient,
        session_factory,
        event_publisher: Optional[EventPublisher] = None,
    ) -> None:
        """
        Initialize extraction worker.
        
        Args:
            redis_client: Redis client for queue operations
            session_factory: Async session factory for DB
            event_publisher: Optional event publisher
        """
        super().__init__(
            client=redis_client,
            queue_name=QueueNames.EXTRACTION,
            poll_timeout=5,
            max_retries=3,
        )
        self.session_factory = session_factory
        self.publisher = event_publisher
    
    async def process_job(self, job: JobPayload) -> bool:
        """
        Process a single extraction job.
        
        Args:
            job: Job payload with extraction_id and raw_jd
            
        Returns:
            True if successful, False to retry
        """
        # Extract job data
        extraction_id = job.data.get("extraction_id")
        raw_jd = job.data.get("raw_jd")
        employer_id = job.data.get("employer_id")
        
        if not extraction_id or not raw_jd:
            logger.error(
                "Invalid job data - missing extraction_id or raw_jd",
                extra={"job_id": job.job_id, "data": job.data},
            )
            return False  # Don't retry invalid jobs
        
        logger.info(
            f"Processing extraction: {extraction_id}",
            extra={
                "extraction_id": extraction_id,
                "jd_length": len(raw_jd),
                "employer_id": employer_id,
            },
        )
        
        # Mark as processing in database
        async with self.session_factory() as session:
            await self._mark_processing(session, extraction_id)
        
        # Call LLM for extraction
        result = await extract_jd(raw_jd)
        
        # Update database with result
        async with self.session_factory() as session:
            if result.success:
                await self._mark_completed(
                    session,
                    extraction_id,
                    result.data,
                    result.tokens_used,
                )
                
                # Emit completion event
                if self.publisher:
                    await self._emit_completion_event(
                        extraction_id,
                        employer_id,
                        result.data,
                    )
                
                return True
            else:
                # Check if retryable
                if result.retryable and job.attempts < job.max_attempts:
                    logger.warning(
                        f"Extraction failed (retryable): {result.error_message}",
                        extra={
                            "extraction_id": extraction_id,
                            "error_type": result.error_type,
                            "attempt": job.attempts,
                        },
                    )
                    return False  # Will be retried
                else:
                    # Mark as failed permanently
                    await self._mark_failed(
                        session,
                        extraction_id,
                        result.error_message,
                    )
                    return True  # Don't retry, job is done (failed state)
    
    async def _mark_processing(self, session, extraction_id: str) -> None:
        """Mark extraction as processing in database."""
        from app.domains.job.repository import ExtractionRepository
        
        try:
            repo = ExtractionRepository(session)
            await repo.mark_processing(UUID(extraction_id))
            await session.commit()
            
            logger.debug(f"Marked extraction {extraction_id} as processing")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to mark processing: {e}")
    
    async def _mark_completed(
        self,
        session,
        extraction_id: str,
        extracted_data: dict,
        tokens_used: int,
    ) -> None:
        """Mark extraction as completed with results."""
        from app.domains.job.repository import ExtractionRepository
        
        try:
            repo = ExtractionRepository(session)
            await repo.mark_completed(UUID(extraction_id), extracted_data)
            await session.commit()
            
            logger.info(
                f"Extraction completed: {extraction_id}",
                extra={
                    "extraction_id": extraction_id,
                    "tokens_used": tokens_used,
                    "confidence": extracted_data.get("extraction_confidence"),
                },
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to mark completed: {e}")
            raise
    
    async def _mark_failed(
        self,
        session,
        extraction_id: str,
        error_message: str,
    ) -> None:
        """Mark extraction as failed."""
        from app.domains.job.repository import ExtractionRepository
        
        try:
            repo = ExtractionRepository(session)
            await repo.mark_failed(UUID(extraction_id), error_message)
            await session.commit()
            
            logger.error(
                f"Extraction failed: {extraction_id}",
                extra={
                    "extraction_id": extraction_id,
                    "error": error_message,
                },
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to mark failed: {e}")
    
    async def _emit_completion_event(
        self,
        extraction_id: str,
        employer_id: Optional[str],
        extracted_data: dict,
    ) -> None:
        """Emit extraction completed event."""
        try:
            await self.publisher.publish(
                event_type=EventTypes.EXTRACTION_COMPLETED,
                data={
                    "extraction_id": extraction_id,
                    "employer_id": employer_id,
                    "title": extracted_data.get("title"),
                    "location": extracted_data.get("location"),
                    "work_type": extracted_data.get("work_type"),
                    "confidence": extracted_data.get("extraction_confidence"),
                },
            )
            logger.debug(f"Emitted extraction completed event: {extraction_id}")
        except Exception as e:
            # Don't fail the job if event emission fails
            logger.warning(f"Failed to emit completion event: {e}")


async def run_extraction_worker(
    shutdown_event: Optional[asyncio.Event] = None,
) -> None:
    """
    Run the extraction worker.
    
    Args:
        shutdown_event: Optional event to signal shutdown
    """
    # Setup logging
    setup_logging()
    
    logger.info("Starting extraction worker...")
    
    # Initialize Redis
    redis = await init_redis()
    redis_client = RedisClient(redis)
    
    # Initialize event publisher
    event_publisher = EventPublisher(redis_client)
    
    # Create worker
    worker = ExtractionWorker(
        redis_client=redis_client,
        session_factory=async_session_factory,
        event_publisher=event_publisher,
    )
    
    # Setup shutdown handler
    if shutdown_event is None:
        shutdown_event = asyncio.Event()
        
        def handle_shutdown(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            shutdown_event.set()
        
        # Register signal handlers (Unix only)
        try:
            signal.signal(signal.SIGINT, handle_shutdown)
            signal.signal(signal.SIGTERM, handle_shutdown)
        except (AttributeError, ValueError):
            # Windows or not main thread
            pass
    
    # Run worker with shutdown handling
    worker_task = asyncio.create_task(worker.start())
    
    # Wait for shutdown signal
    await shutdown_event.wait()
    
    # Stop worker gracefully
    await worker.stop()
    
    # Wait for worker to finish current job
    try:
        await asyncio.wait_for(worker_task, timeout=30)
    except asyncio.TimeoutError:
        logger.warning("Worker didn't stop in time, cancelling...")
        worker_task.cancel()
    
    # Cleanup
    await close_redis()
    
    # Log stats
    stats = worker.get_stats()
    logger.info(
        "Extraction worker stopped",
        extra={
            "processed": stats["processed_count"],
            "failed": stats["failed_count"],
        },
    )


def main() -> None:
    """Entry point for running worker as script."""
    asyncio.run(run_extraction_worker())


if __name__ == "__main__":
    main()
