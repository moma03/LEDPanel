import datetime
import json
import logging
import os
from typing import Union

from src.timetables_client import Timetable, TimetableStop


class TimetableCacheStop:

    def __init__(self, timetable_planned: Union[TimetableStop, None] = None, timetable_changes: list = None):
        self.timetable_planned = timetable_planned
        self.timetable_changes = timetable_changes if timetable_changes is not None else []

    def add_timetable_change(self, timetable_change: TimetableStop):
        # TODO BUG: maybe one need to add an additional timestamp to properly store delay changes
        self.timetable_changes.append(timetable_change)


class TimetableCache:
    """
    Handles caching of planned and changed timetables to disk
    Every station has its own directory it contains:
    - one dir per day with a
    - one _stats.json file with some statistics TimetableCacheStationStats
    """

    def __init__(self, location: str = ''):
        self.location = location
        self.change_count = 0

    def add_timetable_planned(self, timetable_planned: Timetable):
        eva_no = timetable_planned.eva
        if not eva_no:
            logging.error(msg="No eva number in planned timetable, cannot cache")
            return
        if not timetable_planned.s:
            logging.info(msg=f"No planned timetable stored for {eva_no}, because no stops found")
            return
        # Gruppiere alle Stops nach Stunde
        stops_by_hour = {}
        for stop in timetable_planned.s:
            stop_time_str = get_planned_time(stop)
            if not stop_time_str:
                continue
            stop_time = datetime.datetime.strptime(stop_time_str, "%y%m%d%H%M")
            hour = stop_time.hour
            stops_by_hour.setdefault(hour, []).append(stop)
        # Für jede Stunde: Cache laden, Stops einfügen, speichern
        for hour, stops in stops_by_hour.items():
            # Nimm das Datum vom ersten Stop dieser Stunde
            date_str = get_planned_time(stops[0])
            date = datetime.datetime.strptime(date_str, "%y%m%d%H%M")
            already_cached_stops = self.load_cached_stops(self.location, str(eva_no), date)
            stats = self.load_station_stats(self.location, str(eva_no))
            for new_stop in stops:
                # Check if stop already exists in cache (same id)
                existing_stop = next((s for s in already_cached_stops if s.timetable_planned and s.timetable_planned.id == new_stop.id), None)
                if existing_stop:
                    existing_stop.timetable_planned = new_stop
                else:
                    already_cached_stops.append(TimetableCacheStop(timetable_planned=new_stop))
            self.save_cached_stops(self.location, str(eva_no), date, already_cached_stops)

    def add_timetable_change(self, timetable_changes: Timetable):
        """
        Adds the changes to the cached timetable
        :param timetable_changes: Timetable with changes
        :return: None
        """

        # ToDo: When there is a delay of an train that was supposed to arrive before the current planned timetable
        # but is now delayed to arrive during the current planned timetable -> system has to load the planned timetable for that time
        # One should be able to get the planned time by looking in the trip id as it contains the date and time when the trip started at its origin
        # For now we just fetch 3 hours before the current planned timetable start time

        eva_no = timetable_changes.eva
        if not eva_no:
            logging.error(msg="No eva number in changed timetable, cannot cache")
            return
        if not timetable_changes.s:
            logging.info(msg=f"No changed timetable stored for {eva_no}, because no stops found")
            return
        eva_cache_dir = os.path.join(self.location, str(eva_no))
        if not os.path.isdir(eva_cache_dir):
            logging.warning(msg=f"Location {eva_cache_dir} is not a directory, cannot cache changed timetable")
            return

        stats = self.load_station_stats(self.location, str(eva_no))
        tmp_hourly_cache = {}
        for change in timetable_changes.s:
            date_str = get_planned_time(change)
            if not date_str:
                logging.warning(msg=f"No planned time in changed timetable stop {change.id}, cannot cache")
                continue
            date = datetime.datetime.strptime(date_str, "%y%m%d%H%M")
            if date.hour not in tmp_hourly_cache:
                tmp_hourly_cache[date.hour] = self.load_cached_stops(self.location, str(eva_no), date)
            for cached_stop in tmp_hourly_cache[date.hour]:
                if cached_stop.timetable_planned and cached_stop.timetable_planned.id == change.id:
                    cached_stop.add_timetable_change(change)
                    stats.change_count += 1
                    break
        for hour, stops in tmp_hourly_cache.items():
            if stops and stops[0].timetable_planned:
                date_str = get_planned_time(stops[0].timetable_planned)
                if date_str:
                    date = datetime.datetime.strptime(date_str, "%y%m%d%H%M").replace(hour=hour)
                    self.save_cached_stops(self.location, str(eva_no), date, stops)

    def get_planned_cache_time_end(self, eva_no) -> datetime.datetime:
        """
        Returns the newest planned time in the cache
        If no planned timetable is in the cache, returns the current time
        :return: datetime
        """
        if not os.path.isdir(self.location):
            logging.warning(msg=f"Location {self.location} is not a directory, cannot get planned cache time end")
            return datetime.datetime.now()

        eva_cache_dir = os.path.join(self.location, str(eva_no))
        if not os.path.isdir(eva_cache_dir):
            logging.info(msg=f"No cache directory for {eva_no}, cannot get planned cache time end")
            return datetime.datetime.now()

        latest_time = datetime.datetime.min
        latest_day_dir = None
        for day_dir in os.listdir(eva_cache_dir):
            day_path = os.path.join(self.location, str(eva_no), day_dir)
            if not os.path.isdir(day_path):
                continue
            if datetime.datetime.strptime(day_dir, "%y%m%d") > latest_time:
                latest_time = datetime.datetime.strptime(day_dir, "%y%m%d")
                latest_day_dir = day_path

        if not latest_day_dir:
            logging.info(msg=f"No planned timetable found in cache for {eva_no}, returning current time")
            return datetime.datetime.now()

        for hour_file in os.listdir(latest_day_dir):
            if not hour_file.endswith(".json"):
                continue
            hour = int(hour_file.replace(".json", ""))
            file_time = latest_time.replace(hour=hour)
            if file_time > latest_time:
                latest_time = file_time

        if latest_time == datetime.datetime.min:
            logging.info(msg=f"No planned timetable found in cache for {eva_no}, returning current time")
            return datetime.datetime.now()
        logging.info(msg="Found planned cache end time for {eva_no}: {latest_time}")
        return latest_time

    @staticmethod
    def load_cached_stops(location: str, eva_no: str, date: datetime.datetime) -> list[TimetableCacheStop]:
        """
        Loads the list of TimetableCacheStop of an specific hour from a json file
        The file is stored in location/eva_no/YYYYMMDD/HH.json
        If the file does not exist, returns an empty list
        """
        assert os.path.isdir(location), f"Location {location} is not a directory"
        assert isinstance(date, datetime.datetime), f"Date {date} is not a datetime"
        assert isinstance(eva_no, str), f"Eva number {eva_no} is not a string"

        cache_dir = os.path.join(location, str(eva_no), date.strftime('%Y%m%d'))
        cache_file = os.path.join(cache_dir, f"{date.hour}.json")
        if not os.path.isfile(cache_file):
            return []  # No cache file found

        # load the cache file and return the list of TimetableCacheStop
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        stops = []
        for stop_dict in data:
            planned = TimetableStop(**stop_dict.get("timetable_planned")) if stop_dict.get(
                "timetable_planned") else None
            changes = [TimetableStop(**c) for c in stop_dict.get("timetable_changes", [])]
            stops.append(TimetableCacheStop(timetable_planned=planned, timetable_changes=changes))
        return stops

    @staticmethod
    def save_cached_stops(location: str, eva_no: str, date: datetime.datetime, stops: list[TimetableCacheStop]):
        """
        Saves the list of TimetableCacheStop of an specific hour to a json file
        The file is stored in location/eva_no/YYYYMMDD/HH.json
        """
        assert os.path.isdir(location), f"Location {location} is not a directory"
        assert isinstance(date, datetime.datetime), f"Date {date} is not a datetime"
        assert isinstance(eva_no, str), f"Eva number {eva_no} is not a string"

        cache_dir = os.path.join(location, str(eva_no), date.strftime('%Y%m%d'))
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            logging.info(msg=f"Created cache directory for {eva_no} on {date.strftime('%Y%m%d')}")

        cache_file = os.path.join(cache_dir, f"{date.hour}.json")
        # Serialisiere zuerst in einen String, um unvollständige Dateien zu vermeiden
        try:
            serializable_data = [{
                "timetable_planned": stop.timetable_planned.model_dump(mode="json", exclude_none=True) if stop.timetable_planned else None,
                "timetable_changes": [c.model_dump(mode="json", exclude_none=True) for c in stop.timetable_changes]
            } for stop in stops]
            json_str = json.dumps(serializable_data, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Error serializing TimetableCacheStop for eva_no={eva_no}, date={date}: {e}")
            return
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        logging.info(msg=f"Cached planned timetable for {eva_no} on {date.strftime('%Y%m%d')}")

    @staticmethod
    def load_station_stats(location, eva_no):
        """
        Loads the station stats from the _stats.json file. Falls die Datei nicht existiert, wird ein neues Objekt mit Standardwerten zurückgegeben.
        """
        assert os.path.isdir(location), f"Location {location} is not a directory"
        assert isinstance(eva_no, str), f"Eva number {eva_no} is not a string"

        stats_file = os.path.join(location, str(eva_no), "_stats.json")
        if not os.path.isfile(stats_file):
            logging.info(msg=f"No stats file found for {eva_no}, returning default stats.")
            return TimetableCacheStationStats()
        with open(stats_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            stats = TimetableCacheStationStats()
            stats.change_count = data.get("change_count", 0)
            return stats


class TimetableCacheStationStats:

    def __init__(self):
        self.change_count = 0


class TimetableCacheMessage:

    def __init__(self, message):
        self.message = message
        self.timestamp = datetime.datetime.now()
        self.count = 1

    def add_message(self, message):
        self.message = message
        self.timestamp = datetime.datetime.now()
        self.count += 1


def get_planned_time(stop: TimetableStop):
    if stop.ar and hasattr(stop.ar, 'pt') and stop.ar.pt:
        return stop.ar.pt
    if stop.dp and hasattr(stop.dp, 'pt') and stop.dp.pt:
        return stop.dp.pt
    return None
