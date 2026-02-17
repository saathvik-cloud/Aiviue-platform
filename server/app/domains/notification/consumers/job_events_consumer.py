"""
Consumes job events from Redis stream (events:jobs) and triggers notifications.

When job.published is received, sends WhatsApp notification via NotificationService.
Designed so more channels (email, SMS) can be added later for the same event.
"""

import asyncio
from typing import Any, Optional

from app.shared.cache.redis_client import RedisClient, RedisStreamsNotSupportedError
from app.shared.events import EventTypes, StreamNames
from app.shared.logging import get_logger

logger = get_logger(__name__)


async def run_job_events_notification_consumer(
    notification_service: Any,
    redis_client: Optional[RedisClient] = None,
    poll_block_ms: int = 5000,
) -> None:
    """
    Run a loop that reads from events:jobs and triggers notifications for job.published.

    Stops when the task is cancelled (e.g. on app shutdown).
    """
    if not redis_client:
        logger.warning("Redis client not provided - notification consumer will not run")
        return

    last_id = "0"  # Start from beginning; next reads use last message id
    stream = StreamNames.JOBS

    logger.info(
        "Notification consumer started (listening for job.published)",
        extra={"stream": stream},
    )

    while True:
        try:
            messages = await redis_client.stream_read(
                stream,
                last_id=last_id,
                count=10,
                block=poll_block_ms,
            )

            for message_id, parsed in messages:
                last_id = message_id
                event_type = parsed.get("event_type") if isinstance(parsed.get("event_type"), str) else None
                data = parsed.get("data")
                if not isinstance(data, dict):
                    continue

                if event_type == EventTypes.JOB_PUBLISHED:
                    job_id = data.get("job_id")
                    employer_id = data.get("employer_id")
                    title = data.get("title") or ""
                    if job_id and employer_id:
                        try:
                            ok = await notification_service.send_job_published_whatsapp(
                                job_id=str(job_id),
                                employer_id=str(employer_id),
                                job_title=title,
                            )
                            if ok:
                                logger.debug(
                                    "Job published notification sent",
                                    extra={"job_id": job_id, "employer_id": employer_id},
                                )
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            logger.exception(
                                "Failed to send job published notification",
                                extra={"job_id": job_id, "employer_id": employer_id, "error": str(e)},
                            )

        except asyncio.CancelledError:
            logger.info("Notification consumer cancelled (shutdown)")
            break
        except RedisStreamsNotSupportedError as e:
            logger.warning(
                "Notification consumer disabled: %s",
                str(e),
                extra={"event": "notification_consumer_disabled"},
            )
            break
        except Exception as e:
            logger.exception("Notification consumer error", extra={"error": str(e)})
            await asyncio.sleep(1)
            continue
