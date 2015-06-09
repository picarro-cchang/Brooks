"""
Copyright 2013 Picarro Inc

Chi-squared fitting for straight lines.
"""

import pprint

import numpy
from scipy import linalg

import IncompleteGammaFunctions


class ChiSquared(object):

    @staticmethod
    def fitStraightLine(x, y):
        """
        Fit the specified data for y = ax + b with either a single
        sigma or a list of sigmas, one for each point. Returns (a, b,
        sigma_a, sigma_b).
        """

        assert len(x) == len(y)

        # sigmas = []

        # if isinstance(sigma, list):
        #     assert len(x) == len(sigma)
        #     sigmas = sigma
        # else:
        #     sigmas = [sigma] * len(x)

        A = numpy.zeros((len(x), 2))
        b = numpy.zeros((len(x), 1))

        # Normalize times to t0 since they are a big # divided by a
        # really small number.
        for i in xrange(len(x)):
            A[i, 0] = 1.0
            A[i, 1] = x[i] - x[0]
            b[i] = y[i]

        params, resid, rank, s = linalg.lstsq(A, b)

        C = linalg.inv(numpy.dot(A.T, A))

        # Compute the variance from the fit
        var = 0.0
        for i in xrange(len(x)):
            v = y[i] - (params[0, 0] - params[1, 0] * (x[i] - x[0]))
            var += (v * v)

        var /= (len(x) - 2)
        stdDev = numpy.sqrt(var)

        return (params[0, 0], params[1, 0], stdDev * numpy.sqrt(C[0, 0]),
                stdDev * numpy.sqrt(C[1, 1]))

    @staticmethod
    def fitStraightLineNR(x, y, sigma):
        """
        Fit the specified data for y = ax + b with either a single sigma or a list of sigmas,
        one for each point. Returns (a, b, sigma_a, sigma_b).
        """

        assert len(x) == len(y)

        sigmas = []

        if isinstance(sigma, list):
            assert len(x) == len(sigma)
            sigmas = sigma
        else:
            sigmas = [sigma] * len(x)

        # From Numerical Recipes
        S = sum([ 1.0 / (s * s) for s in sigmas])

        Sx = 0.0
        Sy = 0.0
        for i, s in enumerate(sigmas):
            s2 = s * s
            Sx += (x[i] / s2)
            Sy += (y[i] / s2)

        Stt = 0.0
        for i, s in enumerate(sigmas):
            t = (1.0 / s) * (x[i] - (Sx / S))
            Stt += (t * t)

        b = 0.0
        for i, s in enumerate(sigmas):
            t = (1.0 / s) * (x[i] - (Sx / S))
            b += (t * y[i]) / s

        b *= (1.0 / Stt)

        a = (Sy - (Sx * b)) / S

        sigmaA = numpy.sqrt((1.0 / S) * (1.0 + ((Sx * Sx) / (S * Stt))))
        sigmaB = numpy.sqrt(1.0 / Stt)

        chi2 = 0.0
        for i, s in enumerate(sigmas):
            chi = (y[i] - a - (b * x[i])) / s
            chi2 += (chi * chi)

        # XXXX
        sigma2 = 0.0
        for i, xi in enumerate(x):
            sigma2 += ((y[i] - a - (b * xi)) ** 2)

        print "Est. sigma = %s" % (numpy.sqrt(sigma2 / (len(x) - 2.0)))

        return (a, b, sigmaA, sigmaB, chi2, IncompleteGammaFunctions.q((len(x) - 2.0) / 2.0, chi2 / 2.0))
