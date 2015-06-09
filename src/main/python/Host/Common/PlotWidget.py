#!/usr/bin/python
#
# File Name: PlotWidget.py
# Purpose: Customizes the wxWindows plotting system for the CRDI gui
#
# Notes:
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-10-31 sze   Modified to work with numpy

import wx
import sys
if "../Common" not in sys.path: sys.path.append("../Common")
import Host.Common.plot as plot

try:
    import Numeric
except:
    import numpy as Numeric

class MyPlotCanvas(plot.PlotCanvas):
    def __init__(self, *args, **kwds):
        plot.PlotCanvas.__init__(self, *args, **kwds)
        self._panActive = False
        self._zoomActive = False
        self._usePzLimits = False
        self._pzXLim = None
        self._pzYLim = None
        self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRightUp)

    def Draw(self, graphics, xAxis = None, yAxis = None, dc = None):
        if dc == None:
            dc = wx.BufferedDC(wx.ClientDC(self), self._Buffer)
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
        if self._usePzLimits:
            plot.PlotCanvas.Draw(self,graphics,self._pzXLim,self._pzYLim,dc)
        else:
            plot.PlotCanvas.Draw(self,graphics, xAxis , yAxis , dc)

    def OnMotion(self, event):
        """ Drag with the left button to pan and with the right button to zoom. Double-click
        to restore autoscaling """
        if self._panActive:
            if event.LeftIsDown():
                self._zoomCorner2[0], self._zoomCorner2[1] = self.GetXY(event)
                Xmin,Xmax = self._pzXLim
                Ymin,Ymax = self._pzYLim
                dX = self._zoomCorner2[0] - self._zoomCorner1[0]
                dY = self._zoomCorner2[1] - self._zoomCorner1[1]
                self._pzXLim = Xmin-dX, Xmax-dX
                self._pzYLim = Ymin-dY, Ymax-dY
                if self.last_draw is not None:
                    self.Draw(self.last_draw[0],xAxis=self._pzXLim,yAxis=self._pzYLim)
            else: self._panActive = False

        if self._zoomActive:
            if event.RightIsDown():
                newX,newY = event.GetPosition()
                Xmin,Xmax = self._pzXLim
                Xrange = Xmax - Xmin
                Xcen = 0.5*(Xmin+Xmax)
                Ymin,Ymax = self._pzYLim
                Yrange = Ymax - Ymin
                Ycen = 0.5*(Ymin+Ymax)
                dX = newX - self._zoomCursorX
                dY = newY - self._zoomCursorY
                Xfac,Yfac = Numeric.exp((-0.005*dX,0.005*dY))
                self._pzXLim = Xcen-0.5*Xfac*Xrange, Xcen+0.5*Xfac*Xrange
                self._pzYLim = Ycen-0.5*Yfac*Yrange, Ycen+0.5*Yfac*Yrange
                self._zoomCursorX,self._zoomCursorY = newX,newY
                if self.last_draw is not None:
                    self.Draw(self.last_draw[0],xAxis=self._pzXLim,yAxis=self._pzYLim)
            else: self._zoomActive = False

    def OnMouseLeftDown(self,event):
        self._zoomCorner1[0], self._zoomCorner1[1]= self.GetXY(event)
        self._usePzLimits = True
        self._pzXLim = self.GetXCurrentRange()
        self._pzYLim = self.GetYCurrentRange()
        self._panActive = True
        self._zoomActive = False

    def OnMouseLeftUp(self, event):
        self._panActive = False

    def OnMouseDoubleClick(self,event):
        self._usePzLimits = False

    def OnMouseRightDown(self,event):
        self._zoomCursorX, self._zoomCursorY = event.GetPosition()
        self._usePzLimits = True
        self._pzXLim = self.GetXCurrentRange()
        self._pzYLim = self.GetYCurrentRange()
        self._panActive = False
        self._zoomActive = True

    def OnMouseRightUp(self,event):
        self._zoomActive = False

    def _drawAxes(self, dc, p1, p2, scale, shift, xticks, yticks):
        """ Change appearance of gridlines on the axes """
        penWidth = self.printerScale        # increases thickness for printing only
        dc.SetPen(wx.Pen(wx.NamedColour('BLACK'), penWidth))

        yTickLength= 5 * self.printerScale  # lengthens lines for printing
        xTickLength= 5 * self.printerScale

        if self._gridEnabled:
#          dc.SetPen(wx.Pen(wx.NamedColour('LIGHT STEEL BLUE'), penWidth))
            dc.SetPen(wx.Pen(wx.NamedColour('LIGHT GREY'), penWidth))
            xmin, xmax = p1[0],p2[0]
            ymin, ymax = p1[1],p2[1]
            for x, label in xticks:
                pt1 = scale*Numeric.array([x, ymin])+shift
                pt2 = scale*Numeric.array([x, ymax])+shift
                dc.DrawLine(pt1[0],pt1[1],pt2[0],pt2[1]) # draws tick mark d units
            for y, label in yticks:
                pt1 = scale*Numeric.array([xmin, y])+shift
                pt2 = scale*Numeric.array([xmax, y])+shift
                dc.DrawLine(pt1[0],pt1[1],pt2[0],pt2[1]) # draws tick mark d units
            dc.SetPen(wx.Pen(wx.NamedColour('BLACK'), 2*penWidth))

        if self._xSpec != 'none':
            lower, upper = p1[0],p2[0]
            text = 1
            for y, d in [(p1[1], -xTickLength), (p2[1], xTickLength)]:   # miny, maxy and tick lengths
                a1 = scale*Numeric.array([lower, y])+shift
                a2 = scale*Numeric.array([upper, y])+shift
                dc.DrawLine(a1[0],a1[1],a2[0],a2[1])  # draws upper and lower axis line
                for x, label in xticks:
                    pt = scale*Numeric.array([x, y])+shift
                    dc.DrawLine(pt[0],pt[1],pt[0],pt[1] + d) # draws tick mark d units
                    if text:
                        dc.DrawText(label,pt[0],pt[1]+4)
                text = 0  # axis values not drawn on top side

        if self._ySpec != 'none':
            lower, upper = p1[1],p2[1]
            text = 1
            h = dc.GetCharHeight()
            for x, d in [(p1[0], -yTickLength), (p2[0], yTickLength)]:
                a1 = scale*Numeric.array([x, lower])+shift
                a2 = scale*Numeric.array([x, upper])+shift
                dc.DrawLine(a1[0],a1[1],a2[0],a2[1])
                for y, label in yticks:
                    pt = scale*Numeric.array([x, y])+shift
                    dc.DrawLine(pt[0],pt[1],pt[0]-d,pt[1])
                    if text:
                        dc.DrawText(label,pt[0]-dc.GetTextExtent(label)[0]-4,
                                    pt[1]-0.5*h)
                text = 0    # axis values not drawn on right side

class PlotWidget(wx.Panel):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, *args, **kwds)
        self.canvas = MyPlotCanvas(self,-1)
        # Now put all into a sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        self.sizer.Add(self.canvas, 1, wx.LEFT|wx.TOP|wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()