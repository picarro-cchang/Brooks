#!/usr/bin/python
#
# File Name: PulseAnalyzer.py
# Purpose: Basic pulse analyzer functionality
#
# File History:
# 09-01-26  alex  Created file
# 09-02-10 alex  Forced it to continuously calculates statistics aftre triggered

from numpy import *
from time import time

class PulseAnalyzer(object):
    def __init__(self):
        self.timeStamp = time()
        self.concHist = []
        self.status = "waiting"
        self.startNewEntry = False
            
    def runAnalyzer(self, conc, threshold, externalTrigger, waitTime, triggerTime, ignoreThres = False):
        pulseData = None
        newEntry = False
        endNewEntry = False
        if self.status == "waiting":
            if time() - self.timeStamp > waitTime:
                self.status = "armed"
            
        if self.status == "armed":
            if externalTrigger or (conc > threshold and not ignoreThres):
                self.timeStamp = time()
                self.startNewEntry = True              
                self.status = "triggered"    
                
        if self.status == "triggered":
            if (time() - self.timeStamp) <= triggerTime:        
                if self.startNewEntry:
                    newEntry = True
                    self.startNewEntry = False
                self.concHist.append(conc)
                # Continuously calculate statistics
                meanValue = mean(self.concHist)
                stdValue = std(self.concHist)
                dataTime = time()
                pulseData = ((meanValue, dataTime), (stdValue, dataTime))
            else:
                endNewEntry = True
                self.concHist = []
                self.timeStamp = time()
                self.status = "waiting"
        
        return (self.status, pulseData, newEntry, endNewEntry)
