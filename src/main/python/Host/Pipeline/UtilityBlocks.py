import csv
from Host.Pipeline.Blocks import (ActionBlock, TransformBlock, TransformManyBlock, MergeBlock)
import geohash
import json
from numpy import arctan2, asarray, ceil, cos, cross, floor, isfinite, isnan, nan, sin, sqrt
import numpy as np
import simplekml
import sys
from traitlets import (Any, Bool, Dict, Float, Instance, Integer, List, Unicode)

DTR = np.pi/180.0
RTD = 180.0/np.pi
EARTH_RADIUS = 6378100.

class AutoThresholdBlock(TransformBlock):
    normWidthLo = Float()
    normAmplLo = Float()
    normWidthHi = Float()
    normAmplHi = Float()
    normAmplDef = Float()
    """Calculates amplitude threshold from background filter output using a piecewise linear model"""
    def __init__(self, normWidthLo, normAmplLo, normWidthHi, normAmplHi, normAmplDef=None):
        super(AutoThresholdBlock, self).__init__(self.newData)
        self.normWidthLo = normWidthLo
        self.normAmplLo = normAmplLo
        self.normWidthHi = normWidthHi
        self.normAmplHi = normAmplHi
        self.normAmplDef = normAmplDef if normAmplDef is not None else 0.5*(normAmplHi + normAmplLo)

    def newData(self, newDat):
        eps = 1.0e-7
        background = newDat['BASELINE_FILT_OUT']
        if 'SIGMA' not in newDat or 'CAR_SPEED' not in newDat:
            amplThreshold = self.normAmplDef * background
        else:
            speed = newDat['CAR_SPEED']
            timeThroughPeak = newDat['SIGMA']/(speed + eps)
            slope = (self.normAmplHi - self.normAmplLo)/(self.normWidthHi - self.normWidthLo)
            amplThreshold = background * (self.normAmplLo + (timeThroughPeak - self.normWidthLo) * slope)
        return dict(newDat, AMPL_THRESHOLD=amplThreshold)

class CsvWriterBlock(ActionBlock):
    fp = Instance(file)
    headerWritten = Bool()
    writer = Instance(csv.DictWriter, allow_none=True)
    def __init__(self, filename):
        super(CsvWriterBlock, self).__init__(self.newData)
        self.fp = open(filename, "wb")
        self.headerWritten = False
        self.writer = None
        self.setContinuation(self._continuation)

    def newData(self, data):
        if not self.headerWritten:
            self.writer = csv.DictWriter(self.fp, sorted(data.keys()))
            self.writer.writeheader()
            self.headerWritten = True
        self.writer.writerow(data)

    def _continuation(self, srcBlock):
        if self.fp:
            self.fp.close()
        self.defaultContinuation(srcBlock)

class DataFetcherBlock(TransformManyBlock):
    def __init__(self):
        super(DataFetcherBlock, self).__init__(self.newData)

    def pFloat(self, x):
        try:
            return float(x)
        except:
            return float('nan')

    def textAsDict(self, source):
        """Generates data from a white-space delimited text file with headings as a stream consisting
           of dictionaries.
           Raise StopIteration if the source ends
        """
        headerLine = True
        for l in source:
            if headerLine:
                colHeadings = l.split()
                headerLine = False
            else:
                yield {k:self.pFloat(v) for k, v in zip(colHeadings, l.split())}
        source.close()

    def xReadDatFileAsDict(self, fileName):
        """Read a data file with column headings and return a generator which yields dictionaries
            with the file contents"""
        fp = open(fileName, 'r')
        return self.textAsDict(fp)

    def newData(self, filename):
        for d in self.xReadDatFileAsDict(filename):
            yield d

class FrameFetcherBlock(TransformManyBlock):
    def __init__(self):
        super(FrameFetcherBlock, self).__init__(self.newData)

    def newData(self, data_frame):
        for d in data_frame.iterrows():
            result = dict(d[1])
            if 'ValveMask' not in result:
                result['ValveMask'] = result['solenoid_valves']
            yield result

class InterpolatorBlock(TransformManyBlock):
    interpKey = Unicode()
    linInterpKeys = List(Unicode())
    minInterpKeys = List(Unicode())
    maxInterpKeys = List(Unicode())
    previous = Any()
    xInterp = Float(allow_none=True)
    interval = Float()
    row = Integer()
    def __init__(self, interpKey, interval, linInterpKeys=None, minInterpKeys=None, maxInterpKeys=None):
        super(InterpolatorBlock, self).__init__(self.newData)
        assert isinstance(interval, float)
        assert interval > 0
        self.interpKey = interpKey
        self.linInterpKeys = linInterpKeys if linInterpKeys is not None else []
        self.minInterpKeys = minInterpKeys if minInterpKeys is not None else []
        self.maxInterpKeys = maxInterpKeys if maxInterpKeys is not None else []
        self.previous = None
        self.xInterp = None
        self.interval = interval
        self.row = 0

    def newData(self, newDat):
        assert isinstance(newDat, dict)
        assert self.interpKey in newDat
        current = newDat.copy()
        xCurrent = current[self.interpKey]
        if isnan(xCurrent):
            return

        if self.previous is None:
            self.previous = current
            xPrevious = xCurrent
            self.xInterp = self.interval * ceil(xPrevious/self.interval)
        else:
            xPrevious = self.previous[self.interpKey]
            assert xCurrent >= xPrevious
            while self.xInterp <= xCurrent:
                result = {self.interpKey: self.xInterp}
                for k in self.linInterpKeys:
                    if k in current:
                        result[k] = self.linInterp(xPrevious, xCurrent, self.previous[k], current[k], self.xInterp)
                for k in self.minInterpKeys:
                    if k in current:
                        result[k] = self.minInterp(xPrevious, xCurrent, self.previous[k], current[k], self.xInterp)
                for k in self.maxInterpKeys:
                    if k in current:
                        result[k] = self.maxInterp(xPrevious, xCurrent, self.previous[k], current[k], self.xInterp)
                self.row += 1
                result['row'] = self.row
                yield result
                self.xInterp += self.interval
            self.previous = current

    def linInterp(self, x0, x1, y0, y1, xi):
        if x0 == x1:
            return 0.5 * (y0 + y1)
        else:
            return ((x1 - xi) * y0 + (xi - x0) * y1) / (x1 - x0)

    def minInterp(self, x0, x1, y0, y1, xi):
        return min([y0, y1])

    def maxInterp(self, x0, x1, y0, y1, xi):
        return max([y0, y1])

class JoinerBlock(MergeBlock):
    """Adjoins data from input 0 to those from input 1 based on values in a specified "joinKey".

    Both data inputs consist of collections of dictionaries with a common key "joinKey". We use
    the value of joinKey in the data from input1 to look up entries with the corresponding joinKey
    in input0. If there is no exact match for the value of joinKey in input0, linear interpolation
    is used. Only the keys in linInterpKeys are taken from input0 and adjoined to those from input1.

    Data from input0 are sorted by the values of joinKey. All these values should be integer
    multiples of "interval" and be increasing monotonically.

    The values of joinkey in the data from input1 need not be monotonic. So long that there are
    points from input0 which bracket the value of joinKey from input1, the interpolation and joining
    can take place. However, data from input0 are discarded once the values of joinKey are less than
    the current value of joinKey from input1 minus maxLookback*interval.
    """
    joinKey = Unicode()
    interval = Float()
    maxLookback = Integer()
    linInterpKeys = List(Unicode())
    kMin = Integer(allow_none=True)
    kMax = Integer(allow_none=True)
    lookup = Dict()
    def __init__(self, joinKey, interval, maxLookback=1000, linInterpKeys=None):
        super(JoinerBlock, self).__init__(self.newData, nInputs=2)
        assert isinstance(interval, float)
        assert interval > 0
        self.joinKey = joinKey
        self.interval = interval
        self.maxLookback = maxLookback
        self.linInterpKeys = linInterpKeys if linInterpKeys is not None else []
        self.kMin = None
        self.kMax = None
        self.lookup = {}

    def interpolate(self, xi, k1, k2):
        result = {}
        while k1 >= self.kMin:
            if k1 in self.lookup:
                break
            k1 -= 1
        while k2 <= self.kMax:
            if k2 in self.lookup:
                break
            k2 += 1
        x1 = self.lookup[k1][self.joinKey]
        x2 = self.lookup[k2][self.joinKey]
        for dataKey in self.linInterpKeys:
            y1 = self.lookup[k1][dataKey]
            y2 = self.lookup[k2][dataKey]
            result[dataKey] = ((x2 - xi) * y1 + (xi - x1) * y2) / (x2 - x1)
        return result

    def pruneLookup(self, k1):
        """Remove entries from lookup dictionary until smallest index is at least
        k1 - self.maxLookback. Update self.kMin and self.kMax accordingly.
        """
        while self.kMin < k1 - self.maxLookback and len(self.lookup) > 0:
            if self.kMin in self.lookup:
                del self.lookup[self.kMin]
            self.kMin += 1
        if len(self.lookup) == 0:
            self.kMin = None
            self.kMax = None
        else:
            while self.kMin < self.kMax and self.kMin not in self.lookup:
                self.kMin += 1

    def newData(self, deque0, deque1, lastCall=False):
        while len(deque0) > 0:
            data = deque0.popleft()
            xVal = data[self.joinKey]
            if isfinite(xVal):
                key = int(round(xVal/self.interval))
                self.kMin = min(self.kMin, key) if self.kMin is not None else key
                self.kMax = max(self.kMax, key) if self.kMax is not None else key
                self.lookup[key] = data

        if self.kMin is not None:
            while len(deque1) > 0:
                data = deque1.popleft()
                xVal = data[self.joinKey]
                if isfinite(xVal):
                    k1 = int(floor(xVal/self.interval))
                    k2 = k1 + 1
                    # Check if we can do the interpolation, if so yield the adjoined data
                    if self.kMin <= k1 and k2 <= self.kMax:
                        yield dict(data, **self.interpolate(xVal, k1, k2))
                        self.pruneLookup(k1)
                    # If we have not got data to look up, return nan
                    elif lastCall or k1 < self.kMin:
                        raise RuntimeError("Please increase value of maxLookback in JoinerBlock")
                        # yield dict(data, **{k:nan for k in self.linInterpKeys})
                    else:
                        deque1.appendleft(data)
                        return
                # If the key values are not finite, return nan
                else:
                    yield dict(data, **{k:nan for k in self.linInterpKeys})

class LineCountBlock(ActionBlock):
    freq = Integer()
    lineNumber = Integer()
    def __init__(self, freq=1000):
        super(LineCountBlock, self).__init__(self.newData)
        self.freq = freq
        self.lineNumber = 0
        self.setContinuation(self._continuation)

    def newData(self, data):
        self.lineNumber += 1
        if self.lineNumber % self.freq == 0:
            sys.stdout.write('%d ' % self.lineNumber)

    def _continuation(self, srcBlock):
        sys.stdout.write('\n')
        self.defaultContinuation(srcBlock)

class FovKmlWriterBlock(ActionBlock):
    filename = Unicode()
    kml = Instance(simplekml.Kml)
    multipoly = Instance(simplekml.kml.Container)
    lastRow = Integer(allow_none=True)
    lastLat = Float()
    lastLng = Float()
    lastDeltaLat = Float()
    lastDeltaLng = Float()
    def __init__(self, filename):
        super(FovKmlWriterBlock, self).__init__(self.newData)
        self.filename = filename
        self.kml = simplekml.Kml()
        self.multipoly = self.kml.newmultigeometry(name="FOV")
        self.lastRow = None
        self.setContinuation(self._continuation)
        self.lastLat, self.lastLng, self.lastDeltaLat, self.lastDeltaLng = None, None, None, None

    def isClockwise(self, coords):
        '''check if a list of coordinates containing at least three elements is clockwise or not'''
        if len(coords) < 3:
            return False
        a = asarray([coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]])
        b = asarray([coords[2][0] - coords[1][0], coords[2][1] - coords[1][1]])
        return cross(a, b) < 0.

    def newData(self, newDat):
        lat = newDat['GPS_ABS_LAT']
        lng = newDat['GPS_ABS_LONG']
        windN = newDat['WIND_N']
        windE = newDat['WIND_E']
        width = newDat['WIDTH']
        row = newDat['row']
        bearing = arctan2(windE, windN)
        cosLat = cos(lat * DTR)
        deltaLat = RTD*width*cos(bearing)/EARTH_RADIUS
        deltaLng = RTD*width*sin(bearing)/(EARTH_RADIUS*cosLat)
        if isfinite(lat) and isfinite(lng) and isfinite(deltaLat) and isfinite(deltaLng):
            if row-1 == self.lastRow:
                coords = [(self.lastLng, self.lastLat),
                          (lng, lat),
                          (lng + deltaLng, lat + deltaLat),
                          (self.lastLng + self.lastDeltaLng, self.lastLat + self.lastDeltaLat),
                          (self.lastLng, self.lastLat)]
                #if self.isClockwise(coords):
                #    coords.reverse()
                self.multipoly.newpolygon(
                    outerboundaryis=coords,
                    extrude=0
                )
            self.lastRow = row
            self.lastLat, self.lastLng, self.lastDeltaLat, self.lastDeltaLng = lat, lng, deltaLat, deltaLng

    def _continuation(self, srcBlock):
        self.multipoly.style.polystyle.outline = 0
        self.multipoly.style.polystyle.color = "80ff0000"
        with open(self.filename, "w") as kp:
            kp.write(self.kml.kml())
        self.defaultContinuation(srcBlock)

class PathKmlWriterBlock(ActionBlock):
    filename = Unicode()
    kml = Instance(simplekml.Kml)
    lastRow = Integer(allow_none=True)
    points = List()
    def __init__(self, filename):
        super(PathKmlWriterBlock, self).__init__(self.newData)
        self.filename = filename
        self.kml = simplekml.Kml()
        self.lastRow = None
        self.points = []
        self.setContinuation(self._continuation)

    def newData(self, newDat):
        lat = newDat['GPS_ABS_LAT']
        lng = newDat['GPS_ABS_LONG']
        row = newDat['row']
        if isfinite(lat) and isfinite(lng):
            if row-1 != self.lastRow:
                if self.points:
                    lin = self.kml.newlinestring(coords=self.points, extrude=1, altitudemode=simplekml.AltitudeMode.relativetoground)
                    lin.style.linestyle.color = "ffff0000"
                    lin.style.linestyle.width = 6
                    self.points = []
            self.points.append((lng, lat))
            self.lastRow = row

    def _continuation(self, srcBlock):
        if self.points:
            lin = self.kml.newlinestring(coords=self.points, extrude=1, altitudemode=simplekml.AltitudeMode.relativetoground)
            lin.style.linestyle.color = "ffff0000"
            lin.style.linestyle.width = 6
        with open(self.filename, "w") as kp:
            kp.write(self.kml.kml())
        self.defaultContinuation(srcBlock)

class PathWriterBlock(ActionBlock):
    fp = Instance(file)
    firstRow = Bool()
    def __init__(self, filename):
        super(PathWriterBlock, self).__init__(self.newData)
        self.fp = open(filename, "w")
        self.fp.write("[")
        self.firstRow = True
        self.setContinuation(self._continuation)

    def newData(self, newDat):
        lat = newDat['GPS_ABS_LAT']
        lng = newDat['GPS_ABS_LONG']
        pType = newDat['PATH_TYPE']
        row = newDat['row']
        if isfinite(lat) and isfinite(lng):
            path = geohash.encode(lat, lng)
            if self.firstRow:
                self.firstRow = False
            else:
                self.fp.write(",\n")
            self.fp.write(json.dumps({'R':row, 'P':path, 'T':pType}))

    def _continuation(self, srcBlock):
        if self.fp:
            self.fp.write("]\n")
            self.fp.close()
        self.defaultContinuation(srcBlock)

class PeaksKmlWriterBlock(ActionBlock):
    filename = Unicode()
    kml = Instance(simplekml.Kml)
    def __init__(self, filename):
        super(PeaksKmlWriterBlock, self).__init__(self.newData)
        self.filename = filename
        self.kml = simplekml.Kml()
        self.setContinuation(self._continuation)

    def newData(self, newDat):
        lat = newDat['GPS_ABS_LAT']
        lng = newDat['GPS_ABS_LONG']
        scale = 1.0
        color = "ffffffff"
        descr = []
        descr.append('amplitude = %.2f' % newDat['AMPLITUDE'])
        if 'ETHANE_RATIO' in newDat and not isnan(newDat['ETHANE_RATIO']):
            ratio = newDat['ETHANE_RATIO']
            sdev = newDat['ETHANE_RATIO_SDEV']
            descr.append('ethane = %.1f%%' % (100.0*ratio,))
            descr.append('ethane std_dev = %.1f%%' % (100.0*sdev,))
            if ratio + 2*sdev < 0.01:
                color = "ff00ff00"
            elif ratio - 2*sdev > 0.01:
                color = "ff0000ff"
            else:
                color = "ff00ffff"
            scale = 2.0
        descr.append('methane conc = %.2f' % newDat['CH4'])
        descr.append('sigma = %.2f' % newDat['SIGMA'])
        descr.append('epoch_time = %.0f' % newDat['EPOCH_TIME'])
        pnt = self.kml.newpoint(coords=[(lng, lat)], description="\n".join(descr))
        pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/wht-blank.png'
        pnt.style.iconstyle.color = color
        pnt.style.iconstyle.scale = scale

    def _continuation(self, srcBlock):
        with open(self.filename, "w") as kp:
            kp.write(self.kml.kml())
        self.defaultContinuation(srcBlock)

class JsonWriterBlock(ActionBlock):
    filename = Unicode()
    fp = Instance(file)
    firstRow = Bool()
    def __init__(self, filename):
        super(JsonWriterBlock, self).__init__(self.newData)
        self.filename = filename
        self.fp = open(self.filename, "w")
        self.fp.write("[")
        self.firstRow = True
        self.setContinuation(self._continuation)

    def newData(self, data):
        if self.firstRow:
            self.firstRow = False
        else:
            self.fp.write(",\n")
        try:
            self.fp.write(json.dumps(data, allow_nan=False))
        except ValueError:
            result = json.dumps(data)
            result = result.replace("NaN", "null").replace("-Infinity", "null").replace("Infinity", "null")
            self.fp.write(result)


    def _continuation(self, srcBlock):
        if self.fp:
            self.fp.write("]\n")
            self.fp.close()
        self.defaultContinuation(srcBlock)

class PeakWriterBlock(ActionBlock):
    fp = Instance(file)
    firstRow = Bool()
    def __init__(self, filename):
        super(PeakWriterBlock, self).__init__(self.newData)
        self.fp = open(filename, "w")
        self.fp.write("[")
        self.firstRow = True
        self.setContinuation(self._continuation)

    def newData(self, newDat):
        amp = newDat['AMPLITUDE']
        conc = newDat['CH4']
        epochTime = newDat['EPOCH_TIME']
        lat = newDat['GPS_ABS_LAT']
        lng = newDat['GPS_ABS_LONG']
        windN = newDat['WIND_N']
        windE = newDat['WIND_E']
        windStdDev = newDat['WIND_DIR_SDEV']
        dist = newDat['DISTANCE']
        passed_thresh = newDat.get('PASSED_THRESHOLD', 1)
        thresh = newDat.get('AMPL_THRESHOLD', 0.0)
        sigma = newDat['SIGMA']
        carE = 0.
        carN = 0.
        if 'CAR_VEL_E' in newDat:
            carE = newDat['CAR_VEL_E']
            carN = newDat['CAR_VEL_N']
        #carspeed = abs(carN + 1j*carE)
        carspeed = newDat['CAR_SPEED']
        wind = sqrt(windE*windE + windN*windN)
        bearing = RTD * arctan2(windE, windN)
        if isfinite(lat) and isfinite(lng) and isfinite(bearing) and isfinite(windStdDev):
            if self.firstRow:
                self.firstRow = False
            else:
                self.fp.write(",\n")
            peakData = {'ampl':amp, 'CH4':conc, 'Time':epochTime, 'Lat':lat, 'Long':lng, 'WindN':windN, 'WindE':windE,
                        'Wind':wind, 'Sigma':sigma, 'thresh':thresh, 'Dist':dist, 'WStd':windStdDev,
                        'CarSpeed':carspeed, 'carE':carE, 'carN':carN, 'passedThresh':passed_thresh}
            if 'ETHANE_RATIO' in newDat:
                peakData['ethaneRatio'] = newDat.get('ETHANE_RATIO', float('nan'))
                peakData['ethaneRatioStd'] = newDat.get('ETHANE_RATIO_SDEV', float('nan'))
                peakData['ethaneRatioStdRaw'] = newDat.get('ETHANE_RATIO_SDEV_RAW', float('nan'))
                peakData['pipEnergy'] = newDat.get('PIP_ENERGY', float('nan'))
                peakData['ethaneConcStd'] = newDat.get('ETHANE_CONC_SDEV', float('nan'))
                peakData['methanePtp'] = newDat.get('METHANE_PTP', float('nan'))
                peakData['ethyleneRatio'] = newDat.get('ETHYLENE_RATIO', float('nan'))
                peakData['ethyleneRatioStd'] = newDat.get('ETHYLENE_RATIO_SDEV', float('nan'))
                peakData['ethyleneRatioStdRaw'] = newDat.get('ETHYLENE_RATIO_SDEV_RAW', float('nan'))
                peakData['ethyleneConcStd'] = newDat.get('ETHYLENE_CONC_SDEV', float('nan'))

            self.fp.write(json.dumps(peakData))

    def _continuation(self, srcBlock):
        if self.fp:
            self.fp.write("]\n")
            self.fp.close()
        self.defaultContinuation(srcBlock)

class PrinterBlock(ActionBlock):
    filename = Unicode()
    fp = Instance(file)
    def __init__(self, filename=None, append=False):
        super(PrinterBlock, self).__init__(self.newData)
        self.filename = filename
        self.fp = None
        if self.filename:
            self.fp = open(self.filename, "a" if append else "w")
        self.setContinuation(self._continuation)

    def newData(self, data):
        if self.fp is None:
            print data
        else:
            print >> self.fp, data

    def _continuation(self, srcBlock):
        if self.fp:
            self.fp.close()
            self.fp = None
        self.defaultContinuation(srcBlock)

# The following path types are ordered so that a maximum interpolator may be used
NORMAL = 0
ANALYZING = 1
INACTIVE = 2
BADSTATUS = 3
GPS_BAD = 4

class ProcessStatusBlock(TransformManyBlock):
    """This block processes species, ValveMask, InstrumentStatus and GPS_FIT and adds a sequential row number.

    - Only lines of the correct species (2, 25 and 150) are included
    - Whenever GPS_FIT < 1, the latitude and longitude are set to NaN, and pType is set to GPS_BAD
    - A bad instrument status sets the path type to BADSTATUS
    - Bit 0 of ValveMask is used to indicate ANALYZING pType
    - Bit 4 of ValveMask is used to indicate INACTIVE pType
    """
    pathType = Integer()
    row = Integer()
    speciesList = List(Integer())
    def __init__(self, speciesList=None):
        self.pathType = NORMAL
        self.row = 0
        self.speciesList = speciesList if speciesList is not None else [2, 25, 150]
        super(ProcessStatusBlock, self).__init__(self.newData)

    def newData(self, newDat):
        self.row += 1
        newDat["GPS_ABS_LAT"] = round(newDat["GPS_ABS_LAT"], 8)
        newDat["GPS_ABS_LONG"] = round(newDat["GPS_ABS_LONG"], 8)
        lat = newDat["GPS_ABS_LAT"]
        lng = newDat["GPS_ABS_LONG"]
        fit = newDat["GPS_FIT"]
        mask = newDat["ValveMask"]
        pType = self.pathType
        imask = int(round(mask))
        if "species" not in newDat or int(newDat["species"]) in self.speciesList:
            # Note the following clauses are in order of decreasing severity
            if fit < 1.0:
                lat = nan
                lng = nan
                pType = GPS_BAD
            #elif (instStatus & sis.INSTMGR_STATUS_MASK) != sis.INSTMGR_STATUS_GOOD:
            #    pType = BADSTATUS
            elif abs(mask - imask) < 1e-4:
                if imask & 16:
                    pType = INACTIVE
                elif imask & 1:
                    pType = ANALYZING
                else:
                    pType = NORMAL
            self.pathType = pType
            yield dict(newDat, row=self.row, GPS_ABS_LAT=lat, GPS_ABS_LONG=lng, PATH_TYPE=pType)

