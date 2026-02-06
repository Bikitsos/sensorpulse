# ================================
# SensorPulse API - Data Cleanup Service
# ================================
#
# Scheduled job to remove sensor readings older than 30 days.
# Runs as a background task within the FastAPI lifespan,
# executing once per day at 03:00 UTC.
#

import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import text, delete
from db.database import AsyncSessionLocal

logger = structlog.get_logger(__name__)

# Configuration
RETENTION_DAYS = 30
CLEANUP_INTERVAL_HOURS = 24
CLEANUP_BATCH_SIZE = 10_000  # Delete in batches to avoid long locks


async def cleanup_old_readings(retention_days: int = RETENTION_DAYS) -> int:
    """
    Delete sensor readings older than `retention_days` days.

    Deletes in batches to avoid holding long database locks.
    Returns the total number of rows deleted.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    total_deleted = 0

    logger.info(
        "Data cleanup starting",
        retention_days=retention_days,
        cutoff=cutoff.isoformat(),
    )

    async with AsyncSessionLocal() as session:
        while True:
            result = await session.execute(
                text(
                    """
                    DELETE FROM sensor_readings
                    WHERE ctid IN (
                        SELECT ctid FROM sensor_readings
                        WHERE time < :cutoff
                        LIMIT :batch_size
                    )
                    """
                ),
                {"cutoff": cutoff, "batch_size": CLEANUP_BATCH_SIZE},
            )
            await session.commit()

            batch_deleted = result.rowcount
            total_deleted += batch_deleted

            if batch_deleted < CLEANUP_BATCH_SIZE:
                break

            # Small pause between batches to reduce DB pressure
            await asyncio.sleep(0.5)

    logger.info(
        "Data cleanup complete",
        rows_deleted=total_deleted,
        retention_days=retention_days,
    )
    return total_deleted


async def cleanup_scheduler():
    """
    Background loop that runs cleanup once per day.

    Waits until the next 03:00 UTC, then runs and repeats.
    """
    logger.info("Data cleanup scheduler started", interval_hours=CLEANUP_INTERVAL_HOURS)

    while True:
        # Calculate seconds until next 03:00 UTC
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()
        logger.info(
            "Next cleanup scheduled",
            next_run=next_run.isoformat(),
            wait_seconds=int(wait_seconds),
        )

        await asyncio.sleep(wait_seconds)

        try:
            deleted = await cleanup_old_readings()
            logger.info("Scheduled cleanup succeeded", rows_deleted=deleted)
        except Exception:
            logger.exception("Scheduled cleanup failed")

        # Guard against rapid re-execution if the clock hasn't advanced
        await asyncio.sleep(60)
