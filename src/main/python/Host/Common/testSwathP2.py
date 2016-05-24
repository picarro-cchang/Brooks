from pylab import *
from numpy.random import RandomState
import Host.Common.SwathProcessor as SwathProcessor
import swathP as sp

t = arange(0, 400)
v = 15.0
R = 100.0
omega = v/R
xx = R*cos(omega*t)
yy = R*sin(omega*t)
prng = RandomState(1234567890)


for iter in range(5000):

    dist = 1.0 + 200.0*prng.rand()
    u = 10.0*prng.randn()
    v = 10.0*prng.randn()
    dmax = 10 + 300.0*prng.rand()
    sigma = 0.1 + 2.0*prng.rand()

    amin, amax, na = sp.angleRange(xx[:21], yy[:21], dist, u, v, dmax, 10)
    if na[0] > 0:
        p = sp.coverProb(amin[:na[0]], amax[:na[0]], sigma)
    else:
        p = 0

    result1 = SwathProcessor.angleRange(xx[:21], yy[:21], 10, dist, u, v, dmax)
    p1 = SwathProcessor.coverProb(result1, sigma)
    if abs(p - p1) > 1e-5:
        print iter