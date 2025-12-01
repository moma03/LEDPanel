import datetime

from timetables_client import TimetablesClient, format_db_hour, format_db_date
from timetables_loader import TimetablesLoader

if __name__ == "__main__":
    # tc = TimetablesClient("../.env")
    # print(tc.search_station(pattern="Hamburg Hbf"))
    # print(tc.get_planned_timetable_range(
    #     eva_no="8002549",
    #     start=datetime.datetime.now() - datetime.timedelta(hours=5),
    #     end=datetime.datetime.now() + datetime.timedelta(hours=3)
    # ))
    # print(tc._get_planned_timetable_raw(
    #     eva_no="8002549",
    #     day=format_db_date(datetime.datetime.now()),
    #     hour=format_db_hour(datetime.datetime.now())
    # ))
    # print(tc.get_planned_timetable(
    #     eva_no="8002549",
    #     date=datetime.datetime.now()8000297 epd
    # ))

    tl = TimetablesLoader(location="../Data", env_path="../.env", eva_no="8002549")
    tl.main()

