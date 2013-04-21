#!/usr/bin/python
#
"""
File Name: SwathProcessor.py
Purpose: Helper for AnalyzerServer which calculates the field of view
  from a collection of points along the path and the wind statistics

File History:
    17-Apr-2012  sze  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
from collections import deque
from numpy import arctan2, asarray, cos, isfinite, isnan
from numpy import pi, sin, sqrt
import cPickle
import time
import swathP as sp

import SurveyorInstStatus as sis

EARTH_RADIUS = 6378100
DTR = pi/180.0
RTD = 180.0/pi
NOT_A_NUMBER = 1e1000/1e1000


# Function defining the additional wind direction standard deviation based
#  on the wind speed and vehicle speed
# Angles are in RADIANS
def astd(wind, vcar, params):
    # a = 0.15*pi
    # b = 0.25
    # c = 0.0
    return min(pi, params["a"]*(params["b"]+params["c"]*vcar)/(wind+0.01))


def processGen(source, maxWindow, stabClass, minLeak, minAmpl, astdParams):
    fovBuff = deque()
    N = maxWindow              # Use 2*N+1 samples for calculating FOV
    for newdat in source:
        while len(fovBuff) >= 2*N+1:
            fovBuff.popleft()
        fovBuff.append(newdat)
        if len(fovBuff) == 2*N+1:
            d = fovBuff[N]
            lng = d["GPS_ABS_LONG"]
            lat = d["GPS_ABS_LAT"]
            cosLat = cos(lat*DTR)
            t = d["EPOCH_TIME"]
            fit = d["GPS_FIT"]
            windN = d["WIND_N"]
            windE = d["WIND_E"]
            vcar = d.get("CAR_SPEED", 0.0)
            try:
                dstd = DTR*d["WIND_DIR_SDEV"]
            except:
                dstd = NOT_A_NUMBER
            mask = d["ValveMask"]
            instStatus0 = int(d["INST_STATUS"])

            auxStatus = instStatus0 >> sis.INSTMGR_AUX_STATUS_SHIFT
            instStatus = instStatus0 & sis.INSTMGR_STATUS_MASK
            weatherCode = auxStatus & sis.INSTMGR_AUX_STATUS_WEATHER_MASK
            # Note that weatherCode is zero if there are no reported weather data in the file. Otherwise, we
            #  SUBTRACT ONE before using it to look up the stability class in classByWeather. If we have an
            #  invalid code in the data file and try to fetch it using "*", the swath is suppressed.
            if stabClass == "*":
                stabClass = sis.classByWeather.get(weatherCode-1, None).upper()
            if (fit > 0) and (mask < 1.0e-3) and isfinite(dstd) and isfinite(windN) and isfinite(windE) and (instStatus == sis.INSTMGR_STATUS_GOOD) and (stabClass is not None):
                bearing = arctan2(windE, windN)
                wind = sqrt(windE*windE + windN*windN)
                xx = asarray([fovBuff[i]["GPS_ABS_LONG"] for i in range(2*N+1)])
                yy = asarray([fovBuff[i]["GPS_ABS_LAT"] for i in range(2*N+1)])
                xx = DTR*(xx-lng)*EARTH_RADIUS*cosLat
                yy = DTR*(yy-lat)*EARTH_RADIUS
                asd = astd(wind, vcar, astdParams)
                dstd = sqrt(dstd*dstd + asd*asd)
                dmax = sp.getMaxDist(ord(stabClass)-ord("A"), minLeak, wind, minAmpl, 0.5, 1, 2)
                width = sp.maxDist(xx[:2*N+1], yy[:2*N+1], windE, windN, dstd, dmax, 0.7, 1.0)
                # print "Wind speed: %.2f, Wind stdDev (deg): %.2f, dmax: %.2f, Width: %.2f" % (wind,dstd*RTD,dmax,width)
                deltaLat = RTD*width*cos(bearing)/EARTH_RADIUS
                deltaLng = RTD*width*sin(bearing)/(EARTH_RADIUS*cosLat)
            else:
                deltaLat = 0.0
                deltaLng = 0.0
            if isnan(deltaLat) or isnan(deltaLng):
                deltaLat = 0.0
                deltaLng = 0.0
            yield {"EPOCH_TIME": t, "GPS_ABS_LAT": lat, "GPS_ABS_LONG": lng,
                   "DELTA_LAT": deltaLat, "DELTA_LONG": deltaLng, "INST_STATUS": instStatus0}


def process(source, maxWindow, stabClass, minLeak, minAmpl, astdParams, debugFp=None):
    # The stablility class can "A" through "F" for an explicit class, or "*" if the class is
    #  to be determined from the auxiliary instrument status.
    # If debugFp is a file handle, the input and output arguments are pickled and written
    #  to the file for debugging
    print "Calling process"
    if debugFp is not None:
        inArgs = {}
        inArgs["maxWindow"] = maxWindow
        inArgs["stabClass"] = stabClass
        inArgs["minLeak"] = minLeak
        inArgs["minAmpl"] = minAmpl
        inArgs["astdParams"] = astdParams
    fields = ["EPOCH_TIME", "GPS_ABS_LAT", "GPS_ABS_LONG", "DELTA_LAT", "DELTA_LONG", "INST_STATUS"]
    result = {}
    for f in fields:
        result[f] = []
    for r in processGen(source, maxWindow, stabClass, minLeak, minAmpl, astdParams):
        for f in r:
            result[f].append(r[f])
    if debugFp is not None:
        timestamp = time.time()
        cPickle.dump(dict(inArgs=inArgs, outArgs=result, timestamp=timestamp), debugFp, -1)
    return result
