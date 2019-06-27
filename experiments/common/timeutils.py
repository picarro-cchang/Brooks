from datetime import datetime


def get_local_timestamp():
    # Get a current local timestamp in IS0 8601 format
    # Example: '2019-06-27 10:40:34'
    local_iso_8601 = datetime.now().replace(microsecond=0).isoformat(' ')
    return local_iso_8601


def get_utc_timestamp():
    # Get a current utc timestamp in ISO 8601 format
    # Example: '2019-06-27 17:40:34'
    utc_iso_8601 = datetime.utcnow().replace(microsecond=0).isoformat(' ')
    return utc_iso_8601
