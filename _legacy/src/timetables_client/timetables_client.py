from pathlib import Path
from typing import Any, Dict, Union, overload
import os
import datetime
import httpx
from dotenv import load_dotenv

from .models import Timetable, MultipleStationData
from .helpers import format_db_date, format_db_hour
from .parse_xml import parse


class TimetablesClient:
    BASE_URL = "https://apis.deutschebahn.com/db-api-marketplace/apis/timetables/v1"

    def __init__(self, env_path: str, *, timeout: float = 15.0):
        """
        Initialize the client with credentials from a .env file.
        :param env_path: Path to .env file containing DB_CLIENT_ID and DB_CLIENT_SECRET
        :param timeout: Request timeout in seconds (default: 15.0)
        """
        # Load .env file
        # process relative paths
        env_file = Path(env_path).expanduser().resolve()
        if not env_file.exists():
            raise FileNotFoundError(f".env file not found at {env_path}")
        load_dotenv(env_file)

        client_id = os.getenv("DB_CLIENT_ID")
        api_key = os.getenv("DB_CLIENT_SECRET")
        if not client_id or not api_key:
            raise ValueError("DB_CLIENT_ID or DB_CLIENT_SECRET not found in .env file")

        self._session = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "DB-Client-Id": client_id,
                "DB-Api-Key": api_key,
                "Accept": "application/xml",
            },
            timeout=timeout,
        )

    # -------------
    # Endpoints
    # -------------

    @overload
    def get_planned_timetable(self, *, eva_no: str, date: datetime.datetime, day: None = ..., hour: None = ...) -> Timetable: ...

    @overload
    def get_planned_timetable(self, *, eva_no: str, date: None = ..., day: str, hour: str) -> Timetable: ...

    def get_planned_timetable(self, *, eva_no: str, date: Union[datetime.datetime, None] = None, day: Union[str, None] = None, hour: Union[str, None] = None) -> Timetable:
        """
        Fetch planned timetable for the given station EVA number, date, and hour.
        Endpoint: /plan/{evaNo}/{date}/{hour}
        :param eva_no: EVA number of the station
        :param day: day in YYMMDD format or datetime object, optional if date is datetime
        :param hour: Hour in HH format (00-23), optional if date is datetime
        :param date: datetime object representing the date and time, optional if day and hour are provided
        :return: Timetable containing planned trips
        """
        assert eva_no is not None
        if date is not None:
            if hour is None:
                hour = format_db_hour(date)
            day = format_db_date(date)
        elif day is None or hour is None:
            raise ValueError("Either date or both day and hour must be provided.")

        d = parse(self._get_planned_timetable_raw(eva_no=eva_no, day=day, hour=hour))
        # API root element is 'timetable'
        data = d.get("timetable", {})
        d = Timetable.model_validate(data)
        d.eva = eva_no
        return d

    def get_full_changes(self, *, eva_no: Union[str, int]) -> Timetable:
        """
        Fetch full changes for the given station EVA number.
        Endpoint: /fchg/{evaNo}
        :param eva_no: EVA number of the station
        :return: Timetable containing full changes
        """
        d = parse(self._get_full_changes_raw(eva_no=eva_no))
        data = d.get("timetable", {})
        return Timetable.model_validate(data)

    def get_recent_changes(self, *, eva_no: Union[str, int]) -> Timetable:
        """
        Fetch recent changes for the given station EVA number.
        Endpoint: /rchg/{evaNo}
        :param eva_no: EVA number of the station
        :return: Timetable containing recent changes
        """
        d = parse(self._get_recent_changes_raw(eva_no=eva_no))
        data = d.get("timetable", {})
        return Timetable.model_validate(data)

    def search_station(self, *, pattern: str) -> MultipleStationData:
        """
        Fetch station data matching the given pattern (station name or DS100 code).
        Endpoint: /station/{pattern}
        :param pattern: Station name or DS100 code pattern (case-insensitive, supports wildcards)
        :return: MultipleStationData containing matching stations
        """
        d = parse(self._search_station_raw(pattern=pattern))
        # Some responses might be { 'stations': { 'station': [...] } } or just { 'station': [...] }
        payload: Dict[str, Any]
        if "stations" in d and isinstance(d["stations"], dict):
            stations = d["stations"].get("station", [])
            payload = {"station": stations or []}
        else:
            payload = {"station": d.get("station", []), }
        return MultipleStationData.model_validate(payload)

    # -------------
    # Debug get raw XML
    # -------------
    def _get_planned_timetable_raw(self, *, eva_no: str, day: str, hour: str) -> str:
        return self._get_xml(f"/plan/{eva_no}/{day}/{hour}")

    def _get_full_changes_raw(self, *, eva_no: str) -> str:
        return self._get_xml(f"/fchg/{eva_no}")

    def _get_recent_changes_raw(self, *, eva_no: str) -> str:
        return self._get_xml(f"/fchg/{eva_no}")

    def _search_station_raw(self, *, pattern: str) -> str:
        return self._get_xml(f"/station/{pattern}")

    # -------------
    # Low-level GET
    # -------------
    def _get_xml(self, path: str) -> str:
        resp = self._session.get(path)
        resp.raise_for_status()
        return resp.text

    # -------------
    # Higher-level convenience
    # -------------
    def get_planned_timetable_range(self, eva_no: str, start: datetime.datetime, end: datetime.datetime) -> Timetable:
        """
        Fetch the planned timetable for a station (eva_no) in the given time range (start to end).
        Note that maximal data range returned are 24 hours.
        Also note that the API usually just has data for the current day and first hours of the next day.

        :param eva_no: The EVA number of the station.
        :param start: The start time (datetime).
        :param end: The end time (datetime).
        :return: The planned timetable for the given station and time range.
        """
        assert isinstance(start, datetime.datetime)
        assert isinstance(end, datetime.datetime)
        if end < start:
            raise ValueError("end must be after start")

        timetable = Timetable()
        current = start.replace(minute=0, second=0, microsecond=0)
        while current.date() <= end.date():
            if current.date() == start.date():
                hour_start = start.hour
            else:
                hour_start = 0
            if current.date() == end.date():
                hour_end = end.hour
            else:
                hour_end = 23
            for hour in range(hour_start, hour_end + 1):
                dt = current.replace(hour=hour)
                timetable += self.get_planned_timetable(
                    eva_no=eva_no,
                    day=format_db_date(dt),
                    hour=format_db_hour(dt),
                )
            current += datetime.timedelta(days=1)
            current = current.replace(hour=0)
        return timetable

    # -------------
    # Convenience
    # -------------
    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "TimetablesClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


# ----------------------
# JSON convenience mixins (optional usage)
# ----------------------

# class JsonMixin:
#     """Drop-in mixin if you want explicit to_json/from_json methods."""
#     def to_json(self, **kwargs: Any) -> str:
#         return self.model_dump_json(**kwargs)
#
#     @classmethod
#     def from_json(cls, data: str) -> Any:
#         return cls.model_validate_json(data)
#
# # You can also monkey-patch if desired, e.g.:
# # Timetable.to_json = JsonMixin.to_json  # type: ignore
# # Timetable.from_json = JsonMixin.from_json  # type: ignore


# ----------------------
# Small CLI for testing (optional)
# ----------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DB Timetables client")
    parser.add_argument("env", help="Path to .env containing DB_CLIENT_ID and DB_API_KEY")
    sub = parser.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("eva")
    plan.add_argument("date", help="YYMMDD")
    plan.add_argument("hour", help="HH (00-23)")

    fchg = sub.add_parser("fchg")
    fchg.add_argument("eva")

    rchg = sub.add_parser("rchg")
    rchg.add_argument("eva")

    stat = sub.add_parser("station")
    stat.add_argument("pattern", help="Station name or DS100 code pattern")

    args = parser.parse_args()

    with TimetablesClient(args.env) as client:
        if args.cmd == "plan":
            tt = client.get_planned_timetable(eva_no=args.eva, date=args.date, hour=args.hour)
            print(tt.model_dump_json(indent=2))
        elif args.cmd == "fchg":
            tt = client.get_full_changes(eva_no=args.eva)
            print(tt.model_dump_json(indent=2))
        elif args.cmd == "rchg":
            tt = client.get_recent_changes(eva_no=args.eva)
            print(tt.model_dump_json(indent=2))
        elif args.cmd == "station":
            msd = client.search_station(pattern=args.pattern)
            print(msd.model_dump_json(indent=2))
