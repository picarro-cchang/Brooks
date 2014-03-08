#!/usr/bin/python
#
# File Name: PulseAnalyzer.py
# Purpose: Basic pulse analyzer functionality (state machine)
#
# File History:
# 10-06-16  Alex Lee  Created file
# 11-07-26  Alex Lee  Support time extension on both sides

import threading
from numpy import *
from collections import deque

class PulseAnalyzer(object):
    def __init__(self, source, concNameList, targetConc = None,
                 thres1Pair = [0.0, 0.0], thres2Pair = [0.0, 0.0], triggerType = "in", waitTime = 0.0, 
                 validTimeAfterTrigger = 0.0, validTimeBeforeEnd = 0.0, timeout = 0.0, bufSize = 500, numPointsToTrigger = 1,
                 numPointsToRelease = 1, armCond = None):
        self.source = source
        self.concBufferDict = {"timestamp":deque()}
        self.concNameList = concNameList
        for concName in concNameList:
            self.concBufferDict[concName] = deque()
        self.outputBufferDict = {}
        self.targetConc = targetConc
        self.triggerType = triggerType.lower()
        self.thres1Low = min(thres1Pair)
        self.thres1High = max(thres1Pair)
        self.thres2Low = min(thres2Pair)
        self.thres2High = max(thres2Pair)
        self.waitTime = waitTime
        self.validTimeAfterTrigger = validTimeAfterTrigger
        self.validTimeBeforeEnd = validTimeBeforeEnd
        self.timeout = timeout
        self.bufSize = bufSize
        self.numPointsToTrigger = numPointsToTrigger
        self.numPointsToRelease = numPointsToRelease
        self.armCond = armCond
        self.timeMark = None
        self.status = "waiting"
        self.pulseFinished = False
        self.triggeredPoints = 0
        self.releasedPoints = 0
        self.bufferLock = threading.Lock()

    def resetConcBuffer(self):
        self.bufferLock.acquire()
        try:
            for concName in self.concBufferDict:
                self.concBufferDict[concName] = deque()
        except:
            pass
        finally:
            self.bufferLock.release()
        
    def resetAnalyzer(self):
        self.timeMark = None
        self.status = "waiting"
        self.pulseFinished = False
        self.triggeredPoints = 0
        self.releasedPoints = 0
        self.resetConcBuffer()
        self.outputBufferDict = {}
        
    def _isInRange(self, value, thresLow, thresHigh):
        if value >= thresLow and value <= thresHigh:
            return True
        else:
            return False
            
    def isTriggered(self, targetConc):
        if (self.triggerType == "in" and 
           self._isInRange(targetConc, self.thres1Low, self.thres1High)) \
           or \
           (self.triggerType == "out" and 
           not self._isInRange(targetConc, self.thres1Low, self.thres1High)):            
            self.triggeredPoints += 1
        else:
            self.triggeredPoints = 0
        if self.triggeredPoints >= self.numPointsToTrigger:
            self.triggeredPoints = 0
            return True
        else:
            return False

    def isReleased(self, targetConc):
        if self.timeout > 0.0 and (self.currMeasTime - self.timeMark) > self.timeout:
            self.releasedPoints = 0
            return True
            
        if (self.triggerType == "in" and 
           not self._isInRange(targetConc, self.thres2Low, self.thres2High)) \
           or \
           (self.triggerType == "out" and 
           self._isInRange(targetConc, self.thres2Low, self.thres2High)):   
            self.releasedPoints += 1
        else:
            self.releasedPoints = 0
        if self.releasedPoints >= self.numPointsToRelease:
            self.releasedPoints = 0
            return True
        else:
            return False
            
    def addToBuffer(self, measData, maxTimeDuration = -1):
        if measData.Source != self.source: 
            return
            
        self.bufferLock.acquire()
        # Clean up old data if the maximum time range is defined
        if maxTimeDuration > 0 and len(self.concBufferDict["timestamp"]) > 0:
            while self.concBufferDict["timestamp"][0] < (measData.Time - maxTimeDuration):
                for concName in self.concBufferDict:
                    self.concBufferDict[concName].popleft()
                    
        for concName in self.concBufferDict:
            try:
                if concName != "timestamp":
                    self.concBufferDict[concName].append(measData.Data[concName])
                else:
                    self.concBufferDict[concName].append(measData.Time)
                    
                # Control the size of the buffer
                if len(self.concBufferDict[concName]) > self.bufSize:
                    self.concBufferDict[concName].popleft()
                    
            except Exception, err:
                print err

        self.bufferLock.release()
        
    def cutBuffer(self):
        self.bufferLock.acquire()
        try:
            timeArray = array(self.concBufferDict["timestamp"])
            lastIdx = nonzero(timeArray >= (timeArray[-1]-self.validTimeBeforeEnd))[0][0]
            for concName in self.concBufferDict:
                self.concBufferDict[concName] = deque(list(self.concBufferDict[concName])[:lastIdx])
        except Exception, err:
            print err
        finally:
            self.bufferLock.release()
            
    def copyToOutput(self):
        self.bufferLock.acquire()
        try:
            self.outputBufferDict = self.concBufferDict.copy()
        except:
            pass
        finally:
            self.bufferLock.release()
        
    def runAnalyzer(self, measData):
        if measData.Source != self.source: 
            return

        self.currMeasTime = measData.Time
        if self.timeMark == None:
            self.timeMark = self.currMeasTime
            
        if self.status == "waiting":
            if self.validTimeAfterTrigger < 0:
                # Extend time before triggering
                self.addToBuffer(measData, -1*self.validTimeAfterTrigger)
            if self.currMeasTime - self.timeMark >= self.waitTime:
                if self.armCond == None:
                    self.status = "armed"
                elif self._isInRange(measData.Data[self.targetConc], self.armCond[0], self.armCond[1]):
                    self.status = "armed"
            
        if self.status == "armed":
            if self.validTimeAfterTrigger < 0:
                # Extend time before triggering
                self.addToBuffer(measData, -1*self.validTimeAfterTrigger)
            if self.isTriggered(measData.Data[self.targetConc]):
                self.timeMark = self.currMeasTime + self.validTimeAfterTrigger
                self.pulseFinished = False
                self.status = "triggered"
                
        if self.status == "triggered": 
            if not self.isReleased(measData.Data[self.targetConc]):
                if self.currMeasTime >= self.timeMark:
                    self.addToBuffer(measData)
            else:
                if self.validTimeBeforeEnd >= 0:
                    self.cutBuffer()
                    self.copyToOutput()
                    self.resetConcBuffer()
                    self.pulseFinished = True
                    self.timeMark = self.currMeasTime
                    self.status = "waiting"
                else:
                    self.timeMark = self.currMeasTime - self.validTimeBeforeEnd
                    self.status = "extended"
                    
        if self.status == "extended":
            if self.currMeasTime <= self.timeMark:
                self.addToBuffer(measData)
            else:
                self.copyToOutput()
                self.resetConcBuffer()
                self.pulseFinished = True
                self.timeMark = self.currMeasTime
                self.status = "waiting"
        
    def selectBuffer(self):
        """
        Select self.outputBufferDict if pulse analysis was run with state machine and finished.
        Select self.concBufferDict if either:
        1. Pulse analysis was not done yet    
        2. Data was manually added into the conc buffer
        """
        if self.pulseFinished:
            return self.outputBufferDict.copy()
        else:
            return self.concBufferDict.copy()
            
    def getOutput(self):
        outBuffer = self.selectBuffer()
        return [self.status, self.pulseFinished, outBuffer]
        
    def getStatus(self):
        return self.status
        
    def getTimestamp(self):
        return self.currMeasTime
        
    def getDataReady(self):
        """Should only be used in the state transition mode (not manually adding data mode)"""
        return self.pulseFinished
        
    def isTriggeredStatus(self):
        return self.status == "triggered"
            
    def getStatistics(self):
        """Each concentration has statistics values as mean, std, and slope, except "timestamp", which 
        has only mean value"""
        statDict = {}
        outBuffer = self.selectBuffer()
        try:
            timeArray = array(outBuffer["timestamp"])
            statDict["timestamp_mean"] = mean(timeArray)
            for concName in [c for c in outBuffer if c != "timestamp"]:
                try:
                    dataArray = array(outBuffer[concName])
                    statMean = mean(dataArray)
                    statStd = std(dataArray)
                    statSlope = polyfit(timeArray, dataArray, 1)[0]
                except:
                    continue
                statDict["%s_mean"%concName] = statMean
                statDict["%s_std"%concName] = statStd
                statDict["%s_slope"%concName] = statSlope
        except:
            pass

        return statDict.copy()

    def getPulseStartEndTime(self):
        outBuffer = self.selectBuffer()
        timeArray = array(outBuffer["timestamp"])
        return (timeArray[0], timeArray[-1])

    def getConcNameList(self):
        return self.concNameList