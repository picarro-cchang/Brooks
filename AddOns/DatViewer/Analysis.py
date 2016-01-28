import numpy as np
from scipy.misc import comb

class Bunch(object):
    """ This class is used to group together a collection as a single object, so that they may be accessed as attributes of that object"""

    def __init__(self, **kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)

    def __call__(self, *args, **kwargs):
        return self.call(self, *args, **kwargs)

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))        

def bestPolyFit(x, y, d):
    """ Carry out least-squares polynomial fit of degree d with data x,y """
    try:
        p, V = np.polyfit(x, y, d, cov=True)
    except:     # for old numpy
        p, V = numpy_polyfit(x, y, d)
    y = np.reshape(y, (-1,))
    y1 = np.reshape(np.polyval(p, x), (-1,))
    def eval(self, xx):
        return np.polyval(self.coeffs, xx)
    return Bunch(coeffs=p, covariance=V, fittedValues=y1, call=eval)

def bestPolyFitCentered(x, y, d):
    """ Polynomial fitting with the x data shifted and normalized so as to improve the conditioning of the normal
    equations for the fitting (fitting becomes poorly conditioned when x is too large) 
    """
    x = np.array(x)
    mu_x = np.mean(x)
    sdev_x = np.std(x)
    xc = (x - mu_x) / sdev_x
    f = bestPolyFit(xc, y, d)
    t = np.zeros((d+1, d+1))
    for i in range(d+1):
        for j in range(d+1):
            t[i, j] = comb(d-j,i-j)*(-mu_x)**(i-j)/sdev_x**(d-j)
    coeffs = np.dot(t, f.coeffs)
    var = np.dot(t, np.dot(f.covariance, t.T))
    sdev = np.sqrt(var.diagonal())
    def eval(self, xx):
        return np.polyval(self.coeffs, (xx - self.xcen) / self.xscale)
         
    return Bunch(
        xcen=mu_x, xscale=sdev_x, coeffs=coeffs, sdev=sdev, fittedValues=f.fittedValues, call=eval)

def numpy_polyfit(x, y, deg):
    # this piece of code is copied from numpy 1.8.1
    NX = np.core.numeric
    order = int(deg) + 1
    x = NX.asarray(x) + 0.0
    y = NX.asarray(y) + 0.0

    # check arguments.
    if deg < 0 :
        raise ValueError("expected deg >= 0")
    if x.ndim != 1:
        raise TypeError("expected 1D vector for x")
    if x.size == 0:
        raise TypeError("expected non-empty vector for x")
    if y.ndim < 1 or y.ndim > 2 :
        raise TypeError("expected 1D or 2D array for y")
    if x.shape[0] != y.shape[0] :
        raise TypeError("expected x and y to have same length")

    # set rcond
    rcond = len(x)*np.core.finfo(x.dtype).eps

    # set up least squares equation for powers of x
    lhs = np.lib.twodim_base.vander(x, order)
    rhs = y

    # scale lhs to improve condition number and solve
    scale = NX.sqrt((lhs*lhs).sum(axis=0))
    lhs /= scale
    c, resids, rank, s = np.linalg.lstsq(lhs, rhs, rcond)
    c = (c.T/scale).T  # broadcast scale coefficients

    # warn on rank reduction, which indicates an ill conditioned matrix
    if rank != order:
        msg = "Polyfit may be poorly conditioned"
        print "Warning: ", msg

    Vbase = np.linalg.inv(np.dot(lhs.T, lhs))
    Vbase /= NX.outer(scale, scale)
    # Some literature ignores the extra -2.0 factor in the denominator, but
    #  it is included here because the covariance of Multivariate Student-T
    #  (which is implied by a Bayesian uncertainty analysis) includes it.
    #  Plus, it gives a slightly more conservative estimate of uncertainty.
    fac = resids / (len(x) - order - 2.0)
    if y.ndim == 1:
        return c, Vbase * fac
    else:
        return c, Vbase[:,:, NX.newaxis] * fac          
        
def getStatistics(x):
    return Bunch(mean=np.mean(x), std=np.std(x), ptp=np.ptp(x), min=np.amin(x), max=np.amax(x))
    
class AllanVar(object):

    """ Class for computation of Allan Variance of a data series. Variances are computed over sets of
  size 1,2,...,2**(nBins-1). In order to process a new data point call processDatum(value). In order
  to recover the results, call getVariances(). In order to reset the calculation, call reset(). """

    def __init__(self, nBins):
        """ Construct an AllanVar object for calculating Allan variances over 1,2,...,2**(nBins-1) points """
        self.nBins = nBins
        self.counter = 0
        self.bins = []
        for i in range(nBins):
            self.bins.append(AllanBin(2 ** i))

    def reset(self):
        """ Resets calculation """
        self.counter = 0
        for bin in self.bins:
            bin.reset()

    def processDatum(self, value):
        """ Process a value for the Allan variance calculation """
        for bin in self.bins:
            bin.process(value)
        self.counter += 1

    def getVariances(self):
        """ Get the result of the Allan variance calculation as (count,(var1,var2,var4,...)) """
        return (self.counter, tuple([bin.allanVar for bin in self.bins]))

class AllanBin(object):

    """ Internal class for Allan variance calculation """

    def __init__(self, averagingLength):
        self.averagingLength = averagingLength
        self.reset()

    def reset(self):
        self.sum, self.sumSq = 0, 0
        self.sumPos, self.numPos = 0, 0
        self.sumNeg, self.numNeg = 0, 0
        self.nPairs, self.allanVar = 0, 0

    def process(self, value):
        if self.numPos < self.averagingLength:
            self.sumPos += value
            self.numPos += 1
        elif self.numNeg < self.averagingLength:
            self.sumNeg += value
            self.numNeg += 1
        if self.numNeg == self.averagingLength:
            var = (self.sumPos / self.numPos) - (self.sumNeg / self.numNeg)
            self.sum += var
            self.sumSq += var ** 2
            self.nPairs += 1
            self.allanVar = 0.5 * self.sumSq / self.nPairs
            self.sumPos, self.numPos = 0, 0
            self.sumNeg, self.numNeg = 0, 0
            
def AllenStandardDeviation(datViewer):
    x_sel = datViewer.xData[datViewer.boxSel]
    y_sel = datViewer.yData[datViewer.boxSel]
    n = len(x_sel)
    # Find conversion from points to a time axis
    slope, offset = np.polyfit(np.arange(n), x_sel, 1)
        
    npts = int(np.floor(np.log(n) / np.log(2)))
    av = AllanVar(int(npts))
    for var in y_sel:
        av.processDatum(var)
    v = av.getVariances()
    sdev = np.sqrt(np.asarray(v[1]))
    xArray = 2 ** np.arange(npts) * slope*24*3600
    yArray = sdev
    boxSel = (xArray>=1) & (xArray<=2 ** npts)
    fit_xData = xArray[boxSel]
    fit_yData = sdev[boxSel][0] / np.sqrt(fit_xData / fit_xData[0])
    return xArray, yArray, fit_xData, fit_yData