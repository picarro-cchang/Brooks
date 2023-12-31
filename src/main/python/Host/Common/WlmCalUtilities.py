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
import itertools
import pdb
import re
import threading

import numpy as np
from numpy.linalg import eig, inv
from scipy.interpolate import splev, splrep

from Host.Common.configobj import ConfigObj
from Host.autogen import interface
from Host.Common.EventManagerProxy import Log, LogExc


class Bunch(object):
    """ This class is used to group together a collection as a single object, so that they may be accessed as attributes of that object"""
    def __init__(self, **kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)

    def __call__(self, *args, **kwargs):
        return self.call(self, *args, **kwargs)


def bestFit(x, y, d):
    """ Carry out least-squares polynomial fit of degree d with data x,y """
    p = np.polyfit(x, y, d)
    y = np.reshape(y, (-1, ))
    y1 = np.reshape(np.polyval(p, x), (-1, ))
    res = sum((y - y1)**2) / len(y)

    def eval(self, xx):
        return np.polyval(self.coeffs, xx)

    return Bunch(coeffs=p, residual=res, fittedValues=y1, call=eval)


def bestFitCentered(x, y, d):
    """ Polynomial fitting with the x data shifted and normalized so as to improve the conditioning of the normal
    equations for the fitting """
    x = np.array(x)
    mu_x = np.mean(x)
    sdev_x = np.std(x)
    xc = (x - mu_x) / sdev_x
    f = bestFit(xc, y, d)

    def eval(self, xx):
        return np.polyval(self.coeffs, (xx - self.xcen) / self.xscale)

    return Bunch(xcen=mu_x, xscale=sdev_x, coeffs=f.coeffs, residual=f.residual, fittedValues=f.fittedValues, call=eval)


def polyFitEvaluator(coeffs, cen=0, scale=1):
    def eval(self, xx):
        return np.polyval(coeffs, (xx - cen) / scale)

    return Bunch(xcen=cen, xscale=scale, coeffs=coeffs, call=eval)


# Routines for manipulating cubic B-splines defined on a regular
# unit-spaced grid


def bspEval(p0, coeffs, x):
    """Evaluate the sum of polyval(p0,x) and the spline defined by coefficients "coeffs"
       at the position "x" """
    nc = len(coeffs)
    y = np.polyval(p0, x)
    # The "inside" points require explicit calculation of the spline
    inside = (x > -2) & (x < nc + 1)
    x = x[inside]
    ix = np.array(np.floor(x), 'l')
    fx = x - ix
    w1 = np.polyval(np.array([1, 0, 0, 0], 'd') / 6, fx)
    w2 = np.polyval(np.array([-3, 3, 3, 1], 'd') / 6, fx)
    w3 = np.polyval(np.array([3, -6, 0, 4], 'd') / 6, fx)
    w4 = np.polyval(np.array([-1, 3, -3, 1], 'd') / 6, fx)
    pcoeffs = np.zeros(len(coeffs) + 4, coeffs.dtype)
    pcoeffs[1:-3] = coeffs
    y[inside] += w1 * pcoeffs[ix + 3] + w2 * pcoeffs[ix + 2] + \
        w3 * pcoeffs[ix + 1] + w4 * pcoeffs[ix]
    return y


def bspIntEval(coeffs, x):
    """Evaluate the integral of the spline defined by coefficients "coeffs" at the position "x" """
    nc = len(coeffs)
    y = np.zeros(x.shape, 'd')
    sCoeffs = np.cumsum(coeffs)
    # Initialize the y array with the cumulative sum
    ix = np.array(np.floor(x), 'l')
    good = (x >= 2) & (x < nc + 1)
    y[good] = sCoeffs[ix[good] - 2]
    # Treat points outside the range of the coefficients
    y[x >= nc + 1] = sum(coeffs)
    # The "inside" points require explicit calculation of the spline
    inside = (x > -2) & (x < nc + 1)
    x = x[inside]
    ix = ix[inside]
    fx = x - ix
    w1 = np.polyval(np.array([1, 0, 0, 0, 0], 'd') / 24, fx)
    w2 = np.polyval(np.array([-3, 4, 6, 4, 1], 'd') / 24, fx)
    w3 = np.polyval(np.array([3, -8, 0, 16, 12], 'd') / 24, fx)
    w4 = np.polyval(np.array([-1, 4, -6, 4, 23], 'd') / 24, fx)
    pcoeffs = np.zeros(len(coeffs) + 4, coeffs.dtype)
    pcoeffs[1:-3] = coeffs
    y[inside] += w1 * pcoeffs[ix + 3] + w2 * pcoeffs[ix + 2] + \
        w3 * pcoeffs[ix + 1] + w4 * pcoeffs[ix]
    return y


def bspUpdate(N, x, y):
    """Multiply the vector y by the transpose of the collocation matrix of a spline
        whose knots are at 0,1,2,...,N-1 and which is evaluated at the points in x"""
    result = np.zeros(N + 4, y.dtype)
    inside = (x > -2) & (x < N + 1)
    x = x[inside]
    y = y[inside]
    ix = np.array(np.floor(x), 'l')
    fx = x - ix
    W = np.zeros([len(ix), 4], 'd')
    W[:, 3] = np.polyval(np.array([1, 0, 0, 0], 'd') / 6, fx)
    W[:, 2] = np.polyval(np.array([-3, 3, 3, 1], 'd') / 6, fx)
    W[:, 1] = np.polyval(np.array([3, -6, 0, 4], 'd') / 6, fx)
    W[:, 0] = np.polyval(np.array([-1, 3, -3, 1], 'd') / 6, fx)
    for k in range(len(ix)):
        if ix[k] >= 0 and ix[k] < N:
            result[ix[k]:(ix[k] + 4)] = result[ix[k]:(ix[k] + 4)] + y[k] * W[k, :]
    return result[1:-3]


def bspInverse(p0, coeffs, y):
    """Looks up the values of y in a B-spline expansion + a linear polynomial.
    If the coefficients are such that the sum of the spline and the linear term
    is monotonic, an inverse cubic interpolation is performed. If not, the inverse
    interpolation is done using the linear term alone.

    Returns interpolated result together with a flag indicating if the spline+linear
    term is monotonic"""
    y = np.asarray(y)
    x0 = np.arange(1, len(coeffs) - 1, dtype='d')
    # Evaluate spline + linear polynomial at the knots
    ygrid = np.polyval(p0, x0) + (coeffs[:-2] + 4 * coeffs[1:-1] + coeffs[2:]) / 6.0
    # Check for monotonicity within the range of values at which inverse
    #  interpolation is performed
    ymin, ymax = y.min(), y.max()
    index = np.arange(len(ygrid))
    wmin = index[ygrid <= ymin].max()
    wmax = index[ygrid >= ymax].min()
    try:
        b = wmin + np.digitize(y, bins=ygrid[wmin:wmax + 1])
    except:
        return (y - p0[1]) / p0[0], False
    c1 = coeffs[b - 1]
    c2 = coeffs[b]
    c3 = coeffs[b + 1]
    c4 = coeffs[b + 2]
    # Array of cubic coefficients
    cc = np.zeros([len(y), 4], 'd')
    cc[:, 0] = (-c1 + 3 * c2 - 3 * c3 + c4) / 6.0
    cc[:, 1] = (c1 - 2 * c2 + c3) / 2.0
    cc[:, 2] = (-c1 + c3) / 2.0
    cc[:, 3] = (c1 + 4 * c2 + c3) / 6.0 - y
    x = np.array(b, dtype='d')
    for i in range(len(y)):
        pp = cc[i, :]
        pp[2] += p0[0]
        pp[3] += p0[0] * b[i] + p0[1]
        # Remove small leading coefficients since they lead to false
        #  complex roots when the cubic portion of the spline is close to zero
        thresh = 1.0e-8 * abs(pp[2])
        while abs(pp[0]) < thresh:
            pp = pp[1:]
        r = np.roots(pp)
        rr = r[(r == np.real(r)) & (r >= 0) & (r <= 1)]
        x[i] += np.real(rr[0])
        # time.sleep(0)
    return x, True


class BspInterp(object):
    def __init__(self, N):
        self.N = N
        self.coeffs = np.zeros(N + 4, 'd')
        self.weights = np.ones(N + 4, 'd')

    def eval(self, x):
        return bspEval([0], self.coeffs, x + 1.0)

    def seqUpdate(self, x, y, relax):
        """Update the coefficients of a B-spline so that it better interpolates
        the points (x,y). The points are processed sequentially, and the residual
        from a point is used for the next. A relaxation factor relax is used in the
        updating."""
        inside = (x > -2) & (x < self.N + 1)
        x = x[inside]
        y = y[inside]
        ix = np.array(np.floor(x), 'l')
        fx = x - ix
        W = np.zeros([len(ix), 4], 'd')
        W[:, 3] = np.polyval(np.array([1, 0, 0, 0], 'd') / 6, fx)
        W[:, 2] = np.polyval(np.array([-3, 3, 3, 1], 'd') / 6, fx)
        W[:, 1] = np.polyval(np.array([3, -6, 0, 4], 'd') / 6, fx)
        W[:, 0] = np.polyval(np.array([-1, 3, -3, 1], 'd') / 6, fx)
        for k in range(len(ix)):
            i = ix[k]
            if i >= 0 and i < self.N:
                self.coeffs[i:i + 4] = self.coeffs[i:i + 4] + relax * \
                    W[k, :] * (y[k] - np.dot(W[k, :], self.coeffs[i:i + 4]))

    def intEval(self, x):
        """Evaluate the integral of the spline defined by coefficients "coeffs" at the position "x" """
        y = np.zeros(x.shape, 'd')
        coeffs = self.coeffs[1:-3]
        sCoeffs = np.cumsum(coeffs)
        # Initialize the y array with the cumulative sum
        ix = np.array(np.floor(x), 'l')
        good = (x >= 2) & (x < self.N + 1)
        y[good] = sCoeffs[ix[good] - 2]
        # Treat points outside the range of the coefficients
        y[x >= self.N + 1] = sum(coeffs)
        # The "inside" points require explicit calculation of the spline
        inside = (x > -2) & (x < self.N + 1)
        x = x[inside]
        ix = ix[inside]
        fx = x - ix
        w1 = np.polyval(np.array([1, 0, 0, 0, 0], 'd') / 24, fx)
        w2 = np.polyval(np.array([-3, 4, 6, 4, 1], 'd') / 24, fx)
        w3 = np.polyval(np.array([3, -8, 0, 16, 12], 'd') / 24, fx)
        w4 = np.polyval(np.array([-1, 4, -6, 4, 23], 'd') / 24, fx)
        pcoeffs = np.zeros(len(coeffs) + 4, coeffs.dtype)
        pcoeffs[1:-3] = coeffs
        y[inside] += w1 * pcoeffs[ix + 3] + w2 * pcoeffs[ix + 2] + \
            w3 * pcoeffs[ix + 1] + w4 * pcoeffs[ix]
        return y


# Routines for ellipse fitting


def fitEllipse(X, Y):
    """Compute parameters of the best-fit ellipse to the 2D points (x,y).
    The result is returned as (x0,y0,r1,r2,phi) where (x0,y0) is the center
    of the ellipse, and r1 and r2 are the semi-principal axes lengths.
    The first principal axis makes an angle phi with the x axis"""
    # Normalize data
    mx = np.mean(X)
    my = np.mean(Y)
    sx = np.ptp(X) / 2.0
    sy = np.ptp(Y) / 2.0
    x = (X - mx) / sx
    y = (Y - my) / sy
    # Build normal matrix
    D = np.column_stack([x**2, x * y, y**2, x, y, np.ones(len(x), dtype="d")])
    S = np.dot(D.transpose(), D)
    # Build constraint matrix
    C = np.zeros([6, 6], dtype="d")
    C[0, 2] = -2
    C[1, 1] = 1
    C[2, 0] = -2
    # Solve generalized eigensystem
    tmpA = S[0:3, 0:3]
    tmpB = S[0:3, 3:]
    tmpC = S[3:, 3:]
    tmpD = C[0:3, 0:3]
    tmpE = np.dot(inv(tmpC), tmpB.transpose())
    [eval_x, evec_x] = eig(np.dot(inv(tmpD), (tmpA - np.dot(tmpB, tmpE))))
    # Extract eigenvector corresponding to non-positive eigenvalue
    A = evec_x[:, (np.real(eval_x) < 1e-8)]
    # Recover the bottom half
    evec_y = -np.dot(tmpE, A)
    A = np.vstack([A, evec_y]).ravel()
    # Unnormalize
    par = np.array([
        A[0] * sy * sy, A[1] * sx * sy, A[2] * sx * sx, -2 * A[0] * sy * sy * mx - A[1] * sx * sy * my + A[3] * sx * sy * sy,
        -A[1] * sx * sy * mx - 2 * A[2] * sx * sx * my + A[4] * sx * sx * sy, A[0] * sy * sy * mx * mx + A[1] * sx * sy * mx * my +
        A[2] * sx * sx * my * my - A[3] * sx * sy * sy * mx - A[4] * sx * sx * sy * my + A[5] * sx * sx * sy * sy
    ])
    # Find center of ellipse
    den = 4 * par[0] * par[2] - par[1]**2
    x0 = (par[1] * par[4] - 2 * par[2] * par[3]) / den
    y0 = (par[1] * par[3] - 2 * par[0] * par[4]) / den
    # Find orientation of ellipse
    phi = 0.5 * np.arctan2(par[1], par[0] - par[2])
    # Find semi principal axis lengths
    rr = par[0] * x0 * x0 + par[1] * x0 * y0 + par[2] * y0 * y0 - par[5]
    cphi = np.cos(phi)
    sphi = np.sin(phi)
    r1 = np.sqrt(rr / (par[0] * cphi * cphi + par[1] * cphi * sphi + par[2] * sphi * sphi))
    r2 = np.sqrt(rr / (par[0] * sphi * sphi - par[1] * cphi * sphi + par[2] * cphi * cphi))
    return (x0, y0, r1, r2, phi)


def parametricEllipse(X, Y):
    """Fit the 2D points (X,Y) by an ellipse such that
    X = x0 + A*np.cos(theta)
    Y = y0 + B*np.sin(theta+epsilon)
    The parameters are returned as (x0,y0,A,B,epsilon)"""
    (x0, y0, r1, r2, phi) = fitEllipse(X, Y)
    cphi = np.cos(phi)
    sphi = np.sin(phi)
    A = np.sqrt((r1 * cphi)**2 + (r2 * sphi)**2)
    B = np.sqrt((r1 * sphi)**2 + (r2 * cphi)**2)
    epsilon = np.arccos((r1 * r2) / (A * B))
    if (r1 > r2) ^ (cphi * sphi > 0):
        epsilon = -epsilon
    return (x0, y0, A, B, epsilon)


# Routine for reading in WLM files


class WlmFile(object):
    def __init__(self, fp):
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
            comps = [comp.strip() for comp in line.split("=", 1)]
            if len(comps) < 2:
                break
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
            comps = [comp.strip() for comp in line.split("=", 1)]
            if len(comps) < 2:
                break
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
                self.TLaser = np.array(self.data[self.colindex["Laser temperature"]], np.float_)
                self.WaveNumber = np.array(self.data[self.colindex["Wavenumber"]], np.float_)
                self.Ratio1 = np.array(self.data[self.colindex["Wavelength ratio 1"]], np.float_)
                self.Ratio2 = np.array(self.data[self.colindex["Wavelength ratio 2"]], np.float_)
                self.TEtalon = np.array(self.data[self.colindex["Etalon temperature"]], np.float_)
                self.Etalon1 = np.array(self.data[self.colindex["Etalon 1 (offset removed)"]], np.float_)
                self.Reference1 = np.array(self.data[self.colindex["Reference 1 (offset removed)"]], np.float_)
                self.Etalon2 = np.array(self.data[self.colindex["Etalon 2 (offset removed)"]], np.float_)
                self.Reference2 = np.array(self.data[self.colindex["Reference 2 (offset removed)"]], np.float_)
                self.PointsAveraged = np.array(self.data[self.colindex["Points averaged"]], int)
                # Effective calibration temperature for etalon
                self.Tcal = np.mean(self.TEtalon)

                self.generateWTCoeffs()

                return

            comps = line.split()
            for i in range(self.ncols):
                self.data[i].append(float(comps[i]))

    def generateWTCoeffs(self):
        self.WtoT = bestFitCentered(self.WaveNumber, self.TLaser, 3)
        self.TtoW = bestFitCentered(self.TLaser, self.WaveNumber, 3)


# Routine for reading calibration files for analyzers with no WLM
class NoWlmFile(object):
    def __init__(self, fp):
        """ Read data from a .nowlm file into an object """
        # Get parameter values
        while True:
            line = fp.readline()
            if line == "":
                raise Exception("Unexpected end of .nowlm file")
            if line.find('[Parameters]') >= 0:
                break
        self.parameters = {}
        while True:
            line = fp.readline()
            # Look parameter=value pairs
            comps = [comp.strip() for comp in line.split("=", 1)]
            if len(comps) < 2:
                break
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
            comps = [comp.strip() for comp in line.split("=", 1)]
            if len(comps) < 2:
                break
            self.colnames[int(comps[0])] = comps[1]
            self.colindex[comps[1]] = int(comps[0])
        # Skip to the line which marks the start of the data
        while True:
            line = fp.readline()
            if line == "":
                raise Exception("Unexpected end of .nowlm file")
            if line.find('[Data]') >= 0:
                break
        self.ncols = len(self.colnames.keys())
        self.data = []
        for i in range(self.ncols):
            self.data.append(list())
        while True:
            line = fp.readline()
            if line == "":
                self.TLaser = np.array(self.data[self.colindex["Laser temperature"]], np.float_)
                self.WaveNumber = np.array(self.data[self.colindex["Wavenumber"]], np.float_)
                # Calculating polynomial fits of Wavenumber vs Temperature"
                self.WtoT = bestFitCentered(self.WaveNumber, self.TLaser, 3)
                self.TtoW = bestFitCentered(self.TLaser, self.WaveNumber, 3)
                return
            comps = line.split()
            for i in range(self.ncols):
                self.data[i].append(float(comps[i]))


class SgdbrLookup(object):
    def __init__(self,
                 min_freq,
                 max_freq,
                 nfreq_to_front_coeffs,
                 nfreq_to_back_coeffs,
                 freq_to_phase_coeffs,
                 freq_to_phase_xoff,
                 freq_to_phase_yoff,
                 traj,
                 traj_num,
                 knots=None,
                 kindex=None,
                 mindex=None,
                 sfront=None,
                 sback=None,
                 coarse_phase_lookup=None):
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.nfreq_to_front_coeffs = nfreq_to_front_coeffs
        self.nfreq_to_back_coeffs = nfreq_to_back_coeffs
        self.freq_to_phase_coeffs = freq_to_phase_coeffs
        self.freq_to_phase_xoff = freq_to_phase_xoff
        self.freq_to_phase_yoff = freq_to_phase_yoff
        # traj is the trajectory number in the section name [SGDBR_n_LOOKUP_traj]
        self.traj = traj
        # traj_num is the trajectory number initially assigned during calibration while finding trajectories
        #  from the tuning surface. This may be different from traj if some trajectories were discarded during
        #  calibration
        self.traj_num = traj_num
        self.knots = knots
        self.kindex = kindex
        self.mindex = mindex
        self.sfront = sfront
        self.sback = sback
        self.coarse_phase_lookup = coarse_phase_lookup

    def freq_to_front(self, freq):
        if self.knots is None:
            nfreq = (freq - self.min_freq) / (self.max_freq - self.min_freq)
            return np.polyval(self.nfreq_to_front_coeffs, nfreq)
        else:
            indices = np.interp(freq, self.knots, self.kindex)
            return np.interp(indices, self.mindex, self.sfront)**2

    def freq_to_back(self, freq):
        if self.knots is None:
            nfreq = (freq - self.min_freq) / (self.max_freq - self.min_freq)
            return np.polyval(self.nfreq_to_back_coeffs, nfreq)
        else:
            indices = np.interp(freq, self.knots, self.kindex)
            return np.interp(indices, self.mindex, self.sback)**2

    def freq_to_phase(self, freqs, ymin=80.0, ymax=None):
        output = np.zeros(len(freqs), dtype=float)

        if self.coarse_phase_lookup is None:
            p = self.freq_to_phase_coeffs
            xoff = self.freq_to_phase_xoff
            yoff = self.freq_to_phase_yoff

            for i, xi in enumerate(freqs - xoff):
                a = p[4]
                b = p[2] + p[5] * xi
                c = p[0] + p[1] * xi + p[3] * xi * xi
                if ymax is None:
                    eta_min = ymin - yoff
                    n = np.floor(np.polyval(np.asarray([a, b, c]), eta_min) / np.pi)
                else:
                    eta_max = ymax - yoff
                    n = np.ceil(np.polyval(np.asarray([a, b, c]), eta_max) / np.pi)
                disc = b * b - 4 * a * (c - n * np.pi)
                if disc > 0:
                    eta = (-b - np.sqrt(disc)) / (2 * a)
                else:
                    eta = -b / (2 * a)
                output[i] = (eta + yoff)**2
        else:
            # Use coarse phase lookup object to calculate
            #  coarse phase current
            bins = np.digitize(freqs, self.coarse_phase_lookup["ref_freqs"])
            periods = self.coarse_phase_lookup["periods"]
            ripples = np.zeros(2*len(periods), dtype=float)
            for i, freq in enumerate(freqs):
                frag_index = max(bins[i] - 1, 0)
                xoff = self.coarse_phase_lookup["ref_freqs"][frag_index]
                coeffs = self.coarse_phase_lookup["coeffs"][frag_index]
                x = freq - xoff
                ripples[0::2] = np.cos(2.0*np.pi*x/periods)
                ripples[1::2] = np.sin(2.0*np.pi*x/periods)
                output[i] = (np.polyval(coeffs[:3], x) + np.dot(coeffs[3:], ripples))**2
                if output[i] > 32000:
                    output[i] = 0
                    raise ValueError("Overcurrent in spline calculation")

        return output

    @classmethod
    def from_ini(cls, ini, traj):
        # Functions to read in coarse phase lookup coefficients
        def get_coeffs(config, ncoeffs):
            return np.asarray([config.as_float("C%d" % n) for n in range(ncoeffs)])

        def freq_to_phase_lookup(config):
            periods = np.asarray([config.as_float("PERIOD_%d" % n) for n in range(config.as_int("PERIODS"))])
            ref_freqs = np.asarray([config["FRAGMENT_%d" % n].as_float("REF_FREQ") for n in range(config.as_int("FRAGMENTS"))])
            ncoeffs = 3 + 2*len(periods)
            coeffs = [get_coeffs(config["FRAGMENT_%d" % n], ncoeffs) for n in range(config.as_int("FRAGMENTS"))]
            return dict(periods=periods, ref_freqs=ref_freqs, coeffs=coeffs)

        try:
            min_freq = ini.as_float("MIN_FREQ")
            max_freq = ini.as_float("MAX_FREQ")
            nfreq_to_front_dict = {}
            nfreq_to_back_dict = {}
            freq_to_phase_dict = {}
            freq_to_phase_xoff = None
            freq_to_phase_yoff = None
            knots_dict = {}
            kindex_dict = {}
            mindex_dict = {}
            sfront_dict = {}
            sback_dict = {}
            traj_num = None
            fragments = 0
            coarse_phase_lookup = None

            for opt in ini:
                m = re.match("NFREQ_TO_FRONT_([0-9]+)", opt)
                if m:
                    nfreq_to_front_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("NFREQ_TO_BACK_([0-9]+)", opt)
                if m:
                    nfreq_to_back_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("KNOTS_([0-9]+)", opt)
                if m:
                    knots_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("KINDEX_([0-9]+)", opt)
                if m:
                    kindex_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("MINDEX_([0-9]+)", opt)
                if m:
                    mindex_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("SFRONT_([0-9]+)", opt)
                if m:
                    sfront_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("SBACK_([0-9]+)", opt)
                if m:
                    sback_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("FREQ_TO_PHASE_([0-9]+)", opt)
                if m:
                    freq_to_phase_dict[int(m.group(1))] = ini.as_float(opt)
                m = re.match("FREQ_TO_PHASE_XOFF", opt)
                if m:
                    freq_to_phase_xoff = ini.as_float(opt)
                m = re.match("FREQ_TO_PHASE_YOFF", opt)
                if m:
                    freq_to_phase_yoff = ini.as_float(opt)
                m = re.match("TRAJ_NUM", opt)
                if m:
                    traj_num = ini.as_int(opt)
                m = re.match("FRAGMENTS", opt)
                if m:
                    fragments = ini.as_int(opt)

            if knots_dict:
                knots_coeffs = np.zeros(max(knots_dict.keys()) + 1)
                kindex_coeffs = np.zeros(max(kindex_dict.keys()) + 1)
                mindex_coeffs = np.zeros(max(mindex_dict.keys()) + 1)
                sfront_coeffs = np.zeros(max(sfront_dict.keys()) + 1)
                sback_coeffs = np.zeros(max(sback_dict.keys()) + 1)
                for k in knots_dict:
                    knots_coeffs[k] = knots_dict[k]
                for k in kindex_dict:
                    kindex_coeffs[k] = kindex_dict[k]
                for k in mindex_dict:
                    mindex_coeffs[k] = mindex_dict[k]
                for k in sfront_dict:
                    sfront_coeffs[k] = sfront_dict[k]
                for k in sback_dict:
                    sback_coeffs[k] = sback_dict[k]
                nfreq_to_front_coeffs = None
                nfreq_to_back_coeffs = None
            else:
                nfreq_to_front_coeffs = np.zeros(max(nfreq_to_front_dict.keys()) + 1)
                nfreq_to_back_coeffs = np.zeros(max(nfreq_to_back_dict.keys()) + 1)
                freq_to_phase_coeffs = np.zeros(max(freq_to_phase_dict.keys()) + 1)
                for k in nfreq_to_front_dict:
                    nfreq_to_front_coeffs[k] = nfreq_to_front_dict[k]
                for k in nfreq_to_back_dict:
                    nfreq_to_back_coeffs[k] = nfreq_to_back_dict[k]
                knots_coeffs = None
                kindex_coeffs = None
                mindex_coeffs = None
                sfront_coeffs = None
                sback_coeffs = None

            freq_to_phase_coeffs = np.zeros(max(freq_to_phase_dict.keys()) + 1)
            for k in freq_to_phase_dict:
                freq_to_phase_coeffs[k] = freq_to_phase_dict[k]

            if fragments > 0:
                coarse_phase_lookup = freq_to_phase_lookup(ini)

            return cls(min_freq, max_freq, nfreq_to_front_coeffs, nfreq_to_back_coeffs, freq_to_phase_coeffs, freq_to_phase_xoff,
                       freq_to_phase_yoff, traj, traj_num, knots_coeffs, kindex_coeffs, mindex_coeffs, sfront_coeffs, sback_coeffs,
                       coarse_phase_lookup)
        except:
            print("Exception while loading SGDBR lookup section")
            raise ValueError

    def to_ini(self, ini, sec_name):
        ini[sec_name] = {}
        ini[sec_name]["MIN_FREQ"] = self.min_freq
        ini[sec_name]["MAX_FREQ"] = self.max_freq
        if self.knots is None:
            for j, coeff in enumerate(self.nfreq_to_front_coeffs):
                ini[sec_name]["NFREQ_TO_FRONT_%d" % j] = coeff
            for j, coeff in enumerate(self.nfreq_to_back_coeffs):
                ini[sec_name]["NFREQ_TO_BACK_%d" % j] = coeff
        else:
            for j, coeff in enumerate(self.knots):
                ini[sec_name]["KNOTS_%d" % j] = coeff
            for j, coeff in enumerate(self.kindex):
                ini[sec_name]["KINDEX_%d" % j] = coeff
            for j, coeff in enumerate(self.mindex):
                ini[sec_name]["MINDEX_%d" % j] = coeff
            for j, coeff in enumerate(self.sfront):
                ini[sec_name]["SFRONT_%d" % j] = coeff
            for j, coeff in enumerate(self.sback):
                ini[sec_name]["SBACK_%d" % j] = coeff

        for j, coeff in enumerate(self.freq_to_phase_coeffs):
            ini[sec_name]["FREQ_TO_PHASE_%d" % j] = coeff
        ini[sec_name]["FREQ_TO_PHASE_XOFF"] = self.freq_to_phase_xoff
        ini[sec_name]["FREQ_TO_PHASE_YOFF"] = self.freq_to_phase_yoff
        ini[sec_name]["TRAJ_NUM"] = self.traj_num


class WidebandWlm(object):
    # Manipulates transformation from pseudo-angle to wavenumber
    # A cubic spline with angle separation of 0.3 radians is adequate to represent the mapping
    #  to frequency

    def __init__(self):
        self.phiMin = None
        self.phiMax = None
        self.nuMin = None
        self.nuMax = None
        self.phiArray = None
        self.nuArray = None
        self.phiSamp = 0.3

    def loadFromIni(self, ini, paramSec):
        self.phiMin = float(ini[paramSec]["PHI_MIN"])
        self.phiMax = float(ini[paramSec]["PHI_MAX"])
        self.ratio1Cen = float(ini[paramSec]["RATIO1_CENTER"])
        self.ratio2Cen = float(ini[paramSec]["RATIO2_CENTER"])
        self.phiBins = int(ini[paramSec].get("PHI_BINS", 0))
        phi = np.linspace(self.phiMin - self.phiSamp, self.phiMax + self.phiSamp,
                          3 + int(np.ceil((self.phiMax - self.phiMin) / self.phiSamp)))
        self.phiArray = phi
        self.nuArray = np.zeros_like(self.phiArray)
        self.filt = np.zeros(phi.shape, dtype=bool)
        if self.phiBins == 0:
            self.filt = (self.phiArray >= self.phiMin) & (self.phiArray <= self.phiMax)
            for optName in ini[paramSec]:
                m = re.match("([CS])([0-9])([0-9])", optName)
                if m:
                    coeff = float(ini[paramSec][optName])
                    ftype, harmonic, power = (m.group(1), int(m.group(2)), int(m.group(3)))
                    self.nuArray += coeff * self.phiArray**power * \
                        (np.cos if ftype == "C" else np.sin)(harmonic * self.phiArray)
        elif self.phiBins < 0:
            # Handle Chebyshev-weighted coefficients
            phi_norm = 2.0 * (self.phiArray - self.phiMin)/(self.phiMax - self.phiMin) - 1.0
            phi_norm = np.maximum(np.minimum(phi_norm, 1.0), -1.0)
            self.filt = (self.phiArray >= self.phiMin) & (self.phiArray <= self.phiMax)
            for optName in ini[paramSec]:
                m = re.match("T([CS])([0-9])([0-9])", optName)
                if m:
                    coeff = float(ini[paramSec][optName])
                    ftype, harmonic, power = (m.group(1), int(m.group(2)), int(m.group(3)))
                    cheby = np.cos(power*np.arccos(phi_norm))
                    self.nuArray += coeff * cheby * \
                        (np.cos if ftype == "C" else np.sin)(harmonic * (self.phiArray - self.phiMin))
        else:
            for bin in range(self.phiBins):
                binSec = "%s_%d" % (
                    paramSec,
                    bin,
                )
                phiValidMin = phiMin = float(ini[binSec]["PHI_MIN"])
                phiValidMax = float(ini[binSec]["PHI_MAX"])
                # Introduce valid range of WLM angles within the region
                #  so that we can ignore regions for which there are no data
                if "PHI_VALID_MIN" in ini[binSec]:
                    phiValidMin = float(ini[binSec]["PHI_VALID_MIN"])
                if "PHI_VALID_MAX" in ini[binSec]:
                    phiValidMax = float(ini[binSec]["PHI_VALID_MAX"])
                which = (self.phiArray >= phiValidMin) & (self.phiArray <= phiValidMax)
                self.filt |= which
                self.nuArray[which] = 0
                for optName in ini[binSec]:
                    phi = self.phiArray[which] - phiMin
                    m = re.match("([CS])([0-9])([0-9])", optName)
                    if m:
                        coeff = float(ini[binSec][optName])
                        ftype, harmonic, power = (m.group(1), int(m.group(2)), int(m.group(3)))
                        self.nuArray[which] += coeff * phi**power * \
                            (np.cos if ftype == "C" else np.sin)(harmonic * phi)
        # Calculate splines for rapid computation of transformations
        self.phiArray = self.phiArray[self.filt]
        self.nuArray = self.nuArray[self.filt]
        tck1 = splrep(self.phiArray, self.nuArray, s=0)
        self.phiToFreq = lambda x, wlmOffsetValue: splev(x, tck1) + wlmOffsetValue
        tck2 = splrep(self.nuArray, self.phiArray, s=0)
        self.freqToPhi = lambda x, wlmOffsetValue: splev(x - wlmOffsetValue, tck2)


class SgdbrCal(object):
    # Calibration for an SGDBR laser involves a WidebandWlm object for translating frequency to wavelength monitor
    #  angle and a list of SgdbrLookup objects for the tuning trajectories
    def __init__(self, ini, laserIdent):
        """Reads the WidebandWlm and SgdbrLookup information for 'laserIdent' which
           can be 'A', 'B', 'C' or 'D'"""
        self.widebandWlm = None
        self.sgdbrLuts = []
        self.breaks = None
        self.trajs = None
        prefix = "SGDBR_%s" % laserIdent
        paramSec = prefix + "_PHI_TO_FREQ"
        if paramSec in ini:
            self.widebandWlm = WidebandWlm()
            self.widebandWlm.loadFromIni(ini, paramSec)
            for traj in itertools.count():
                sec_name = prefix + "_LOOKUP_%d" % traj
                if sec_name not in ini:
                    break
                self.sgdbrLuts.append(SgdbrLookup.from_ini(ini[sec_name], traj))
        traj_select = prefix + "_TRAJ_SELECT"
        if traj_select in ini:
            breaks = {}
            trajs = {}
            for key in ini[traj_select]:
                if key.startswith("BREAK_"):
                    breaks[int(key[len("BREAK_"):])] = float(ini[traj_select][key])
                elif key.startswith("TRAJ_"):
                    if ini[traj_select][key].strip():
                        trajs[int(key[len("TRAJ_"):])] = [int(x) for x in ini[traj_select][key].split(',')]
                    else:
                        trajs[int(key[len("TRAJ_"):])] = []
            if breaks.keys() != trajs.keys():
                raise ValueError("Mismatch between BREAK and TRAJ entries")
            self.breaks = np.asarray([breaks[i] for i in sorted(breaks)])
            self.trajs = [trajs[i] for i in sorted(trajs)]


class AutoCal(object):
    # Calibration requires us to store:
    # Laser calibration constants which map laser temperature to laser wavenumber
    # WLM constants: ratio1Center, ratio2Center, ratio1Scale, ratio2Scale, wlmPhase, wlmTempSensitivity, tEtalonCal
    # Spline scaling constants: dTheta, thetaBase
    # Linear term for spline: sLinear

    def __init__(self):
        self.lock = threading.Lock()  # Protects access to the parameters
        self.offset = 0
        # If this is non-zero, an error has occured in the frequency-angle
        # conversion
        self.autocalStatus = 0
        #  Currently bit 0 indicates a non-monotonic spline for frequency conversion
        # Reset whenever the Autocal object is reloaded from an INI or WLM file
        self.thetaMeasured = None
        self.waveNumberMeasured = None
        self.ignoreSpline = False
        self.tempOffset = 0.0
        self.laserType = 0
        self.sgdbrCal = None  # Set if laserType == 1, i.e., if this is an SGDBR laser
        self.baseTemp = 15.0  # Temperature for SGDBR laser. May be overridden in warm box calibration file.

    def loadFromWlmFile(self, wlmFile, dTheta=0.05, wMin=None, wMax=None):
        # Construct an Autocal object from a WlmFile object based on measured data which lie within the
        #  wavenumber range wMin to wMax
        with self.lock:
            # Select those data which lie within the specified range of
            # wavenumbers
            if wMin is None:
                wMin = wlmFile.WaveNumber.min()
            if wMax is None:
                wMax = wlmFile.WaveNumber.max()
            if wMin < wlmFile.WaveNumber.min() or wMax > wlmFile.WaveNumber.max():
                raise ValueError("Range of wavenumbers requested is not available in WLM file")
            window = (wlmFile.WaveNumber >= wMin) & (wlmFile.WaveNumber <= wMax)
            # Fit ratios to a parametric ellipse
            self.ratio1Center, self.ratio2Center, self.ratio1Scale, self.ratio2Scale, self.wlmPhase = \
                parametricEllipse(
                    wlmFile.Ratio1[window], wlmFile.Ratio2[window])
            # Ensure that both ratioScales are larger than 1.05 to avoid issues
            # with ratio multipliers exceeding 1
            factor = 1.05 / min([self.ratio1Scale, self.ratio2Scale])
            self.ratio1Scale *= factor
            self.ratio2Scale *= factor
            self.tEtalonCal = wlmFile.Tcal
            # Calculate the unwrapped WLM angles
            X = wlmFile.Ratio1[window] - self.ratio1Center
            Y = wlmFile.Ratio2[window] - self.ratio2Center
            thetaCalMeasured = np.unwrap(
                np.arctan2(self.ratio1Scale * Y - self.ratio2Scale * X * np.sin(self.wlmPhase),
                           self.ratio2Scale * X * np.cos(self.wlmPhase)))
            # Extract parameters of angle vs laser temperature
            self.laserTemp2WaveNumber = lambda T: wlmFile.TtoW(T - self.tempOffset)
            self.waveNumber2LaserTemp = lambda W: wlmFile.WtoT(W) + self.tempOffset
            # Extract parameters of wavenumber against angle
            thetaCal2WaveNumber = bestFit(thetaCalMeasured, wlmFile.WaveNumber[window], 1)
            # Include Burleigh data in object for plotting and debug
            self.thetaMeasured = thetaCalMeasured
            self.waveNumberMeasured = wlmFile.WaveNumber[window]
            # Extract spline scaling constants
            self.thetaBase = (wMin - thetaCal2WaveNumber.coeffs[1]) / thetaCal2WaveNumber.coeffs[0]
            self.dTheta = dTheta
            self.sLinear0 = np.array([thetaCal2WaveNumber.coeffs[0] * self.dTheta,
                                      thetaCal2WaveNumber([self.thetaBase])[0]],
                                     dtype="d")
            self.sLinear = self.sLinear0 + np.array([0.0, self.offset])
            # Find number of spline coefficients needed and initialize the
            # coefficients to zero
            self.nCoeffs = int(np.ceil((wMax - wMin) / (thetaCal2WaveNumber.coeffs[0] * self.dTheta)))
            self.coeffs = np.zeros(self.nCoeffs, dtype="d")
            self.coeffsOrig = np.zeros(self.nCoeffs, dtype="d")
            # Temperature sensitivity of etalon
            self.wlmTempSensitivity = -0.185 * \
                (np.mean(wlmFile.WaveNumber[window]) / 6158.0)  # radians/degC
            self.autocalStatus = 0
        return self

    def loadFromEepromDict(self, eepromDict, dTheta, wMin, wMax):
        # Construct an Autocal object from a Eeprom dictionary based on measured data which lie within the
        #  wavenumber range wMin to wMax
        with self.lock:
            ratio1 = np.array([row['ratio1'] for row in eepromDict['wlmCalRows']])
            ratio2 = np.array([row['ratio2'] for row in eepromDict['wlmCalRows']])
            waveNumber = np.array([1.0e-5 * row['waveNumberAsUint'] for row in eepromDict['wlmCalRows']])
            # Select those data which lie within the specified range of
            # wavenumbers
            if wMin < waveNumber.min() or wMax > waveNumber.max():
                raise ValueError("Range of wavenumbers requested is not available in EEPROM")
            window = (waveNumber >= wMin) & (waveNumber <= wMax)
            # Fit ratios to a parametric ellipse
            self.ratio1Center, self.ratio2Center, self.ratio1Scale, self.ratio2Scale, self.wlmPhase = \
                parametricEllipse(ratio1[window], ratio2[window])
            # Ensure that both ratioScales are larger than 1.05 to avoid issues
            # with ratio multipliers exceeding 1
            factor = 1.05 / min([self.ratio1Scale, self.ratio2Scale])
            self.ratio1Scale *= factor
            self.ratio2Scale *= factor
            self.tEtalonCal = float(eepromDict['header']['etalon_temperature'])
            # Calculate the unwrapped WLM angles
            X = ratio1[window] - self.ratio1Center
            Y = ratio2[window] - self.ratio2Center
            thetaCalMeasured = np.unwrap(
                np.arctan2(self.ratio1Scale * Y - self.ratio2Scale * X * np.sin(self.wlmPhase),
                           self.ratio2Scale * X * np.cos(self.wlmPhase)))
            # Extract parameters of wavenumber against angle
            thetaCal2WaveNumber = bestFit(thetaCalMeasured, waveNumber[window], 1)
            # Extract spline scaling constants
            self.thetaBase = (wMin - thetaCal2WaveNumber.coeffs[1]) / thetaCal2WaveNumber.coeffs[0]
            self.dTheta = dTheta
            self.sLinear0 = np.array([thetaCal2WaveNumber.coeffs[0] * self.dTheta,
                                      thetaCal2WaveNumber([self.thetaBase])[0]],
                                     dtype="d")
            self.sLinear = self.sLinear0 + np.array([0.0, self.offset])
            # Find number of spline coefficients needed and initialize the
            # coefficients to zero
            self.nCoeffs = int(np.ceil((wMax - wMin) / (thetaCal2WaveNumber.coeffs[0] * self.dTheta)))
            self.coeffs = np.zeros(self.nCoeffs, dtype="d")
            self.coeffsOrig = np.zeros(self.nCoeffs, dtype="d")
            # Temperature sensitivity of etalon
            self.wlmTempSensitivity = -0.185 * \
                (np.mean(waveNumber[window]) / 6158.0)  # radians/degC
            self.autocalStatus = 0
        return self

    def loadFromIni(self, ini, vLaserNum):
        """Fill up the AutoCal structure based on the information in the .ini file
        using the specified "vLaserNum" to indicate which virtual laser (1-origin) is involved.
        The INI file must have valid ACTUAL_LASER and LASER_MAP sections as well as the
        VIRTUAL_PARAMS, VIRTUAL_CURRENT and VIRTUAL_ORIGINAL sections for the specified
        vLaserNum. If the VIRTUAL_* sections are all missing, this returns None indicating
        that the specified virtual laser is absent. Otherwise, an exception is raised."""
        def fetchCoeffs(sec, prefix):
            # Fetches coefficients from a section of an INI file into a list
            coeffs = []
            i = 0
            while True:
                try:
                    coeffs.append(float(sec["%s%d" % (prefix, i)]))
                    i += 1
                except:
                    break
            return coeffs

        with self.lock:
            paramSec = "VIRTUAL_PARAMS_%d" % vLaserNum
            currentSec = "VIRTUAL_CURRENT_%d" % vLaserNum
            originalSec = "VIRTUAL_ORIGINAL_%d" % vLaserNum

            if (paramSec not in ini) and (currentSec not in ini) and (originalSec not in ini):
                return None  # i.e., vLaserNum is not specified
            if paramSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % paramSec)
            if currentSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % currentSec)
            if originalSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % originalSec)
            # Find the actual laser
            mapSec = "LASER_MAP"
            self.currentActiveIni = ini
            if mapSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s" % mapSec)
            aLaserNum = int(ini[mapSec]["ACTUAL_FOR_VIRTUAL_%d" % vLaserNum])
            aLaserSec = "ACTUAL_LASER_%d" % aLaserNum
            if aLaserSec not in ini:
                raise ValueError("loadFromIni failed due to missing section %s (required by virtual laser %d)" %
                                 (aLaserSec, vLaserNum))
            cen = float(ini[aLaserSec]["WAVENUM_CEN"])
            scale = float(ini[aLaserSec]["WAVENUM_SCALE"])
            coeffs = np.array(fetchCoeffs(ini[aLaserSec], "W2T_"))
            # Function w2t is defined here so that changes in coeffs, cen and scale before self.waveNumber2LaserTemp
            #  is called do not affect its value. However, we do want self.tempOffset to be evaluated when
            #  self.waveNumber2LaserTemp is invoked.
            w2t = polyFitEvaluator(coeffs, cen, scale)
            self.waveNumber2LaserTemp = lambda W: w2t(W) + self.tempOffset

            cen = float(ini[aLaserSec]["TEMP_CEN"])
            scale = float(ini[aLaserSec]["TEMP_SCALE"])
            coeffs = np.array(fetchCoeffs(ini[aLaserSec], "T2W_"))
            # Function t2w is defined here so that changes in coeffs, cen and scale before self.laserTemp2WaveNumber
            #  is called do not affect its value. However, we do want self.tempOffset to be evaluated when
            #  self.laserTemp2WaveNumber is invoked.
            t2w = polyFitEvaluator(coeffs, cen, scale)
            self.laserTemp2WaveNumber = lambda T: t2w(T - self.tempOffset)
            if "LASER_TYPE" in ini[aLaserSec]:
                self.laserType = int(ini[aLaserSec]["LASER_TYPE"])
            self.baseTemp = float(ini[aLaserSec].get("BASE_TEMP", 15.0))

            self.ratio1Center = float(ini[paramSec]["RATIO1_CENTER"])
            self.ratio2Center = float(ini[paramSec]["RATIO2_CENTER"])
            self.ratio1Scale = float(ini[paramSec]["RATIO1_SCALE"])
            self.ratio2Scale = float(ini[paramSec]["RATIO2_SCALE"])
            self.wlmPhase = float(ini[paramSec]["PHASE"])
            self.tEtalonCal = float(ini[paramSec]["CAL_TEMP"])
            self.wlmTempSensitivity = float(ini[paramSec]["TEMP_SENSITIVITY"])
            self.thetaBase = float(ini[paramSec]["ANGLE_BASE"])
            self.dTheta = float(ini[paramSec]["ANGLE_INCREMENT"])
            self.sLinear0 = np.array([float(ini[paramSec]["LINEAR_MODEL_SLOPE"]), float(ini[paramSec]["LINEAR_MODEL_OFFSET"])])
            self.offset = float(ini[paramSec]["WLM_OFFSET"])
            self.sLinear = self.sLinear0 + np.array([0.0, self.offset])
            self.tempOffset = float(ini[paramSec].get("TEMP_OFFSET", 0.0))
            self.nCoeffs = int(ini[paramSec]["NCOEFFS"])

            self.coeffs = []
            for i in range(self.nCoeffs):
                self.coeffs.append(float(ini[currentSec]["COEFF%d" % i]))
            self.coeffs = np.array(self.coeffs)
            self.autocalStatus = 0

            self.coeffsOrig = []
            for i in range(self.nCoeffs):
                self.coeffsOrig.append(float(ini[originalSec]["COEFF%d" % i]))
            self.coeffsOrig = np.array(self.coeffsOrig)
            return self

    def updateIni(self, ini, vLaserNum):
        """Update (and possibly create) sections and keys in "ini" to describe the current
        AutoCal object, using the specified "vLaserNum" to indicate which virtual laser
        (1-origin) is involved"""
        self.lock.acquire()

        # For some unknow reason, may be 1:100 times the read in config is object is empty and the update
        # results in a corrupt warmbox active file that is missing the necessary "ACTUAL_LASER_#"
        # and "LASER_MAP" sections.  I think there is a race condition where the ConfigObj module
        # can get confused and return an empty ConfigObj object after reading a valid warmbox
        # ini file.
        #
        # So what we are doing in the original warmbox file read is to save it to currentActiveIni.
        # If we are doing an update with new spline coefficients we look at the ini object to
        # update.  If it's missing the ACTUAL_LASER AND LASER_MAP sections, rewrite our saved
        # copies to the config obj getting the new spline coefficients.
        # RSF 20171022
        #
        # This method is also called by Host/MfgUtilities/makeCalFromEeproms.py during the
        # initial configuration of a new analyzer. In this mode the IntegrationTool does
        # not load an active file, loadFromIni() is not called, and so self.currentActiveIni
        # remains equal to None.  If currentActiveIni is None, we assume we are are
        # configuring a new analyzer and bypass this section.
        # This fixes bug I2-434.
        # RSF 20180123
        #
        if self.currentActiveIni is not None:
            for key in self.currentActiveIni.keys():
                if "ACTUAL_LASER" in key and key not in ini:
                    print("Writing key:", key)
                    ini[key] = self.currentActiveIni[key]
            print("Writing laser_map")
            if "LASER_MAP" not in ini:
                ini["LASER_MAP"] = self.currentActiveIni["LASER_MAP"]

        try:
            paramSec = "VIRTUAL_PARAMS_%d" % vLaserNum
            currentSec = "VIRTUAL_CURRENT_%d" % vLaserNum
            originalSec = "VIRTUAL_ORIGINAL_%d" % vLaserNum
            if paramSec not in ini:
                ini[paramSec] = {}
                # Following options are not overwritten if they are already in
                # the INI file
                ini[paramSec]["CAL_PRESSURE"] = 760.0
                ini[paramSec]["PRESSURE_C0"] = 0.0
                ini[paramSec]["PRESSURE_C1"] = 0.0
                ini[paramSec]["PRESSURE_C2"] = 0.0
                ini[paramSec]["PRESSURE_C3"] = 0.0
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
            ini[paramSec]["TEMP_OFFSET"] = self.tempOffset
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

    def thetaCal2WaveNumber(self, thetaCal):
        """Look up in current calibration to get wavenumbers from WLM angles"""
        with self.lock:
            x = (thetaCal - self.thetaBase) / self.dTheta
            if self.ignoreSpline:
                return np.polyval(self.sLinear, x)
            else:
                return bspEval(self.sLinear, self.coeffs, x)

    def calcInjectSettings(self, waveNum, schemeRows, traj_filt=-1):
        result = dict(laserType=self.laserType)
        if self.laserType == 0:
            wlmAngle = self.waveNumber2ThetaCal(waveNum)
            result["angleSetpoint"] = wlmAngle
            result["laserTemp"] = self.thetaCal2LaserTemp(wlmAngle)
        elif self.laserType == 1:
            with self.lock:
                done = np.zeros(len(waveNum), bool)
                npts = len(waveNum)
                frontMirrorDac = {}
                backMirrorDac = {}
                coarsePhaseDac = {}
                # Use -1.0e6 as the angle setpoint to indicate an inaccessible frequency
                #  (NaN is not handled properly by TI C compiler)
                angleSetpoint = {}
                laserTemp = {}
                traj_selected = None
                if self.sgdbrCal.breaks is not None:
                    # Determine trajectories for each wavenumber by looking these up within the collection of breakpoints
                    #  Choose the first suitable trajectory for subiterval associated with the breakpoints
                    # -1 indicates that no suitable trajectory exists
                    traj_selected = np.zeros(waveNum.shape, int)
                    for i, subinterval in enumerate(np.digitize(waveNum, self.sgdbrCal.breaks)):
                        traj_selected[i] = self.sgdbrCal.trajs[subinterval - 1][0] if subinterval > 0 else -1
                for sgdbrLut in self.sgdbrCal.sgdbrLuts:
                    if traj_filt >= 0 and sgdbrLut.traj != traj_filt:
                        continue
                    if done.all():
                        break
                    # We select the trajectory either on the basis of the min_freq to max_freq
                    #  range in the [SGDBR_x_LOOKUP_n] section of the calibration file or on the basis
                    #  of the [SGDBR_x_TRAJ_SELECT] section if this exists
                    if self.sgdbrCal.breaks is None or traj_filt >= 0:
                        sel = ((sgdbrLut.min_freq <= waveNum) & (waveNum < sgdbrLut.max_freq) & ~done)
                    else:
                        sel = (traj_selected == sgdbrLut.traj)
                    if sel.any():
                        # Log("In calcInjectSettings", 
                        #     Verbose="Selection vector for ringdowns: %s for trajectory %s" % (sel, sgdbrLut.traj))
                        front = sgdbrLut.freq_to_front(waveNum[sel])
                        back = sgdbrLut.freq_to_back(waveNum[sel])
                        # The offset 5439.5 (used to be 1418) depends on the relative gain of
                        #  the fine and coarse phase current sources. It represents the
                        #  coarse digitizer units which give the same current as 32768
                        #  fine digitizer units
                        # Based on resistor values R23=15k, R21=2490, offset is 32768 * R21 / R23
                        # coarsePhase = sgdbrLut.freq_to_phase(waveNum[sel]) - 5439.5
                        coarsePhase = np.maximum(500.0, sgdbrLut.freq_to_phase(waveNum[sel], ymin=75) - 5439.5)
                        setpoint = self.sgdbrCal.widebandWlm.freqToPhi(waveNum[sel], self.offset)
                        # Populate the results
                        for j, i in enumerate(schemeRows[sel]):
                            frontMirrorDac[i] = front[j]
                            backMirrorDac[i] = back[j]
                            coarsePhaseDac[i] = coarsePhase[j]
                            angleSetpoint[i] = setpoint[j]
                            laserTemp[i] = self.baseTemp
                        done[sel] = True
                if not done.all():
                    print("%d scheme frequencies are not accessible and will be skipped" % (len(done) - sum(done), ))
                result["frontMirrorDac"] = frontMirrorDac
                result["backMirrorDac"] = backMirrorDac
                result["coarsePhaseDac"] = coarsePhaseDac
                result["angleSetpoint"] = angleSetpoint
                result["laserTemp"] = laserTemp
        else:
            raise ValueError("Unknown laser type while compiling scheme")
        return result

    def calcWaveNumber(self, thetaCal, laserTemp):
        if self.laserType == 0:
            return self.thetaCalAndLaserTemp2WaveNumber(thetaCal, laserTemp)
        else:
            return self.sgdbrCal.widebandWlm.phiToFreq(thetaCal, self.getOffset())

    def thetaCalAndLaserTemp2WaveNumber(self, thetaCal, laserTemp):
        """Use laser temperature to place calibrated angles on the correct revolution and look up
        in current calibration to get wavenumbers"""
        self.lock.acquire()
        try:
            approxWaveNum = self.laserTemp2WaveNumber(laserTemp)
            # Convert wavenumber to thetaHat via inverse of linear model
            thetaHat = self.thetaBase + self.dTheta * \
                (approxWaveNum - self.sLinear[1]) / self.sLinear[0]
            thetaCal += 2 * np.pi * \
                np.floor((thetaHat - thetaCal) / (2 * np.pi) + 0.5)
            x = (thetaCal - self.thetaBase) / self.dTheta
            if self.ignoreSpline:
                return np.polyval(self.sLinear, x)
            else:
                return bspEval(self.sLinear, self.coeffs, x)
        finally:
            self.lock.release()

    def laserTemp2ThetaCal(self, laserTemp):
        """Determine calibrated WLM angle associated with given laser temperature"""
        self.lock.acquire()
        try:
            approxWaveNum = self.laserTemp2WaveNumber(laserTemp)
            # Convert wavenumber to angle via inverse of linear model
            return self.thetaBase + self.dTheta * (approxWaveNum - self.sLinear[1]) / self.sLinear[0]
        finally:
            self.lock.release()

    def thetaCal2LaserTemp(self, thetaCal):
        """Determine laser temperature to target to achieve a particular calibrated WLM angle"""
        self.lock.acquire()
        try:
            x = (thetaCal - self.thetaBase) / self.dTheta
            waveNum = np.polyval(self.sLinear, x)
            return self.waveNumber2LaserTemp(waveNum)
        finally:
            self.lock.release()

    def waveNumber2ThetaCal(self, waveNumbers):
        """Look up current calibration to find WLM angle for a given wavenumber"""
        self.lock.acquire()
        try:
            if self.ignoreSpline:
                result = (waveNumbers - self.sLinear[1]) / self.sLinear[0]
            else:
                result, monotonic = bspInverse(self.sLinear, self.coeffs, waveNumbers)
                if not monotonic:
                    self.autocalStatus |= 1
            return self.thetaBase + self.dTheta * result
        finally:
            self.lock.release()

    def updateWlmCal(self,
                     thetaCal,
                     waveNumbers,
                     weights=1,
                     relax=5e-3,
                     relative=True,
                     relaxDefault=5e-3,
                     relaxZero=5e-5,
                     maxDiff=0.4):
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
        maxDiff       If any difference between the current wavenumber and the "corrected" wavenumber exceeds maxDiff,
                       do not update the calibration
        """
        self.lock.acquire()
        try:
            x = (thetaCal - self.thetaBase) / self.dTheta
            currentWaveNumbers = bspEval(self.sLinear, self.coeffs, x)
            res = waveNumbers - currentWaveNumbers
            if relative:
                res = res - np.mean(res)
            if max(abs(res)) <= maxDiff:
                res = res / weights
                update = relax * bspUpdate(self.nCoeffs, x, res)
                updatePeak = np.argmax(abs(update))
                self.coeffs += update

                # Apply regularization, becoming more and more aggressive if
                # the result is non-increasing
                self.relaxTowardsOriginal(updatePeak, relaxDefault, relaxZero)
                # print "Maximum change from relaxation to default: %s" %
                # (abs(self.coeffs-update).max(),)

        finally:
            self.lock.release()

    def relaxTowardsOriginal(self, updatePeak, relax, relaxZero=0):
        """Relax the new coefficients towards the original, using a Laplacian term for regularization
            for relax and a raw residual for relax."""
        dev = self.coeffsOrig - self.coeffs
        self.coeffs[1:-1] = self.coeffs[1:-1] + relax * \
            (dev[1:-1] - 0.5 * dev[2:] - 0.5 *
             dev[:-2]) + relaxZero * dev[1:-1]
        # Fix up any non-monotone issues
        thresh = -0.75 * self.sLinear[0]
        for k in range(min(updatePeak, len(self.coeffs) - 2), -1, -1):
            if (self.coeffs[k + 1] - self.coeffs[k]) < thresh:
                self.coeffs[k] = self.coeffs[k + 1] - thresh
        for k in range(updatePeak + 1, len(self.coeffs)):
            if (self.coeffs[k] - self.coeffs[k - 1]) < thresh:
                self.coeffs[k] = self.coeffs[k - 1] + thresh

    def isIncreasing(self):
        """Determine if the current coefficients + linear model results in a monotonically increasing angle to
        wavenumber transformation at the knots"""
        ygrid = self.sLinear[0] * np.arange(1,
                                            self.nCoeffs - 1) + (self.coeffs[:-2] + 4 * self.coeffs[1:-1] + self.coeffs[2:]) / 6.0
        return (np.diff(ygrid) >= 0).all()

    def replaceCurrent(self):
        """Replace current values with original values"""
        self.coeffs[:] = self.coeffsOrig

    def replaceOriginal(self):
        """Replace original values with current values"""
        self.coeffsOrig[:] = self.coeffs

    def setOffset(self, offset):
        """Apply a spectroscopically determined wavelength monitor offset."""
        self.lock.acquire()
        try:
            self.offset = offset
            self.sLinear = self.sLinear0 + np.array([0.0, self.offset])
        finally:
            self.lock.release()

    def getOffset(self):
        """Returns the current value of the offset."""
        self.lock.acquire()
        try:
            return self.offset
        finally:
            self.lock.release()

    def setTempOffset(self, offset):
        """Apply a spectroscopically determined laser temp offset."""
        self.lock.acquire()
        try:
            self.tempOffset = offset
        finally:
            self.lock.release()

    def getTempOffset(self):
        """Returns the current value of the temp offset."""
        self.lock.acquire()
        try:
            return self.tempOffset
        finally:
            self.lock.release()

    def shiftWlmCal(self, thetaCal, waveNumber, relax=0.1):
        """Shift entire calibration table on basis of a known waveNumber
        thetaCal      calibrated WLM angle
        waveNumber    wavenumber to which it corresponds
        relax         relaxation parameter for update"""
        self.lock.acquire()
        try:
            x = (thetaCal - self.thetaBase) / self.dTheta
            if self.ignoreSpline:
                currentWaveNumber = np.polyval(self.sLinear, np.asarray([x]))[0]
            else:
                currentWaveNumber = bspEval(self.sLinear, self.coeffs, np.asarray([x]))[0]
            res = waveNumber - currentWaveNumber
            self.sLinear[1] += relax * res
            offset = self.sLinear[1] - self.sLinear0[1]
        finally:
            self.lock.release()


if __name__ == "__main__":
    # Check inverse interpolation via a linear function
    x = bspInverse([2, 3], np.zeros(10, 'd'), np.array([4, 5, 6], 'd'))
    assert np.allclose(x[0], [0.5, 1, 1.5])
    assert x[1]
    # Test polynomial fitting and evaluation
    x = np.linspace(0.0, 10.0, 5)
    y = x**3 + 5 * x + 6
    f = bestFitCentered(x, y, 3)
    assert np.allclose(y, f(x))
    # Test ellipse fitting
    t = np.linspace(0, 2 * np.pi, 17)
    X = 1.5 + 2 * np.cos(t)
    Y = 3.7 + np.sin(t + 2 * np.pi / 7)
    (x0, y0, A, B, epsilon) = parametricEllipse(X, Y)
    X1 = x0 + A * np.cos(t)
    Y1 = y0 + B * np.sin(t + epsilon)
    assert np.allclose(X, X1)
    assert np.allclose(Y, Y1)
    # Make a B-spline pass through some generated data
    N = 20
    coeffs = np.zeros(N, 'd')
    x = np.linspace(0.5, 19.5, 30)
    xf = np.linspace(0, 20, 500)
    y = np.sin(x)
    for iter in range(100):
        y0 = bspEval([0, 0], coeffs, x)
        coeffs += bspUpdate(N, x, 0.1 * (y - y0))
    # plot(xf,bspEval([0,0],coeffs,xf),x,y,'x')
    # show()
    target = np.array([-30.0, -40.0, -19.0, -57.3])
    xx = bspInverse([-5, 0], coeffs, target)
    assert np.allclose(bspEval([-5, 0], coeffs, xx[0]), target)

    w = WlmFile(file("../../Utilities/Laser_818028_CH4.wlm", "r"))
    a = AutoCal()
    a.loadFromWlmFile(w)
    ini = ConfigObj()
    a.updateIni(ini, 2)
    a.setOffset(0.04)
    a.updateIni(ini, 2)
    ini.filename = "../../Utilities/newfoo.ini"
    ini.write()
