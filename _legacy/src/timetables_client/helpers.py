from datetime import datetime


def format_db_date(dt: datetime) -> str:
    """Convert datetime to DB API YYMMDD format."""
    return dt.strftime("%y%m%d")


def format_db_hour(dt: datetime) -> str:
    """Convert datetime to DB API HH format (24h)."""
    v = dt.strftime("%H")
    return v


def split_stop_id(stop_id: str) -> tuple[str, datetime, str]:
    """
    separates a stop id into: start date, number of stop in trip, daily trip id
    :param stop_id: the stop id to split
    :return: tuple of (number of stop in trip, daily trip id)
    """
    train_id = stop_id.rsplit('-', 2)[0]
    date = stop_id.rsplit('-', 2)[1]
    date = datetime.strptime(date, "%y%m%d%H%M")
    stop_number = stop_id.rsplit('-', 2)[2]
    return train_id, date, stop_number


if __name__ == "__main__":
    now = datetime.now()
    print(format_db_date(now))
    print(format_db_date(datetime(1902, 1, 1)))
    print(format_db_hour(now))

    print(format_db_hour(datetime(2024, 1, 1, 5, 0, 0)))
    print(format_db_hour(datetime(2024, 1, 1, 0, 1, 0)))

    assert split_stop_id("-7874571842864554321-1403311221-11") == ("-7874571842864554321", datetime(year=2014, month=3, day=31, hour=12, minute=21), "11")
    assert split_stop_id("123-2401010000-1") == ("123", datetime(year=2024, month=1, day=1, hour=0, minute=0), "1")
    assert split_stop_id("-123-2401010000-101") == ("-123", datetime(year=2024, month=1, day=1, hour=0, minute=0), "101")
