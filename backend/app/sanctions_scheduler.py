"""
LEATrace Sanctions Scheduler — Production.

Background scheduler for automated sanctions data synchronization.
Uses asyncio periodic tasks (no external dependency required).

Features:
- Configurable sync interval per environment variable
- Automatic initial sync on startup (configurable)
- Health monitoring of all providers
- Sync failure alerting via structured logging
- Thread-safe operation
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import time
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger("leatrace.sanctions.scheduler")

# Configuration via environment variables
SANCTIONS_SYNC_INTERVAL_HOURS = float(os.getenv("SANCTIONS_SYNC_INTERVAL_HOURS", "24"))
SANCTIONS_AUTO_SYNC_ON_STARTUP = os.getenv("SANCTIONS_AUTO_SYNC_ON_STARTUP", "false").lower() in {"1", "true", "yes"}
SANCTIONS_HEALTH_CHECK_INTERVAL_MINUTES = float(os.getenv("SANCTIONS_HEALTH_CHECK_INTERVAL_MINUTES", "60"))


class SanctionsBackgroundScheduler:
    """
    Async background scheduler for sanctions feed synchronization.

    Runs as an asyncio task within the FastAPI application lifespan.
    Does not require APScheduler or any external scheduling library.
    """

    def __init__(self):
        self._running = False
        self._sync_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        self._last_sync_result: Optional[Dict[str, Any]] = None
        self._last_health_result: Optional[Dict[str, Any]] = None
        self._last_sync_time: Optional[float] = None
        self._sync_count = 0
        self._error_count = 0
        self._lock = threading.Lock()

    async def start(self) -> None:
        """Starts the background scheduler tasks."""
        if self._running:
            logger.warning("Sanctions scheduler already running.")
            return

        self._running = True
        logger.info(
            "Starting sanctions background scheduler: "
            "sync_interval=%.1fh, auto_sync_on_startup=%s, health_check_interval=%.0fmin",
            SANCTIONS_SYNC_INTERVAL_HOURS,
            SANCTIONS_AUTO_SYNC_ON_STARTUP,
            SANCTIONS_HEALTH_CHECK_INTERVAL_MINUTES,
        )

        # Start sync loop
        self._sync_task = asyncio.create_task(self._sync_loop())

        # Start health check loop
        self._health_task = asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stops the background scheduler."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
        if self._health_task:
            self._health_task.cancel()
        logger.info("Sanctions background scheduler stopped.")

    async def _sync_loop(self) -> None:
        """Periodic sync loop."""
        interval_seconds = SANCTIONS_SYNC_INTERVAL_HOURS * 3600

        # Optional initial sync on startup
        if SANCTIONS_AUTO_SYNC_ON_STARTUP:
            logger.info("Auto-sync on startup enabled. Running initial sync...")
            await asyncio.sleep(10)  # Brief delay to let DB initialize
            await self._run_sync()

        while self._running:
            try:
                logger.info(
                    "Next sanctions sync in %.1f hours.",
                    SANCTIONS_SYNC_INTERVAL_HOURS,
                )
                await asyncio.sleep(interval_seconds)
                if self._running:
                    await self._run_sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Sanctions sync loop error: %s", e)
                self._error_count += 1
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

    async def _run_sync(self) -> None:
        """Executes a single sync cycle in a thread pool to avoid blocking."""
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._sync_in_thread)
            with self._lock:
                self._last_sync_result = result
                self._last_sync_time = time.time()
                self._sync_count += 1

            status = result.get("status", "unknown")
            if status == "completed":
                success = result.get("success", 0)
                failed = result.get("failed", 0)
                logger.info(
                    "Scheduled sanctions sync completed: %d success, %d failed",
                    success, failed,
                )
                if failed > 0:
                    self._error_count += 1
                    logger.warning(
                        "ALERT: %d sanctions provider(s) failed during scheduled sync. "
                        "Check provider health.",
                        failed,
                    )
            else:
                logger.warning("Scheduled sanctions sync returned status: %s", status)

        except Exception as e:
            self._error_count += 1
            logger.error("Scheduled sanctions sync failed: %s", e)
            with self._lock:
                self._last_sync_result = {"status": "error", "error": str(e)[:500]}

    def _sync_in_thread(self) -> Dict[str, Any]:
        """Runs sync in a separate thread with its own DB session."""
        from .database import SessionLocal
        from .providers.sanctions_provider_manager import sanctions_provider_manager
        from .feed_scheduler import feed_scheduler

        db = SessionLocal()
        try:
            result = feed_scheduler.run_daily_sync(db=db)
            return result
        except Exception as e:
            logger.error("Thread sync error: %s", e)
            return {"status": "error", "error": str(e)[:500]}
        finally:
            db.close()

    async def _health_check_loop(self) -> None:
        """Periodic health check loop for all providers."""
        interval_seconds = SANCTIONS_HEALTH_CHECK_INTERVAL_MINUTES * 60

        # Initial delay
        await asyncio.sleep(30)

        while self._running:
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._health_check_in_thread)
                with self._lock:
                    self._last_health_result = result

                unhealthy = result.get("unhealthy", 0)
                if unhealthy > 0:
                    logger.warning(
                        "ALERT: %d sanctions provider(s) are unhealthy. "
                        "Check connectivity and configuration.",
                        unhealthy,
                    )

                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check loop error: %s", e)
                await asyncio.sleep(300)

    def _health_check_in_thread(self) -> Dict[str, Any]:
        """Runs health check in a separate thread."""
        from .providers.sanctions_provider_manager import sanctions_provider_manager
        try:
            return sanctions_provider_manager.health_check_all()
        except Exception as e:
            return {"status": "error", "error": str(e)[:500]}

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Returns current scheduler status."""
        with self._lock:
            return {
                "running": self._running,
                "sync_interval_hours": SANCTIONS_SYNC_INTERVAL_HOURS,
                "auto_sync_on_startup": SANCTIONS_AUTO_SYNC_ON_STARTUP,
                "health_check_interval_minutes": SANCTIONS_HEALTH_CHECK_INTERVAL_MINUTES,
                "sync_count": self._sync_count,
                "error_count": self._error_count,
                "last_sync_time": (
                    datetime.datetime.fromtimestamp(self._last_sync_time).isoformat() + "Z"
                    if self._last_sync_time else None
                ),
                "last_sync_result_status": (
                    self._last_sync_result.get("status") if self._last_sync_result else None
                ),
                "last_health_check": self._last_health_result,
            }

    async def trigger_manual_sync(self) -> Dict[str, Any]:
        """Triggers an immediate sync (for API use)."""
        logger.info("Manual sanctions sync triggered.")
        await self._run_sync()
        with self._lock:
            return self._last_sync_result or {"status": "unknown"}


# ─── Singleton ────────────────────────────────────────────────────────────────

sanctions_scheduler = SanctionsBackgroundScheduler()
