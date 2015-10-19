from numpy import *
from scipy.misc import comb
from scipy.optimize import curve_fit

class Bunch(object):
    """ This class is used to group together a collection as a single object, so that they may be accessed as attributes of that object"""

    def __init__(self, **kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)

    def __call__(self, *args, **kwargs):
        return self.call(self, *args, **kwargs)

def bestPolyFit(x, y, d):
    """ Carry out least-squares polynomial fit of degree d with data x,y """
    p, V = polyfit(x, y, d, cov=True)
    y = reshape(y, (-1,))
    y1 = reshape(polyval(p, x), (-1,))
    def eval(self, xx):
        return polyval(self.coeffs, xx)
    return Bunch(coeffs=p, covariance=V, fittedValues=y1, call=eval)

def bestPolyFitCentered(x, y, d):
    """ Polynomial fitting with the x data shifted and normalized so as to improve the conditioning of the normal
    equations for the fitting (fitting becomes poorly conditioned when x is too large) 
    """
    x = array(x)
    mu_x = mean(x)
    sdev_x = std(x)
    xc = (x - mu_x) / sdev_x
    f = bestPolyFit(xc, y, d)
    t = zeros((d+1, d+1))
    for i in range(d+1):
        for j in range(d+1):
            t[i, j] = comb(d-j,i-j)*(-mu_x)**(i-j)/sdev_x**(d-j)
    coeffs = dot(t, f.coeffs)
    var = dot(t, dot(f.covariance, t.T))
    sdev = sqrt(var.diagonal())
    def eval(self, xx):
        return polyval(self.coeffs, (xx - self.xcen) / self.xscale)
         
    return Bunch(
        xcen=mu_x, xscale=sdev_x, coeffs=coeffs, sdev=sdev, fittedValues=f.fittedValues, call=eval)
        
def getStatistics(x):
    return Bunch(mean=mean(x), std=std(x), ptp=ptp(x), min=amin(x), max=amax(x))