"""
Copyright 2013 Picarro Inc.

Gamma functions

This is a Python translation of the methods in Numerical Recipes in C.
"""

import math


MAX_ITERATIONS = 100
EPSILON = 3.0e-7
# XXX This value is from the _C_ implementation. Double-check
# within the context of numpy and CPython math module. The Python
# documentation says that the `math` module is a thin wrapper
# around the C libraries so we should expect to be safe using this
# value of FP_MIN.
FP_MIN = 1.0e-30


class MaxIterationsExceededError(Exception): pass


def q(a, x):
    """
    Incomplete gamma function Q(a, x) = 1.0 - P(a, x).
    """

    assert isinstance(a, float)
    assert a > 0.0
    assert isinstance(x, float)
    assert x >= 0.0

    if x < (a + 1.0):
        return 1.0 - _serialRepr(a, x)
    else:
        return _continuedFracRepr(a, x)

def p(a, x):
    """
    Incomplete gamma function P(a, x).
    """

    assert isinstance(a, float)
    assert a > 0.0
    assert isinstance(x, float)
    assert x >= 0.0

    if x < (a + 1.0):
        return _serialRepr(a, x)
    else:
        return 1.0 - _continuedFracRepr(a, x)

def _serialRepr(a, x):
    aIdx = a
    delta = 1.0 / a
    s = 1.0 / a

    for i in xrange(MAX_ITERATIONS):
        aIdx += 1
        delta *= (x / aIdx)
        s += delta

        if math.fabs(delta) < (math.fabs(s) * EPSILON):
            return s * math.exp(-x + (a * math.log(x)) - math.lgamma(a))

    raise MaxIterationsExceededError

def _continuedFracRepr(a, x):
    # Uses the Modified Lentz Method for computing CFs.
    b = x + 1.0 - a
    c = 1.0 / FP_MIN
    d = 1.0 / b
    h = d
    delta = 0.0

    for i in xrange(1, MAX_ITERATIONS + 1):
        an = -i * (i - a)
        b += 2.0

        d = (an * d) + b
        if math.fabs(d) < FP_MIN:
            d = FP_MIN

        c = b + (an / c)
        if math.fabs(c) < FP_MIN:
            c = FP_MIN

        d = 1.0 / d
        delta = d * c
        h *= delta

        if math.fabs(delta - 1.0) < EPSILON:
            return h * math.exp(-x + (a * math.log(x)) - math.lgamma(a))

    return MaxIterationsExceededError
