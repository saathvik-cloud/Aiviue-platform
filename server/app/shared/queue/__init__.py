"""
Queue module for Aiviue Platform.

Provides Redis-based job queue for async background processing.

Components:
- QueueProducer: Enqueue jobs for background processing
- QueueConsumer: Process jobs from queue (used by workers)
- SimpleConsumer: Quick consumer with callback function

Usage:
    from app.shared.queue import QueueProducer, QueueNames
    
    # Enqueue a job
    producer = QueueProducer(redis_client)
    await producer.enqueue(
        QueueNames.EXTRACTION,
        {"extraction_id": "123", "raw_jd": "..."},
    )
"""

from app.shared.queue.producer import QueueProducer, QueueNames, JobPayload
from app.shared.queue.consumer import QueueConsumer, SimpleConsumer

__all__ = [
    "QueueProducer",
    "QueueConsumer",
    "SimpleConsumer",
    "QueueNames",
    "JobPayload",
]
