#!/usr/bin/python
"""
FILE:
  processorFindWindInst.py

DESCRIPTION:
  Peripheral Interface Processor script for finding true wind speed and direction

SEE ALSO:
  Specify any related information.

HISTORY:
   6-Feb-2012  sze  Initial version
  10-Dec-2013  sze  Added modifications for maximum true wind speed (MAXTRUEWINDSPEED
                    parameter in the INI file). Added comments and assertions for type checking.

 Copyright (c) 2013-2014 Picarro, Inc. All rights reserved
"""
from Host.Common.namedtuple import namedtuple
from collections import deque
from Host.Common.configobj import ConfigObj
import Queue
import time

from numpy import angle, arcsin, arctan, arctan2, asarray, column_stack, concatenate, conj
from numpy import cos, exp, floor, imag, isfinite, isnan, mod, pi, real, sin, sqrt, tan
from scipy.optimize import leastsq

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
                alpha = float(requestTs - ts) / (savedTs - ts)
                di = tuple([alpha * y + (1 - alpha) * y_p for y, y_p in zip(savedValTuple, valTuple)])
                return SourceTuple(requestTs, self.DataTuple(*di))
            else:
                savedTs = ts
                savedValTuple = valTuple
        else:
            return self.oldData[0]


class GpsSource(RawSource):
    """Source for GPS data.
    """
    pass


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
SyncCdataTuple = namedtuple('SyncCdataTuple', StatusTuple._fields + ('ts', 'lon', 'lat', 'fit', 'zPos', 'mHead', 'rVel'))
DerivCdataTuple = namedtuple('DerivCdataTuple', SyncCdataTuple._fields + ('zVel', 'kappa'))
CalibCdataTuple = namedtuple('CalibCdataTuple', DerivCdataTuple._fields + ('tVel', 'calParams', 'wCorr'))
StatsCdataTuple = namedtuple('StatsCdataTuple', CalibCdataTuple._fields + ('wMean', 'aStdDev'))


def syncCdataSource(syncDataSrc):
    """Convert GPS lat and lon to Cartesian coordinates.

    Represent vectors of interest as complex numbers (North)+1j*(East) so that the argument of the
    complex number is the bearing.

    Args:
        syncDataSrc: Synchronized data source with GPS, compass and anemometer data
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
    for ts, [gps, mag, anem] in syncDataSrc:
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
        mHead = mag.WS_COS_HEADING + 1j * mag.WS_SIN_HEADING
        rVel = (anem.WS_WIND_LON + 1j * anem.WS_WIND_LAT)
        yield SyncCdataTuple(ts, lon, lat, fit, zPos, mHead, rVel)


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


def orientAnem(cSpeed0, rVel0):
    """Calculate anemometer orientation.

    Args:
        cSpeed0: array of vehicle speeds
        rVel0: complex relative velocity of wind relative to axes of vehicle

    Returns:
        Rotation angle of anemometer relative to vehicle axes
    """
    assert isinstance(cSpeed0, float)
    assert isinstance(rVel0, float)
    return -arctan2(sum(imag(rVel0) * cSpeed0), sum(real(rVel0) * cSpeed0))


def calCompass(phi, theta, params0=None):
    """Calibrate magnetic compass against GPS derived direction.

    Args:
        phi: GPS derived heading
        theta: Compass heading
        params0: Initial value of parameters used for fitting

    Returns: Optimal parameter values [p0, p1, p2] where

        theta = p0 + arctan2(p2+sin(phi),p1+cos(phi))
    """
    if params0 is None:
        params0 = [0.0, 0.0, 0.0]
    phi = asarray(phi)
    theta = asarray(theta)
    data = concatenate((cos(theta), sin(theta)))
    def mock(params, phi):
        """Generates mock data.
        """
        p0, p1, p2 = params
        th = p0 + arctan2(p2 + sin(phi), p1 + cos(phi))
        return concatenate((cos(th), sin(th)))

    def fun(params):
        """Function whose sum of squares is to be minimized.
        """
        return mock(params, phi) - data

    def dfun(params):
        """Jacobian of fun.
        """
        N = len(phi)
        dm = mock(params, phi)
        cth = dm[:N]
        sth = dm[N:]
        p0, p1, p2 = params
        f1 = p1 + cos(phi)
        f2 = p2 + sin(phi)
        den = f1 * f1 + f2 * f2
        c0 = concatenate((-sth, cth))
        c1 = concatenate((sth * f2 / den, -cth * f2 / den))
        c2 = concatenate((-sth * f1 / den, cth * f1 / den))
        return column_stack((c0, c1, c2))
    x0 = asarray(params0)
    x, ier = leastsq(fun, x0, Dfun=dfun)
    if ier in [1, 2, 3, 4]:    # Successful return
        return x
    else:
        raise RuntimeError("Calibration failed")


def trueWindSource(derivCdataSrc, distFromAxle, speedFactor=1.0, maxTrueWindSpeed=20.0):
    """Calculates the true wind velocity and updates compass calibration.

    This simply subtracts the vehicle velocity from the anemometer velocity. The calculation is done
    in the frame of the anemometer, which is nominally aligned with the vehicle.

    Args:
        derivCdataSrc: Iterable containing the following properties:
            mHead: Complex heading (unit modulus) given by the magnetic compass
            rVel: Apparent complex wind speed along (real) and across (imaginary) vehicle
            kappa: Inverse of radius of curvature of path
            zVel: Complex velocity of vehicle
        distFromAxle: Distance (m) that the GPS is in front of the rear axle of the vehicle
        speedFactor: Apparent wind velocity is multiplied by this factor before the car velocity is subtracted
        maxTrueWindSpeed: If the calculated wind speed exceeds this quantity, it is replaced by NOT_A_NUMBER

    Yields:
        CalibCdataTuple objects consisting of the properties of derivCdataSrc, the calculated true wind,
        a list of calibration constants for the magnetic compass, and a list of correlations between car speed
        and apparent wind velocity.
    """
    #
    # We want to fit the most recent magnetometer data to a model consisting of a static bias field.
    #  This model maps the GPS derived heading phi to the magnetometer heading theta. Data are required
    #  over a range of phi to get a good fit. We divide the range of phi into four bins. In each bin, we
    #  have a deque of recent data points consisting of (phi,theta) pairs. Each deque has a certain
    #  maximum number of points. The fit is carried out on the points which are currently in the deques
    # We also use these deques to store vehicle speed, together with longitudinal and lateral wind
    #  velocity components, so that we can estimate the orientation of the anemometer. This involves
    #  finding the angle through which the anemometer needs to be rotated to make the correlation
    #  betwen the vehicle speed and the transvere velocity component vanish.
    #
    # We only use points where the vehicle speed is not too small, and we also discard bad points as those
    #  in which vehicle_speed/(5+wind_speed)>2.
    # If the reconstructed wind speed exceeds maxTrueWindSpeed, replace it with NaN since it is likely
    #  that the anemometer has failed.

    assert isinstance(distFromAxle, (int, long, float))
    assert isinstance(speedFactor, (int, long, float))
    assert isinstance(maxTrueWindSpeed, (int, long, float))
    p0 = 0  # Parameters of magnetometer calibration
    p1 = 0  # theta = p0 + arctan2(p2+sin(phi),p1+cos(phi))
    p2 = 0
    rot = 0.0
    rCorr = 0.0  # Rotation between axis of anemometer and axis of vehicle
    iCorr = 0.0

    nBins = 4
    maxPoints = 200
    dataDeques = [deque() for i in range(nBins)]

    num = 0.0
    den = 0.0

    def whichBin(phi, nBins):
        return int(min(nBins - 1, floor(nBins * (mod(phi, 2 * pi) / (2 * pi)))))

    for i, d in enumerate(derivCdataSrc):
        # Apply corrections to the anemometer wind velocity using the current magnetometer
        #  calibration.
        #
        # theta = p0 + arctan2(p2+sin(phi),p1+cos(phi))
        #
        #  where theta is the observed magnetometer heading and phi is the corresponding
        #  GPS heading. The rotation required for aVel to get the bearing relative to the
        #  vehicle is phi-theta+p0
        theta = -angle(d.mHead)  # Negative sign appears to be the magnetometer convention for angles
        w = p1 + 1j * p2
        b = -2.0 * real(w * exp(-1j * (theta - p0)))
        c = abs(w) * abs(w) - 1.0
        disc = b * b - 4.0 * c
        r = 0.5 * (-b + sqrt(disc))
        phi = angle(r * exp(1j * (theta - p0)) - w)

        # Rotate the anemometer measured wind to the axes of the vehicle
        # In this version we only measure the rotation using correlation between car speed and
        #  the sonic anemometer components. We do NOT apply the measured rotation to the data to
        #  correct them, as it is assumed that the anemometer will be rotated to make it point
        #  in the correct direction
        # rot = 0.0
        # sVel = d.rVel*exp(1j*rot)
        sVel = d.rVel
        # Compute an angular correction based on the curvature of the path
        #  and the distance between anemometer and the rear axle of the car
        axleCorr = d.kappa * distFromAxle

        if isfinite(d.zVel) and isfinite(sVel) and isfinite(axleCorr) and isfinite(phi):
            num += real(d.zVel * abs(d.zVel) * exp(-1j * axleCorr) * exp(-1j * (phi - p0)))
            den += real(d.zVel * conj(sVel) * exp(-1j * (phi - p0)))

        if isfinite(d.zVel):
            # Subtract velocity of vehicle
            cVel = speedFactor * sVel - abs(d.zVel) * exp(1j * axleCorr)
            #

            #print "cVel = %s, maxTrueWindSpeed = %s" % (abs(cVel), maxTrueWindSpeed)

            if abs(cVel) > maxTrueWindSpeed:
                d = d._replace(status=d.status | PeripheralStatus.WIND_ANOMALY)
                tVel = NOT_A_NUMBER
            else:
                # Rotate back to geographic coordinates, use either GPS direction if car is travelling
                #  quickly or the compass direction if travelling slowly
                cutOver = 2
                fac = abs(d.zVel) ** 2 / (abs(d.zVel) ** 2 + cutOver ** 2)
                optAngle = angle((1 - fac) * exp(1j * phi) + fac * exp(1j * angle(d.zVel)))
                tVel = cVel * exp(1j * optAngle)
        else:
            tVel = NOT_A_NUMBER

        #print "tVel = %s, direction = %s" % (abs(tVel), (180/pi) * angle(tVel))
        #print 'True wind speed and direction', abs(tVel), (180/pi)*angle(tVel)

        # Update the parameters of the calibration from time to time
        if isfinite(d.zVel):      # Reject bad GPS data
            phi0 = angle(d.zVel)
            theta0 = -angle(d.mHead)
            if abs(d.zVel) > 3.0 and abs(d.zVel) < 2.0 * (5.0 + abs(d.rVel)):  # Car is moving fast if speed > 3m/s.
                # Also reject points where car speed is too great. Use these for calibrating magnetometer against GPS
                #  and for finding orientation of anemometer.
                # Determine which deque to put data onto
                b = whichBin(phi0, nBins)
                dataDeques[b].append((phi0, theta0))
                # Limit size of deque
                while len(dataDeques[b]) > maxPoints:
                    dataDeques[b].popleft()
                rCorr += abs(d.zVel) * real(d.rVel)
                iCorr += abs(d.zVel) * imag(d.rVel)

        if i % 20 == 0:  # Carry out the compass and orientation calibration based on available data
            phi0, theta0 = [], []
            for q in dataDeques:
                phi0 += [p for (p, t) in q]
                theta0 += [t for (p, t) in q]
            phi0 = asarray(phi0)
            theta0 = asarray(theta0)

            if len(phi0) >= 50:
                #print "Samples", i
                try:
                    p0, p1, p2 = calCompass(phi0, theta0)
                    # print "Compass params: %10.2f %10.2f %10.2f" % (p0, p1, p2)
                    rot = -arctan2(iCorr, rCorr)
                    #print ("Rotation: %10.2f degrees %10.2f degrees, Scale:%10.4f" %
                    # ((180 / pi) * rot, (180 / pi) * p0, num / den))
                except:
                    pass
        yield CalibCdataTuple(*(d + (tVel, [p0, p1, p2], [rCorr, iCorr])))


def windStatistics(windSource, statsInterval):
    """Calculate wind statistics within a specified time interval.

    Args:
        windSource: iterable with a property .tVel, which, for each sample, is a complex number representing
            the instantaneous wind velocity. The real part is the component from the north and the imaginary
            part is the component from the east.
        statsInterval: number of samples over which to compute the mean and Yamartino standard deviation.

    Yields:
        A StatsCdataTuple which contains all the properties from windSource, to which is appended the
            mean and standard deviation, evaluated for statsInterval in the past of the current sample.
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
    compassDelay_ms = round(1000 * float(PARAMS.get("COMPASSDELAY", 0.0)))
    distFromAxle = float(PARAMS.get("DISTFROMAXLE", 1.5))
    speedFactor = float(PARAMS.get('SPEEDFACTOR', 1.0))
    maxTrueWindSpeed = float(PARAMS.get('MAXTRUEWINDSPEED', 20.0))

    msOffsets = [0, compassDelay_ms, anemDelay_ms]  # ms offsets for GPS, magnetometer and anemometer
    syncDataSource = syncSources([gpsSource, wsSource, wsSource], msOffsets, 1000)
    statsAvg = int(PARAMS.get("STATSAVG", 10))
    for d in windStatistics(trueWindSource(derivCdataSource(syncCdataSource(syncDataSource)),
                                           distFromAxle, speedFactor, maxTrueWindSpeed), statsAvg):
        p0, p1, p2 = d.calParams
        rCorr, iCorr = d.wCorr
        vCar = abs(d.zVel)
        WRITEOUTPUT(d.ts, [float(real(d.wMean)), float(imag(d.wMean)),    # Mean wind N and E
                           d.aStdDev,                                     # Wind direction std dev (degrees)
                           float(real(d.zVel)), float(imag(d.zVel)),      # Car velocity N and E
                           float(real(d.mHead)), -float(imag(d.mHead)),   # Compass heading N and E
                           float(real(d.tVel)), float(imag(d.tVel)),      # Instantaneous wind N and E
                           p0, p1, p2,                                    # Calibration parameters
                           (180 / pi) * arctan2(iCorr, rCorr),            # Angle of anemometer from true
                           vCar,                                          # Speed of car
                           d.status
        ])


# This script is run by compiling it and executing it within an environment defined by the peripheral processor
if "DONE" not in locals():
    DONE = lambda: False
runAsScript()
