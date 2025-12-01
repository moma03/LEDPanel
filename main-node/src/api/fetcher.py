"""Dynamic fetcher for DB Timetables API — planned and change data."""
import asyncio
import structlog
import xmltodict
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.future import select

from ..config import settings
from ..db.session import AsyncSessionLocal
from ..db.models import Station, Trip, TimetableStop, PlannedEvent, ChangedEvent

log = structlog.get_logger(__name__)

API_BASE = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"
HEADERS = {
    "DB-Client-Id": settings.DB_CLIENT_ID,
    "DB-Api-Key": settings.DB_API_KEY,
    "Accept": "application/xml",
}

async def fetch_timetable(eva: int, date: str, hour: str, session):
    url = f"{API_BASE}/plan/{eva}/{date}/{hour}"
    async with AsyncClient(headers=HEADERS, timeout=20) as client:
        r = await client.get(url)
        if r.status_code != 200:
            log.warning("plan_fetch_failed", eva=eva, code=r.status_code)
            return None
        data = xmltodict.parse(r.text)
        return data.get("timetable", {})

async def fetch_changes(eva: int, session):
    url = f"{API_BASE}/fchg/{eva}"
    async with AsyncClient(headers=HEADERS, timeout=20) as client:
        r = await client.get(url)
        if r.status_code != 200:
            log.warning("change_fetch_failed", eva=eva, code=r.status_code)
            return None
        data = xmltodict.parse(r.text)
        return data.get("timetable", {})

async def fetch_recent_changes(eva: int, session):
    """Fetch recent changes (last ~2 minutes)."""
    url = f"{API_BASE}/rchg/{eva}"
    async with AsyncClient(headers=HEADERS, timeout=20) as client:
        r = await client.get(url)
        if r.status_code != 200:
            log.warning("recent_change_fetch_failed", eva=eva, code=r.status_code)
            return None
        data = xmltodict.parse(r.text)
        return data.get("timetable", {})

async def fetch_station(pattern: str):
    """Fetch station data by ar DS100 or full Name"""
    url = f"{API_BASE}/station/{pattern}"
    async with AsyncClient(headers=HEADERS, timeout=20) as client:
        r = await client.get(url)
        if r.status_code != 200:
            log.warning("station_fetch_failed", pattern=pattern, code=r.status_code)
            return None
        data = xmltodict.parse(r.text)
        return data.get("stations", {}).get("station", [])

async def process_plan_data(data, eva: int, session: AsyncSessionLocal):
    """
    Process and store planned timetable data.
    """
    if not data:
        return 0
    stops = data.get("s", [])
    if isinstance(stops, dict):
        stops = [stops]

    new_records = 0
    for stop in stops:
        stop_id = stop.get("id")
        trip_label = stop.get("tl", {})
        trip_id = f"{trip_label.get('c','')}-{trip_label.get('n','')}"

        # Trip upsert
        trip = (await session.execute(select(Trip).where(Trip.trip_id == trip_id))).scalar_one_or_none()
        if not trip:
            trip = Trip(trip_id=trip_id, category=trip_label.get("c"), number=trip_label.get("n"))
            session.add(trip)

        # Stop upsert
        existing_stop = (await session.execute(select(TimetableStop).where(TimetableStop.stop_id == stop_id))).scalar_one_or_none()
        if not existing_stop:
            stop_obj = TimetableStop(stop_id=stop_id, eva=eva, trip=trip)
            session.add(stop_obj)
            new_records += 1

            # Planned arrival/departure events
            for ev_type in ["ar", "dp"]:
                if ev := stop.get(ev_type):
                    pe = PlannedEvent(
                        stop=stop_obj,
                        event_type="arrival" if ev_type == "ar" else "departure",
                        planned_time=ev.get("pt"),
                        planned_platform=ev.get("pp"),
                    )
                    session.add(pe)

    await session.commit()
    return new_records

async def process_change_data(data, eva: int, session):
    if not data:
        return 0
    stops = data.get("s", [])
    if isinstance(stops, dict):
        stops = [stops]

    new_changes = 0
    for stop in stops:
        stop_id = stop.get("id")
        db_stop = (await session.execute(select(TimetableStop).where(TimetableStop.stop_id == stop_id))).scalar_one_or_none()
        if not db_stop:
            continue

        for ev_type in ["ar", "dp"]:
            ev = stop.get(ev_type)
            if not ev:
                continue

            changed_event = ChangedEvent(
                stop=db_stop,
                event_type="arrival" if ev_type == "ar" else "departure",
                changed_time=ev.get("ct"),
                changed_platform=ev.get("cp"),
                changed_status=ev.get("cs"),
            )
            try:
                session.add(changed_event)
                await session.commit()
                new_changes += 1
            except Exception:
                await session.rollback()  # likely a duplicate
    return new_changes

async def fetch_all():
    async with AsyncSessionLocal() as session:
        stations = (await session.execute(select(Station))).scalars().all()
        now = datetime.utcnow()
        date = now.strftime("%y%m%d")
        hour = now.strftime("%H")

        for station in stations:
            eva = station.eva
            plan_data = await fetch_timetable(eva, date, hour, session)
            changes_data = await fetch_changes(eva, session)

            added_plans = await process_plan_data(plan_data, eva, session)
            added_changes = await process_change_data(changes_data, eva, session)
            log.info("fetch_cycle", eva=eva, added_plans=added_plans, added_changes=added_changes)


async def fetch_future(lookahead_hours: int = 3):
    async with AsyncSessionLocal() as session:
        stations = (await session.execute(select(Station))).scalars().all()
        now = datetime.utcnow()

        for hour_offset in range(lookahead_hours):
            future_time = now + timedelta(hours=hour_offset)
            date = future_time.strftime("%y%m%d")
            hour = future_time.strftime("%H")

            for station in stations:
                eva = station.eva
                plan_data = await fetch_timetable(eva, date, hour, session)
                added_plans = await process_plan_data(plan_data, eva, session)
                log.info("future_fetch_cycle", eva=eva, hour=hour, added_plans=added_plans)