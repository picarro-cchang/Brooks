from numpy import *

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
                if dxL == 0 or dxR == 0:
                    raise ValueError("Repeating values in x_array is not allowed.")
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
        x_bins = digitize(x,bins=self.x_vals)
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