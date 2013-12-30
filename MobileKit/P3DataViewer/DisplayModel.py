#!/usr/bin/python
"""
File Name: DisplayModel.py
Purpose: Model for plots that are displayed.

File History:
    19-Dec-2013  sze   Initial Version

Copyright (c) 2013 Picarro, Inc. All rights reserved
"""
import numpy as np

from Host.Common.GraphPanel import Series
from Subject import Subject

SERIES_POINTS = 10000

class DisplayModel(Subject):
    def __init__(self, dataModel):
        Subject.__init__(self)
        self.dataModel = dataModel
        self.xvar = ''
        self.yvar = ''
        self.xSeries = Series(SERIES_POINTS)
        self.ySeries = Series(SERIES_POINTS)
        self.xySeries = Series(SERIES_POINTS)
        self.nextPlotPoint = 0
        self.timeRange = None
        self.dataModel.addListener(self.dataListener)
        self.addListener(self.displayListener)
        
    def setVariables(self, xvar, yvar):
        self.set('xvar', xvar)
        self.set('yvar', yvar)

    def setTimeRange(self, timeRange):
        self.set('timeRange', timeRange)
        
    def fillSeries(self):
        if self.dataModel.logData is not None and self.xvar and self.yvar:
            epochTimes = self.dataModel.logData['EPOCH_TIME']
            xValues = self.dataModel.logData[self.xvar]
            yValues = self.dataModel.logData[self.yvar]
            while self.nextPlotPoint < len(xValues):
                epochTime = epochTimes[self.nextPlotPoint]
                xValue = xValues[self.nextPlotPoint]
                yValue = yValues[self.nextPlotPoint]
                xGood = (xValue is not None) and np.isfinite(xValue)
                yGood = (yValue is not None) and np.isfinite(yValue)
                
                if xGood:
                    self.xSeries.Add(epochTime, xValue)
                else:    
                    self.xSeries.Add(epochTime, np.NaN)
                if yGood:
                    self.ySeries.Add(epochTime, yValue)
                else:    
                    self.ySeries.Add(epochTime, np.NaN)
                self.nextPlotPoint += 1
                
            if self.timeRange is not None:
                tMin, tMax = self.timeRange
                self.xySeries.Clear()
                for tvalue, xvalue, yvalue in zip(self.xSeries.GetX(), self.xSeries.GetY(), self.ySeries.GetY()):
                    if tMin <= tvalue <= tMax:
                        self.xySeries.Add(xvalue, yvalue)
        
    def displayListener(self, displayModel):
        changed = self.changed
        if changed in ['xvar', 'yvar']:
            self.xSeries.Clear()
            self.ySeries.Clear()
            self.xySeries.Clear()
            self.nextPlotPoint = 0
            self.fillSeries()
        if changed == 'timeRange':
            if displayModel.timeRange is not None:
                tMin, tMax = displayModel.timeRange
                self.xySeries.Clear()
                for tvalue, xvalue, yvalue in zip(self.xSeries.GetX(), self.xSeries.GetY(), self.ySeries.GetY()):
                    if tMin <= tvalue <= tMax:
                        self.xySeries.Add(xvalue, yvalue)
                
        
    def dataListener(self, dataModel):
        changed = dataModel.changed
        if changed in ["logFileId"]:
            self.xSeries.Clear()
            self.ySeries.Clear()
            self.xySeries.Clear()
            self.nextPlotPoint = 0
        if changed in ["logData"]:
            self.fillSeries()
        
