from dateutil import tz
from datetime import datetime


def convert_utc_into_ist(utc_time_str: str):
    utc_time = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S%z")
    from_utc = tz.gettz('UTC')
    to_ist = tz.gettz('Asia/Kolkata')
    utc = utc_time.replace(tzinfo=from_utc)
    ist = utc.astimezone(to_ist)
    formatted_ist_time = ist.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_ist_time

print(convert_utc_into_ist("2023-02-11 04:00:00+00:00"))