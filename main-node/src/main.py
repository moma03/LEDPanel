"""
Main orchestration module for the Deutsche Bahn station monitor.

Flow:
1. Verify database connectivity
2. For each monitored station:
   a. Ensure station metadata is in DB
   b. Ensure planned events exist for the monitoring window
   c. Fetch all recent changes for today
   d. Handle anomalies (e.g., delayed trains without plan data)
3. Enter continuous monitoring loop:
   - Every 30 seconds: fetch recent changes (last 2 min)
   - Every 1 hour: fetch plan departures (now + lookahead + 1 hour)
"""

import asyncio
import signal
from contextlib import suppress
import time
from datetime import datetime, timedelta
from typing import Dict, List

from .config import settings
from .logger import setup_logger
from .exceptions import (
    FetchError,
    DatabaseError,
    RetryExhausted,
    ERROR_ESCALATION_THRESHOLD,
)
from .db_manager import db
from .fetcher import fetcher
from .models import StationData

logger = setup_logger(__name__)


class StationMonitor:
    """Monitors a single station for timetable changes."""
    
    def __init__(self, eva: int):
        self.eva = eva
        self.last_planned_fetch = None
        self.last_changes_fetch = None
        self.escalation_backoff_until = None
    
    def should_fetch_planned_events(self) -> bool:
        """Check if it's time to fetch planned events (every 1 hour)."""
        if self.last_planned_fetch is None:
            return True
        return (datetime.now() - self.last_planned_fetch) >= timedelta(seconds=settings.PLANNED_FETCH_INTERVAL_SECONDS)
    
    def should_fetch_changes(self) -> bool:
        """Check if it's time to fetch recent changes (every 30 seconds)."""
        if self.last_changes_fetch is None:
            return True
        return (datetime.now() - self.last_changes_fetch) >= timedelta(seconds=settings.FETCH_INTERVAL_SECONDS)
    
    def should_backoff(self) -> bool:
        """Check if we're in escalation backoff (1 min interval after 5 consecutive errors)."""
        if self.escalation_backoff_until is None:
            return False
        if datetime.now() < self.escalation_backoff_until:
            return True
        self.escalation_backoff_until = None
        return False
    
    def trigger_escalation_backoff(self):
        """Trigger 1-minute backoff after too many errors."""
        self.escalation_backoff_until = datetime.now() + timedelta(minutes=1)
        logger.warning(f"Station {self.eva}: Entering 1-minute backoff due to repeated failures")
    
    async def initialize(self) -> bool:
        """
        Perform initial setup for the station.
        Returns True if successful, False otherwise.
        """
        try:
            # 1. Ensure station metadata exists
            if not await db.has_station_data(self.eva):
                logger.info(f"Station {self.eva}: Fetching station metadata")
                station = await fetcher.fetch_station_data(self.eva)
                await db.save_station_data(station)
                logger.info(f"Station {self.eva}: Metadata saved")
            else:
                logger.debug(f"Station {self.eva}: Metadata already in DB")
            
            # 2. Ensure planned events exist for the monitoring window
            now = datetime.now()
            window_start = now - timedelta(hours=settings.LOOKBEHIND_HOURS)
            window_end = now + timedelta(hours=settings.LOOKAHEAD_HOURS)
            
            if not await db.has_planned_events_for_interval(self.eva, window_start, window_end):
                logger.info(f"Station {self.eva}: Fetching planned events for interval")
                events = await fetcher.fetch_planned_events(self.eva, window_start, window_end)
                saved = await db.save_planned_events(self.eva, events)
                logger.info(f"Station {self.eva}: Saved {saved} planned events")
            else:
                logger.debug(f"Station {self.eva}: Planned events already in DB")
            
            # 3. Fetch all changes for today
            logger.info(f"Station {self.eva}: Fetching today's changes")
            changes = await fetcher.fetch_all_changes_for_day(self.eva)
            saved = await db.save_changed_events(self.eva, changes)
            logger.info(f"Station {self.eva}: Saved {saved} changes")
            
            # 4. Handle anomalies: delayed trains without plan data
            delayed_ids = await db.get_delayed_trains_without_plan(self.eva)
            if delayed_ids:
                logger.warning(f"Station {self.eva}: Found {len(delayed_ids)} delayed trains without plan")
            
            logger.info(f"Station {self.eva}: Initialization complete")
            return True
            
        except (FetchError, DatabaseError, RetryExhausted) as e:
            logger.error(f"Station {self.eva}: Initialization failed: {e}")
            return False
    
    async def fetch_recent_changes(self) -> bool:
        """Fetch and save recent changes. Returns True if successful."""
        try:
            if not self.should_fetch_changes():
                return True
            
            changes = await fetcher.fetch_recent_changes(self.eva, minutes_back=2)
            await db.save_changed_events(self.eva, changes)
            self.last_changes_fetch = datetime.now()
            
            if changes:
                logger.debug(f"Station {self.eva}: Fetched {len(changes)} recent changes")
            
            return True
            
        except (FetchError, DatabaseError, RetryExhausted) as e:
            logger.error(f"Station {self.eva}: Failed to fetch recent changes: {e}")
            return False
    
    async def fetch_planned_events(self) -> bool:
        """Fetch and save planned events. Returns True if successful."""
        try:
            if not self.should_fetch_planned_events():
                return True
            
            now = datetime.now()
            window_start = now
            window_end = now + timedelta(hours=settings.LOOKAHEAD_HOURS + 1)
            
            events = await fetcher.fetch_planned_events(self.eva, window_start, window_end)
            await db.save_planned_events(self.eva, events)
            self.last_planned_fetch = datetime.now()
            
            if events:
                logger.debug(f"Station {self.eva}: Fetched {len(events)} planned events")
            
            return True
            
        except (FetchError, DatabaseError, RetryExhausted) as e:
            logger.error(f"Station {self.eva}: Failed to fetch planned events: {e}")
            return False
    
    async def monitor_cycle(self) -> None:
        """Execute one monitoring cycle for this station."""
        # Check if in escalation backoff
        if self.should_backoff():
            logger.debug(f"Station {self.eva}: In backoff, skipping this cycle")
            return
        
        # Attempt fetches
        changes_ok = await self.fetch_recent_changes()
        planned_ok = await self.fetch_planned_events()
        
        # Track for escalation
        if not (changes_ok and planned_ok):
            self.trigger_escalation_backoff()


class ApplicationOrchestrator:
    """Main application orchestrator."""
    
    def __init__(self):
        self.monitors: Dict[int, StationMonitor] = {}
        self.running = False
    
    async def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            True if all stations initialized successfully
        """
        logger.info("=== Starting Application Initialization ===")
        
        # 1. Check database connectivity
        try:
            if not await db.check_connection():
                logger.critical("Failed to connect to database. Aborting.")
                return False
        except (DatabaseError, RetryExhausted) as e:
            logger.critical(f"Database connection failed: {e}. Aborting.")
            return False
        
        # 2. Initialize monitors for each station
        all_ok = True
        for eva in settings.STATIONS:
            monitor = StationMonitor(eva)
            self.monitors[eva] = monitor
            
            if not await monitor.initialize():
                logger.error(f"Failed to initialize station {eva}")
                all_ok = False
        
        if not all_ok:
            logger.warning("Some stations failed to initialize, but continuing...")
        
        logger.info("=== Initialization Complete ===\n")
        return True
    
    async def run_monitoring_loop(self) -> None:
        """
        Main monitoring loop - runs indefinitely.
        Fetches recent changes every 30 seconds, planned events every 1 hour.
        """
        logger.info("=== Starting Monitoring Loop ===")
        self.running = True
        
        try:
            while self.running:
                logger.debug("--- Monitoring cycle start ---")
                
                # Run all monitors concurrently
                tasks = [
                    monitor.monitor_cycle()
                    for monitor in self.monitors.values()
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait configured interval before next cycle
                await asyncio.sleep(settings.FETCH_INTERVAL_SECONDS)
                
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        except Exception as e:
            logger.critical(f"Unexpected error in monitoring loop: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("=== Shutting Down ===")
        self.running = False
        logger.info("Shutdown complete")

    async def shutdown_async(self) -> None:
        """Async shutdown: stop monitors and close DB connections."""
        logger.info("=== Async Shutdown Start ===")
        self.running = False
        try:
            await db.close()
        except Exception as e:
            logger.warning(f"Error closing DB during shutdown: {e}")
        logger.info("=== Async Shutdown Complete ===")


async def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    orchestrator = ApplicationOrchestrator()

    try:
        if not await orchestrator.initialize():
            logger.error("Initialization failed")
            return 1

        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _stop_signal() -> None:
            logger.info("Received stop signal, initiating shutdown")
            stop_event.set()

        for _sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(_sig, _stop_signal)
            except NotImplementedError:
                # Some platforms (Windows) may not support add_signal_handler
                pass

        monitor_task = asyncio.create_task(orchestrator.run_monitoring_loop())

        # Wait until a stop signal is received
        await stop_event.wait()

        # Cancel monitoring and shutdown
        monitor_task.cancel()
        with suppress(asyncio.CancelledError):
            await monitor_task

        await orchestrator.shutdown_async()
        return 0

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down")
        await orchestrator.shutdown_async()
        return 0
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        try:
            await orchestrator.shutdown_async()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
        

