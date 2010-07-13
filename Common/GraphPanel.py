#!/usr/bin/python
#
# File Name: GraphPanel.py
# Purpose: Defines data Series and the GraphPanel classes which are used to
#  display all graphs in the Controller GUI
#
# Notes:
#
# File History:
# 05-??-?? sze   Created first release
# 05-12-05 sze   Added this header
# 06-10-31 sze   Modified to work with numpy
# 07-02-01 sze   Avoid unecessary updates, and allow these to be done less frequently
# 07-05-18 sze   Added font, foregroundColour and fontSizeAxis properties
# 07-09-27 sze   Added setMaxPoints method for Sequences that limit number of displayed points.
#                 Note that additional points are not deleted, so maxPoints can be changed on-the-fly.
# 07-09-27 sze   Added Text methods to GraphPanel to allow strings within graphs
# 08-03-07 sze   Add GetPointers and SerPointers to Sequences
# 09-02-12 alex  Always update statistics window when running Update() on timer, even witout re-drawing 
# 09-07-10 alex Support time-axis locking function from QuickGui
# 09-08-04 alex Define a flag to detect if x-axis has been changed since last update. Support forced re-draw even when new data hasn't come in yet.

import wx
import plot
import numpy.oldnumeric as _Numeric
from MyPlotCanvas import MyPlotCanvas
import time
import sys
import threading
from numpy import *

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    TimeStamp = time.clock
else:
    TimeStamp = time.time

class Sequence(object):
    nCreated = 0    # Keep track of number of sequences created
    def __init__(self,npoints,dataType='d'):
        Sequence.nCreated += 1
        self.size = npoints
        self.next = 0
        self.count = 0
        self.values = _Numeric.zeros(npoints,dataType)
        self.latestUpdate = TimeStamp()
    @classmethod
    def numCreated(cls):
        return cls.nCreated
    def GetPointers(self):
        """Get a tuple which specifies where in the sequence the next data are to be placed"""
        return self.next, self.count
    def SetPointers(self,ptrs):
        self.next, self.count = ptrs
    def CopyPointers(self,seq):
        """Sets pointers in a sequence to line up with those in another"""
        self.SetPointers(seq.GetPointers())
    def Add(self,v):
        self.values[self.next] = v
        if self.count < self.size: self.count += 1
        self.next += 1
        if self.next >= self.size: self.next = 0
        self.latestUpdate = TimeStamp()
    def Clear(self):
        self.next = 0
        self.count = 0
        self.latestUpdate = TimeStamp()
    def GetValues(self):
        if self.count < self.size:
            return self.values[0:self.count]
        else:
            return _Numeric.concatenate((self.values[self.next:],self.values[0:self.next]))
    def GetLatest(self):
        if self.count < self.size:
            return self.values[self.count-1]
        else:
            return self.values[(self.next-1) % self.size]
    def GetLevelAndSize(self):
        return self.count, self.size
    def GetLatestUpdate(self):
        return self.latestUpdate

class Series(object):
    def __init__(self,*args,**kwargs):
        if isinstance(args[0],Sequence) and isinstance(args[1],Sequence):
            self.x = args[0]
            self.y = args[1]
        elif isinstance(args[0],int):
            self.x = Sequence(args[0])
            self.y = Sequence(args[0])
        self.maxPoints = None
    def GetLatestUpdate(self):
        return max(self.x.GetLatestUpdate(),self.y.GetLatestUpdate())
    def Add(self,t,v):
        self.x.Add(t)
        self.y.Add(v)
    def Clear(self):
        self.x.Clear()
        self.y.Clear()
    def GetX(self):
        if self.maxPoints == None:
            return self.x.GetValues()
        else:
            return self.x.GetValues()[-self.maxPoints:]
    def GetY(self):
        if self.maxPoints == None:
            return self.y.GetValues()
        else:
            return self.y.GetValues()[-self.maxPoints:]
    def setMaxPoints(self,maxPoints):
        self.maxPoints = maxPoints

class GraphPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        # self.Graph = PlotWidget(self, -1)
        self.canvas = MyPlotCanvas(parent=self,id=-1)
        self.__do_layout()
        self._lineSeries = []
        self._pointSeries = []
        self._text = {}
        self.forcedXAxis = None
        self.lastXAxis = None
        self.isNewXAxis = False
        self.stats = []
        self.nextHandle = 1
        self.xlabel = ''
        self.ylabel = ''
        self.title = ''
        self.canvas.SetEnableGrid(False)
        self.canvas.SetGridColour('light grey')
        self.canvas.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.NORMAL))
        self.canvas.SetFontSizeAxis(8)
        self.canvas.SetBackgroundColour('white')
        self.canvas.SetEnableZoom(True)
        self.latestUpdate = None
        self.colorList = []
        self.colorTimeList = []
    def getNumColors(self):
        return len(self.colorList)
    def AddColorTime(self, colorTime):
        self.colorTimeList.append(colorTime)
    def AddColor(self, color):
        self.colorList.append(color)
    def GetUnzoomed(self):
        return self.canvas.GetUnzoomed()
    def SetUnzoomed(self, unzoomedFalg):
        self.canvas.unzoomed = unzoomedFalg
    def GetLastDraw(self):
        return self.canvas.last_draw
    def SetForcedXAxis(self, xAxisTuple):
        self.forcedXAxis = xAxisTuple
    def GetForcedXAxis(self):
        return self.forcedXAxis        
    def ClearForcedXAxis(self):
        self.forcedXAxis = None
    def AddSeriesAsLine(self,series,select=None,statsFlag=False,**attr):
        self._lineSeries.append((series,select,statsFlag,attr))
        self.latestUpdate = None
    def AddSeriesAsPoints(self,series,select=None,statsFlag=False,**attr):
        self._pointSeries.append((series,select,statsFlag,attr))
        self.latestUpdate = None
    def RemoveAllSeries(self):
        self._lineSeries = []
        self._pointSeries = []
        self.latestUpdate = None
    def Text(self,x,y,strings,color="black",font=None,just=(0.5,0.5)):
        L = 1
        if _Numeric.iterable(x): L = len(x)
        if _Numeric.iterable(y): L = max(L,len(y))
        points = _Numeric.zeros((L,2),"d")
        points[:,0] = x
        points[:,1] = y
        self._text[self.nextHandle] = plot.PolyText(points,strings=strings,colour=color,font=font,just=just)
        self.nextHandle += 1
        self.latestUpdate = None
    def RemoveText(self,handle):
        del self._text[handle]
        self.latestUpdate = None
    def RemoveAllText(self):
        self._text.clear()
        self.latestUpdate = None

    def SetGraphProperties(self,**kwargs):
        # Change only the properties specified in the argument list
        self.latestUpdate = None
        save_last_draw = self.canvas.last_draw
        self.canvas.last_draw = None
        for k,v in kwargs.iteritems():
            if k=="xlabel": self.xlabel = v
            elif k =="ylabel": self.ylabel = v
            elif k =="title": self.title = v
            elif k =="timeAxes": self.canvas.SetTimeAxes(v)
            elif k =="logScale": self.canvas.SetLogScale(v)
            elif k =="XTickFormat": self.canvas.SetXTickFormat(v)
            elif k =="YTickFormat": self.canvas.SetYTickFormat(v)
            elif k =="XSpec": self.canvas.SetXSpec(v)
            elif k =="YSpec": self.canvas.SetYSpec(v)
            elif k =="grid": self.canvas.SetEnableGrid(v)
            elif k =="gridColour": self.canvas.SetGridColour(v)
            elif k =="frameColour": self.canvas.SetBackgroundColour(v)
            elif k =="backgroundColour": self.canvas.SetGraphBackgroundColour(v)
            elif k =="font": self.canvas.SetFont(v)
            elif k =="fontSizeAxis": self.canvas.SetFontSizeAxis(v)
            elif k =="foregroundColour": self.canvas.SetForegroundColour(v)
            else:
                raise ValueError("Unknown graph property %s" % (k,))
        self.canvas.last_draw = save_last_draw

    def calcStats(self,data,canvas):
        # Calculate mean, std dev and slope of the data within the current window
        mu = 0
        sigma = 0
        slope = 0
        x = data[:,0]
        y = data[:,1]
        (graphics, xAxis, yAxis) = canvas.last_draw
        xAxis = tuple(xAxis)
        yAxis = tuple(yAxis)
        # Restrict data to those within window
        filt = (xAxis[0]<=x) & (x<=xAxis[1]) & (yAxis[0]<=y) & (y<=yAxis[1])
        x = x[filt]
        y = y[filt]
        if len(x)>0:
            mu = _Numeric.mean(y)
            sigma = _Numeric.std(y)
            if len(x)>=2: slope = _Numeric.polyfit(x,y,1)[0]
        return (mu, sigma, slope)

    def GetIsNewXAxis(self):
        return self.isNewXAxis
        
    def Update(self,delay=0.0,forcedRedraw=False):
        # Check to see if we do not need to update after all, since nothing has changed since the last one
        self.stats = []
        mostRecentChange = 0
        skipDrawing = False
        for series,select,statsFlag,attr in self._lineSeries:
            mostRecentChange = max(mostRecentChange,series.GetLatestUpdate())
        for series,select,statsFlag,attr in self._pointSeries:
            mostRecentChange = max(mostRecentChange,series.GetLatestUpdate())
        if (self.latestUpdate is not None) and (self.latestUpdate >= mostRecentChange-delay) \
           and (not forcedRedraw) and (not isinstance(self.forcedXAxis,tuple)):
            skipDrawing = True
   
        self.latestUpdate = mostRecentChange
        canvas = self.canvas
        plot_objects = []
        for series,select,statsFlag,attr in self._lineSeries:
            timeSeries = series.GetX()
            dataSeries = series.GetY()
            if len(self.colorList)-len(self.colorTimeList) == 1:    
                try:
                    changePtList = self._getColorTimeIndices(timeSeries.copy())
                    #print changePtList, self.colorList
                    statData = zeros((0,2), dtype=float)
                    for i in range(len(changePtList)-1):
                        startPt = max(0, changePtList[i]-1)
                        endPt = changePtList[i+1]
                        data = _Numeric.column_stack((timeSeries[startPt:endPt],dataSeries[startPt:endPt]))
                        color = self.colorList[i]
                        if len(data) > 0:
                            if select != None:
                                selSequence,selValue = select
                                data = data[selSequence.GetValues() == selValue]
                            if len(data)>0:
                                plot_objects.append(plot.PolyLine(data,colour=color,**attr))
                                statData = concatenate((statData,data)) 
                        del data
                    if statsFlag:
                        self.stats.append(self.calcStats(statData,canvas))
                except Exception, err:
                    print err
            else:    
                data = _Numeric.column_stack((timeSeries,dataSeries))
                if len(data) > 0:
                    if select != None:
                        selSequence,selValue = select
                        data = data[selSequence.GetValues() == selValue]
                    if len(data)>0: 
                        plot_objects.append(plot.PolyLine(data,**attr))
                    if statsFlag:
                        self.stats.append(self.calcStats(data,canvas))
                del data
        for series,select,statsFlag,attr in self._pointSeries:
            timeSeries = series.GetX()
            dataSeries = series.GetY()
            if len(self.colorList)-len(self.colorTimeList) == 1:
                try:
                    changePtList = self._getColorTimeIndices(timeSeries.copy())
                    statData = zeros((0,2), dtype=float)
                    for i in range(len(changePtList)-1):
                        startPt = max(0, changePtList[i]-1)
                        endPt = changePtList[i+1]
                        data = _Numeric.column_stack((timeSeries[startPt:endPt],dataSeries[startPt:endPt]))
                        color = self.colorList[i]
                        if len(data) > 0:
                            if select != None:
                                selSequence,selValue = select
                                data = data[selSequence.GetValues() == selValue]
                            if len(data)>0:
                                plot_objects.append(plot.PolyMarker(data,colour=color,fillcolour=color,**attr))
                                statData = concatenate((statData,data)) 
                        del data
                    if statsFlag:
                        self.stats.append(self.calcStats(statData,canvas))
                except Exception, err:
                    print err
            else:  
                data = _Numeric.column_stack((timeSeries,dataSeries))
                if len(data) > 0:            
                    if select != None:
                        selSequence,selValue = select
                        data = data[selSequence.GetValues() == selValue]
                    if len(data)>0: 
                        plot_objects.append(plot.PolyMarker(data,**attr))
                    if statsFlag:
                        self.stats.append(self.calcStats(data,canvas))
                del data
        for h in self._text:
            plot_objects.append(self._text[h])
        
        if skipDrawing:
            del plot_objects
            self.isNewXAxis = False
            return
            
        if len(plot_objects) > 0:
            if not isinstance(canvas.GetXSpec(),tuple):
                canvas.SetXSpec('min')
            xAxis = None
            yAxis = None
            if not canvas.GetUnzoomed():
                (graphics, xAxis, yAxis) = canvas.last_draw
                xAxis = tuple(xAxis)
                yAxis = tuple(yAxis)
            if isinstance(self.forcedXAxis,tuple):
                xAxis = self.forcedXAxis

            if xAxis != self.lastXAxis:
                self.isNewXAxis = True
            else:
                self.isNewXAxis = False

            canvas.Draw(plot.PlotGraphics(plot_objects,self.title,self.xlabel,self.ylabel),
                        xAxis = xAxis, yAxis = yAxis)
            self.lastXAxis = xAxis
        else:
            dummy = [plot.PolyMarker([(0,0),(1,1)])]
            canvas.Draw(plot.PlotGraphics(dummy,self.title,self.xlabel,self.ylabel))
        del plot_objects

    def _getColorTimeIndices(self, timeSeries):
        """Return a list of indices where to change the color in the timeSeries"""
        numData = len(timeSeries)
        if numData == 0:
            return []
        elif len(self.colorTimeList) == 0:
            return [0, numData]
        else:
            minTime = min(timeSeries)
            while self.colorTimeList[0] < minTime:
                self.colorTimeList = self.colorTimeList[1:]
                self.colorList = self.colorList[1:]
                
        if len(self.colorTimeList) > 0:
            changePtList = digitize(self.colorTimeList, timeSeries)
            changePtList = compress(changePtList<numData, changePtList).tolist()
            changePtList = [0]+changePtList+[numData]
            return changePtList
        else:
            return [0, numData]
        
    def GetCanvas(self):
        #return self.Graph.canvas
        return self.canvas
    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        #sizer_1.Add(self.Graph, 1, wx.EXPAND, 0)
        sizer_1.Add(self.canvas, 1, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        sizer_1.SetSizeHints(self)
