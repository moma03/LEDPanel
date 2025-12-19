"""
API Fetcher module for Deutsche Bahn station and timetable data.
Handles all external API calls with retry logic using Deutsche Bahn Timetables API v1.

API Endpoints:
- /station/{pattern} - Query stations by name, EVA, or DS100
- /plan/{evaNo}/{date}/{hour} - Fetch planned departures/arrivals for an hourly slice
- /rchg/{evaNo} - Fetch recent changes (last 2 minutes)
- /fchg/{evaNo} - Fetch all known changes
"""

import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote

from .logger import setup_logger
from .exceptions import FetchError, retry_with_backoff
from .models import StationData, PlannedEvent, ChangedEvent
from .config import settings

logger = setup_logger(__name__)

# Deutsche Bahn API constants
DB_API_BASE_URL = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"


def parse_db_time(time_str: str) -> datetime:
    """
    Parse Deutsche Bahn time format 'YYMMddHHmm' to datetime.
    
    Args:
        time_str: Time in format like '2501181430' (18 Dec 2025 14:30)
    
    Returns:
        datetime object
    """
    if not time_str or len(time_str) < 10:
        return datetime.now()
    
    # Format: YYMMddHHmm
    yy = int(time_str[0:2])
    mm = int(time_str[2:4])
    dd = int(time_str[4:6])
    hh = int(time_str[6:8])
    minute = int(time_str[8:10])
    
    # Handle century (assume 20XX for now, adjust if needed)
    year = 2000 + yy if yy < 50 else 1900 + yy
    
    return datetime(year, mm, dd, hh, minute)


class DataFetcher:
    """Fetches data from Deutsche Bahn Timetables API."""
    
    def __init__(self):
        """Initialize fetcher with API credentials from settings."""
        self.api_key = settings.DB_API_KEY
        self.client_id = settings.DB_CLIENT_ID
        self.timeout = settings.TIMEOUT_SECONDS
        self.base_url = DB_API_BASE_URL
    
    def _get_headers(self) -> dict:
        """Get headers with authentication for DB API."""
        return {
            "DB-Api-Key": self.api_key,
            "DB-Client-Id": self.client_id,
            "Accept": "application/xml",
        }
    
    @retry_with_backoff(operation_name="fetch_station_data")
    async def fetch_station_data(self, eva: int) -> StationData:
        """
        Fetch station information by EVA number.
        
        Args:
            eva: EVA station identifier
        
        Returns:
            StationData object
        
        Raises:
            FetchError: If fetch fails after retries
        """
        try:
            logger.info(f"Fetching station data for EVA {eva}")
            
            url = f"{self.base_url}/station/{eva}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.text)
            
            # Navigate to first station element
            # Response format: <multipleStationData><station.../></multipleStationData>
            station_elem = root.find(".//station")
            if station_elem is None:
                raise FetchError(f"No station data found for EVA {eva}")
            
            # Extract station data from attributes
            station = StationData(
                eva=int(station_elem.get("eva", eva)),
                name=station_elem.get("name", f"Station {eva}"),
                ds100=station_elem.get("ds100"),
                platforms=len(station_elem.get("p", "").split("|")) if station_elem.get("p") else 0,
            )
            
            logger.debug(f"Successfully fetched station data: {station.name}")
            return station
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching station data for {eva}: {e}")
            raise FetchError(f"HTTP error: {e}") from e
        except Exception as e:
            logger.error(f"Error fetching station data for {eva}: {e}")
            raise FetchError(f"Failed to fetch station data: {e}") from e
    
    @retry_with_backoff(operation_name="fetch_planned_events")
    async def fetch_planned_events(
        self,
        eva: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[PlannedEvent]:
        """
        Fetch planned departures/arrivals for a station in time interval.
        
        The DB API provides planned data in hourly slices, so we fetch
        all hours in the given interval.
        
        Args:
            eva: EVA station identifier
            start_time: Start of time window
            end_time: End of time window
        
        Returns:
            List of planned events
        
        Raises:
            FetchError: If fetch fails after retries
        """
        events = []
        
        try:
            logger.info(f"Fetching planned events for station {eva} ({start_time} - {end_time})")
            
            # Generate hourly API calls for the interval
            current = start_time.replace(minute=0, second=0, microsecond=0)
            
            while current <= end_time:
                date_str = current.strftime("%y%m%d")  # YYMMdd format
                hour_str = current.strftime("%H")       # HH format
                
                url = f"{self.base_url}/plan/{eva}/{date_str}/{hour_str}"
                
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(url, headers=self._get_headers())
                        response.raise_for_status()

                    # Parse XML response
                    root = ET.fromstring(response.text)
                    
                    # Extract events from timetable stops
                    for stop in root.findall(".//s"):
                        stop_eva = int(stop.get("eva", 0))
                        stop_id = stop.get("id", "")
                        
                        # Parse departure event
                        dp_elem = stop.find("dp")
                        if dp_elem is not None:
                            pt = dp_elem.get("pt")
                            if pt:
                                    planned_path = dp_elem.get("ppth") or stop.get("ppth")
                                    wings = dp_elem.get("wings") or stop.get("wings")
                                    events.append(PlannedEvent(
                                        stop_id=stop_id,
                                        event_type="dep",
                                        planned_time=parse_db_time(pt),
                                        planned_platform=dp_elem.get("pp"),
                                        planned_path=planned_path,
                                        wings=wings,
                                    ))
                        
                        # Parse arrival event
                        ar_elem = stop.find("ar")
                        if ar_elem is not None:
                            pt = ar_elem.get("pt")
                            if pt:
                                planned_path = ar_elem.get("ppth") or stop.get("ppth")
                                wings = ar_elem.get("wings") or stop.get("wings")
                                events.append(PlannedEvent(
                                    stop_id=stop_id,
                                    event_type="arr",
                                    planned_time=parse_db_time(pt),
                                    planned_platform=ar_elem.get("pp"),
                                    planned_path=planned_path,
                                    wings=wings,
                                ))
                
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        # No data for this hour, skip
                        logger.debug(f"No planned data for {eva} on {date_str}:{hour_str}")
                    else:
                        logger.warning(f"HTTP error for hour {date_str}:{hour_str}: {e}")
                
                current += timedelta(hours=1)
            
            logger.debug(f"Fetched {len(events)} planned events for station {eva}")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching planned events: {e}")
            raise FetchError(f"Failed to fetch planned events: {e}") from e
    
    @retry_with_backoff(operation_name="fetch_recent_changes")
    async def fetch_recent_changes(
        self,
        eva: int,
        minutes_back: int = 2
    ) -> List[ChangedEvent]:
        """
        Fetch recent changes (actual departures/arrivals) for a station.
        Recent changes are always a subset of full changes and represent
        changes that became known within the last 2 minutes.
        
        Args:
            eva: EVA station identifier
            minutes_back: How far back to look (API always returns last ~2 min)
        
        Returns:
            List of changed events
        
        Raises:
            FetchError: If fetch fails after retries
        """
        try:
            logger.debug(f"Fetching recent changes for station {eva}")
            
            url = f"{self.base_url}/rchg/{eva}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()

            events = self._parse_changes_xml(response.text, eva)
            
            if events:
                logger.debug(f"Fetched {len(events)} recent changes for station {eva}")
            
            return events
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching recent changes for {eva}: {e}")
            raise FetchError(f"HTTP error: {e}") from e
        except Exception as e:
            logger.error(f"Error fetching recent changes: {e}")
            raise FetchError(f"Failed to fetch recent changes: {e}") from e
    
    @retry_with_backoff(operation_name="fetch_all_changes_for_day")
    async def fetch_all_changes_for_day(self, eva: int, date: Optional[datetime] = None) -> List[ChangedEvent]:
        """
        Fetch all changes for a given day (for comprehensive updates).
        
        Args:
            eva: EVA station identifier
            date: Date to fetch for (None = today)
        
        Returns:
            List of all changed events for the day
        
        Raises:
            FetchError: If fetch fails after retries
        """
        if date is None:
            date = datetime.now()
        
        try:
            logger.info(f"Fetching all changes for station {eva} on {date.date()}")
            
            url = f"{self.base_url}/fchg/{eva}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()

            events = self._parse_changes_xml(response.text, eva)
            
            logger.debug(f"Fetched {len(events)} all changes for station {eva}")
            return events
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching all changes for {eva}: {e}")
            raise FetchError(f"HTTP error: {e}") from e
        except Exception as e:
            logger.error(f"Error fetching all changes for day: {e}")
            raise FetchError(f"Failed to fetch all changes: {e}") from e
    
    def _parse_changes_xml(self, xml_text: str, eva: int) -> List[ChangedEvent]:
        """
        Parse changed events from XML response.
        
        Args:
            xml_text: XML response body
            eva: Station EVA for context
        
        Returns:
            List of parsed ChangedEvent objects
        """
        events = []
        root = ET.fromstring(xml_text)
        
        # Extract events from timetable stops
        for stop in root.findall(".//s"):
            stop_id = stop.get("id", "")
            
            # Parse departure changes
            dp_elem = stop.find("dp")
            if dp_elem is not None:
                ct = dp_elem.get("ct")  # Changed time
                cs = dp_elem.get("cs")  # Changed status
                if ct or cs:
                    changed_path = dp_elem.get("cpth") or dp_elem.get("ppth") or stop.get("cpth") or stop.get("ppth")
                    wings = dp_elem.get("wings") or stop.get("wings")
                    events.append(ChangedEvent(
                        stop_id=stop_id,
                        event_type="departure",
                        changed_time=parse_db_time(ct) if ct else None,
                        changed_platform=dp_elem.get("cp"),
                        changed_status=cs,
                        changed_path=changed_path,
                        wings=wings,
                    ))
            
            # Parse arrival changes
            ar_elem = stop.find("ar")
            if ar_elem is not None:
                ct = ar_elem.get("ct")
                cs = ar_elem.get("cs")
                if ct or cs:
                    changed_path = ar_elem.get("cpth") or ar_elem.get("ppth") or stop.get("cpth") or stop.get("ppth")
                    wings = ar_elem.get("wings") or stop.get("wings")
                    events.append(ChangedEvent(
                        stop_id=stop_id,
                        event_type="arrival",
                        changed_time=parse_db_time(ct) if ct else None,
                        changed_platform=ar_elem.get("cp"),
                        changed_status=cs,
                        changed_path=changed_path,
                        wings=wings,
                    ))
        
        return events
    
    @retry_with_backoff(operation_name="fetch_train_plan_data")
    async def fetch_train_plan_data(
        self,
        train_id: str,
        start_time: datetime
    ) -> List[PlannedEvent]:
        """
        Fetch plan data for a specific train starting from a given time.
        Used when a train is delayed but no plan departure exists in DB.
        
        Note: The current Deutsche Bahn API doesn't have a direct endpoint
        for fetching a specific train's route. This would require additional
        logic or a different data source. For now, this returns empty.
        
        Args:
            train_id: Unique train identifier
            start_time: Time to start fetching plan data from
        
        Returns:
            List of planned events for the train
        
        Raises:
            FetchError: If fetch fails after retries
        """
        try:
            logger.warning(f"fetch_train_plan_data not yet implemented for train {train_id}")
            # TODO: Implement if DB API adds specific train query endpoint
            return []
            
        except Exception as e:
            logger.error(f"Error fetching train plan data: {e}")
            raise FetchError(f"Failed to fetch train plan data: {e}") from e


# Global instance
fetcher = DataFetcher()
