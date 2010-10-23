#!/usr/bin/python
#
"""
File Name: fitterCore.py
Purpose:
    Low-level fitter routines

File History:
    07-09-?? sze   In development
    07-10-03 sze   Allow scalar arguments to be passed to BasisFunctions.
    07-10-03 sze   Allow natural splines to be defined without 2nd derivatives
                   and check supplied second derivatives for consistency
    07-10-03 sze   Added "peak" option for bi-splines
    08-02-15 sze   Allow search window around peak of a bispline to be specified
                   Make analysis INI configuration data available to fit scripts
    08-04-22 sze   Let sparse filter report statistics to filterHistory
    08-09-18 alex  Replaced ConfigParser with CustomConfigObj
    09-06-30 alex  Support HDF5 format for spectra data
    10-06-14 john  Outlier filter added to sparser
    10-06-24 sze   Added numGroups key to RdData objects

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import os
import sys
from Host.Common.CustomConfigObj import CustomConfigObj
from copy import copy
import cPickle
from cStringIO import StringIO
from glob import glob
from numpy import arange, arctan, argmax, argmin, argsort, array, asarray, bool_, concatenate, cos
from numpy import diff, searchsorted, dot, exp, flatnonzero, float_, frompyfunc
from numpy import int8, int_, invert, iterable, linspace, logical_and, mean, median, ndarray, ones
from numpy import pi, polyfit, ptp, shape, sin, sqrt, std, unique, zeros 
from os.path import getmtime, join, split, exists
from scipy.optimize import leastsq, brent
from string import strip
from struct import calcsize, unpack
from time import strptime, mktime, time, localtime
from Host.Common.EventManagerProxy import Log
from tables import *
from Host.Common.timestamp import unixTime
import traceback
################################################################################
# GLOBAL VARIABLES
################################################################################
spectralLibrary = None
splineLibrary = None
physicalConstants = {}

# The following are used by class Galatry when processing initial values
#  (in initializeModel) and also by classes InitialValues, Dependencies
#  and Analysis
#
galDict0 = dict(peak=0,base=1)
galDict1 = dict(center=0,strength=1,y=2,z=3,v=4)
galDict2 = dict(scaled_strength=1,scaled_y=2,scaled_z=3)
availableAnalysisParams = ["name","std_dev_res","time"]
################################################################################
# Set up AppPath to location of executing code
################################################################################
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

def getAppPath():
    return AppPath

def prependAppDir(fname):
    """Prepends the directory of the application to the specified filename"""
    AppDir = split(AppPath)[0]
    return join(AppDir,fname)

def readConfig(fname):
    """Returns a ConfigParser object initialized with data from the specified
    file, located (by default) in the application directory"""
    # config = CustomConfigObj(prependAppDir(fname))
    config = CustomConfigObj(fname)
    return config
################################################################################
# Functions available to fitter scripts
################################################################################
def loadSpectralLibrary(fnameOrConfig):
    global spectralLibrary
    if not isinstance(fnameOrConfig,CustomConfigObj):
        fnameOrConfig = readConfig(fnameOrConfig)
    spectralLibrary = SpectralLibrary(fnameOrConfig)
    return spectralLibrary

def loadPhysicalConstants(fnameOrConfig):
    global physicalConstants
    if not isinstance(fnameOrConfig,CustomConfigObj):
        fnameOrConfig = readConfig(fnameOrConfig)
    physicalConstants = PhysicalConstants(fnameOrConfig)
    return physicalConstants

def loadSplineLibrary(fnameOrConfig):
    global splineLibrary
    if not isinstance(fnameOrConfig,CustomConfigObj):
        fnameOrConfig = readConfig(fnameOrConfig)
    splineLibrary = SplineLibrary(fnameOrConfig)
    return splineLibrary


################################################################################
# Spectral lineshape functions
################################################################################

Ts = array([ 0.314240376, 0.947788391,
                   1.597682640, 2.279507080,
                   3.020637030, 3.889724900])

Cs = array([ 1.011728050E+0,-7.519714700E-1,
                   1.255772700E-2, 1.002200820E-2,
                  -2.420681350E-4, 5.008480610E-7])

Ss = array([ 1.393237000E+0, 2.311524060E-1,
                  -1.553514660E-1, 6.218366240E-3,
                   9.190829860E-5,-6.275259580E-7])

def voigt(x,y):
    """Evaluate the Voigt function with parameter y at the points in vector x."""

    def voigtCases():
        """Implementation of Voigt Cases.vi"""
        mask1 = abs(x) < 18.1*abs(y) + 1.65
        mask2 = invert(mask1)
        mask3 = logical_and(abs(x) < 12,mask2)
        return mask1, mask2, mask3

    ReKvs = zeros(shape(x),'d')
    ImKvs = zeros(shape(x),'d')
    Y1 = abs(y) + 1.5
    Y2 = Y1**2
    if abs(y) > 0.85:
        for i in range(len(Ts)):
            Rs = x - Ts[i]
            Ds = 1.0/(Rs**2 + Y2)
            D1s = Y1*Ds
            D2s = Rs*Ds
            Rs = x + Ts[i]
            Ds = 1.0/(Rs**2 + Y2)
            D3s = Y1*Ds
            D4s = Rs*Ds
            ReKvs = ReKvs + Cs[i]*(D1s+D3s) - Ss[i]*(D2s-D4s)
            ImKvs = ImKvs + Cs[i]*(D2s+D4s) + Ss[i]*(D1s-D3s)
    else:
        mask1, mask2, mask3 = voigtCases()
        Y3 = abs(y) + 3
        for i in range(len(Ts)):
            Rs = x - Ts[i]
            Rs2 = Rs**2
            ReKvs3 = exp(-x**2)/6.0
            Ds = 1.0/ (Rs2+Y2)
            D1s = Y1*Ds
            D2s = Rs*Ds
            temp = abs(y)*(Cs[i]*(Rs*D2s-1.5*D1s)+Ss[i]*Y3*D2s)/(Rs2+2.25)
            Rs = x + Ts[i]
            Rs2 = Rs**2
            Ds = 1.0/(Rs2+Y2)
            D3s = Y1*Ds
            D4s = Rs*Ds
            ReKvs1 = Cs[i]*(D1s + D3s) - Ss[i]*(D2s - D4s)
            ReKvs2 = temp + abs(y)*(Cs[i]*(Rs*D4s-1.5*D3s) - \
                                    Ss[i]*Y3*D4s)/(Rs2+2.25)
            ImKvs = ImKvs + Cs[i]*(D2s + D4s) + Ss[i]*(D1s - D3s)
            ReKvs[mask1] = ReKvs[mask1] + ReKvs1[mask1]
            ReKvs[mask2] = ReKvs[mask2] + ReKvs2[mask2]
            ReKvs[mask3] = ReKvs[mask3] + ReKvs3[mask3]
    return ReKvs + 1j*ImKvs
################################################################################
def galatry(x,y,z,strength=1.0,minimum_loss=0.001):
    """Evaluate the Galatry function at locations x."""
    # Determine which formula to use (region) for each value of x
    result = zeros(shape(x),'d')
    y = abs(y)
    z = abs(z)
    xm = y*sqrt(abs(strength/minimum_loss-1.0))
    xm = min(max(xm,10.0),300.0)
    if z<0.04 and y<0.5: r=1
    elif z<0.1: r=3
    elif z>5.0: r=2
    elif y>4*z**0.868: r=3
    else: r=2
    region_array = r*ones(shape(x),dtype='l')
    region_array[abs(x)>xm] = 4
    # Move some x from region 1 to region 3 if their values are greater than 2 (avoid divergenece of Humlicek routine)
    # The switch is turned off since it doesn't help to compute the result
    #if r==1: region_array[logical_and(abs(x)>2,abs(x)<=xm)]=3

    # Evaluate the function in four possible regions
    region1 = region_array == 1
    if region1.any():
        c3r = z/12.0
        c4r = -z**2/48.0
        c5r = z**3/240.0
        c = array([1.0,
                    0.0,
                    0.0,
                    1j*c3r,
                    c4r,
                    -1j*c5r,
                    -1*(-z**4/1440.0 + c3r**2/2.0),
                    1j*(z**5/10080.0 + c3r*c4r),
                    -z**6/80640.0 + c3r*c5r + c4r**2/2.0],'D')
        xx = x[region1]
        vv = voigt(xx,y)
        qq = xx + 1j*y
        ww = zeros((len(xx),9),'D')
        ww[:,0] = vv
        ww[:,1] = 2j/sqrt(pi) - 2*vv*qq
        for i in range(7):
            ww[:,i+2] = -2.0*((i+1)*ww[:,i] + qq*ww[:,i+1])
        result[region1] = dot(ww,c).real

    region2 = region_array == 2
    if region2.any():
        N = int(4 + z**(-1.05)*(1.0+3.0*exp(-1.1*y)))+1
        assert N>0
        if abs(N)>5000: N=5000
        xx = x[region2]
        delta = 0.5/(z**2)
        theta = (y - 1j*xx)/z + delta
        sum = 0.0
        term = 1.0/(z*sqrt(pi)*delta)
        for i in range(N):
            term = term*delta/(i+theta)
            sum = sum + term
        result[region2] = sum.real

    region3 = region_array == 3
    if region3.any():
        xx = x[region3]
        # Extra terms in N calculation are added when z and y are small
        # This can be removed because we no longer move x from region 1 to region 3
        # The max N based on the paper is 39, but we use 100 here just to be safe
        try:
            if z<0.2: Nz = 5.0*sqrt(1.0/abs(z))
            else: Nz = 0
            if y<0.2: N = int(2 + Nz + 37.0/sqrt((abs(y)))*exp(-0.6*y))+1
            else: N = int(2 + 37.0*exp(-0.6*y))+1
            assert N>0
            if N>100: N = 100
        except:
            N = 100
        qq = y - 1j*xx
        f = 0.0
        for i in range(N):
            f = 0.5*(N-i)/(f+(N-i)*z+qq)
        result[region3] = (1.0/(sqrt(pi) * (qq + f))).real

    region4 = region_array == 4
    if region4.any():
        result[region4] = 0.0

    return result
################################################################################
def makeSplineSection(config,secName,descr,xVal,yVal,y2Val=None):
    config.add_section(secName)
    config.set(secName,"d",descr)
    for i,x in enumerate(xVal):
        config.set(secName,"f%d"%(i,),"%.10g"%(x,))
        config.set(secName,"a%d"%(i,),"%.10g"%(yVal[i],))
        if y2Val != None: config.set(secName,"i%d"%(i,),"%.10g"%(y2Val[i],))

def makeConfigFromNestedDict(config,nestedDict):
    for section in nestedDict:
        config.add_section(section)
        for option in nestedDict[section]:
            config.set(section,option,nestedDict[section][option])

################################################################################
# Key tuples are used to define initial conditions and dependencies
################################################################################
def classifyKeyTuple(keyTuple):
    try:
        if not isinstance(keyTuple,tuple):
            keyTuple = (keyTuple,)
        if isinstance(keyTuple[0],int):
            key1 = keyTuple[0]
            if key1>=0 and key1<=999: class1 = 0
            elif key1>=1000: class1 = 1
            else: raise ClassifyError
        elif isinstance(keyTuple[0],str):
            key1 = keyTuple[0].lower()
            if key1 in ["base"]: class1 = 2
            elif key1 in availableAnalysisParams: class1 = 3
            else: raise ClassifyError
        else: raise ClassifyError
        if len(keyTuple) == 1:
            class2 = 0
            key2 = None
        elif isinstance(keyTuple[1],int):
            key2 = keyTuple[1]
            class2 = 1
        elif isinstance(keyTuple[1],str):
            key2 = keyTuple[1].lower()
            if key2 in galDict0:
                class2 = 2
            elif key2 in galDict1:
                class2 = 3
            elif key2 in galDict2:
                class2 = 4
            else: raise ClassifyError
        else: raise ClassifyError
        # Check for peak/base of special functions (>=1000), which may need extra parameters
        if (len(keyTuple) > 2) and not (class1 == 1 and class2 == 2):
            raise ClassifyError
        return class1, class2, key1, key2, keyTuple[2:]
    except:
        raise ClassifyError,("Invalid keyTuple: %s" % (keyTuple,))

################################################################################
# sigma filter is used to select good points out of a vector of data
################################################################################
def sigmaFilter(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = ones(x.shape,bool_)
    nIter = 0
    while True:
        mu = mean(x[good])
        sigma = std(x[good])
        new_good = abs(x-mu)<=(threshold*sigma)
        nIter += 1
        if (new_good==good).all() or new_good.sum()<=minPoints: break
        good = new_good
    return new_good, dict(iterations=nIter)

################################################################################
# outlier filter is used to select good points out of a vector of data
################################################################################
def outlierFilter(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = ones(x.shape,bool_)
    order = list(x.argsort())
    while len(order)>minPoints:
        maxIndex = order.pop()
        good[maxIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[maxIndex]-mu)>=(threshold*sigma):
            continue
        good[maxIndex] = 1
        minIndex = order.pop(0)
        good[minIndex] = 0
        mu = mean(x[good])
        sigma = std(x[good])
        if abs(x[minIndex]-mu)>=(threshold*sigma):
            continue
        good[minIndex] = 1
        break
    return good, dict(nDiscarded=len(x)-len(order))

################################################################################
# sigma filter is used to select good points out of a vector of data
################################################################################
def sigmaFilterMedian(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the median. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    new_good = good = ones(x.shape,bool_)
    nIter = 0
    while new_good.sum()>1 and len(x)>1:
        med = median(x[good])
        sigma = std(x[good])
        new_good = abs(x-med)<=(threshold*sigma)
        nIter += 1
        if (new_good==good).all() or new_good.sum()<=minPoints: break
        good = new_good
    return new_good, dict(iterations=nIter)

################################################################################
# Repository generation programs for producing RdfData objects from files
################################################################################
def convHdf5ToDict(h5Filename):
    h5File = openFile(h5Filename, "r")
    retDict = {}
    for tableName in h5File.root._v_children.keys():
        table = h5File.root._v_children[tableName]
        retDict[tableName] = {}
        for colKey in table.colnames:
            retDict[tableName][colKey] = table.read(field=colKey)
    h5File.close()
    return retDict
    
def hdf5RepositoryFromList(hdf5Files):
    """Generator which yields successive spectra (in HDF5 format) from a
    list of .h5 files"""
    # Decorate the file list with the filename portion of the path
    decList = [(split(f)[-1].split(".")[0][-13:],f) for f in hdf5Files]
    decList.sort()
    # Iterate through files
    for (d,f) in decList:
        baseName = split(f)[-1].strip()[:-3]
        rdfDict = convHdf5ToDict(f)
        for rdfData in RdfData.getSpectraDict(rdfDict):
            yield rdfData, baseName

def pickledRepository(dirName,startIndex,endIndex):
    """Generator which yields successive spectra (in RDF format) from a
    directory containing .rdf files"""
    pathName = join(dirName,"*.rdf")
    pickledFiles = glob(pathName)
    # Decorate the file list with the index
    decList = [(split(f)[-1].split(".")[0][-13:],f) for f in pickledFiles]
    decList.sort()
    # Iterate through files between start and end indices
    return pickledRepositoryFromList([f for (d,f) in decList if d>=startIndex and d<=endIndex])

def pickledRepositoryFromList(pickledFiles):
    """Generator which yields successive spectra (in pickled format) from a
    list of pickled .rdf files"""
    # Decorate the file list with the filename portion of the path
    decList = [(split(f)[-1].split(".")[0][-13:],f) for f in pickledFiles]
    decList.sort()
    # Iterate through files
    for (d,f) in decList:
        baseName = split(f)[-1].strip()[:-4]
        pData = file(f,"rb").read()
        rdfDict = cPickle.loads(pData)
        for rdfData in RdfData.getSpectraDict(rdfDict):
            yield rdfData, baseName

class ClassifyError(ValueError):
    """This is a custom exception thrown when classifying KeyTuples"""
    pass
class PhysicalConstants(dict):
    def __init__(self,config):
        # Read in physical constants
        section = "Fundamental constants"
        self["c"] = config.getfloat(section,"c")
        self["k"] = config.getfloat(section,"k")
        self["amu"] = config.getfloat(section,"amu")
class SplineLibrary(object):
    def __init__(self,config):
        self.splineList = CubicSpline.getListFromConfig(config)
class SpectralLibrary(object):
    """A SpectralLibrary contains parameters for a collection of spectral lines. These lines are numbered from 0 through 999
    and are the same for all instruments"""
    def __init__(self,config):
        self.peakDict = {}    # Peaks keyed by index (0-999)
        self.speciesDict = {} # Species names, keyed by index
        # Read species names
        section = "species list"
        for k in config.list_options(section):
            self.speciesDict[config.getint(section,k)] = k
        # Read in peak information
        for section in config.list_sections():
            if section[:4] == "peak":
                peakNum = int(section[4:])
                name = config.get(section,"peak name").strip('"')
                mass = config.getfloat(section,"mass")
                center = config.getfloat(section,"center")
                strength = config.getfloat(section,"strength")
                y = config.getfloat(section,"y")
                z = config.getfloat(section,"z")
                v = config.getfloat(section,"v")
                snum = config.getint(section,"species")
                try:
                    species = self.speciesDict[snum]
                except KeyError:
                    species = "%d" % (snum,)
                self.peakDict[peakNum] = (name,mass,center,strength,y,z,v,species)
################################################################################
# CubicSpline objects
################################################################################

class CubicSpline(object):
    def __init__(self, x_array, y_array, low_slope=None, high_slope=None, y2_array=None, tol=1.0e-7):
        """Construct a cubic spline, passing through the points specified by x_array and y_array.
        If y2_array is not specified, the spline is computed to have the slope low_slope at
         x_array[0] and high_slope at x_array[-1]. If either of low_slope or high_slope is None,
         the curvature at the corresponding endpoint is zero.
        If y2_array is specified, it is used as the vector of second derivatives at the knots. A check
         is performed to see if the second derivatives are consistent with the provided values. The parameter
         "tol" specifies the tolerance at which the consistency test fails.
        """
        self.x_vals = x_array
        self.y_vals = y_array
        if y2_array is not None:
            if len(y2_array) != len(y_array):
                raise ValueError("y_array and y2_array must be of the same length in Spline")
            self.y2_vals = y2_array
            # Check that the y2 values are compatible with the x and y values
            misfit = 0
            slope = 0
            for j in range(1,len(x_array)-1):
                dxL = x_array[j] - x_array[j-1]
                dxR = x_array[j+1] - x_array[j]
                slopeL = (y_array[j] - y_array[j-1])/dxL
                slopeR = (y_array[j+1] - y_array[j])/dxR
                misfit = max(misfit,abs((dxL*y2_array[j-1] + 2*(dxL+dxR)*y2_array[j] + dxR*y2_array[j+1])/6.0 - (slopeR - slopeL)))
                slope  = max(slope,abs(slopeR),abs(slopeL))
            if misfit > tol*slope:
                raise ValueError("Specified spline second derivatives are inconsistent with values")
        else:
            self.low_slope  = low_slope
            self.high_slope = high_slope
            # must be careful, so that a slope of 0 still works...
            self.use_low_slope = low_slope is not None
            self.use_high_slope = high_slope is not None
            self.calc_ypp()

    def calc_ypp(self):
        x_vals = self.x_vals
        y_vals = self.y_vals
        n = len(x_vals)
        y2_vals  = zeros(n, 'd')
        u        = zeros(n-1, 'd')

        if self.use_low_slope:
            u[0] = (3.0/(x_vals[1]-x_vals[0])) * \
                   ((y_vals[1]-y_vals[0])/
                    (x_vals[1]-x_vals[0])-self.low_slope)
            y2_vals[0] = -0.5
        else:
            u[0] = 0.0
            y2_vals[0] = 0.0   # natural spline

        for i in range(1, n-1):
            sig = (x_vals[i]-x_vals[i-1]) / \
                  (x_vals[i+1]-x_vals[i-1])
            p   = sig*y2_vals[i-1]+2.0
            y2_vals[i] = (sig-1.0)/p
            u[i] = (y_vals[i+1]-y_vals[i]) / \
                   (x_vals[i+1]-x_vals[i]) - \
                   (y_vals[i]-y_vals[i-1])/ \
                   (x_vals[i]-x_vals[i-1])
            u[i] = (6.0*u[i]/(x_vals[i+1]-x_vals[i-1]) -
                    sig*u[i-1]) / p

        if self.use_high_slope:
            qn = 0.5
            un = (3.0/(x_vals[n-1]-x_vals[n-2])) * \
                 (self.high_slope - (y_vals[n-1]-y_vals[n-2]) /
                  (x_vals[n-1]-x_vals[n-2]))
        else:
            qn = 0.0
            un = 0.0    # natural spline

        y2_vals[n-1] = (un-qn*u[n-2])/(qn*y2_vals[n-2]+1.0)

        rng = range(n-1)
        rng.reverse()
        for k in rng:         # backsubstitution step
            y2_vals[k] = y2_vals[k]*y2_vals[k+1]+u[k]
        self.y2_vals = y2_vals

    def getDomain(self):
        """Returns minimum and maximum values at which the spline can be computed"""
        return self.x_vals[0],self.x_vals[-1]

    def call(self,x):
        """Evaluate the spline at the points specified by the array x"""
        assert isinstance(x,ndarray)
        y = zeros(x.shape,'d')
        h = diff(self.x_vals)
        n = len(self.x_vals)
        x_bins = searchsorted(self.x_vals,x,'right')
        # Deal with points which are out of range
        y[x_bins==0] = self.y_vals[0]
        y[x_bins==n] = self.y_vals[-1]
        good = logical_and(x_bins > 0, x_bins < n)
        xg = x[good]; xbg = x_bins[good]
        A = (self.x_vals[xbg] - xg)/h[xbg-1]
        B = 1-A
        C = (A**3-A)*h[xbg-1]**2/6.0
        D = (B**3-B)*h[xbg-1]**2/6.0
        y[good] = A*self.y_vals[xbg-1]+B*self.y_vals[xbg]+C*self.y2_vals[xbg-1]+D*self.y2_vals[xbg]
        return y

    def __call__(self, x):
        "Simulate a ufunc. Either an array or a scalar may be passed"
        if isinstance(x,ndarray):
            return self.call(x)
        else:
            return self.call(array([x],'d'))[0]

    @staticmethod
    def getFromConfig(config,secName):
        assert isinstance(config,CustomConfigObj)
        f = []; a = []; i = []
        k = 0
        while True:
            if config.has_option(secName,'f%d' % (k,)):
                f.append(config.getfloat(secName,'f%d' % (k,)))
                if config.has_option(secName,'a%d' % (k,)):
                    a.append(config.getfloat(secName,'a%d' % (k,)))
                else:
                    raise ValueError("Spline %s has missing function value at index %d" % (secName,k))
                if config.has_option(secName,'i%d' % (k,)):
                    i.append(config.getfloat(secName,'i%d' % (k,)))
            else:
                break
            k += 1
        if len(i) == len(a):
            return CubicSpline(x_array=array(f,float_),y_array=array(a,float_),y2_array=array(i,float_))
        elif len(i) == 0:
            return CubicSpline(x_array=array(f,float_),y_array=array(a,float_))
        else:
            raise ValueError("Cubic spline configuration has inconsistent number of values and second derivatives")

    @staticmethod
    def getListFromConfig(config):
        """Read the splines in the specified configuration file and return the spline objects as a list"""
        assert isinstance(config,CustomConfigObj)
        k = 0
        splineList = []
        while True:
            secName = 'spline%d' % (k,)
            if config.has_section(secName):
                s = CubicSpline.getFromConfig(config,secName)
                s.name = config.get(secName,'d')
                splineList.append(s)
                k += 1
            else:
                break
        return splineList
################################################################################
# The model consists of a collection of functions and parameter values for
#  these functions
################################################################################

class Model(object):
    def __init__(self):
        self.pressure = 140
        self.temperature = 298
        self.dummyParameters = []
        self.parameters = None
        self.xModifier = None
        self.x_center = 0
        self.nParameters = 0
        self.funcList = []
        self.okToSet = ["pressure","temperature","x_center"]

    def setAttributes(self,**kwargs):
        for k in kwargs:
            if k in self.okToSet:
                setattr(self,k,kwargs[k])
            else:
                raise ValueError("Cannot set model attribute %s" % k)
    def addDummyParameter(self,value):
        self.dummyParameters.append((self.nParameters,value))
        self.nParameters += 1
    def addToModel(self,f,index):
        f.parent = self
        f.funcIndex = index
        nParams = f.numParams()
        f.setParamIndices(arange(self.nParameters,self.nParameters+nParams))
        self.nParameters += nParams
        self.funcList.append(f)
    def registerXmodifier(self,f):
        f.parent = self
        nParams = f.numParams()
        f.setParamIndices(arange(self.nParameters,self.nParameters+nParams))
        self.nParameters += nParams
        self.xModifier = f
    def createParamVector(self,initVals=None):
        # Set up the initial parameter vector, taking into account any initial values found in the
        #  InitialValues() object initVals
        self.parameters = zeros(self.nParameters,float_)
        for f in self.funcList:
            initDict = None
            if initVals is not None: initDict = initVals.ivDict.get(f.funcIndex,None)
            f.initializeModel(initDict)
        for d in self.dummyParameters:
            self.parameters[d[0]] = d[1]
        if self.xModifier is not None:
            self.xModifier.initializeModel()
        if initVals is not None:
            initDict = initVals.ivDict.get("base",None)
            if initDict is not None:
                for p in initDict:
                    self.parameters[p] = initDict[p]
    def __call__(self,x):
        y = zeros(shape(x),x.dtype)
        if len(x)>0:
            if self.xModifier is not None: x = self.xModifier(x)
            for f in self.funcList: y = y + f(x)
        return y

################################################################################
# Basis functions are summed together to produce a model spectrum
################################################################################
class BasisFunctions(object):
    """Base class of model functions which sum to form the mock spectrum. Instances of its subclasses
    can be evaluated at a set of frequencies to give the spectrum."""
    # The base class also :
    #  1) implements memoization for its subclasses to avoid unnecessary recomputations
    #  2) allows the subclass function to be called with a "useModifier" parameter, so that 
    #      any xModifier defined in the parent model is applied before evaluating the function
    def __init__(self):
        self.parent = None
        self.asaved = None
        self.xsaved = None
        self.ysaved = None
        self.funcIndex = None
        self.memoUsed = False
        self.useModifierSaved = None
    # The following is declared as a class method so that we can determine the number of parameters
    #  for any instance of a subclass of BasisFunctions without having to construct the instance first.
    #  For example Galatry.numParams() returns the number of parameters for the Galatry function.
    @classmethod
    def numParams(cls):
        return cls.nParams
    def setParamIndices(self,indices):
        self.paramIndices = indices
    def getCurrentParametersFromModel(self):
        return self.parent.parameters[self.paramIndices]
    def __call__(self,x,useModifier=False):
        # Actual computations are delegated to the call method of the subclass. The base class
        #  keeps track of past results in case the instance is called with the same parameters
        # Deal with scalar input
        if not iterable(x): return self.__call__(array([x],float_),useModifier)[0]
        a = self.parent.parameters[self.paramIndices]
        self.memoUsed = True
        if self.asaved is None or self.xsaved is None \
           or (self.asaved != a).any() \
           or len(self.xsaved)!=len(x) or (self.xsaved != x).any() \
           or useModifier \
           or useModifier != self.useModifierSaved:
            self.asaved = a.copy()
            self.xsaved = x.copy()
            if useModifier and self.parent != None and self.parent.xModifier is not None: 
                x = self.parent.xModifier(x)
            self.ysaved = self.call(a,x)
            self.memoUsed = False
            self.useModifierSaved = useModifier
        return self.ysaved
    # Following function copies initial conditions to the model. Override as necessary
    def initializeModel(self,initDict=None):
        self.parent.parameters[self.paramIndices] = self.initialParams
        if initDict is not None:
            for p in initDict:
                if not isinstance(p,int) or p < 0 or p >=self.numParams():
                    raise ValueError("Initial value index %s is invalid for class %s" % (p,type(self)))
                self.parent.parameters[self.paramIndices[p]] = initDict[p]

################################################################################
# Quadratic object for representing baseline
################################################################################
class Quadratic(BasisFunctions):
    nParams = 3
    name = "quadratic"
    def __init__(self,params=None,**kwargs):
        BasisFunctions.__init__(self)
        if params is not None:
            self.initialParams = params
        else:
            self.initialParams = array([kwargs["offset"],kwargs["slope"],kwargs["curvature"]],float_)
    def call(self,a,x):
        xs = x - self.parent.x_center
        return a[0] + a[1]*xs + a[2]*xs**2

################################################################################
# FrequencySquish for frequency offset and scale
################################################################################
class FrequencySquish(BasisFunctions):
    nParams = 2
    name = "frequency squish"
    def __init__(self,params=None,**kwargs):
        BasisFunctions.__init__(self)
        if params is not None:
            self.initialParams = params
        else:
            self.initialParams = array([kwargs["offset"],kwargs["squish"]],float_)
    def call(self,a,x):
        xs = x - self.parent.x_center
        return x + a[0] + a[1]*xs
################################################################################
# Sinusoid object for representing baseline
################################################################################
class Sinusoid(BasisFunctions):
    nParams = 4
    name = "sinusoid"
    def __init__(self,params=None,**kwargs):
        BasisFunctions.__init__(self)
        if params is not None:
            self.initialParams = params
        else:
            self.initialParams = array([kwargs["amplitude"],kwargs["center"],
                                        kwargs["period"],kwargs["phase"]],float_)
    def call(self,a,x):
        return a[0]*cos(2*pi*(x-a[1])/a[2] + a[3])
################################################################################
# Spline object
################################################################################
class Spline(BasisFunctions):
    nParams = 5
    name = "spline"
    def __init__(self,params=None,**kwargs):
        BasisFunctions.__init__(self)
        if params is not None:
            self.initialParams = params
        else:
            self.initialParams = array([kwargs["freqShift"],kwargs["baselineShift"],
                                        kwargs["amplitude"],kwargs["squishParam"],
                                        kwargs["squishCenter"]],float_)
        self.index = kwargs["splineIndex"]
        self.spline = splineLibrary.splineList[self.index]
    def call(self,a,x):
        xs = a[4] + (x-a[4])*(1. + 0.02*arctan(a[3]))
        return a[1] + a[2]*self.spline(xs - a[0])
    def getDomain(self):
        return self.spline.getDomain()
################################################################################
# Bispline object
################################################################################
class BiSpline(BasisFunctions):
    nParams = 7
    name = "bispline"
    def __init__(self,params=None,**kwargs):
        BasisFunctions.__init__(self)
        if params is not None:
            self.initialParams = params
        else:
            self.initialParams = array([kwargs["freqShift"],kwargs["baselineShift"],
                                        kwargs["amplitude"],kwargs["squishParam"],
                                        kwargs["squishCenter"],kwargs["yEffective"],
                                        kwargs["yMultiplier"]],float_)
        self.indexA = kwargs["splineIndexA"]
        self.indexB = kwargs["splineIndexB"]
        self.splineA = splineLibrary.splineList[self.indexA]
        self.splineB = splineLibrary.splineList[self.indexB]
    def call(self,a,x):
        xs = a[4] + (x-a[4])*(1. + 0.02*arctan(a[3]))
        sA = a[1] + a[2]*self.splineA(xs - a[0])
        sB = a[1] + a[2]*self.splineB(xs - a[0])
        wt = a[6]*(a[5]-1.0)
        return (1.0-wt)*sA + wt*sB
    def getDomain(self):
        xAmin,xAmax = self.splineA.getDomain()
        xBmin,xBmax = self.splineB.getDomain()
        return max(xAmin,xBmin),min(xAmax,xBmax)
    def getPeak(self,peakInterval=()):
        """Returns location and value of the peak of the bispline. If peakInterval is specified, it must be a
            tuple of min and max values (including effects of x-axis modification). """
        nTestPoints = 9
        if peakInterval == ():
            useModifier = False
            xmin,xmax = self.getDomain()
        else:
            useModifier = True
            xmin,xmax = peakInterval
        x = linspace(xmin,xmax,nTestPoints)
        y = self(x,useModifier)
        a = self.getCurrentParametersFromModel()
        # Find minimum if a[2]<0 and maximum if a[2]>0
        if a[2]>0:
            ix = argmax(y)
            if ix==0 or ix==nTestPoints-1:
                Log('Maximum of bispline is not in interior of domain')
                return x[ix],y[ix]
            xmin = brent(lambda x: -self(x,useModifier),brack=(x[ix-1],x[ix],x[ix+1]))
        elif a[2]<0:
            ix = argmin(y)
            if ix==0 or ix==nTestPoints-1:
                Log('Minimum of bispline is not in interior of domain')
                return x[ix],y[ix]
            xmin = brent(lambda x: self(x,useModifier),brack=(x[ix-1],x[ix],x[ix+1]))
        else:
            xmin = x[0]
        return xmin,self(xmin,useModifier)
################################################################################
# Galatry object
################################################################################
class Galatry(BasisFunctions):
    nParams = 5
    name = "galatry"
    def __init__(self,params=None,**kwargs):
        BasisFunctions.__init__(self)
        if params is not None:
            self.initialParams = params
        elif "peakNum" in kwargs:
            self.peakNum = int(kwargs["peakNum"])
            name,self.mass,center,scaled_strength,scaled_y,scaled_z,v,species = spectralLibrary.peakDict[self.peakNum]
            self.initialParams = array([center,scaled_strength,scaled_y,scaled_z,v],float_)
        else:
            self.initialParams = array([kwargs["center"],kwargs["scaled_strength"],
                                        kwargs["scaled_y"],kwargs["scaled_z"],kwargs["v"]],float_)
            self.mass = float(kwargs["mass"])
        self.base = None
        self.peak = None
    def getPeakAndBase(self):
        """Calculate the peak and baseline for this Galatry peak using the parameter values from the
        current model (which is the parent of  this object)"""
        if self.peak is None:
            center = array([self.parent.parameters[self.paramIndices[0]]],float_)
            peak = self(center)[0]
            y = 0.0
            for g in self.parent.funcList:
                if g != self: y = y + g(center)
            base = y[0]
            self.peak, self.base = peak, base
        return (self.peak,self.base)
    def call(self,a,x):
        self.peak = None
        return a[1]*galatry((x-a[0])/a[4],a[2],a[3],a[1])
    # For the Galatry, the model initial conditions are derived from self.initialParams
    #  together with the physical conditions of the cavity
    def initializeModel(self,initDict=None):
        kB = physicalConstants["k"]
        c =  physicalConstants["c"]
        amu = physicalConstants["amu"]
        params = array(self.initialParams)
        if initDict is not None: # Handle scaled initial conditions
            for p in initDict:
                if p in galDict2:
                    params[galDict2[p]] = initDict[p]
        params[1] = params[1]*self.parent.pressure # Need to multiply by concentration, if specified
        params[2] = params[2]*self.parent.pressure
        params[3] = params[3]*self.parent.pressure
        if params[4]<=0:
            params[4] = sqrt(2*kB*self.parent.temperature/((self.mass*amu)*c**2))*params[0]
        if initDict is not None: # Handle unscaled initial conditions
            for p in initDict:
                if isinstance(p,int):
                    if p < 0 or p >=self.numParams():
                        raise ValueError("Initial value index %s is invalid for class %s" % (p,type(self)))
                    else:
                        params[p] = initDict[p]
        self.parent.parameters[self.paramIndices] = params

################################################################################
# Class for initial value specifications
################################################################################
class InitialValues(object):
    def __init__(self):
        self.ivDict = {}
    def __setitem__(self,key,value):
        class1,class2,key1,key2,extra = classifyKeyTuple(key)
        if class2 == 3: key2 = galDict1[key2] # Translate unscaled peak values to integer indices
        if (class1 == 0 and class2 in [1,3,4]) or (class1 == 1 and class2 == 1) or (class1 == 2 and class2 == 1):
            if key1 not in self.ivDict:
                self.ivDict[key1] = {}
            if value is None:
                try:
                    del self.ivDict[key1][key2]
                    if not self.ivDict[key1]:
                        del self.ivDict[key1]
                except:
                    pass
            else:
                self.ivDict[key1][key2] = value
        else:
            raise ClassifyError("Invalid keyTuple for an initial value: %s" % (key,))
    def clear(self):
        self.ivDict.clear()
################################################################################
# Class for specifying variable dependencies
################################################################################
class Dependencies(object):
    """ Dependencies defined in script files are stored in a dictionary keyed by the destination
    key tuple. The entries contain the source key tuple, the slope and the offset. """
    def __init__(self):
        self.depDict = {}
    def setDep(self,keyDest,keySource,slope,offset):
        class1d, class2d, key1d, key2d, extra = classifyKeyTuple(keyDest)
        if class2d == 3: key2d = galDict1[key2d] # Translate unscaled peak values to integer indices
        class1s, class2s, key1s, key2s, extra = classifyKeyTuple(keySource)
        if class2s == 3: key2s = galDict1[key2s] # Translate unscaled peak values to integer indices
        keyDestOk = (class1d == 0 and class2d in [1,3]) or (class1d == 1 and class2d == 1) or (class1d == 2 and class2d == 1)
        keySourceOk = (class1s == 0 and class2s in [1,3]) or (class1s == 1 and class2s == 1) or (class1s == 2 and class2s == 1)
        if not keyDestOk:
            raise ValueError("Invalid keyTuple for destination dependency: %s" % (keyDest,))
        if not keySourceOk:
            raise ValueError("Invalid keyTuple for source dependency: %s" % (keySource,))
        self.depDict[(key1d,key2d)] = (key1s,key2s,slope,offset)
    def clear(self, keyDest=None):
        if keyDest is None:
            self.depDict.clear()
        else:
            class1d, class2d, key1d, key2d, extra = classifyKeyTuple(keyDest)
            if class2d == 3: key2d = galDict1[key2d] # Translate unscaled peak values to integer indices
            try:
                del self.depDict[(key1d,key2d)]
            except:
                pass
################################################################################
# RdfData objects contain ringdown data for a single spectrum
################################################################################
class RdfData(object):
    _pacing = {}
    def __init__(self):
        """An RdfData object is essentially just a bunch of dynamically created attributes for holding
        ringdown data. 
        
            self.rdfKeys holds the list of dynamic attribute names
            self.sensorDict is a dictionary of averaged sensor data
            self.indexVector is used for selection and permutation so that we can sort and filter the data
            self.nrows    }
            self.startRow } count ringdown rows in HDF5 file for display in fit viewer
            self.endRow   }
        """
        # filterHistory is a list of tuples (filterName,pointsRemoved,pointsRemaining) containing a record of
        #  what filters have been applied to the data
        self.filterHistory = []
        self.rdfKeys = []
        self.indexVector = []
        self.nrows = 0
        self.sensorDict = {}
        
    def merge(self,rdfDataList):
        """Make a composite RdfData object from the current object and those in rdfDataList. We check
        that they are all compatible in the sense of having the same rdfKeys and sensorDict.
        
        The numpy concatenate function is used to join the corresponding arrays in rdfDataList. 
        The keys in the sensorDicts are averaged together, weighted according to the number of 
        rows in each RdfData object.
        
        indexVector is set to select all the data in natural order
        nrows is set to the sum of the rows of the original object and those in the list
        """
        sensorKeys = sorted(self.sensorDict.keys())
        for d in rdfDataList:
            if not self.rdfKeys:
                self.rdfKeys = d.rdfKeys[:]
            else:
                if self.rdfKeys != d.rdfKeys:
                    raise ValueError("Cannot merge RdfData objects with incompatible keys")
            if not sensorKeys:
                sensorKeys = sorted(d.sensorDict.keys())
            else:
                s = sorted(d.sensorDict.keys())
                if sensorKeys != s:
                    raise ValueError("Cannot merge RdfData objects with incompatible sensorDicts")
        for k in self.rdfKeys:
            try:
                aList = [getattr(self,k)]
            except AttributeError:
                aList = []
            aList += [getattr(d,k) for d in rdfDataList]
            object.__setattr__(self, k, concatenate(aList))
                    
        if self.sensorDict:
            for k in sensorKeys:
                self.sensorDict[k] *= self.nrows

        for d in rdfDataList:
            for k in sensorKeys:
                self.sensorDict[k] = d.nrows * d.sensorDict[k] + self.sensorDict.get(k,0.0)
            self.nrows += d.nrows

        for k in sensorKeys:
            self.sensorDict[k] /= self.nrows
            
        self.indexVector = arange(self.nrows)
        self.startRow = 0
        self.endRow = self.nrows
        
    @staticmethod
    def getSpectraDict(rdfDict):
        """Generates individual spectra (in RdfData() format) from a dictionary with keys 
        "rdData", "sensorData" and optionally "controlData" and "tagalongData". 
        
        rdfDict["controlData"] is typically a numpy record array with a field "RDDataSize"
        which indicates how the rows of rdfDict["rdData"] are to be divided into "chunks" 
        containing individual spectra. 
        
        """
        rdData = rdfDict["rdData"]
        otherData = rdfDict["sensorData"]
        if "tagalongData" in rdfDict: 
            otherData.update(rdfDict["tagalongData"])
        try:
            controlData = rdfDict["controlData"]
            # Experimental pacing algorithm for fitter
            rdChunkSizes = controlData["RDDataSize"]
            qSizes = controlData["SpectrumQueueSize"]
        except:
            rdChunkSizes = [len(rdData["waveNumber"])]
            qSizes = [0]
            
        RED_THRESHOLD = 100
        RED_DISCARD_ALL = 200

        def allowYield(pace,id):
            if id in RdfData._pacing:
                RdfData._pacing[id] += pace
            else:
                RdfData._pacing[id] = pace
            if RdfData._pacing[id] >= 1.0:
                RdfData._pacing[id] -= 1.0
                return True
            else:
                return False

        # Split file into chunks according to information in controlData table
        start = 0
        for i,rdChunkSize in enumerate(rdChunkSizes):
            if rdChunkSize == 0:
                continue
            otherDataForChunk = {}
            for key in otherData:
                otherDataForChunk[key] = otherData[key][i]
                
            # Returns an RdfData object from ringdown data between indices low and high
            def makeRdfData(low,high):
                rdfData = RdfData()
                rdfData.sensorDict = otherDataForChunk
                # Store ringdown data for current section as attributes of the RdfData object
                rdfData.rdfKeys = sorted(rdData.keys())
                for s in rdfData.rdfKeys:
                    object.__setattr__(rdfData, s, rdData[s][low:high])
                # Initialize indexVector to the identity permutation to indicate that
                #  all data are (initially) good
                rdfData.nrows = len(rdData[s][low:high])
                rdfData.indexVector = arange(rdfData.nrows)
                # Set the average time of the sensor data
                rdfData.avgSpectrumTime = unixTime(mean(rdfData.timestamp))
                rdfData.startRow = low
                rdfData.endRow = high
                return rdfData

            pace = min(1.0,float(RED_DISCARD_ALL-qSizes[i])/(RED_DISCARD_ALL-RED_THRESHOLD))
            # Split spectra further according to subfield of the subschemeId
            low = start
            high = start + rdChunkSize
            
            splits = flatnonzero(diff(rdData["subschemeId"][low:high] & 0x3FF))
            for s in splits:
                id = rdData["subschemeId"][low] & 0x3FF
                if allowYield(pace,id):
                    yield makeRdfData(low,start+s+1)
                low = start+s+1
            id = rdData["subschemeId"][low] & 0x3FF
            if allowYield(pace,id):
                yield makeRdfData(low,high)
            start = high

    def getTime(self):
        """Returns the averaged time of a spectrum"""
        return self.avgSpectrumTime

    """Container for holding ringdown data associated with a single spectrum"""
    def pickledRead(self,fp):
        """Reads a pickled dictionary containing ringdown information"""
        s = fp.read()
        self.sensorDict = cPickle.loads(s)
        self.rdfKeys = sorted(self.sensorDict.keys())
        for s in self.rdfKeys:
            object.__setattr__(self, s, self.sensorDict[s])
        fp.close()
        # Initialize indexVector to the identity permutation to indicate that
        #  all data are (initially) good
        self.nrows = len(self.time)
        self.indexVector = arange(self.nrows)
        return self
        
    def __getitem__(self,key):
        # Use item notation to recover certain properties of a data set for use in scripting
        try:
            if key.lower() == "cavitypressure": return float(mean(self.cavityPressure))
            elif key.lower() == "cavitytemperature": return self.sensorDict["CavityTemp"]
            elif key.lower() == "datapoints": return len(self.indexVector)
            elif key.lower() == "spectrumid": return self.sensorDict["SpectrumID"]
            elif key.lower() == "filterhistory": return self.filterHistory
            elif key.lower() == "numgroups": return len(self.groups)
            else:
                raise KeyError("Unknown item for RdfData()")
        except:
            return None
    def defineFitData(self,freq,loss,sdev):
        self.fitData = dict(freq=freq,loss=loss,sdev=sdev)
    def sortBy(self,field):
        # Change the index vector so that the data are now sorted by the specified field
        #  For example data.sortBy("waveNumber") will reorder the currently selected
        #  points in data so that the waveNumbers are in ascending order.
        x = getattr(self,field)
        perm = argsort(x[self.indexVector])
        self.indexVector = self.indexVector[perm]
    def filterByScalar(self,fields,sPredicate,name="Anonymous filter"):
        # Convenience wrapper for filterBy for use with scalar predicates
        self.filterBy(fields,frompyfunc(sPredicate,len(fields),1),name)
    def filterBy(self,fields,uPredicate,name="Anonymous filter"):
        # Change the index vector so that the data only contain points for which the predicate
        #  (specified as a numpy ufunc) evaluates to True. "fields" is a list of fields which
        #  are passed to the successive input arguments of uPredicate. For example if we define
        #
        # def pred(x,y):
        #    return numpy.logical_and(x<56000.0,y>6547.0)
        #
        # data.filterBy(['tunerValue','waveNumber'],pred)
        #  will change the indexVector so that only data for which
        #  data.tunerValue<56000 and waveNumber>6547.0 are selected
        args = [getattr(self,field)[self.indexVector] for field in fields]
        sel = flatnonzero(uPredicate(*args))
        nStart = len(self.indexVector)
        self.indexVector = self.indexVector[sel]
        nEnd = len(self.indexVector)
        self.filterHistory.append((name,nStart-nEnd,nEnd))
    def groupBy(self,fields,aggregator):
        # Pass the specified collection of data fields to an aggregator function which
        #  defines a collection of "groups" which is a list of index arrays. These indices
        #  within these groups are translated back to the original data indices via the
        #  current self.indexVector and stored in self.groups
        args = [getattr(self,field)[self.indexVector] for field in fields]
        localGroups = aggregator(*args)
        self.groups = [self.indexVector[g] for g in localGroups]
    def evaluateGroups(self,fields):
        """Create grouped data from the data columns and self.groups.
        The dictionaries self.groupMeans and self.groupStdDevs contain the grouped data, with
        keys given by the field names. self.groupSizes is filled with the sizes of the groups
        """
        self.groupMeans = {}
        self.groupMedians = {}
        self.groupStdDevs = {}
        self.groupPtp = {}
        self.groupSizes = array(map(len,self.groups))
        for field in fields:
            x = getattr(self,field)
            self.groupMeans[field] = array([mean(x[g]) for g in self.groups])
            self.groupMedians[field] = array([median(x[g]) for g in self.groups])
            self.groupStdDevs[field] = array([std(x[g]) for g in self.groups])
            self.groupPtp[field] = array([ptp(x[g]) for g in self.groups])
##  14 June 2010  added modified sigma filter named "outlierFilter            
    def sparse(self,maxPoints,width,height,xColumn,yColumn,sigmaThreshold=-1,outlierThreshold=-1):
        """Sparse the ringdown data by binning the data specified by "xColumn" and
        "yColumn" into rectangles of maximum dimensions "width" by "height",
        with no more than "maxPoints" data in each bin. A sigma filter
        with the specified "sigmaThreshold" or outlier filter with specified
        "outlierThreshold" is applied to the y values in each bin.
        Returns a list of bins, each specified by an array of indices of points
        within the bin.
        """
        height = 0.001*height # Convert from ppb/cm to ppm/cm

        def sparseAgg(xx,yy):
            """This is the aggregator function, curried with the input arguments to sparse
            which needs to be passed to groupBy"""
            groups = []
            if len(xx)==0: return groups
            for i in range(len(xx)):
                x = xx[i]; y = yy[i]
                if i>0:
                    # A group consists of points within a rectangle
                    if nPoints<maxPoints:
                        ymin = min(ymin,y); ymax = max(ymax,y)
                        if x-xmin <= width and ymax-ymin <= height:
                            g.append(i)
                            nPoints += 1
                            continue
                    # We need to start a new group, close off the previous one and apply
                    #  the sigma filter
                    g = array(g)
                    if outlierThreshold < 0:
                        sel = flatnonzero(sigmaFilter(yy[g],sigmaThreshold)[0])
                    else:
                        sel = flatnonzero(outlierFilter(yy[g],outlierThreshold)[0])
                    groups.append(g[sel])
                g = [i]
                xmin = x
                ymin = ymax = y
                nPoints = 1
            # Finish off the last group, if non-empty
            if len(g)>0:
                g = array(g)
                if outlierThreshold < 0:
                    sel = flatnonzero(sigmaFilter(yy[g],sigmaThreshold)[0])
                else:
                    sel = flatnonzero(outlierFilter(yy[g],outlierThreshold)[0])
                groups.append(g[sel])
                groups.append(g[sel])
            return groups
        # end of sparseAgg
        self.sortBy(xColumn)
        self.groupBy([xColumn,yColumn],sparseAgg)
        # Calculate number of points removed by sparse filter
        nStart = len(self.indexVector)
        nEnd = sum([len(g) for g in self.groups])
        self.filterHistory.append(("sparseFilter",nStart-nEnd,nEnd))
    
    def calcGroupStats(self):
        self.evaluateGroups(["waveNumber","uncorrectedAbsorbance","waveNumberSetpoint","pztValue","ratio1","ratio2","wlmAngle","laserTemperature"])
        self.groupStats = {}
        pztArray = asarray(self.groupMeans["pztValue"])
        sizeArray = asarray(self.groupSizes)
        ensemblePzt = dot(pztArray, sizeArray)/(1e-10+sum(sizeArray))
        for idx,key in enumerate(self.groupMeans["waveNumber"]):
            self.groupStats[key] = dict(freq_mean=self.groupMeans["waveNumber"][idx],
                                   freq_stddev=self.groupStdDevs["waveNumber"][idx],
                                   uLoss_mean=self.groupMeans["uncorrectedAbsorbance"][idx],
                                   uLoss_stddev=self.groupStdDevs["uncorrectedAbsorbance"][idx],
                                   pzt_mean=self.groupMeans["pztValue"][idx],
                                   pzt_stddev=self.groupStdDevs["pztValue"][idx],
                                   ratio1_mean=self.groupMeans["ratio1"][idx],
                                   ratio1_stddev=self.groupStdDevs["ratio1"][idx],
                                   ratio2_mean=self.groupMeans["ratio2"][idx],
                                   ratio2_stddev=self.groupStdDevs["ratio2"][idx],
                                   wlm_angle_mean=self.groupMeans["wlmAngle"][idx],
                                   wlm_angle_stddev=self.groupStdDevs["wlmAngle"][idx],
                                   laser_temperature_mean=self.groupMeans["laserTemperature"][idx],
                                   laser_temperature_stddev=self.groupStdDevs["laserTemperature"][idx],
                                   setpoint_mean = self.groupMeans["waveNumberSetpoint"][idx],
                                   target_error = self.groupMeans["waveNumber"][idx] - key,
                                   pzt_ensemble_offset = self.groupMeans["pztValue"][idx] - ensemblePzt,
                                   group_size = self.groupSizes[idx]
                                   )
            
    def selectGroupStats(self, nameWaveNumList):
        """
        nameWaveNumList = [(name, waveNum), ...]
        """
        keys = self.groupStats.keys()
        results = {}
        for name, waveNum in nameWaveNumList:
            closestKey = keys[argmin(abs(waveNum-asarray(keys)))]
            closestGroupStats = self.groupStats[closestKey]
            for key in closestGroupStats:
                results[name+"_"+key] = closestGroupStats[key]
        return results
    
    def calcSpectrumStats(self):
        ringdownsInSpectrum = unique(concatenate([s for s in self.groups]))
        ringdownsInSpectrum = ringdownsInSpectrum[self.uncorrectedAbsorbance[ringdownsInSpectrum] != 0.0]
        self.spectrumStats = {}
        self.spectrumStats["ss_num_ringdowns"] = len(ringdownsInSpectrum)
        self.spectrumStats["ss_duration"] = ptp(self.timestamp[ringdownsInSpectrum])*0.001
        s = (self.correctedAbsorbance - self.uncorrectedAbsorbance)[ringdownsInSpectrum]
        self.spectrumStats["ss_loss_diff_mean"] = mean(s)
        self.spectrumStats["ss_loss_diff_stddev"] = std(s)
        s = self.pztValue[ringdownsInSpectrum]
        self.spectrumStats["ss_pzt_mean"] = mean(s)
        self.spectrumStats["ss_pzt_stddev"] = std(s)
        s = self.fineLaserCurrent[ringdownsInSpectrum]
        self.spectrumStats["ss_fine_current_mean"] = mean(s)
        self.spectrumStats["ss_fine_current_min"] = min(s)
        self.spectrumStats["ss_fine_current_max"] = max(s)
        s = (self.waveNumber - self.waveNumberSetpoint)[ringdownsInSpectrum]
        self.spectrumStats["ss_target_error_mean"] = mean(s)
        self.spectrumStats["ss_target_error_stddev"] = std(s)
        s = self.groupMeans["waveNumber"] - self.groupMeans["waveNumberSetpoint"]
        self.spectrumStats["ss_group_target_error_slope"] = polyfit(self.groupMeans["waveNumber"], s, 1)[0]
        self.spectrumStats["ss_group_target_error_stddev"] = std(s)
        s = self.groupMeans["pztValue"]
        self.spectrumStats["ss_group_pzt_slope"] = polyfit(self.groupMeans["waveNumber"], s, 1)[0]
        self.spectrumStats["ss_group_pzt_stddev"] = std(s)
        
    def getSpectrumStats(self):
        return self.spectrumStats
        
    def badRingdownFilter(self,fieldName,minVal=0.50,maxVal=20.0):
        """Remove entries whose "field" value lies outside the specified range"""
        def goodValue(x):
            return (x>=minVal) & (x<=maxVal)
        self.filterBy([fieldName],goodValue,name="badRingdownFilter")
    def wlmSetpointFilter(self,maxDev=0.005,sigmaThreshold=10):
        """Remove data in which the difference between wavelength setpoint and measurement
        exceeds the specified bounds"""
        def goodWlmData1(x,y):
            wlmError = x-y
            return abs(wlmError) <= maxDev
        def goodWlmData2(x,y):
            wlmError = x-y
            return sigmaFilterMedian(wlmError,sigmaThreshold)[0]
        self.filterBy(["waveNumber","waveNumberSetpoint"],goodWlmData1,name="wlmSetpointFilter_1")
        self.filterBy(["waveNumber","waveNumberSetpoint"],goodWlmData2,name="wlmSetpointFilter_2")
    def tunerEnsembleFilter(self,maxDev=500000,sigmaThreshold=100):
        """Remove data for which the tuner value differs from the median of all tuner values
        by more than maxDev and apply a median sigma filter to the result"""
        def goodTunerData1(x):
            return abs(x-median(x)) <= maxDev
        def goodTunerData2(x):
            return sigmaFilterMedian(x,sigmaThreshold)[0]
        self.filterBy(["tunerValue"],goodTunerData1,name="tunerEnsembleFilter_1")
        self.filterBy(["tunerValue"],goodTunerData2,name="tunerEnsembleFilter_2")
################################################################################
# Analysis objects wrap calls to the Levenberg-Marquardt fitter
################################################################################
class Analysis(object):
    """An analysis is defined by a FitINI file. It contains:
    A definition of the region(s) to fit and the peaks from the spectral library to use,
    A sequence of fits to apply the Levenberg Marquardt algorithm to,
    Which variables to vary, and dependency lists for each LM fit,
    A collection of special functions (other than peaks) to use in the objective function
    """
    index = 0
    @staticmethod
    def resetIndex():
        """Resets class variable index to zero"""
        Analysis.index = 0

    def __init__(self,fnameOrConfig,name=None):
        if not isinstance(fnameOrConfig,CustomConfigObj):
            fnameOrConfig = readConfig(fnameOrConfig)
        self.config = fnameOrConfig
        self.serialNumber = Analysis.index
        if name is None:
            self.name = "analysis_%d" % (Analysis.index,)
        else:
            self.name = name
        Analysis.index += 1
        self.regionStart = []
        self.regionEnd = []
        self.basisFunctionByIndex = {}
        self.centerFrequency = None
        self.regionName = None
        self.fitSequenceParameters = []
        section = "Region Fit Definitions"
        for k in range(self.config.getint(section,"number of sections")):
            self.regionStart.append(self.config.getfloat(section,"Start frequency_%d" % k))
            self.regionEnd.append(self.config.getfloat(section,"End frequency_%d" % k))

        self.nPeaks = self.config.getint(section,"number of peaks")
        peakId = self.config.get(section,"peak identification")
        if peakId.strip() != "":
            self.basisArray = array([int(p) for p in peakId.split(",")])
        else:
            self.basisArray = array([],int_)
        if ((self.basisArray[:self.nPeaks] < 0) & (self.basisArray[:self.nPeaks] > 1000)).any():
            raise ValueError("The first %d elements of the peak identification list must be between 0 and 999" % \
                             (self.nPeaks,))
        if (self.basisArray[self.nPeaks:] < 1000).any():
            raise ValueError("Elements %d and above of the peak identification list must be 1000 or larger" % \
                             (self.nPeaks,))

        self.centerFrequency = self.config.getfloat(section,"center frequency")
        self.regionName = self.config.get(section,"region fit name")
        #
        # Process fit sequence
        section = "Fit Sequence Parameters"
        fitSeqIndex = 0
        while True:
            try:
                #passToNext = self.config.getboolean(section,"passtonext_%d" % (fitSeqIndex,))
                #subtractFromData = self.config.getboolean(section,"subtract_from_data_%d" % (fitSeqIndex,))
                useFine = self.config.getboolean(section,"use fine?%d" % (fitSeqIndex,))
            except KeyError:
                break
            #self.fitSequenceParameters.append(dict(passToNext=passToNext,subtractFromData=subtractFromData,useFine=useFine))
            self.fitSequenceParameters.append(dict(useFine=useFine))
            fitSeqIndex += 1
        #
        for k in range(fitSeqIndex):
            section = "DS%d" % (k,)
            variables = flatnonzero(array(map(int,self.config.get(section,"vary coefficients").split(","))))
            self.fitSequenceParameters[k]["variables"] = variables
            depList = []
            depIndex = 0
            while True:
                try:
                    depList.append(self.config.get(section,"dependency%d" % (depIndex,)).split(","))
                except KeyError:
                    break
                depIndex += 1
            self.fitSequenceParameters[k]["depSrc"] = [int(d[0]) for d in depList]
            self.fitSequenceParameters[k]["depDest"] = [int(d[1]) for d in depList]
            self.fitSequenceParameters[k]["depSlope"] = [float(d[2]) for d in depList]
            self.fitSequenceParameters[k]["depOffset"] = [float(d[3]) for d in depList]
        #
        # Go through basisArray to assemble the dictionary basisFunctionByIndex
        #
        for i in self.basisArray:
            if i<1000:
                self.basisFunctionByIndex[i] = Galatry(peakNum=i)
            else: # We need to read details of the basis function from the file
                section = "function%d" % i
                # Local function to construct a basis function with parameters "a%d" from the ini file
                def FP(basisFunc,extra={}):
                    nParams = basisFunc.numParams()
                    a = []
                    for j in range(nParams): a.append(self.config.getfloat(section,"a%d" % j))
                    return basisFunc(params=array(a,float_),**extra)

                form = self.config.get(section,"functional_form")
                if form == "sinusoid":
                    self.basisFunctionByIndex[i] = FP(Sinusoid)
                elif form[:6] == "spline":
                    self.basisFunctionByIndex[i] = FP(Spline,dict(splineIndex=int(form[6:])))
                elif form[:8] == "bispline":
                    ndx = form[8:].split("_")
                    self.basisFunctionByIndex[i] = FP(BiSpline,dict(splineIndexA=int(ndx[0]),
                                                                    splineIndexB=int(ndx[1])))
                else:
                    raise ValueError("Unimplemented functional form: %s" % form)

        # We now construct the model
        m = Model()
        m.setAttributes(x_center=self.centerFrequency)
        m.addToModel(Quadratic(offset=0.0,slope=0.0,curvature=0.0),index=None)
        m.registerXmodifier(FrequencySquish(offset=0.0,squish=0.0))
        m.addDummyParameter(self.nPeaks)
        for f,i in [(self.basisFunctionByIndex[i],i) for i in self.basisArray]:
            m.addToModel(f,index=i)
        self.model = m
    def __getstate__(self):
        """Remove self.config from deepcopy() dictionary to avoid errors"""
        odict = self.__dict__.copy()
        del odict['config']
        return odict
        
    def setData(self,xx,yy,stdDev):
        """Specify the data which are to be fitted. Only the points within the fit regions are used"""
        selected = zeros(shape(xx),bool_)
        for s,e in zip(self.regionStart,self.regionEnd):
            selected = selected | ((xx>=s) & (xx<=e))
        self.xData = xx[selected]
        self.yData = yy[selected]
        self.weight = 1/(stdDev[selected])
    def processDeps(self,seqIndex,deps):
        dlist = []
        slist = []
        c1list = []
        c2list = []
        if deps is not None:
            for key1d,key2d in deps.depDict:
                key1s,key2s,slope,offset = deps.depDict[(key1d,key2d)]
                if key1d == "base": dlist.append(key2d)
                else:
                    f = self.basisFunctionByIndex[key1d]
                    if key2d >= f.numParams():
                        raise ValueError("Function %s does not have parameter %s in dependency list" % (type(f),key2d))
                    else:
                        dlist.append(f.paramIndices[key2d])
                if key1s == "base": slist.append(key2s)
                else:
                    f = self.basisFunctionByIndex[key1s]
                    if key2s >= f.numParams():
                        raise ValueError("Function %s does not have parameter %s in dependency list" % (type(f),key2s))
                    else:
                        slist.append(f.paramIndices[key2s])
                c1list.append(slope)
                c2list.append(offset)
        fitSeqPar = self.fitSequenceParameters[seqIndex]
        v = fitSeqPar["variables"]
        d = array(fitSeqPar["depDest"] + dlist)
        s = array(fitSeqPar["depSrc"] + slist)
        c1 = array(fitSeqPar["depSlope"] + c1list)
        c2 = array(fitSeqPar["depOffset"] + c2list)
        return v,d,s,c1,c2
    def doFit(self,seqIndex,fine=True):
        """Carry out a fit using the dependency information specified by seqIndex and self.deps
        Return the fitted parameters. """
        deps = self.deps
        m = self.model
        v,d,s,c1,c2 = self.processDeps(seqIndex,deps)
        p0 = m.parameters[v]
        self.pscale = ones(p0.shape,dtype=float_)
        self.poffset = p0
        #self.poffset = zeros(p0.shape,dtype=float_)
        #freqVar = abs(p0-self.centerFrequency) < 10.0
        #self.poffset[freqVar] = self.centerFrequency
        # Normalize parameters for benefit of fitter
        def normalize(p):
            return self.pscale*(p-self.poffset)
        def unnormalize(q):
            return self.poffset+(q/self.pscale)
        # Objective function whose sum-of-squares is minimized
        def fitfunc(q):
            p = unnormalize(q)
            # print "Fitfunc parameters: ",p
            m.parameters[v] = p
            if len(s)>0: m.parameters[d] = c1*m.parameters[s]+c2
            return self.weight*(self.yData-m(self.xData))
        # Compute residuals between fitted model and data
        def fitres(p):
            m.parameters[v] = p
            if len(s)>0: m.parameters[d] = c1*m.parameters[s]+c2
            return self.yData-m(self.xData)
        try:
            if fine:
                #params, self.ier = leastsq(fitfunc,p0,xtol=1e-4,epsfcn=1e-11)
                qparams, cov, infodict, msg, self.ier = leastsq(fitfunc,normalize(p0),full_output=1,xtol=1e-4,epsfcn=1e-6,maxfev=30*len(p0))
            else:
                #params, self.ier = leastsq(fitfunc,p0,ftol=1e-3,xtol=1e-3,epsfcn=1e-11)
                qparams, cov, infodict, msg, self.ier = leastsq(fitfunc,normalize(p0),full_output=1,ftol=1e-3,xtol=1e-3,epsfcn=1e-6,maxfev=30*len(p0))
            params = unnormalize(qparams)
            # print "Leastsq problem size: %d, function evaluations: %d" % (len(p0),infodict['nfev'])
        except TypeError:
            params = p0
            tbmsg = traceback.format_exc()
            Log('Exception in leastsq',Verbose=tbmsg)
            print tbmsg
        # print "Best fit parameters: ",params
        self.objective = sum(fitfunc(normalize(params))**2)
        self.res = fitres(params)
        # Return a copy since parameters will change between stages of fitting
        return copy(m.parameters)
    def mockData(self,seqIndex,x):
        # Compute mock data associated with a stage within the fitting.
        self.model.parameters = self.parameters[seqIndex]
        return self.model(x)
    def computeResiduals(self,seqIndex):
        x = self.xData
        self.res = self.yData - self.mockData(seqIndex,x)
    def nSteps(self):
        """Returns number of fitting steps in analysis"""
        return len(self.fitSequenceParameters)

    def __call__(self,dList,initVals=None,deps=None):
        """Run the specified analysis on the RdfData object or on a list of RdfData objects.
        For a list of objects, all of the data are combined before analysis takes place.
        We take into account the dependencies and initial values which override the defaults from 
        the spectral library and .ini files.
        Returns "self", the Analysis object"""
        # print "Analysis %d call" % id(self)
        self.initVals = initVals
        self.deps = deps
        if not isinstance(dList,list): dList = [dList]
        nPoints = sum([len(d.timestamp) for d in dList])
        self.time = unixTime(sum([sum(d.timestamp) for d in dList])/nPoints)
        pressure = sum([sum(d.cavityPressure) for d in dList])/nPoints
        temperature = 273.15 + mean([d["cavityTemperature"] for d in dList])
        freq = concatenate([d.fitData["freq"] for d in dList])
        loss = concatenate([d.fitData["loss"] for d in dList])
        sdev = concatenate([d.fitData["sdev"] for d in dList])
        perm = argsort(freq)
        self.setData(freq[perm],loss[perm],sdev[perm])
        self.model.setAttributes(pressure=pressure, temperature=temperature)
        self.model.createParamVector(self.initVals)
        self.parameters = []
        for seqIndex in range(len(self.fitSequenceParameters)):
            fitSeqPar = self.fitSequenceParameters[seqIndex]
            self.parameters.append(self.doFit(seqIndex,fine=fitSeqPar["useFine"]))
            # print sum(self.res**2)
        return self
    def __getitem__(self,key):
        """We use index notation to extract the values of various fit parameters. If the first
        index is an integer, it represents a function within the basisFunctionByIndex dictionary
        For example self[17,3] returns the a3 parameter of basisFunctionByIndex[17]. For Galatry peaks
        (first index from 0 through 999), the following special names are recognized for the second
        index:

        "peak":            height of the peak, evaluated at the line center
        "base":            contributions of all other functions under the peak
        "center":          synonym for 0, the center wavenumber of the peak
        "strength":        synonym for 1, the strength of the peak
        "y":               synonym for 2, the y parameter at the given pressure
        "z":               synonym for 3, the z parameter at the given pressure
        "v":               synonym for 4, the Doppler factor, at the given temperature
        "scaled_strength": strength divided by the pressure
        "scaled_y":        the y parameter divided by the pressure
        "scaled_z":        the z parameter divided by the pressure

        For bispline functions, the second index can also be the string "peak". This returns the peak value of the bispline.

        If the first parameter is the string "base", simply return the model parameter with the index
         given by the second parameter.
        """
        m = self.model
        class1, class2, key1, key2, extra = classifyKeyTuple(key)
        if class1 == 0: # We have a function between 0 and 999
            f = self.basisFunctionByIndex[key1]
            if class2 == 1: # This is a particular index
                if key2>=f.numParams():
                    raise ValueError("Function %d of type %s has only %d parameters" % (funcIndex,type(f),f.numParams()))
                return m.parameters[f.paramIndices[key2]]
            elif class2 == 2: # This is "peak" or "base"
                return f.getPeakAndBase()[galDict0[key2]]
            elif class2 == 3: # This is "center", "strength", "y", "z" or "v"
                return m.parameters[f.paramIndices[galDict1[key2]]]
            elif class2 == 4: # This is "scaled_strength", "scaled_y" or "scaled_z"
                return m.parameters[f.paramIndices[galDict2[key2]]]/m.pressure
        elif class1 == 1: # We have a function greater than or equal to 1000
            f = self.basisFunctionByIndex[key1]
            if class2 == 1: # This is a particular index
                if key2>=f.numParams():
                    raise ValueError("Function %d of type %s has only %d parameters" % (funcIndex,type(f),f.numParams()))
                return m.parameters[f.paramIndices[key2]]
            elif class2 == 2 and galDict0[key2] == 0: # This is a "peak" request
                if isinstance(f,BiSpline):
                    return f.getPeak(peakInterval = extra)[1]
        elif class1 == 2 and class2 == 1: # First key is "base", so we just use the second key as an index into the model parameters
            try:
                return m.parameters[key2]
            except:
                raise ValueError("Model parameter %s is not defined" % (key2,))
        elif class1 == 3 and class2 == 0: # This asks for some attribute of the analysis object
            if key1 == "std_dev_res":
                if len(self.res)>0:
                    return sqrt(sum(self.res**2)/len(self.res))
                else:
                    return 0
            elif hasattr(self,key1):
                return getattr(self,key1)
            else:
                raise ValueError("Unknown analysis parameter: %s" % (key1,))
        raise ValueError("Unrecognized key tuple for analysis output: %s" % (key,))
