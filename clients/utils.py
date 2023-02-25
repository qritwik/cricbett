from datetime import datetime, timedelta
from dateutil import tz


def convert_utc_into_ist(utc_time_str: str, minutes=0):
    utc_time = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S%z")
    from_utc = tz.gettz('UTC')
    to_ist = tz.gettz('Asia/Kolkata')
    utc = utc_time.replace(tzinfo=from_utc)
    ist = utc.astimezone(to_ist)
    subtracted_time = ist - timedelta(minutes=int(minutes))
    formatted_ist_time = subtracted_time.strftime("%Y-%m-%d %H:%M %Z")
    return formatted_ist_time

# time_string = "2023-02-11 04:00:00+00:00"
# print(convert_utc_into_ist(time_string, 30))
