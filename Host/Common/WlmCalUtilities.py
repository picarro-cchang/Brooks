#!/usr/bin/python
#
# FILE:
#   WlmCalUtilities.py
#
# DESCRIPTION:
#   Utilities for processing wavelength monitor calibration
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   8-Oct-2009  sze  Initial version.
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#

from numpy import *
from numpy.dual import *
from ctypes import *
import threading
import time
from configobj import ConfigObj

class Bunch(object):
    """ This class is used to group together a collection as a single object, so that they may be accessed as attributes of that object"""
    def __init__(self,**kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)
    def __call__(self,*args,**kwargs):
        return self.call(self,*args,**kwargs)

def bestFit(x,y,d):
    """ Carry out least-squares polynomial fit of degree d with data x,y """
    p = polyfit(x,y,d)
    y = reshape(y,(-1,))
    y1 = reshape(polyval(p,x),(-1,))
    res = sum((y-y1)**2)/len(y)
    def eval(self,xx): return polyval(self.coeffs,xx)
    return Bunch(coeffs=p,residual=res,fittedValues=y1,call=eval)

def bestFitCentered(x,y,d):
    """ Polynomial fitting with the x data shifted and normalized so as to improve the conditioning of the normal
    equations for the fitting """
    x = array(x)
    mu_x = mean(x)
    sdev_x = std(x)
    xc = (x-mu_x)/sdev_x
    f = bestFit(xc,y,d)
    def eval(self,xx): return polyval(self.coeffs,(xx-self.xcen)/self.xscale)
    return Bunch(xcen=mu_x,xscale=sdev_x,coeffs=f.coeffs,residual=f.residual,fittedValues=f.fittedValues,
                 call=eval)

def polyFitEvaluator(coeffs,cen=0,scale=1):
    def eval(self,xx): return polyval(coeffs,(xx-cen)/scale)
    return Bunch(xcen=cen,xscale=scale,coeffs=coeffs,call=eval)

# Routines for manipulating cubic B-splines defined on a regular unit-spaced grid

def bspEval(p0,coeffs,x):
    """Evaluate the spline defined by coefficients "coeffs" at the position "x" """
    nc = len(coeffs)
    y = polyval(p0,x)
    inside = (x>-1)&(x<nc)
    x = x[inside]
    ix = array(floor(x),'l')
    fx = x-ix
    w1 = polyval(array([1,0,0,0],'d')/6,fx)
    w2 = polyval(array([-3,3,3,1],'d')/6,fx)
    w3 = polyval(array([3,-6,0,4],'d')/6,fx)
    w4 = polyval(array([-1,3,-3,1],'d')/6,fx)
    pcoeffs = zeros(len(coeffs)+3,coeffs.dtype)
    pcoeffs[1:-2] = coeffs
    y[inside] += w1*pcoeffs[ix+3]+w2*pcoeffs[ix+2]+w3*pcoeffs[ix+1]+w4*pcoeffs[ix]
    return y

def bspUpdate(N,x,y):
    """Multiply the vector y by the transpose of the collocation matrix of a spline
        whose knots are at 0,1,2,...,N-1 and which is evaluated at the points in x"""
    result = zeros(N+3,y.dtype)
    inside = (x>-1)&(x<N)
    x = x[inside]
    y = y[inside]
    ix = array(floor(x),'l')
    fx = x-ix
    W = zeros([len(ix),4],'d')
    W[:,3] = polyval(array([1,0,0,0],'d')/6,fx)
    W[:,2] = polyval(array([-3,3,3,1],'d')/6,fx)
    W[:,1] = polyval(array([3,-6,0,4],'d')/6,fx)
    W[:,0] = polyval(array([-1,3,-3,1],'d')/6,fx)
    for k in range(len(ix)):
        if ix[k]>=0 and ix[k]<N-1:
            result[ix[k]:(ix[k]+4)] += y[k]*W[k,:]
    return result[1:-2]

def bspInverse(p0,coeffs,y):
    """Looks up the values of y in a B-spline expansion + a linear polynomial.
    If the coefficients are such that the sum of the spline and the linear term
    is monotonic, an inverse cubic interpolation is performed. If not, the inverse
    interpolation is done using the linear term alone.

    Returns interpolated result together with a flag indicating if the spline+linear
    term is monotonic"""

    x0 = arange(1,len(coeffs)-1,dtype='d')
    # Evaluate spline + linear polynomial at the knots
    ygrid = polyval(p0,x0) + (coeffs[:-2] + 4*coeffs[1:-1] + coeffs[2:])/6.0
    try:
        b = digitize(y,bins=ygrid)
    except:
        return (y-p0[1])/p0[0],False
    c1 = coeffs[b-1]
    c2 = coeffs[b]
    c3 = coeffs[b+1]
    c4 = coeffs[b+2]
    # Array of cubic coefficients
    cc = zeros([len(y),4],'d')
    cc[:,0] = (-c1+3*c2-3*c3+c4)/6.0
    cc[:,1] = (c1-2*c2+c3)/2.0
    cc[:,2] = (-c1+c3)/2.0
    cc[:,3] = (c1+4*c2+c3)/6.0 - y
    x = array(b,dtype='d')
    for i in range(len(y)):
        pp = cc[i,:]
        pp[2] += p0[0]
        pp[3] += p0[0]*b[i]+p0[1]
        r = roots(pp)
        x[i] += r[(r == real(r)) & (r>=0) & (r<=1)][0]
        # time.sleep(0)
    return x,True

# Routines for ellipse fitting

def fitEllipse(X,Y):
    """Compute parameters of the best-fit ellipse to the 2D points (x,y). The result is returned as (x0,y0,r1,r2,phi) where (x0,y0) is the center of the ellipse, and r1 and r2 are the semi-principal axes lengths. The first principal axis makes an angle phi with the x axis"""
    # Normalize data
    mx = mean(X)
    my = mean(Y)
    sx = ptp(X)/2.0
    sy = ptp(Y)/2.0
    x = (X-mx)/sx
    y = (Y-my)/sy
    # Build normal matrix
    D = column_stack([x**2,x*y,y**2,x,y,ones(len(x),dtype="d")])
    S = dot(D.transpose(),D)
    # Build constraint matrix
    C = zeros([6,6],dtype="d")
    C[0,2] = -2; C[1,1] = 1; C[2,0] = -2
    # Solve generalized eigensystem
    tmpA = S[0:3,0:3]
    tmpB = S[0:3,3:]
    tmpC = S[3:,3:]
    tmpD = C[0:3,0:3]
    tmpE = dot(inv(tmpC),tmpB.transpose())
    [eval_x, evec_x] = eig(dot(inv(tmpD),(tmpA - dot(tmpB,tmpE))))
    # Extract eigenvector corresponding to non-positive eigenvalue
    A = evec_x[:,(real(eval_x) < 1e-8)]
    # Recover the bottom half
    evec_y = -dot(tmpE,A)
    A = vstack([A,evec_y]).ravel()
    # Unnormalize
    par = array([A[0]*sy*sy, A[1]*sx*sy, A[2]*sx*sx,\
                 -2*A[0]*sy*sy*mx - A[1]*sx*sy*my + A[3]*sx*sy*sy,\
                 -A[1]*sx*sy*mx - 2*A[2]*sx*sx*my + A[4]*sx*sx*sy,\
                 A[0]*sy*sy*mx*mx + A[1]*sx*sy*mx*my + A[2]*sx*sx*my*my -\
                 A[3]*sx*sy*sy*mx - A[4]*sx*sx*sy*my + A[5]*sx*sx*sy*sy])
    # Find center of ellipse
    den = 4*par[0]*par[2]-par[1]**2
    x0 = (par[1]*par[4]-2*par[2]*par[3])/den
    y0 = (par[1]*par[3]-2*par[0]*par[4])/den
    # Find orientation of ellipse
    phi = 0.5*arctan2(par[1],par[0]-par[2])
    # Find semi principal axis lengths
    rr = par[0]*x0*x0+par[1]*x0*y0+par[2]*y0*y0-par[5]
    cphi = cos(phi)
    sphi = sin(phi)
    r1 = sqrt(rr/(par[0]*cphi*cphi+par[1]*cphi*sphi+par[2]*sphi*sphi))
    r2 = sqrt(rr/(par[0]*sphi*sphi-par[1]*cphi*sphi+par[2]*cphi*cphi))
    return (x0,y0,r1,r2,phi)

def parametricEllipse(X,Y):
    """Fit the 2D points (X,Y) by an ellipse such that
    X = x0 + A*cos(theta)
    Y = y0 + B*sin(theta+epsilon)
    The parameters are returned as (x0,y0,A,B,epsilon)"""
    (x0,y0,r1,r2,phi) = fitEllipse(X,Y)
    cphi = cos(phi)
    sphi = sin(phi)
    A = sqrt((r1*cphi)**2 + (r2*sphi)**2)
    B = sqrt((r1*sphi)**2 + (r2*cphi)**2)
    epsilon = arccos((r1*r2)/(A*B))
    if (r1>r2)^(cphi*sphi>0): epsilon = -epsilon
    return (x0,y0,A,B,epsilon)

# Routine for reading in WLM files
class WlmFile(object):
    def __init__(self,fp):
        """ Read data from a .wlm file into an object """
        # Get parameter values
        while True:
            line = fp.readline()
            if line == "":
                raise Exception("Unexpected end of .wlm file")
            if line.find('[Parameters]') >= 0:
                break
        self.parameters = {}
        while True:
            line = fp.readline()
            # Look parameter=value pairs
            comps = [comp.strip() for comp in line.split("=",1)]
            if len(comps)<2: break
            self.parameters[comps[0]] = comps[1]

        # Get the data column names information
        while True:
            line = fp.readline()
            if line == "":
                raise Exception("Unexpected end of .wlm file")
            if line.find('[Data column names]') >= 0 or line.find('[Data_column_names]') >= 0:
                break
        self.colnames = {}
        self.colindex = {}
        while True:
            line = fp.readline()
            # Look for column_index=column_name pairs
            comps = [comp.strip() for comp in line.split("=",1)]
            if len(comps)<2: break
            self.colnames[int(comps[0])] = comps[1]
            self.colindex[comps[1]] = int(comps[0])
        # Skip to the line which marks the start of the data
        while True:
            line = fp.readline()
            if line == "":
                raise Exception("Unexpected end of .wlm file")
            if line.find('[Data]') >= 0:
                break
        self.ncols = len(self.colnames.keys())
        self.data = []
        for i in range(self.ncols):
            self.data.append(list())
        while True:
            line = fp.readline()
            if line == "":
                self.TLaser = array(self.data[self.colindex["Laser temperature"]],float_)
                self.WaveNumber = array(self.data[self.colindex["Wavenumber"]],float_)
                self.Ratio1 = array(self.data[self.colindex["Wavelength ratio 1"]],float_)
                self.Ratio2 = array(self.data[self.colindex["Wavelength ratio 2"]],float_)
                self.TEtalon = array(self.data[self.colindex["Etalon temperature"]],float_)
                self.Etalon1 = array(self.data[self.colindex["Etalon 1 (offset removed)"]],float_)
                self.Reference1 = array(self.data[self.colindex["Reference 1 (offset removed)"]],float_)
                self.Etalon2 = array(self.data[self.colindex["Etalon 2 (offset removed)"]],float_)
                self.Reference2 = array(self.data[self.colindex["Reference 2 (offset removed)"]],float_)
                self.PointsAveraged = array(self.data[self.colindex["Points averaged"]],int)
                self.Tcal = mean(self.TEtalon) # Effective calibration temperature for etalon
                # Calculating polynomial fits of Wavenumber vs Temperature"
                self.WtoT = bestFitCentered(self.WaveNumber,self.TLaser,3)
                self.TtoW = bestFitCentered(self.TLaser,self.WaveNumber,3)
                return
            comps = line.split()
            for i in range(self.ncols):
                self.data[i].append(float(comps[i]))

class AutoCal(object):
    # Calibration requires us to store:
    # Laser calibration constants which map laser temperature to laser wavenumber
    # WLM constants: ratio1Center, ratio2Center, ratio1Scale, ratio2Scale, wlmPhase, wlmTempSensitivity, tEtalonCal
    # Spline scaling constants: dTheta, thetaBase
    # Linear term for spline: sLinear

    def __init__(self):
        self.lock = threading.Lock() # Protects access to the parameters
        self.offset = 0
        self.autocalStatus = 0  #  If this is non-zero, an error has occured in the frequency-angle conversion
                                #  Currently bit 0 indicates a non-monotonic spline for frequency conversion
                                #  Reset whenever the Autocal object is reloaded from an INI or WLM file
        self.thetaMeasured = None
        self.waveNumberMeasured = None

    def loadFromWlmFile(self,wlmFile,dTheta = 0.05,wMin = None,wMax = None):
        # Construct an Autocal object from a WlmFile object based on measured data which lie within the 
        #  wavenumber range wMin to wMax
        self.lock.acquire()
        try:
            # Select those data which lie within the specified range of wavenumbers
            if wMin is None: wMin = wlmFile.WaveNumber.min()
            if wMax is None: wMax = wlmFile.WaveNumber.max()
            if wMin < wlmFile.WaveNumber.min() or wMax > wlmFile.WaveNumber.max():
                raise ValueError("Range of wavenumbers requested is not available in WLM file")
            window = (wlmFile.WaveNumber >= wMin) & (wlmFile.WaveNumber <= wMax)
            # Fit ratios to a parametric ellipse
            self.ratio1Center,self.ratio2Center,self.ratio1Scale,self.ratio2Scale,self.wlmPhase = \
                parametricEllipse(wlmFile.Ratio1[window],wlmFile.Ratio2[window])
            # Ensure that both ratioScales are larger than 1.05 to avoid issues with ratio multipliers exceeding 1
            factor = 1.05/min([self.ratio1Scale,self.ratio2Scale])
            self.ratio1Scale *= factor
            self.ratio2Scale *= factor
            self.tEtalonCal = wlmFile.Tcal
            # Calculate the unwrapped WLM angles
            X = wlmFile.Ratio1[window] - self.ratio1Center
            Y = wlmFile.Ratio2[window] - self.ratio2Center
            thetaCalMeasured = unwrap(arctan2(
              self.ratio1Scale * Y - self.ratio2Scale * X * sin(self.wlmPhase),
              self.ratio2Scale * X * cos(self.wlmPhase)))
            # Extract parameters of angle vs laser temperature
            self.laserTemp2WaveNumber = wlmFile.TtoW
            self.waveNumber2LaserTemp = wlmFile.WtoT
            # Extract parameters of wavenumber against angle
            thetaCal2WaveNumber = bestFit(thetaCalMeasured,wlmFile.WaveNumber[window],1)
            # Include Burleigh data in object for plotting and debug
            self.thetaMeasured = thetaCalMeasured
            self.waveNumberMeasured = wlmFile.WaveNumber[window]
            # Extract spline scaling constants
            self.thetaBase = (wMin - thetaCal2WaveNumber.coeffs[1])/thetaCal2WaveNumber.coeffs[0]
            self.dTheta = dTheta
            self.sLinear0 = array([thetaCal2WaveNumber.coeffs[0]*self.dTheta,
                                   thetaCal2WaveNumber([self.thetaBase])[0]],dtype="d")
            self.sLinear = self.sLinear0 + array([0.0,self.offset])
            # Find number of spline coefficients needed and initialize the coefficients to zero
            self.nCoeffs = int(ceil((wMax-wMin)/(thetaCal2WaveNumber.coeffs[0]*self.dTheta)))
            self.coeffs = zeros(self.nCoeffs,dtype="d")
            self.coeffsOrig = zeros(self.nCoeffs,dtype="d")
            # Temperature sensitivity of etalon
            self.wlmTempSensitivity = -0.185 * (mean(wlmFile.WaveNumber[window])/6158.0)# radians/degC
            self.autocalStatus = 0
        finally:    
            self.lock.release()
        return self

    def loadFromIni(self,ini,vLaserNum):
        """Fill up the AutoCal structure based on the information in the .ini file
        using the specified "vLaserNum" to indicate which virtual laser (1-origin) is involved.
        The INI file must have valid ACTUAL_LASER and LASER_MAP sections as well as the 
        VIRTUAL_PARAMS, VIRTUAL_CURRENT and VIRTUAL_ORIGINAL sections for the specified
        vLaserNum."""
        def fetchCoeffs(sec,prefix):
            # Fetches coefficients from a section of an INI file into a list
            coeffs = []
            i = 0
            while True:
                try:
                    coeffs.append(float(sec["%s%d" % (prefix,i)]))
                    i += 1
                except:
                    break
            return coeffs
        
        self.lock.acquire()
        try:
            paramSec = "VIRTUAL_PARAMS_%d" % vLaserNum
            currentSec = "VIRTUAL_CURRENT_%d" % vLaserNum
            originalSec = "VIRTUAL_ORIGINAL_%d" % vLaserNum
            if paramSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % paramSec)
            if currentSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % currentSec)
            if originalSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % originalSec)
            # Find the actual laser
            mapSec = "LASER_MAP"
            if mapSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % mapSec)
            aLaserNum = int(ini[mapSec]["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum])
            aLaserSec = "ACTUAL_LASER_%d" % aLaserNum
            if aLaserSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % mapSec)
            cen = float(ini[aLaserSec]["WAVENUM_CEN"])
            scale = float(ini[aLaserSec]["WAVENUM_SCALE"])
            coeffs = array(fetchCoeffs(ini[aLaserSec],"W2T_"))
            self.waveNumber2LaserTemp = polyFitEvaluator(coeffs,cen,scale)

            cen = float(ini[aLaserSec]["TEMP_CEN"])
            scale = float(ini[aLaserSec]["TEMP_SCALE"])
            coeffs = array(fetchCoeffs(ini[aLaserSec],"T2W_"))
            self.laserTemp2WaveNumber = polyFitEvaluator(coeffs,cen,scale)

            self.ratio1Center = float(ini[paramSec]["RATIO1_CENTER"])
            self.ratio2Center = float(ini[paramSec]["RATIO2_CENTER"])
            self.ratio1Scale  = float(ini[paramSec]["RATIO1_SCALE"])
            self.ratio2Scale  = float(ini[paramSec]["RATIO2_SCALE"])
            self.wlmPhase     = float(ini[paramSec]["PHASE"])
            self.tEtalonCal   = float(ini[paramSec]["CAL_TEMP"])
            self.wlmTempSensitivity = float(ini[paramSec]["TEMP_SENSITIVITY"])
            self.thetaBase    = float(ini[paramSec]["ANGLE_BASE"])
            self.dTheta       = float(ini[paramSec]["ANGLE_INCREMENT"])
            self.sLinear0     = array([float(ini[paramSec]["LINEAR_MODEL_SLOPE"]),
                                       float(ini[paramSec]["LINEAR_MODEL_OFFSET"])])
            self.offset       = float(ini[paramSec]["WLM_OFFSET"])
            self.sLinear      = self.sLinear0 + array([0.0,self.offset])
            self.nCoeffs      = int(ini[paramSec]["NCOEFFS"])

            self.coeffs = []
            for i in range(self.nCoeffs):
                self.coeffs.append(float(ini[currentSec]["COEFF%d" % i]))
            self.coeffs = array(self.coeffs)
            self.autocalStatus = 0

            self.coeffsOrig = []
            for i in range(self.nCoeffs):
                self.coeffsOrig.append(float(ini[originalSec]["COEFF%d" % i]))
            self.coeffsOrig = array(self.coeffsOrig)
            return self
        finally:
            self.lock.release()
    
    def updateIni(self,ini,vLaserNum):
        """Update (and possibly create) sections and keys in "ini" to describe the current 
        AutoCal object, using the specified "vLaserNum" to indicate which virtual laser 
        (1-origin) is involved"""
        self.lock.acquire()
        try:
            paramSec = "VIRTUAL_PARAMS_%d" % vLaserNum
            currentSec = "VIRTUAL_CURRENT_%d" % vLaserNum
            originalSec = "VIRTUAL_ORIGINAL_%d" % vLaserNum
            if paramSec not in ini:
                ini[paramSec] = {}
                # Following options are not overwritten if they are already in the INI file
                ini[paramSec]["CAL_PRESSURE"] = 760.0
                ini[paramSec]["PRESSURE_C0"]  = 0.0
                ini[paramSec]["PRESSURE_C1"]  = 0.0
                ini[paramSec]["PRESSURE_C2"]  = 0.0
                ini[paramSec]["PRESSURE_C3"]  = 0.0
                ini[paramSec]["TEMP_SENSITIVITY"] = self.wlmTempSensitivity
            if currentSec not in ini:
                ini[currentSec] = {}
            if originalSec not in ini:
                ini[originalSec] = {}

            ini[paramSec]["ANGLE_BASE"] = self.thetaBase
            ini[paramSec]["ANGLE_INCREMENT"] = self.dTheta
            ini[paramSec]["LINEAR_MODEL_OFFSET"] = self.sLinear0[1]
            ini[paramSec]["LINEAR_MODEL_SLOPE"] = self.sLinear0[0]
            ini[paramSec]["NCOEFFS"] = self.nCoeffs
            ini[paramSec]["WLM_OFFSET"] = self.offset
            ini[paramSec]["CAL_TEMP"] = self.tEtalonCal
            ini[paramSec]["RATIO1_CENTER"] = self.ratio1Center
            ini[paramSec]["RATIO1_SCALE"] = self.ratio1Scale
            ini[paramSec]["RATIO2_CENTER"] = self.ratio2Center
            ini[paramSec]["RATIO2_SCALE"] = self.ratio2Scale
            ini[paramSec]["PHASE"] = self.wlmPhase

            ini[currentSec] = {}
            for i in range(len(self.coeffs)):
                ini[currentSec]["COEFF%d" % i] = self.coeffs[i]
            
            ini[originalSec] = {}
            for i in range(len(self.coeffs)):
                ini[originalSec]["COEFF%d" % i] = self.coeffsOrig[i]

        finally:
            self.lock.release()

    def getAutocalStatus(self):
        return self.autocalStatus

    def thetaCal2WaveNumber(self,thetaCal):
        """Look up in current calibration to get wavenumbers from WLM angles"""
        self.lock.acquire()
        try:
            x = (thetaCal-self.thetaBase)/self.dTheta
            return bspEval(self.sLinear,self.coeffs,x)
        finally:
            self.lock.release()

    def thetaCalAndLaserTemp2WaveNumber(self,thetaCal,laserTemp):
        """Use laser temperature to place calibrated angles on the correct revolution and look up 
        in current calibration to get wavenumbers"""
        self.lock.acquire()
        try:
            approxWaveNum = self.laserTemp2WaveNumber(laserTemp)
            # Convert wavenumber to thetaHat via inverse of linear model
            thetaHat = self.thetaBase + self.dTheta*(approxWaveNum - self.sLinear[1])/self.sLinear[0]
            thetaCal += 2*pi*floor((thetaHat-thetaCal)/(2*pi)+0.5)
            x = (thetaCal-self.thetaBase)/self.dTheta
            return bspEval(self.sLinear,self.coeffs,x)
        finally:
            self.lock.release()

    def laserTemp2ThetaCal(self,laserTemp):
        """Determine calibrated WLM angle associated with given laser temperature"""
        self.lock.acquire()
        try:
            approxWaveNum = self.laserTemp2WaveNumber(laserTemp)
            # Convert wavenumber to angle via inverse of linear model
            return self.thetaBase + self.dTheta*(approxWaveNum - self.sLinear[1])/self.sLinear[0]
        finally:
            self.lock.release()

    def thetaCal2LaserTemp(self,thetaCal):
        """Determine laser temperature to target to achieve a particular calibrated WLM angle"""
        self.lock.acquire()
        try:
            x = (thetaCal-self.thetaBase)/self.dTheta
            waveNum = polyval(self.sLinear,x)
            return self.waveNumber2LaserTemp(waveNum)
        finally:
            self.lock.release()

    def waveNumber2ThetaCal(self,waveNumbers):
        """Look up current calibration to find WLM angle for a given wavenumber"""
        self.lock.acquire()
        try: 
            result, monotonic = bspInverse(self.sLinear,self.coeffs,waveNumbers)
            if not monotonic: self.autocalStatus |= AutocalStatus_NonMonotonic
            return self.thetaBase + self.dTheta * result
        finally:
            self.lock.release()

    def updateWlmCal(self,thetaCal,waveNumbers,weights=1,relax=5e-3,relative=True,
                     relaxDefault=5e-3,relaxZero=5e-5):
        """Update the calibration coefficients
        thetaCal      array of calibrated WLM angles
        waveNumbers   array of waveNumbers to which these angles map
        weights       array of weights. The wavenumber residuals are DIVIDED by these before being used for correction.
        relax         relaxation parameter of update
        relative      True if only waveNumber differences are significant
                      False if absolute waveNumbers are specified
        relaxDefault  Factor used to relax coefficients towards the original default values.
                      Relaxation takes place with Laplacian regularization.
        relaxZero     Factor used to relax coefficients towards the original default values.
                      Relaxation is based on unfiltered deviation from the original
        """
        self.lock.acquire()
        try: 
            x = (thetaCal-self.thetaBase)/self.dTheta
            currentWaveNumbers = bspEval(self.sLinear,self.coeffs,x)
            res = waveNumbers - currentWaveNumbers
            if relative:
                res = res - mean(res)

            res = res/weights
            update = relax*bspUpdate(self.nCoeffs,x,res)
            self.coeffs += update

            # Apply regularization, becoming more and more aggressive if the result is non-increasing
            self.relaxTowardsOriginal(relaxDefault,relaxZero)
            # print "Maximum change from relaxation to default: %s" % (abs(self.coeffs-update).max(),)

        finally:
            self.lock.release()

    MAX_ITER = 20
    def relaxTowardsOriginal(self,relax,relaxZero=0,n=MAX_ITER):
        """Relax the new coefficients towards the original, using a Laplacian term for regularization
            for relax and a raw residual for relax."""
        for i in range(n):
            dev = self.coeffsOrig - self.coeffs
            self.coeffs[1:-1] = self.coeffs[1:-1] + relax*(dev[1:-1]-0.5*dev[2:]-0.5*dev[:-2]) + relaxZero*dev[1:-1]
            if relax<0.5: relax += relax
            if self.isIncreasing(): break

    def isIncreasing(self):
        """Determine if the current coefficients + linear model results in a monotonically increasing angle to
        wavenumber transformation at the knots"""
        ygrid = self.sLinear[0]*arange(1,self.nCoeffs-1) + (self.coeffs[:-2] + 4*self.coeffs[1:-1] + self.coeffs[2:])/6.0
        return (diff(ygrid)>=0).all()

    def replaceCurrent(self):
        """Replace current values with copy of originals"""
        self.coeffs = self.coeffsOrig.copy()

    def replaceOriginal(self):
        """Replace original values with copy of current values"""
        self.coeffsOrig = self.coeffs.copy()

    def setOffset(self,offset):
        """Apply a spectroscopically determined wavelength monitor offset."""
        self.lock.acquire()
        try: 
            self.offset = offset
            self.sLinear = self.sLinear0 + array([0.0,self.offset])
        finally:
            self.lock.release()

    def getOffset(self):
        """Returns the current value of the offset."""
        self.lock.acquire()
        try: 
            return self.offset
        finally:
            self.lock.release()

    def shiftWlmCal(self,thetaCal,waveNumber,relax=0.1):
        """Shift entire calibration table on basis of a known waveNumber
        thetaCal      calibrated WLM angle
        waveNumber    wavenumber to which it corresponds
        relax         relaxation parameter for update"""
        self.lock.acquire()
        try: 
            x = (thetaCal-self.thetaBase)/self.dTheta
            currentWaveNumber = bspEval(self.sLinear,self.coeffs,[x])[0]
            res = waveNumber - currentWaveNumber
            self.sLinear[1] += relax * res
            offset = self.sLinear[1] - self.sLinear0[1]
        finally:
            self.lock.release()
    
if __name__ == "__main__":
    from pylab import *
    # Check inverse interpolation via a linear function
    x = bspInverse([2,3],zeros(10,'d'),array([4,5,6],'d'))
    assert allclose(x[0],[0.5,1,1.5])
    assert x[1]
    # Test polynomial fitting and evaluation
    x = linspace(0.0,10.0,5)
    y = x**3 + 5*x + 6
    f = bestFitCentered(x,y,3)
    assert allclose(y,f(x))
    # Test ellipse fitting
    t = linspace(0,2*pi,17)
    X = 1.5+2*cos(t)
    Y = 3.7+sin(t+2*pi/7)
    (x0,y0,A,B,epsilon) = parametricEllipse(X,Y)
    X1 = x0+A*cos(t)
    Y1 = y0+B*sin(t+epsilon)
    assert allclose(X,X1)
    assert allclose(Y,Y1)
    # Make a B-spline pass through some generated data
    N = 20
    coeffs = zeros(N,'d')
    x = linspace(0.5,19.5,30)
    xf = linspace(0,20,500)
    y = sin(x)
    for iter in range(100):
        y0 = bspEval([0,0],coeffs,x)
        coeffs += bspUpdate(N,x,0.1*(y-y0))
    #plot(xf,bspEval([0,0],coeffs,xf),x,y,'x')
    #show()
    target = array([-30.0,-40.0,-19.0,-57.3])
    xx = bspInverse([-5,0],coeffs,target)
    assert allclose(bspEval([-5,0],coeffs,xx[0]),target)
    
    w = WlmFile(file("../../Utilities/firstTest.wlm","r"))
    a = AutoCal()
    a.loadFromWlmFile(w)
    ini = ConfigObj(file("../../Utilities/foo.ini","r"))
    a.updateIni(ini,2)
    ini.filename = "../../Utilities/newfoo.ini"
    ini.write()
    

