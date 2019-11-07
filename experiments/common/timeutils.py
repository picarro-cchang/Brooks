from datetime import datetime


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
