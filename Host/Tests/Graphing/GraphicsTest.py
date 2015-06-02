#!/usr/bin/python
#
"""
File Name: GraphicsTest.py
Purpose: Simple program utilizing GraphPanel to test its operation

File History:
    19-Feb-2012  sze       Initial version

Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
import wx
from numpy import *
from Host.Tests.Graphing.GraphicsTestGui import GraphicsFrameGui
from Host.Common.GraphPanel import Series

SERIES_POINTS = 500
NaN = 1e1000/1e1000

class GraphicsFrame(GraphicsFrameGui):
    def __init__(self,*a,**k):
        GraphicsFrameGui.__init__(self,*a,**k)
        self.series1 = Series(SERIES_POINTS)
        self.graphPanelMain.SetGraphProperties(xlabel='x',timeAxes=(False,False),ylabel='y',grid=True,
            frameColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            backgroundColour=wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE),
            logScale=(False,False))
        self.graphPanelMain.AddSeriesAsLine(self.series1,colour='blue',width=2)
        self.graphPanelMain.AddSeriesAsPoints(self.series1,colour='red',fillcolour='red',marker='square',size=3,width=1)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(200)

    def onClose(self,evt):
        self.timer.Stop()
        if evt: evt.Skip()

    def onTimer(self,evt):
        self.graphPanelMain.Update(delay=0)
        if evt: evt.Skip()

    def onPlot(self,evt):
        self.series1.Clear()
        x = linspace(0.0,4*pi,SERIES_POINTS)
        x[11] = NaN
        x[17] = NaN
        x[20] = NaN
        y = sin(x)
        for i in range(len(x)):
            self.series1.Add(x[i],y[i])
        self.graphPanelMain.Text(x,y,len(x)*["Hello"])

if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frameMain = GraphicsFrame(None, -1, "")
    app.SetTopWindow(frameMain)
    frameMain.Show()
    app.MainLoop()