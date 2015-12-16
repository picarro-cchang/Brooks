#!/usr/bin/python
#
# FILE:
#   timestamp.py
#
# DESCRIPTION:
#   timeStamp: number of milliseconds since Jan 1st, 1AD.
#   unixTime (Epoch time): number of seconds since Jan 1st, 1970 AD
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   28-Mar-2009  sze  Initial version.
#   01-Oct-2015  yuan add datenumToUnixTime, datetimeTzToUnixTime
#
#  Copyright (c) 2015 Picarro, Inc. All rights reserved
#
import datetime
import pytz

ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
UNIXORIGIN = datetime.datetime(1970,1,1,0,0,0,0)

def datetimeToTimestamp(t):
    td = t - ORIGIN
    return (td.days*86400 + td.seconds)*1000 + td.microseconds//1000

def getTimestamp():
    """Returns 64-bit millisecond resolution timestamp for instrument"""
    return datetimeToTimestamp(datetime.datetime.utcnow())

def timestampToUtcDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to UTC datetime"""
    return ORIGIN + datetime.timedelta(microseconds=1000*timestamp)

def timestampToLocalDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to local datetime"""
    offset = datetime.datetime.now() - datetime.datetime.utcnow()
    return timestampToUtcDatetime(timestamp) + offset

def formatTime(dateTime):
    ms = dateTime.microsecond//1000
    return dateTime.strftime("%Y/%m/%d %H:%M:%S") + (".%03d" % ms)

def unixTime(timestamp):
    dt = (ORIGIN-UNIXORIGIN)+datetime.timedelta(microseconds=1000*float(timestamp))
    return 86400.0*dt.days + dt.seconds + 1.e-6*dt.microseconds

def unixTimeToTimestamp(u):
    dt = UNIXORIGIN + datetime.timedelta(seconds=float(u))
    return datetimeToTimestamp(dt)
    
def datenumToUnixTime(dateNum):
    """Converts matplotlib datenum to unix time"""
    return dateNum * 86400.0 - 62135683200.0
    
def datetimeTzToUnixTime(t, timezone):
    """Converts datetime with timezone to unix time
    t is a native python datetime without offset
    timezone is a python datetime.tzinfo object"""
    dt = timezone.localize(t)
    return (dt - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()