#!/usr/bin/python
#
# File Name: calUtilities.py
# Purpose: Utilities for polynomial fitting, spline computations and ellipse fitting
#  for angle-based wavelength monitor calibration.
#
# Notes:
#
# File History:
# 06-11-07 sze   Created file
# 06-12-21 russ  Added processor yield to bspInverse

from numpy import *
from numpy.dual import *
from ctypes import *
import time

class Bunch(object):
    """ This class is used to group together a collection as a single object, so that they may be accessed as attributes of that object"""
    def __init__(self,**kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)
    def __call__(self,*args,**kwargs):
        return self.call(self,*args,**kwargs)

def bestFitEval(self,xx): return polyval(self.coeffs,xx)

def bestFit(x,y,d):
    """ Carry out least-squares polynomial fit of degree d with data x,y """
    p = polyfit(x,y,d)
    y = reshape(y,(-1,))
    y1 = reshape(polyval(p,x),(-1,))
    res = sum((y-y1)**2)/len(y)
    return Bunch(coeffs=p,residual=res,fittedValues=y1,call=bestFitEval)

def bestFitCenteredEval(self,xx): return polyval(self.coeffs,(xx-self.xcen)/self.xscale)

def bestFitCentered(x,y,d):
    """ Polynomial fitting with the x data shifted and normalized so as to improve the conditioning of the normal
    equations for the fitting """
    x = array(x)
    mu_x = mean(x)
    sdev_x = std(x)
    xc = (x-mu_x)/sdev_x
    f = bestFit(xc,y,d)
    return Bunch(xcen=mu_x,xscale=sdev_x,coeffs=f.coeffs,residual=f.residual,fittedValues=f.fittedValues,
                 call=bestFitCenteredEval)

def getFitParameters(bunch):
    """Get the polynomial fitting parameters from the result of a bestFit or a bestFitCentered"""
    if hasattr(bunch,"xcen"):
        return bunch.coeffs,bunch.xcen,bunch.xscale
    else:
        return bunch.coeffs,None,None

def setFitParameters(coeffs,cen=None,scale=None):
    """Construct an evaluatable quantity from a set of fit parameters which define a polynomial"""
    if cen==None:
        return Bunch(coeffs=coeffs,call=bestFitEval)
    else:
        return Bunch(xcen=cen,xscale=scale,coeffs=coeffs,call=bestFitCenteredEval)

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
            result[ix[k]:(ix[k]+4)] = result[ix[k]:(ix[k]+4)] + y[k]*W[k,:]
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

# Routines for reading in WLM files
class WlmFile(object):
    def __init__(self,fname):
        """ Open a .wlm file and read data into an object """
        self.fname = fname
        fp = file(fname,'r')
        print "Reading wavelength monitor calibration file"
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
                self.wmin = min(self.WaveNumber)
                self.wmax = max(self.WaveNumber)
                return
            comps = line.split()
            for i in range(self.ncols):
                self.data[i].append(float(comps[i]))

if __name__ == "__main__":
    print bspInverse([2,3],zeros(10,'d'),array([4,5,6],'d'))
    #x = linspace(0,10,5)
    #y = x**3 + 5*x + 6
    #fitObject = bestFitCentered(x,y,3)
    #f = setFitParameters(*getFitParameters(fitObject))
    #print y
    #print f(x)

    #t = linspace(0,2*pi,17)
    #X = 1.5+2*cos(t)
    #Y = 3.7-sin(t-2*pi/7)
    #(x0,y0,A,B,epsilon) = parametricEllipse(X,Y)
    #tf = linspace(0,2*pi,501)
    #plot(X,Y,'o',x0+A*cos(tf),y0+B*sin(tf+epsilon))
    #show()
    #N = 20
    #coeffs = zeros(N,'d')
    #x = linspace(0.5,19.5,30)
    #xf = linspace(0,20,500)
    #y = sin(x)
    #for iter in range(100):
                #y0 = bspEval([0,0],coeffs,x)
                #coeffs += bspUpdate(N,x,0.1*(y-y0))
    #xx = bspInverse([-5,0],coeffs,array([-30.0,-40.0,-19.0,-57.3]))
    #print xx
    #print bspEval([-5,0],coeffs,xx)