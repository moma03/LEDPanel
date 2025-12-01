# Notes on what to do next:
# When loading a timetable for a station
# 1. Get the planned timetable for a station (e.g. Hamburg Hbf) using the TimetablesClient.
# 2. Get the full changed timetable for the same station.
# 3. Compare the planned and changed timetables to identify differences.
# 4. loop in 2 min intervals and fetch the recent changes

# - store the planned and changed data together in a structured format JSON
# - make one file per day and station (e.g. Hamburg Hbf 2024-10-01.json)
# - store the data in a directory structure like data/{station}/{year}/{month}/{day
# - add a timestamp to each change to know when it was added

import datetime
import logging

from src.timetable_cache import TimetableCache
from src.timetables_client import TimetablesClient


def setup_logger(name: str, log_file: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger("timetables_loader", log_file="timetables_loader.log")


class TimetablesLoader:

    def __init__(self, eva_no: str, env_path: str = "../.env", location: str = "data"):
        self.client = TimetablesClient(env_path=env_path)
        self.timetable = TimetableCache(location=location)
        self.eva_no = eva_no

    def main(self):
        try:
            logger.info(msg="Starting TimetablesLoader")
            self.init_timetable_fetch(before_hours=2, ahead_hours=3)
            logger.info(msg="Finished initial fetch")
            self.loop_fetch_n_sleep(wait_time=90)

        except KeyboardInterrupt:
            logger.info(msg="Stopping TimetablesLoader")
            self.client.close()
            logger.info(msg="TimetablesLoader stopped")
        except Exception as e:
            logger.error(msg=f"Error in TimetablesLoader: {e}")
            self.client.close()
            logger.info(msg="TimetablesLoader stopped due to error")

    def init_timetable_fetch(self, before_hours: int = 2, ahead_hours: int = 3):
        # Init the timetable with the planned data for the next 3 hours
        start_time = datetime.datetime.now() - datetime.timedelta(hours=before_hours)
        end_time = datetime.datetime.now() + datetime.timedelta(hours=ahead_hours)
        self.timetable.add_timetable_planned(self.client.get_planned_timetable_range(
            eva_no=self.eva_no,
            start=start_time,
            end=end_time
        ))
        self.timetable.add_timetable_change(self.client.get_full_changes(eva_no=self.eva_no))

    def loop_fetch_n_sleep(self, wait_time: int = 90):
        logger.info(msg="Start interval fetching ...")
        time_last_fetch = datetime.datetime.now()
        while True:
            # fetch planned data so that allways 3 hours ahead are covered
            if self.timetable.get_planned_cache_time_end(self.eva_no) < datetime.datetime.now() + datetime.timedelta(hours=3):
                logger.info(msg="Loading more planned data ...")
                start_time = self.timetable.get_planned_cache_time_end(self.eva_no)
                end_time = datetime.datetime.now() + datetime.timedelta(hours=3)
                self.timetable.add_timetable_planned(self.client.get_planned_timetable_range(
                    eva_no=self.eva_no,
                    start=start_time,
                    end=end_time
                ))

            # fetch changes every 1.5 minutes and add them to the timetable
            if time_last_fetch + datetime.timedelta(seconds=wait_time) < datetime.datetime.now():
                logger.info(msg="Loading recent changes ...")
                self.timetable.add_timetable_change(self.client.get_recent_changes(eva_no=self.eva_no))
                time_last_fetch = datetime.datetime.now()
