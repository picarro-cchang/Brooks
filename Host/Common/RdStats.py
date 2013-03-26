#!/usr/bin/python
#
# FILE:
#   RdStats.py
#
# DESCRIPTION:
#   Routines for calculating ringdown statistics
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#  1-Sep-2009  sze  Ported from Silverstone code
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved

import math

class RdStats(object):
    """ Class for computation of ringdown statistics. Accumulates number of points, sum and
    sum-of-squares of losses as well as an exponential average of the ringdown rate """

    def __init__(self,rateAverage):
        """ rateAverage is the number of ringdowns to use for calculating the average ringdown rate """
        self.rateAverageFactor = 1./rateAverage
        self.n = 0
        self.sumLoss = 0
        self.sumSquareLoss = 0
        self.meanTime = 0.1
        self.lastTime = None

    def reset(self):
        """ Resets calculation """
        self.n = 0
        self.sumLoss = 0
        self.sumSquareLoss = 0

    def processDatum(self,time,loss):
        """ Process a value for the rdStats calculation """
        if self.lastTime is not None:
            self.meanTime = (1.0-self.rateAverageFactor)*self.meanTime + self.rateAverageFactor*(time-self.lastTime)
        self.lastTime = time
        self.n += 1
        self.sumLoss += loss
        self.sumSquareLoss += loss * loss

    def getStats(self):
        """ Get the result of ringdown statistics calculation as the tuple (mean,shot2shot,rate) """
        mean = 0
        shot2shot = 0
        rate = 0
        if self.n > 0:
            mean = self.sumLoss / self.n
            var = max(0.0,self.sumSquareLoss / self.n - mean*mean)
            if mean != 0: shot2shot = math.sqrt(var) / mean
        if self.meanTime != 0: rate = 1/self.meanTime
        return (mean,shot2shot,rate)


if __name__ == "__main__":
    import random
    rd = RdStats(100)
    for i in range(10000):
        rd.processDatum(0.01*i,random.gauss(10.0,1.0))
    print rd.getStats()
