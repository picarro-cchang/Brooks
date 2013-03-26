#!/usr/bin/python
#
# FILE:
#   Allan.py
#
# DESCRIPTION:
#   Routines for calculating Allan variances
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#  1-Sep-2009  sze  Ported from Silverstone code
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved

class AllanVar(object):
    """ Class for computation of Allan Variance of a data series. Variances are computed over sets of
  size 1,2,...,2**(nBins-1). In order to process a new data point call processDatum(value). In order
  to recover the results, call getVariances(). In order to reset the calculation, call reset(). """

    def __init__(self,nBins):
        """ Construct an AllanVar object for calculating Allan variances over 1,2,...,2**(nBins-1) points """
        self.nBins = nBins
        self.counter = 0
        self.bins = []
        for i in range(nBins):
            self.bins.append(AllanBin(2**i))

    def reset(self):
        """ Resets calculation """
        self.counter = 0
        for bin in self.bins:
            bin.reset()

    def processDatum(self,value):
        """ Process a value for the Allan variance calculation """
        for bin in self.bins:
            bin.process(value)
        self.counter += 1

    def getVariances(self):
        """ Get the result of the Allan variance calculation as (count,(var1,var2,var4,...)) """
        return (self.counter,tuple([bin.allanVar for bin in self.bins]))

class AllanBin(object):
    """ Internal class for Allan variance calculation """
    def __init__(self,averagingLength):
        self.averagingLength = averagingLength
        self.reset()

    def reset(self):
        self.sum, self.sumSq = 0, 0
        self.sumPos, self.numPos = 0, 0
        self.sumNeg, self.numNeg = 0, 0
        self.nPairs, self.allanVar = 0, 0

    def process(self,value):
        if self.numPos < self.averagingLength:
            self.sumPos += value
            self.numPos += 1
        elif self.numNeg < self.averagingLength:
            self.sumNeg += value
            self.numNeg += 1
        if self.numNeg == self.averagingLength:
            y = (self.sumPos/self.numPos) - (self.sumNeg/self.numNeg)
            self.sum += y
            self.sumSq += y**2
            self.nPairs += 1
            self.allanVar = 0.5*self.sumSq/self.nPairs
            self.sumPos, self.numPos = 0, 0
            self.sumNeg, self.numNeg = 0, 0

if __name__ == "__main__":
    import random
    av = AllanVar(12)
    for i in range(10000):
        av.processDatum(random.gauss(0.0,1.0))
    print av.getVariances()
