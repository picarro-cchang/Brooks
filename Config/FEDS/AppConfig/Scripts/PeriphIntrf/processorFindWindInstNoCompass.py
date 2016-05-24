#!/usr/bin/python
"""
FILE:
  processorFindWindInstNoCompass.py

DESCRIPTION:
  Peripheral Interface Processor script for finding true wind speed and direction

SEE ALSO:
  Specify any related information.

HISTORY:
   6-Feb-2012  sze  Initial version
  10-Dec-2013  sze  Added modifications for maximum true wind speed (MAXTRUEWINDSPEED 
                    parameter in the INI file). Added comments and assertions for type checking.
   2-Jan-2014  sze  Removed processing of compass for use with Gill anemometer

 Copyright (c) 2013-2014 Picarro, Inc. All rights reserved
"""
from Host.Common.namedtuple import namedtuple
from collections import deque
from Host.Common.configobj import ConfigObj
import Queue
import time
from datetime import datetime

from numpy import angle, arcsin, arctan, arctan2, asarray, column_stack, concatenate, conj
from numpy import cos, exp, floor, imag, isfinite, isnan, mod, pi, real, sin, sqrt, tan

from Host.PeriphIntrf.PeripheralStatus import PeripheralStatus


NOT_A_NUMBER = 1e1000 / 1e1000
SourceTuple = namedtuple('SourceTuple', ['ts', 'valTuple'])


class RawSource(object):
    """Interface to data being collected on a queue, allowing for interpolation to arbitrary times.
    
    The getData method is used to request the values at a specified timestamp. Linear
    interpolation is used to calculate the source tuple at the desired time, unless
    the requested timestamp is in the future of all the data present in the queue, in
    which case None is returned. Up to maxStore previous queue entries are buffered in
    a deque for the interpolation. If the requested timestamp is earlier than all the
    buffered entries, the first entry in the buffer is returned.
    
    Args:
        queue: queue which contains tuples consisting of a timestamp and a dictionary of
            key-value pairs representing the data at that timestamp
        maxStore: Maximum number of points to store for linear interpolation    
    """
    def __init__(self, queue, maxStore=20):
        assert isinstance(queue, Queue.Queue)
        assert isinstance(maxStore, (int, long))
        self.queue = queue
        self.DataTuple = None
        self.oldData = deque()
        self.maxStore = maxStore
        self.latestTimestamp = None
        
    def getDataTupleType(self, d):
        """Construct a namedtuple type for data in the queue.
        
        Sets self.DataTuple to a tuple whose fields are the keys of the dictionary
            specifying the data in the queue.
            
        Args:
            d a typical datum from the queue. This should be a tuple with a timestamp as
                the first element and a dictionary of values as the second element.
        """
        assert isinstance(d, tuple)
        assert isinstance(d[0], (int, long, float))
        assert isinstance(d[1], dict)
        self.DataTuple = namedtuple(self.__class__.__name__ + '_tuple', sorted(d[1].keys()))
        
    def getFromQueue(self):
        """Gets a datum from the queue (if available) and adds it to the deque.
        
        The length of the deque is always kept no greater than self.maxStore. 

        Returns:
            True if a point was transferred from the queue to the deque
        """
        try:
            d = self.queue.get(block=False)
            if d is None:
                return False
            if self.DataTuple is None:
                self.getDataTupleType(d)
            self.oldData.append(SourceTuple(d[0], self.DataTuple(**d[1])))
            self.latestTimestamp = d[0]
            if len(self.oldData) > self.maxStore:
                self.oldData.popleft()
            # print self.oldData
            return True
        except Queue.Empty:
            return False
            
    def getOldestTimestamp(self):
        """Get the timestamp of the oldest data available in the deque.
        
        Returns:
            Timestamp of oldest data available, or None if no data are available
        """
        if not self.oldData:
            self.getFromQueue()
        return self.oldData[0].ts if self.oldData else None

    def getData(self, requestTs):
        """Get data at specified timestamp using interpolation if needed.
        
        Args:
            requestTs: Time stamp at which data are required.
        Returns:
            SourceTuple consisting of requestTs and the interpolated data.
            None if no data are available.
        """
        assert isinstance(requestTs, (int, long, float))
        while self.latestTimestamp < requestTs:
            if not self.getFromQueue():
                return None
        ts, savedTs = None, None
        valTuple, savedValTuple = None, None
        for (ts, valTuple) in reversed(self.oldData):
            if ts < requestTs:
                try:
                    alpha = float(requestTs - ts) / (savedTs - ts)
                    di = tuple([alpha * y + (1 - alpha) * y_p for y, y_p in zip(savedValTuple, valTuple)])
                    return SourceTuple(requestTs, self.DataTuple(*di))
                except TypeError:   # requestTs is newer than the latest ts in oldData
                    return None
            else:
                savedTs = ts
                savedValTuple = valTuple
        else:
            return self.oldData[0]

class GpsSource(RawSource):
    def __init__(self, queue, maxStore=20):
        RawSource.__init__(self, queue, maxStore)
        self.weight = 1.0
        self.offset = 0
        self.oldGpsTime = -1
        td = datetime.utcnow() - datetime(1,1,1,0,0,0,0)
        self.GpsBaseTime = td.days * 86400000
        
    def getGpsTimeOffset(self):
        ts, valTuple = self.oldData[-1]
        GpsTime = valTuple.GPS_TIME * 1000
        if GpsTime != self.oldGpsTime:
            if GpsTime < self.oldGpsTime: # just pass GMT midnight
                self.GpsBaseTime += 86400000
            offset = (ts - GpsTime - self.GpsBaseTime) / self.weight + (1-1.0/self.weight) * self.offset
            self.offset = offset
            self.oldGpsTime = GpsTime
            self.weight += 1 if self.weight < 50 else 0
            return offset
        else:  
            return self.offset
        
    def getData(self, requestTs):
        """Get data at specified timestamp using interpolation if needed.
        
        Args:
            requestTs: Time stamp at which data are required.
        Returns:
            SourceTuple consisting of requestTs and the interpolated data.
            None if no data are available.
        """
        assert isinstance(requestTs, (int, long, float))
        while self.latestTimestamp < requestTs:
            if not self.getFromQueue():
                return None
        ts, savedTs = None, None
        savedGpsTime = None
        valTuple, savedValTuple = None, None
        offset = self.getGpsTimeOffset()
        for (ts, valTuple) in reversed(self.oldData):
            GpsTime = valTuple.GPS_TIME * 1000 + offset + self.GpsBaseTime
            if ts < requestTs:
                try:
                    alpha = float(requestTs - GpsTime) / (savedGpsTime - GpsTime)
                except ZeroDivisionError:   # lose GPS signal so GPS time is not updated
                    alpha = float(requestTs - ts) / (savedTs - ts)
                except TypeError:   # requestTs is newer than the latest time in oldData
                    return None
                di = tuple([alpha * y + (1 - alpha) * y_p for y, y_p in zip(savedValTuple, valTuple)])
                return SourceTuple(requestTs, self.DataTuple(*di))
            savedTs = ts
            savedGpsTime = GpsTime
            savedValTuple = valTuple
        else:
            return self.oldData[0]
            
class WsSource(RawSource):
    """Source for weather station data.
    """
    pass


def distVincenty(lat1, lon1, lat2, lon2):
    """Calculate distance between points on ellipsoidal earth .
    
    The WGS-84 ellipsiod is used. 
    
    Args:
        lat1: Latitude in degrees of first point
        long1: Longitude in degrees of first point
        lat2: Latitude in degrees of second point
        long2: Longitude in degrees of second point
        
    Returns:
        Distance between points in meters
    """
    assert isinstance(lat1, float)
    assert isinstance(lon1, float)
    assert isinstance(lat2, float)
    assert isinstance(lon2, float)
    a = 6378137
    b = 6356752.3142
    f = 1 / 298.257223563
    toRad = pi / 180.0
    L = (lon2 - lon1) * toRad
    U1 = arctan((1 - f) * tan(lat1 * toRad))
    U2 = arctan((1 - f) * tan(lat2 * toRad))
    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)
  
    Lambda = L
    iterLimit = 100
    for _ in range(iterLimit):
        sinLambda = sin(Lambda)
        cosLambda = cos(Lambda)
        sinSigma = sqrt((cosU2 * sinLambda) * (cosU2 * sinLambda) +
                        (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) * (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda))
        if sinSigma == 0:
            return 0  # co-incident points
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = arctan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha * sinAlpha
        if cosSqAlpha == 0:
            cos2SigmaM = 0
        else:
            cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cosSqAlpha
        C = f / 16 * cosSqAlpha * (4 + f * (4 - 3 * cosSqAlpha))
        lambdaP = Lambda
        Lambda = L + (1 - C) * f * sinAlpha * \
            (sigma + C * sinSigma * (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM)))
        if abs(Lambda - lambdaP) <= 1.e-12:
            break
    else:
        raise ValueError("Failed to converge")

    uSq = cosSqAlpha * (a * a - b * b) / (b * b)
    A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma * (-1 + 2 * cos2SigmaM * cos2SigmaM) -
                 B / 6 * cos2SigmaM * (-3 + 4 * sinSigma * sinSigma) * (-3 + 4 * cos2SigmaM * cos2SigmaM)))
    return b * A * (sigma - deltaSigma)


def toXY(lat, lon, lat_ref, lon_ref):
    """Convert points on earth near a reference point to local (x,y) plane
    
    Args:
        lat: Latitude of point in degrees
        lon: Longitude of point in degrees
        lat_ref: Latitude of reference point in degrees
        lon_ref: Longitude of reference point in degrees
        
    Returns:
        Tuple of (x,y) coordinates of point (in meters) releative to reference. x is in the 
        easterly direction and y is in the northerly direction.
    """
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert isinstance(lat_ref, float)
    assert isinstance(lon_ref, float)
    
    x = distVincenty(lat_ref, lon_ref, lat_ref, lon)
    if lon < lon_ref:
        x = -x
    y = distVincenty(lat_ref, lon, lat, lon)
    if lat < lat_ref:
        y = -y
    return x, y


def syncSources(sourceList, msOffsetList, msInterval, sleepTime=0.01):
    """Synchronize a collection of sources to a common time grid.
    
    Linear interpolation is used as needed.
    
    Args:
        sourceList: List of sources which are descendents of RawSource
        msOffsetList: Per-source timestamp offset to apply before synchronization. The data for the source is
            sampled at the sum of the common (synchronized) timestamp and the offset for that source
        msInterval: Timestamps for the synchronized data sources are integer multiples of msInterval
        sleepTime: Time to sleep (in s) between calling getData for each source.
    Yields: 
        A tuple consisiting of a timestamp and a list of tuples of synchronized data, one from each source
    """
    assert isinstance(msInterval, (int, long, float))
    assert isinstance(sleepTime, (int, long, float))
    # First determine when to start synchronized timestamps
    oldestTs = []
    for s in sourceList:
        assert isinstance(s, RawSource)
        while True:
            ts = s.getOldestTimestamp()
            if ts is not None:
                oldestTs.append(ts)
                break
            time.sleep(sleepTime)
            
    oldestAvailableFromAll = max([ts - offset for ts, offset in zip(oldestTs, msOffsetList)])
    # Round to the grid of times which are multiples of msInterval
    ts = msInterval * (1 + oldestAvailableFromAll // msInterval)
    
    # Get all the valTuples at the specified timestamp
    while True:
        valTuples = []
        for s, offset in zip(sourceList, msOffsetList):
            assert isinstance(offset, (int, long, float))
            while True:
                d = s.getData(ts + offset)
                if DONE():
                    return
                if d is not None:
                    valTuples.append(d.valTuple)
                    break
                time.sleep(sleepTime)
        yield ts, valTuples
        ts += msInterval
        

StatusTuple = namedtuple('StatusTuple', ['status'])
SyncCdataTuple = namedtuple('SyncCdataTuple', StatusTuple._fields + ('ts', 'lon', 'lat', 'fit', 'zPos', 'rVel'))
DerivCdataTuple = namedtuple('DerivCdataTuple', SyncCdataTuple._fields + ('zVel', 'kappa'))
CalibCdataTuple = namedtuple('CalibCdataTuple', DerivCdataTuple._fields + ('tVel', 'wCorr'))
StatsCdataTuple = namedtuple('StatsCdataTuple', CalibCdataTuple._fields + ('wMean', 'aStdDev'))
    

def syncCdataSource(syncDataSrc):
    """Convert GPS lat and lon to Cartesian coordinates.
    
    Represent vectors of interest as complex numbers (North)+1j*(East) so that the argument of the 
    complex number is the bearing.
    
    Args:
        syncDataSrc: Synchronized data source with GPS and anemometer data
    Yields:
        SyncCdataTuple objects with fields:
            ts: millisecond timestamp
            lon: longitude (degrees)
            lat: latitude (degrees)
            fit: GPS fit flag (N.B. may be interpolated)
            
    """
    lon_ref, lat_ref = None, None
    x, y = 0.0, 0.0
    gpsOkThreshold = 4  # Need these many good GPS points before using data
    
    gpsCount = gpsOkThreshold
    for ts, [gps, anem] in syncDataSrc:
        lat, lon, fit = gps.GPS_ABS_LAT, gps.GPS_ABS_LONG, gps.GPS_FIT
        if gpsCount > 0:
            gpsCount -= 1
        if fit < 1.0:
            gpsCount = gpsOkThreshold  # Indicate bad GPS
        if lat_ref is None and gpsCount == 0:
            lat_ref, lon_ref = lat, lon
        if lat_ref is not None:
            if gpsCount == 0:
                x, y = toXY(lat, lon, lat_ref, lon_ref)
            else:
                x, y = NOT_A_NUMBER, NOT_A_NUMBER
        zPos = y + 1j * x
        rVel = (anem.WS_WIND_LON + 1j * anem.WS_WIND_LAT)
        yield SyncCdataTuple(anem.WS_STATUS, ts, lon, lat, fit, zPos, rVel)


def derivCdataSource(syncCdataSrc):
    """Compute velocity and curvature of path.
    
    Use centered 5-point finite difference to find velocity from position and 
    finite difference approximation to the curvature of the path.
    
    Args:
        syncCdataSrc: iterable with complex position in property zPos
    
    Yields:
        DerivCdataTuple containing all properties in the source followed by the complex
            velocity and the curvature of the path.
    """
    dBuff = []
    for d in syncCdataSrc:
        dBuff.append(d)
        dBuff[:] = dBuff[-5:]
        if len(dBuff) == 5:
            d4 = dBuff[4]
            d3 = dBuff[3]
            d2 = dBuff[2]
            d1 = dBuff[1]
            d0 = dBuff[0]
            # Use higher order velocity estimate
            zVel = (-d4.zPos + 8.0 * d3.zPos - 8.0 * d1.zPos + d0.zPos) / 12.0
            dz = d3.zPos - d1.zPos
            d2z = d3.zPos - 2 * d2.zPos + d1.zPos
            r = abs(dz)
            r2 = r * r
            # Calculate curvature of path, with protection for low speeds
            kappa = 4.0 * imag(conj(dz) * d2z) * r / (r2 * r2 + 4.0)
            yield DerivCdataTuple(*(d2 + (zVel, kappa)))

        
def trueWindSource(derivCdataSrc, distFromAxle, speedFactor=1.0, maxTrueWindSpeed=20.0):
    """Calculates the true wind velocity and updates compass calibration.

    This simply subtracts the vehicle velocity from the anemometer velocity. The calculation is done 
    in the frame of the anemometer, which is nominally aligned with the vehicle.
    
    Args:
        derivCdataSrc: Iterable containing the following properties:
            rVel: Apparent complex wind speed along (real) and across (imaginary) vehicle
            kappa: Inverse of radius of curvature of path
            zVel: Complex velocity of vehicle
        distFromAxle: Distance (m) that the GPS is in front of the rear axle of the vehicle
        speedFactor: Apparent wind velocity is multiplied by this factor before the car velocity is subtracted
        maxTrueWindSpeed: If the calculated wind speed exceeds this quantity, it is replaced by NOT_A_NUMBER
        
    Yields:
        CalibCdataTuple objects consisting of the properties of derivCdataSrc, the calculated true wind,
        and a list of correlations between car speed and the apparent wind velocity.
    """
    # If the reconstructed wind speed exceeds maxTrueWindSpeed, replace it with NaN since it is likely
    #  that the anemometer has failed.
    
    assert isinstance(distFromAxle, (int, long, float))
    assert isinstance(speedFactor, (int, long, float))
    assert isinstance(maxTrueWindSpeed, (int, long, float))

    rCorr = 0.0  # Rotation between axis of anemometer and axis of vehicle
    iCorr = 0.0
    optAngle = None    
        
    def whichBin(phi, nBins):
        return int(min(nBins - 1, floor(nBins * (mod(phi, 2 * pi) / (2 * pi)))))
    
    for i, d in enumerate(derivCdataSrc):
        # Rotate the anemometer measured wind to the axes of the vehicle

        sVel = d.rVel
        # Compute an angular correction based on the curvature of the path
        #  and the distance between anemometer and the rear axle of the car
        axleCorr = d.kappa * distFromAxle
                
        if isfinite(d.zVel):
            # Subtract velocity of vehicle
            cVel = speedFactor * sVel - abs(d.zVel) * exp(1j * axleCorr)
            #
            if abs(cVel) > maxTrueWindSpeed:
                d = d._replace(status=int(d.status) | PeripheralStatus.WIND_ANOMALY)
                tVel = NOT_A_NUMBER
            else:
                # Rotate back to geographic coordinates, using GPS direction if car is travelling
                #  quickly or the previous direction if the speed falls below 1 m/s
                if abs(d.zVel) > 1:
                    optAngle = angle(d.zVel)
                    
                if optAngle is not None:
                    tVel = cVel * exp(1j * optAngle)
                else:
                    tVel = NOT_A_NUMBER                    
        else:
            tVel = NOT_A_NUMBER
        
        # Determine the anemometer rotation
        if isfinite(d.zVel):      # Reject bad GPS data
            if abs(d.zVel) > 3.0 and abs(d.zVel) < 2.0 * (5.0 + abs(d.rVel)):  # Car is moving fast if speed > 3m/s.
                # Also reject points where car speed is too great.
                rCorr += abs(d.zVel) * real(d.rVel)
                iCorr += abs(d.zVel) * imag(d.rVel)
                            
        yield CalibCdataTuple(*(d + (tVel, [rCorr, iCorr])))


def windStatistics(windSource, statsInterval):
    """Calculate wind statistics within a specified time interval.
    
    Args:
        windSource: iterable with a property .tVel, which, for each sample, is a complex number representing
            the instantaneous wind velocity. The real part is the component from the north and the imaginary
            part is the component from the east.
        statsInterval: number of samples over which to compute the mean and Yamartino standard deviation.
        
    Yields:
        ResultsTuple: all statistics + system status
    """
    assert isinstance(statsInterval, (int, long, float))
    wSum = 0.0
    aSum = 0.0
    buff = deque()
    for w in windSource:
        if isnan(w.tVel):
            wSum = 0.0
            aSum = 0.0
            buff.clear()
            wMean = NOT_A_NUMBER + 1j * NOT_A_NUMBER
            aStdDev = NOT_A_NUMBER
        else:
            buff.append(w.tVel)
            wSum += w.tVel
            aSum += exp(1j * angle(w.tVel))
            if len(buff) > statsInterval:
                oldest = buff.popleft()
                wSum -= oldest
                aSum -= exp(1j * angle(oldest))
            n = len(buff)
            wMean = wSum / n
            if n > 0:
                vmean = abs(aSum / n)
                eps = sqrt(1 - vmean * vmean)
                aStdDev = arcsin(eps) * (1 + 0.1547 * eps * eps * eps)
            else:
                aStdDev = pi / 2.0
            aStdDev = 180.0 / pi * aStdDev
        yield StatsCdataTuple(*(w + (wMean, aStdDev)))
        

def runAsScript():
    """Run the processor
    
    This needs to be run in an environment in which the following are defined:
        SENSORLIST: The list of data queues for the input sensors (GPS and Weather Station)
        PARAMS: Parameters used by the processor script
        WRITEOUTPUT: Function taking a timestamp and a list of outputs from the processor
        DONE: Function which when called returns a boolean indicating if there is no more data 
            to process
    """
    gpsSource = GpsSource(SENSORLIST[0])
    wsSource = WsSource(SENSORLIST[1])
    gpsDelay_ms = 0
    anemDelay_ms = round(1000 * float(PARAMS.get("ANEMDELAY", 1.5)))
    distFromAxle = float(PARAMS.get("DISTFROMAXLE", 1.5))
    speedFactor = float(PARAMS.get('SPEEDFACTOR', 1.0))
    maxTrueWindSpeed = float(PARAMS.get('MAXTRUEWINDSPEED', 20.0))

    msOffsets = [gpsDelay_ms, anemDelay_ms]  # ms offsets for GPS and anemometer
    syncDataSource = syncSources([gpsSource, wsSource], msOffsets, 1000)
    statsAvg = int(PARAMS.get("STATSAVG", 10))
    for d in windStatistics(trueWindSource(derivCdataSource(syncCdataSource(syncDataSource)), 
                                           distFromAxle, speedFactor, maxTrueWindSpeed), statsAvg):
        rCorr, iCorr = d.wCorr
        vCar = abs(d.zVel)
        WRITEOUTPUT(d.ts, [float(real(d.wMean)), float(imag(d.wMean)),    # Mean wind N and E
                           d.aStdDev,                                     # Wind direction std dev (degrees)
                           float(real(d.zVel)), float(imag(d.zVel)),      # Car velocity N and E
                           float(real(d.tVel)), float(imag(d.tVel)),      # Instantaneous wind N and E
                           (180 / pi) * arctan2(iCorr, rCorr),            # Angle of anemometer from true
                           vCar,                                          # Speed of car
                           d.status
        ])
        

# This script is run by compiling it and executing it within an environment defined by the peripheral processor
if "DONE" not in locals():
    DONE = lambda: False
runAsScript()
