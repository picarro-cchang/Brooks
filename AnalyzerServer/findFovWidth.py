from scipy.special import erf
import numpy as np
import pylab as pl

# Calculate maximum width of field of view about the point (x_N,y_N) based on a path of 2N+1 points (x_0,y_0) through (x_{2N},y_{2N})
#  where the mean wind bearing is (u=WIND_E,v=WIND_N) and there is a standard deviation of the wind direction given by d_sdev

def angleRange(x,y,N,dist,u,v,dmax=100.0):
    """
    Consider a segment of path specified by (x[0],y[0]) through (x[2*N],y[2*N]). A line is drawn through (x[N],y[N]) in the 
    direction of (u,v) and the trial source position is placed at a distance "dist" along this line. This function calculates
    the angle range subtended by the path segment at the trial source position, where zero angle corresponds to the line joining
    the source to (x[N],y[N]). The angle range is returned as a list containing tuples 
    [(minAngle_1,maxAngle_1),(minAngle_2,maxAngle_2),...] which together determine the angles covered by the path.
    """
    x = np.asarray([x[i] for i in range(0,2*N+1)])
    y = np.asarray([y[i] for i in range(0,2*N+1)])
    w = np.sqrt(u*u+v*v)
    uhat, vhat = u/w, v/w
    # Calculate trial source position
    sx, sy = x[N]+dist*uhat, y[N]+dist*vhat
    alist = np.arctan2(sy-y,sx-x)
    # Unwrap, ignoring non finite quantities
    mask = np.isfinite(alist)
    alist[mask] = np.unwrap(alist[mask])
    d = np.sqrt((sx-x)**2+(sy-y)**2)
    good = np.isfinite(d) & (d<=dmax)
    da = alist-alist[N]
    # Go through "good" to find groups of valid path segments. These contribute to the covered angles
    i = start = 0
    groups = []
    while i<=2*N:
        if good[i]:
            while i<=2*N and good[i]: i+= 1
            groups.append((da[start:i].min(),da[start:i].max()))
        while i<=2*N and not good[i]: i+= 1
        start = i
    #if dist == 0.1:
    #    print "angleRange",x[N],y[N],N,u,v,dmax,groups
    #    print x
    #    print y
    #    print da
    #    raw_input()
    return groups

def coverProb(angleRanges,sigma):
    """Find the probability that in covered by a set of angleRanges [(amin1,amax1),(amin2,amax2)...] for a normal probability
    distribution with zero mean and standard deviation sigma"""
    z = np.asarray(angleRanges)/sigma
    if z.size == 0: return 0.0
    p = 0.5*erf(z/np.sqrt(2))
    return sum(p[:,1]-p[:,0])

def maxDist(x,y,N,u,v,sigma,dmax=100,thresh=0.8,tol=1.0):
    """Find the maximum width of the swath (to a tolerance of tol) attached to the point x[N],y[N] in
    the direction of (u,v) when the standard deviation of the wind direction is sigma. The swath width 
    is never greater than dmax, and the probability that the path covers the the range of wind directions
    exceeds thresh"""
    dmin = 0.1
    if np.isnan(x[N]) or np.isnan(y[N]):
        return 0.0
    func = lambda d: coverProb(angleRange(x,y,N,d,u,v),sigma)-thresh
    fdmin = func(dmin)
    fdmax = func(dmax)
    if fdmax>0: 
        return dmax
    elif fdmin<0:
        return 0.0
    else:
        return binSearch(dmin,dmax,fdmin,fdmax,tol,func)
    
def binSearch(xmin,xmax,fxmin,fxmax,tol,func):
    """
    Use binary search to find a zero of func lying between xmin and xmax to a tolerance tol
    """
    xcen = 0.5*(xmax+xmin)
    if fxmin*fxmax > 0:
        raise ValueError("No zero between %s and %s" % (xmin,xmax))
    elif xmax-xmin < tol:
        return xcen
    else:
        fxcen = func(xcen)
        if fxmin*fxcen < 0:
            return binSearch(xmin,xcen,fxmin,fxcen,tol,func)
        else:            
            return binSearch(xcen,xmax,fxcen,fxmax,tol,func)
            
if __name__ == "__main__":
    R = 30
    N = 10
    t = np.arange(-N,N+1)
    x = R*np.cos(2*np.pi*t/(2*N))
    y = R*np.sin(2*np.pi*t/(2*N))

    #x = np.zeros(t.shape)
    #y = 5*t
    # Specify direction of wind
    u = -1.0
    v = 0.0
    dmax = 100.0
    sigma = 0.5
    
    print angleRange(x,y,N,150.0,u,v)
    dist = maxDist(x,y,N,u,v,sigma,dmax)
    print dist, coverProb(angleRange(x,y,N,dist,u,v),sigma)

    #pl.plot(t,x,t,y)
    #pl.grid(True)
    #pl.show()
