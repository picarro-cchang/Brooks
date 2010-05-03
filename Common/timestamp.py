#!/usr/bin/python
#
# FILE:
#   timestamp.py
#
# DESCRIPTION:
#   Routines for handling timestamps on the instrument. These are 64-bit integers with
#    millisecond resolution which are based on UTC, to avoid issues with daylight saving
#    and timezones.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   28-Mar-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#
import datetime

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
    dt = (ORIGIN-UNIXORIGIN)+datetime.timedelta(microseconds=1000*timestamp)
    return 86400.0*dt.days + dt.seconds + 1.e-6*dt.microseconds

def unixTimeToTimestamp(u):
    dt = UNIXORIGIN + datetime.timedelta(seconds=u)
    return datetimeToTimestamp(dt)
