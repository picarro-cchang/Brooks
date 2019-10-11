from datetime import MINYEAR, datetime, timedelta

ORIGIN = datetime(MINYEAR, 1, 1, 0, 0, 0, 0)
UNIXORIGIN = datetime(1970, 1, 1, 0, 0, 0, 0)


def get_local_timestamp():
    # Get a current local timestamp in IS0 8601 format
    # Example: '2019-06-27 10:40:34'
    local_iso_8601 = datetime.now().isoformat(' ')
    return local_iso_8601


def get_utc_timestamp():
    # Get a current utc timestamp in ISO 8601 format
    # Example: '2019-06-27 17:40:34'
    utc_iso_8601 = datetime.utcnow().isoformat(' ')
    return utc_iso_8601


def get_epoch_timestamp():
    # Get a current epoch timestamp
    epoch_time = datetime.timestamp(datetime.now())
    return epoch_time


def datetime_to_timestamp(t):
    # Converts a datetime object to a Picarro millisecond resolution timestamp
    td = t - ORIGIN
    return (td.days * 86400 + td.seconds) * 1000 + td.microseconds // 1000


def get_timestamp():
    # Returns current Picarro millisecond resolution timestamp
    return datetime_to_timestamp(datetime.utcnow())


def timestamp_to_utc_datetime(timestamp):
    # Converts Picarro 64-bit millisecond resolution timestamp to UTC datetime
    return ORIGIN + timedelta(microseconds=1000 * timestamp)


def timestamp_to_local_datetime(timestamp):
    # Converts Picarro 64-bit millisecond resolution timestamp to local datetime
    offset = datetime.now() - datetime.utcnow()
    return timestamp_to_utc_datetime(timestamp) + offset


def format_time(date_time):
    # Convert `date_time` of type datetime to printable format %Y/%m/%d %H:%M:%S.SSS
    ms = date_time.microsecond // 1000
    return date_time.strftime("%Y/%m/%d %H:%M:%S") + (".%03d" % ms)


def unix_time(timestamp):
    # Converts Picarro 64-bit millisecond resolution timestamp to floating point seconds
    #  since Unix epoch
    dt = (ORIGIN - UNIXORIGIN) + timedelta(microseconds=1000 * float(timestamp))
    return 86400.0 * dt.days + dt.seconds + 1.e-6 * dt.microseconds


def unix_time_to_timestamp(u):
    # Converts  seconds since Unix epoch to Picarro 64-bit millisecond resolution timestamp
    dt = UNIXORIGIN + timedelta(seconds=float(u))
    return datetime_to_timestamp(dt)
