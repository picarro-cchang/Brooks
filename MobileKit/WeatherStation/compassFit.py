from numpy import *
from scipy.optimize import leastsq
from pylab import *
import time

A = genfromtxt('compassfit_20120113.txt')
#A = genfromtxt('compassfit_20120117a.txt')
#A = genfromtxt('compassfit_20120119a.txt')
phi = gpsHead = A[:,0] # phi
theta = wsHead = -A[:,1] # theta
wsDir = A[:,2]

theta = asarray(theta)
phi = asarray(phi)
data = concatenate((cos(theta),sin(theta)))
def mock(params,phi):    # Generates mock data
    p0,p1,p2 = params
    th = p0 + arctan2(p2+sin(phi),p1+cos(phi))
    return concatenate((cos(th),sin(th)))
def fun(params):
    return mock(params,phi)-data
def dfun(params):
    N = len(phi)
    dm = mock(params,phi)
    cth = dm[:N]
    sth = dm[N:]
    p0,p1,p2 = params
    f1 = p1+cos(phi)
    f2 = p2+sin(phi)
    den = f1**2 + f2**2
    c0 = concatenate((-sth,cth))
    c1 = concatenate((sth*f2/den,-cth*f2/den))
    c2 = concatenate((-sth*f1/den,cth*f1/den))
    return column_stack((c0,c1,c2))
    
x0 = array([0.0,0.0,0.0])
t1 = time.clock()
x,ier = leastsq(fun,x0)
t2 = time.clock()
x,ier = leastsq(fun,x0,Dfun=dfun)
t3 = time.clock()
phifine=linspace(-pi,pi,500)
N = len(phifine)    
yfine = mock(x,phifine)
plot(phi,theta,'o',phifine,arctan2(yfine[N:],yfine[:N]),'.')
show()
print 'Time without derivatives',(t2-t1)
print 'Time with derivatives',(t3-t2)