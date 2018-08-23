#!/usr/bin/python
#
"""PeaksBlocks.py: Blocks for pipelined processing of peaks

Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
from collections import deque, namedtuple
from Host.Pipeline.Blocks import TransformBlock, TransformManyBlock
from Host.Pipeline.PeakFinder import peakF
from numpy import arange, arctan, arctan2, asarray, ceil, cos, cumsum, exp, isnan, ndarray, pi, sin, sqrt, std, tan, zeros
from traitlets import Any, Bool, Float, Instance, Integer, List, Tuple, Unicode, Union

NOT_A_NUMBER = float('nan')
def distVincenty(lat1, lon1, lat2, lon2):
    # WGS-84 ellipsiod. lat and lon in DEGREES
    a = 6378137
    b = 6356752.3142
    f = 1/298.257223563
    toRad = pi/180.0
    L = (lon2-lon1)*toRad
    U1 = arctan((1-f) * tan(lat1*toRad))
    U2 = arctan((1-f) * tan(lat2*toRad))
    sinU1 = sin(U1)
    cosU1 = cos(U1)
    sinU2 = sin(U2)
    cosU2 = cos(U2)

    Lambda = L
    iterLimit = 100
    for _ in range(iterLimit):
        sinLambda = sin(Lambda)
        cosLambda = cos(Lambda)
        sinSigma = sqrt((cosU2*sinLambda) * (cosU2*sinLambda) +
                        (cosU1*sinU2-sinU1*cosU2*cosLambda) * (cosU1*sinU2-sinU1*cosU2*cosLambda))
        if sinSigma == 0:
            return 0  # co-incident points
        cosSigma = sinU1*sinU2 + cosU1*cosU2*cosLambda
        sigma = arctan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cosSqAlpha = 1 - sinAlpha*sinAlpha
        if cosSqAlpha == 0:
            cos2SigmaM = 0
        else:
            cos2SigmaM = cosSigma - 2*sinU1*sinU2/cosSqAlpha
        C = f/16*cosSqAlpha*(4+f*(4-3*cosSqAlpha))
        lambdaP = Lambda
        Lambda = L + (1-C) * f * sinAlpha * \
          (sigma + C*sinSigma*(cos2SigmaM+C*cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)))
        if abs(Lambda-lambdaP) <= 1.e-12: break
    else:
        raise ValueError("Failed to converge")

    uSq = cosSqAlpha * (a*a - b*b) / (b*b)
    A = 1 + uSq/16384*(4096+uSq*(-768+uSq*(320-175*uSq)))
    B = uSq/1024 * (256+uSq*(-128+uSq*(74-47*uSq)))
    deltaSigma = B*sinSigma*(cos2SigmaM+B/4*(cosSigma*(-1+2*cos2SigmaM*cos2SigmaM)-
                                            B/6*cos2SigmaM*(-3+4*sinSigma*sinSigma)*(-3+4*cos2SigmaM*cos2SigmaM)))
    return b*A*(sigma-deltaSigma)

class AddDistanceBlock(TransformBlock):
    jumpMax = Float()
    dist = Float(allow_none=True)
    lastLat = Float(allow_none=True)
    lastLng = Float(allow_none=True)
    def __init__(self, jumpMax=500):
        super(AddDistanceBlock, self).__init__(self.newData)
        self.jumpMax = jumpMax
        self.dist = None
        self.lastLat = None
        self.lastLng = None

    def newData(self, newDat):
        assert isinstance(newDat, dict)
        lng = newDat["GPS_ABS_LONG"]
        lat = newDat["GPS_ABS_LAT"]
        fit = newDat["GPS_FIT"]
        if fit < 1 or isnan(lng) or isnan(lat):
            result = NOT_A_NUMBER
        else:
            if self.lastLat is None and self.lastLng is None:
                result = self.dist = 0.0
            else:
                jump = distVincenty(lat, lng, self.lastLat, self.lastLng)
                if jump < self.jumpMax:
                    self.dist += jump
                    result = self.dist
                else:
                    result = NOT_A_NUMBER
            self.lastLat = lat
            self.lastLng = lng
        return dict(newDat, DISTANCE=result)

class BaselineFilterBlock(TransformBlock):
    baselineFiltLen = Integer()
    dataKey = Unicode()
    baselineBuffer = Instance(deque)
    warmupDist = Integer()
    countDown = Integer()
    def __init__(self, dataKey, baselineFilterLength):
        super(BaselineFilterBlock, self).__init__(self.newData)
        self.baselineFiltLen = baselineFilterLength
        self.dataKey = dataKey
        self.baselineBuffer = deque()
        self.warmupDist = 10
        self.countDown = self.warmupDist

    def newData(self, newDat):
        if newDat["PATH_TYPE"] != 0:
            self.countDown = self.warmupDist
        else:
            self.countDown = max(self.countDown-1, 0)
        if self.countDown > 0:
            self.baselineBuffer.clear()
        self.baselineBuffer.append(newDat[self.dataKey])
        if len(self.baselineBuffer) > self.baselineFiltLen:
            self.baselineBuffer.popleft()
        return dict(DISTANCE=newDat["DISTANCE"], BASELINE_FILT_OUT=std(self.baselineBuffer))

class MinimumFilterBlock(TransformBlock):
    minFiltLen = Integer()
    dataKey = Unicode()
    minBuffer = Instance(deque)
    warmupDist = Integer()
    countDown = Integer()
    def __init__(self, dataKey, minimumFilterLength):
        super(MinimumFilterBlock, self).__init__(self.newData)
        self.minFiltLen = minimumFilterLength
        self.dataKey = dataKey
        self.minBuffer = deque()
        self.warmupDist = 10
        self.countDown = self.warmupDist

    def newData(self, newDat):
        if newDat["PATH_TYPE"] != 0:
            self.countDown = self.warmupDist
        else:
            self.countDown = max(self.countDown-1, 0)
        if self.countDown > 0:
            self.minBuffer.clear()
        self.minBuffer.append(newDat[self.dataKey])
        if len(self.minBuffer) > self.minFiltLen:
            self.minBuffer.popleft()
        return dict(DISTANCE=newDat["DISTANCE"], MIN_FILT_OUT=min(self.minBuffer), PATH_TYPE=newDat["PATH_TYPE"])

class PeakFilterBlock(TransformManyBlock):
    minAmpl = Float()
    maxWidth = Float()
    """Filters peaks by amplitude and maximum width"""
    def __init__(self, minAmpl, maxWidth):
        super(PeakFilterBlock, self).__init__(self.newData)
        self.minAmpl = minAmpl
        self.maxWidth = maxWidth

    def newData(self, newDat):
        sigma = newDat['SIGMA']
        ampl = newDat['AMPLITUDE']
        amplThreshold = newDat.get('AMPL_THRESHOLD', 0.0)
        newDat['PASSED_THRESHOLD'] = int(ampl >= amplThreshold)
        if ampl >= self.minAmpl and sigma <= self.maxWidth:
            yield newDat

class SpaceScaleAnalyzerBlock(TransformManyBlock):
    dx = Float()
    nlevels = Integer()
    minAmpl = Float()

    initBuff = Bool()
    DataTuple = Any()
    PeakTuple = Any()
    cache = Instance(ndarray, allow_none=True)
    concIndex = Integer(allow_none=True)
    etmIndex = Integer(allow_none=True)
    dataLen = Integer(allow_none=True)
    distIndex = Integer(allow_none=True)
    hList = Union((Instance(ndarray, allow_none=True), List(Float())))
    indexToClear = Integer(allow_none=True)
    init = Bool()
    kernelCenterIndex = Integer(allow_none=True)
    kernelCenterStart = Integer(allow_none=True)
    kernels = Instance(ndarray, allow_none=True)
    maxKernel = Integer(allow_none=True)
    npoints = Integer(allow_none=True)
    scaleList = Union((Instance(ndarray, allow_none=True), List(Float())))
    ssbuff = Instance(ndarray, allow_none=True)
    sumDat = Float()
    sumDat2 = Float()
    valveIndex = Integer(allow_none=True)
    def __init__(self, dx, minAmpl, t_0, nlevels, tfactor):
        """Analyze source at a variety of scales using the differences of Gaussians of
        different scales. We define
            g(x;t) = exp(-0.5*x**2/t)/sqrt(2*pi*t)
        and let the convolution kernels be
            (tfactor+1)/(tfactor-1) * (g(x,t_i) - g(x,tfactor*t_i))
        where t_i = tfactor * t_i-1. There are a total of "nlevels" kernels each defined
        on a grid with an odd number of points which just covers the interval
        [-5*sqrt(tfactor*t_i),5*sqrt(tfactor*t_i)]
        """
        super(SpaceScaleAnalyzerBlock, self).__init__(self.newData)
        self.dx = dx
        self.nlevels = nlevels
        self.minAmpl = minAmpl

        self.initBuff = True
        self.DataTuple = None
        self.PeakTuple = None
        self.cache = None
        self.concIndex = None
        self.etmIndex = None
        self.dataLen = None
        self.distIndex = None
        self.hList = None
        self.indexToClear = None
        self.init = True
        self.kernelCenterIndex = None
        self.kernelCenterStart = None
        self.kernels = None
        self.maxKernel = None
        self.npoints = None
        self.scaleList = None
        self.ssbuff = None
        self.sumDat = 0
        self.sumDat2 = 0
        self.valveIndex = None
        self.initKernels(t_0, tfactor)

    def initKernels(self, t_0, tfactor):
        self.hList = [] # Kernels are defined on -h,...,0,...,h
        kernelList = []
        self.scaleList = []
        ta, tb = t_0, tfactor * t_0
        amp = (tfactor + 1) / (tfactor - 1)
        for i in range(self.nlevels):
            h = int(ceil(5 * sqrt(tb) / self.dx))
            self.hList.append(h)
            x = arange(-h, h + 1) * self.dx
            gaussA = exp(-0.5 * x * x / ta) / sqrt(2 * pi * ta)
            gaussB = exp(-0.5 * x * x / tb) / sqrt(2 * pi * tb)
            kernel = amp * (gaussA - gaussB) * self.dx
            kernelList.append(kernel)
            self.scaleList.append(sqrt(ta * tb))
            ta, tb = tb, tfactor * tb
        self.hList = asarray(self.hList)
        self.scaleList = asarray(self.scaleList)
        # The size of the kernels get larger with i. We wish to pack them into a 2d rectangular array
        self.maxKernel = len(kernelList[-1])
        self.kernels = zeros((self.nlevels, self.maxKernel), dtype=float)
        for i in range(self.nlevels):
            self.kernels[i][:2 * self.hList[i] + 1] = kernelList[i]
        hmax = self.hList[-1]
        self.npoints = 2 * hmax + 4
        self.kernelCenterStart = hmax + 3

    def newData(self, newDat):
        if self.init:
            self.DataTuple = namedtuple("DataTuple", newDat.keys())
            data = self.DataTuple(**newDat)
            self.PeakTuple = namedtuple("PeakTuple", data._fields + ("AMPLITUDE", "SIGMA"))
            fields = list(data._fields)
            self.dataLen = len(fields)
            self.concIndex = fields.index('CH4')
            self.etmIndex = fields.index('EPOCH_TIME')
            self.distIndex = fields.index('DISTANCE')
            self.valveIndex = fields.index('ValveMask')
            self.init = False
        else:
            data = self.DataTuple(**newDat)

        dist = data[self.distIndex]
        if dist is None:
            self.initBuff = True
            return

        # Initialize the buffer
        if self.initBuff:
            self.ssbuff = zeros((self.nlevels, self.npoints), float)
            # Define a cache for the data so that the
            #  coordinates and value of peaks can be looked up
            self.cache = zeros((len(data), self.npoints), float)
            # kernelCenterIndex is the where in self.ssbuff the center of the kernel is placed
            self.kernelCenterIndex = self.kernelCenterStart
            # indexToClear is the column in self.ssbuff which has to be set to zero before adding
            #  in the kernels
            self.indexToClear = 0
            for i in range(self.nlevels):
                self.ssbuff[i, self.kernelCenterIndex - self.hList[i]:self.kernelCenterIndex + self.hList[i] + 1] = \
                    -data[self.concIndex] * cumsum(self.kernels[i][0:2 * self.hList[i] + 1])
            self.initBuff = False

        minAmpl = self.minAmpl * 2.0 * 3.0 ** (-1.5)
        p, np = peakF.findPeaks(asarray(data), self.hList, self.scaleList, self.kernels, self.ssbuff, self.cache,
                                minAmpl, self.indexToClear, self.kernelCenterIndex, self.concIndex, self.distIndex,
                                self.etmIndex, self.valveIndex, self.dataLen, self.nlevels, self.npoints,
                                self.maxKernel)
        peaks = p[:np[0], :]

        self.kernelCenterIndex += 1
        if self.kernelCenterIndex >= self.npoints:
            self.kernelCenterIndex -= self.npoints
        self.indexToClear += 1
        if self.indexToClear >= self.npoints:
            self.indexToClear -= self.npoints

        for peak in peaks:
            yield dict(self.PeakTuple(*peak)._asdict())

