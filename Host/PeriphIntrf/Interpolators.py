"""
Copyright 2014 Picarro Inc.
"""

class Interpolators(object):

    @staticmethod
    def linear(pPair, tPair, t):
        try:
            t = float(t)
            tPair = [float(u) for u in tPair]
            pPair = [float(p) for p in pPair]
            dtime = tPair[1] - tPair[0]
            if dtime == 0:
                return 0.5*(pPair[0] + pPair[1])
            else:
                return ((t-tPair[0])*pPair[1] + (tPair[1]-t)*pPair[0]) / dtime
        except:
            return None

    @staticmethod
    def max(pPair, tPair, t):
        pPair = [float(x) for x in pPair]
        return max(pPair)

    @staticmethod
    def bitwiseOr(pPair, tPair, t):
        pPair = [int(x) for x in pPair]
        return float(pPair[0] | pPair[1])
