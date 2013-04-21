from pylab import *
from numpy.random import RandomState
import SwathProcessor
import swathP as sp
import time

t = arange(0, 400)
v = 15.0
R = 100.0
omega = v/R
xx = R*cos(omega*t)
yy = R*sin(omega*t)
d = []
d1 = []

prng = RandomState(1234567890)
start = time.time()
for iter in range(5000):

    dist = 1.0 + 200.0*prng.rand()
    u = 10.0*prng.randn()
    v = 10.0*prng.randn()
    dmax = 10 + 300.0*prng.rand()
    sigma = 0.1 + 2.0*prng.rand()
    thresh = 0.7
    tol = 1.0
    N = 10

    d.append(sp.maxDist(xx[:21], yy[:21], u, v, sigma, dmax, thresh, tol))
print time.time() - start

prng = RandomState(1234567890)
start = time.time()
for iter in range(5000):

    dist = 1.0 + 200.0*prng.rand()
    u = 10.0*prng.randn()
    v = 10.0*prng.randn()
    dmax = 10 + 300.0*prng.rand()
    sigma = 0.1 + 2.0*prng.rand()
    thresh = 0.7
    tol = 1.0
    N = 10

    d1.append(SwathProcessor.maxDist(xx[:21], yy[:21], N, u, v, sigma, dmax, thresh, tol))
print time.time() - start
