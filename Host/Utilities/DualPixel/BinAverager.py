
from numpy import *

# This implements a set of buffers which store averages of data binned by time. An averaging interval is used to
#  partition time into segments whose boundaries are integer multiples of the interval. Data are averaged within
#  each segment by storing a total and the number of points so far in that interval.

class BinAverager(object):
    def __init__(self, avgInterval, nStreams, maxPoints=500):
        """
        avgInterval is the averaging interval in ms.
        nStreams is the number of variables which are to be averaged and binned.
        """
        self.avgInterval = avgInterval
        self.maxPoints = maxPoints
        self.nStreams = nStreams
        self.streamLatest = zeros(nStreams)
        self.streamTotals = zeros((nStreams, maxPoints), dtype=float)
        self.streamPoints = zeros((nStreams, maxPoints), dtype=int)
        self.baseIndex = 0
        
    def setAvgInterval(self, avgInterval):
        self.avgInterval = avgInterval
        self.clear()
    
    def clear(self):
        self.streamLatest = zeros(self.nStreams)
        self.streamTotals = zeros((self.nStreams, self.maxPoints), dtype=float)
        self.streamPoints = zeros((self.nStreams, self.maxPoints), dtype=int)
        self.baseIndex = 0
                
    def insertData(self, timestamp, streamNum, datVal):
        """
        Insert data into the specified streamNum at the specified timestamp (ms). We update the totals
        and the number of points to allow averages to be computed
        """
        bin = timestamp//self.avgInterval
        index = bin - self.baseIndex
        if index >= self.maxPoints:
            self.shiftBuffers(timestamp, self.maxPoints//2)
            # Need to shift down the buffers, since the new data are currently beyond the ends of the buffers
            index = bin - self.baseIndex
        elif index < 0:
            return # These data are too old to be included in the buffers
        self.streamTotals[streamNum, index] += datVal
        self.streamPoints[streamNum, index] += 1
        self.streamLatest[streamNum] = max(self.streamLatest[streamNum],timestamp)
        
    def shiftBuffers(self, timestamp, targetIndex):
        """
        Shift data in the buffers so that timestamp maps to targetIndex after the shift.
        """
        bin = timestamp//self.avgInterval
        currentIndex = bin - self.baseIndex
        # Points from startIndex to the end of the buffer are to be moved to the start of
        #  the new buffers
        startIndex = currentIndex - targetIndex
        temp1 = zeros((self.nStreams, self.maxPoints), dtype=float)
        temp2 = zeros((self.nStreams, self.maxPoints), dtype=int)
        if self.maxPoints > startIndex:
            temp1[:,:self.maxPoints-startIndex] = self.streamTotals[:,startIndex:self.maxPoints]
            temp2[:,:self.maxPoints-startIndex] = self.streamPoints[:,startIndex:self.maxPoints]
        self.streamTotals = temp1
        self.streamPoints = temp2
        self.baseIndex = bin - targetIndex    
    
    def getRecentStreamData(self, streamNum, timestamp, maxPoints):
        """
        Get averaged stream data from the specified streamNum, finishing at the specified timestamp
        into a numpy array of length no greater than maxPoints
        """
        bin = timestamp//self.avgInterval
        currentIndex = bin - self.baseIndex
        startIndex = currentIndex - maxPoints
        if currentIndex > self.maxPoints: currentIndex = self.maxPoints
        if currentIndex < 0: currentIndex = 0
        if startIndex > self.maxPoints: startIndex = self.maxPoints
        if startIndex < 0: startIndex = 0
        startIndex = int(startIndex)
        currentIndex = int(currentIndex)
        timestamps = []
        result = []
        for i in range(startIndex, currentIndex):
            result.append(self.streamTotals[streamNum,i]/self.streamPoints[streamNum,i] if self.streamPoints[streamNum,i]>0 else NaN)
            timestamps.append(self.avgInterval*(self.baseIndex + i))
        return asarray(timestamps), asarray(result)
            