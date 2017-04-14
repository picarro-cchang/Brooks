import datetime
import sys

ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
OFFSET = datetime.datetime.now() - datetime.datetime.utcnow()

def timestampToLocalDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to local datetime"""
    return datetime.timedelta(microseconds=1000*timestamp) + ORIGIN + OFFSET

def format_timestamp(ts):
    # format timestamp into string "YYMMDDhhmmss"
    dt = timestampToLocalDatetime(ts)
    return dt.strftime("%y%m%d%H%M%S")

def alarm_high_H2O2(x):
    return True if x > 0.0 else False
    
def set_time():
    # Get timestamp of int-64 bit format
    trial_count = 3
    curr_trail = 0
    while curr_trail < trial_count:
        sync_time = GetValue("SyncTime")
        if int(sync_time) > 0:
            break
    else:
        print "Fail to read SyncTime from Modbus!"
        return
    # Set syncTime as the system current time
    dt = timestampToLocalDatetime(sync_time)
    if sys.platform == 'win32':
        import win32api
        win32api.SetSystemTime(
            dt.year,
            dt.month,
            0,  # day of week
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond / 1000
        )
    elif sys.platform == 'linux2':
        import subprocess
        import shlex
        #subprocess.call(shlex.split("timedatectl set-ntp false"))  # May be necessary
        subprocess.call(shlex.split("sudo date -s '%s'" % dt.strftime("%d %b %Y %H:%M:%S")))
        subprocess.call(shlex.split("sudo hwclock -w"))
    # Set syncTime to 0 in Modbus
    SetValue("SyncTime", 0)