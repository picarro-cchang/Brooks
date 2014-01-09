#!/usr/bin/python
#
# File Name: MyPlotCanvas.py
# Purpose: Customizes the wxWindows plotting system for the CRDI gui
#
# Notes:
#
# File History:
# 07-02-01 sze   Created file
# 07-03-07 sze   Added getTopLevel to improve handling of window focus
# 07-03-12 sze   Patched daylight saving time issue in normalize
# 07-05-18 sze   Added color handling for graph text and axis lines
import wx
import plot
import numpy
import time
import calendar
import math

def getTopLevel(win):
    p = c = win
    while c is not None:
        p = c
        c = c.GetParent()
    return p

class MyPlotCanvas(plot.PlotCanvas):
    def __init__(self,*args,**kwargs):
        plot.PlotCanvas.__init__(self,*args,**kwargs)
        self.topLevel = getTopLevel(self.canvas)
        self.unzoomed = True
        self.plotOptions = {}
        self.canvas.Bind(wx.EVT_RIGHT_UP, self.OnMouseRightUp)
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.OnKeyChange)
        self.canvas.Bind(wx.EVT_KEY_UP, self.OnKeyChange)
        self.canvas.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
        self.canvas.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
        self.inWindow = False
        self.GraphBackgroundColour = None
        self.xTickFormat = None
        self.yTickFormat = None
        self._timeAxes = (False,False)
        self.busy = False

    def Reset(self):
        self.unzoomed = True
        plot.PlotCanvas.Reset(self)

    # When the graph is zoomed or panned, we suppress changing the axes limits in the Update
    #  method of the graph panel (which can occur due to autoscaling when new points are added). The
    #  self.unzoomed flag is used to indicate that the graph is not being zoomed or panned.
    def GetUnzoomed(self):
        return self.unzoomed


    def SetZoomDrag(self):
        """Sets the graph window to zoom or drag mode, depending on the current state of the Ctrl key"""
        if wx.GetMouseState().ControlDown():
            if not self.GetEnableDrag(): self.SetEnableDrag(True)
        else:
            if not self.GetEnableZoom(): self.SetEnableZoom(True)

    def OnMouseLeftDown(self,event):
        self.unzoomed = False
        plot.PlotCanvas.OnMouseLeftDown(self,event)

    def OnMouseRightDown(self,event):
        self.unzoomed = False
        self._screenCoordinates = numpy.array(event.GetPosition())
        plot.PlotCanvas.OnMouseRightDown(self,event)

    def OnMouseLeftUp(self,event):
        plot.PlotCanvas.OnMouseLeftUp(self,event)
        self.SetZoomDrag()

    def OnMouseRightUp(self,event):
        self.SetZoomDrag()
        #if self.canvas.HasCapture():
        #    self.canvas.ReleaseMouse()

    # The Ctrl key is checked to switch between zoom and drag modes, provided that the cursor
    #  is within the graph window. In order for key presses to be captured, the graph window
    #  (self.canvas) must have the focus (which may be lost if the user operates an on-screen
    #  widget), so we capture the focus when the pointer enters the window.

    def OnKeyChange(self,event):
        mouseState = wx.GetMouseState()
        if self.inWindow and \
           not(mouseState.LeftDown() or mouseState.MiddleDown() or mouseState.RightDown()):
            self.SetZoomDrag()
        event.Skip()

    def OnEnterWindow(self,event):
        pw = getTopLevel(wx.Window.FindFocus())
        if pw == self.topLevel: self.canvas.SetFocus()
        self.inWindow = True
        mouseState = wx.GetMouseState()
        if self.inWindow and \
           not(mouseState.LeftDown() or mouseState.MiddleDown() or mouseState.RightDown()):
            self.SetZoomDrag()
        event.Skip()

    ## The self._hasDragged variable is True while a rubber-band zoom box is being drawn. We use
    ##  it to suppress drawing to the graph so that the box is not corrupted by updates. The zoom
    ##  is reset and drawing of the zoom box is aborted if the mouse is dragged outside the window
    ##  while a zoom box is being defined. Otherwise, the mouse up message indicating that the zoom
    ##  box is complete is not received, and a partial box is left on the screen.
    def OnLeaveWindow(self,event):
        #self.inWindow = False
        #if self._hasDragged:
        #    self._hasDragged = False
        #    self.Reset()
        plot.PlotCanvas.OnLeave(self,event)

    def OnMotion(self, event):
        if self.busy:
            event.Skip()
            return
        try:
            self.busy = True
            if self._zoomEnabled and event.LeftIsDown():
                if self._hasDragged:
                    self._drawRubberBand(self._zoomCorner1, self._zoomCorner2) # remove old
                else:
                    self._hasDragged= True
                self._zoomCorner2[0], self._zoomCorner2[1] = self._getXY(event)
                self._drawRubberBand(self._zoomCorner1, self._zoomCorner2) # add new
            elif self._dragEnabled:
                coordinates = event.GetPosition()
                newpos, oldpos = map(numpy.array, map(self.PositionScreenToUser, [coordinates, self._screenCoordinates]))
                dist = newpos-oldpos
                self._screenCoordinates = coordinates
                if self.last_draw is not None:
                    graphics, xAxis, yAxis= self.last_draw
                    if event.LeftIsDown():
                        yAxis -= dist[1]
                        xAxis -= dist[0]
                        self.Draw(graphics,xAxis,yAxis)
                    elif event.RightIsDown():
                        ymin,ymax = yAxis
                        yextra = (numpy.exp(-dist[1]/(ymax-ymin))-1)*(ymax-ymin)/2.0
                        yAxis[0] -= yextra
                        yAxis[1] += yextra
                        xmin,xmax = xAxis
                        xextra = (numpy.exp(-dist[0]/(xmax-xmin))-1)*(xmax-xmin)/2.0
                        xAxis[0] -= xextra
                        xAxis[1] += xextra
                        self.Draw(graphics,xAxis,yAxis)
        finally:
            self.busy = False

    # Setter and getter routines for miscellaneous properties of the canvas
    def SetXTickFormat(self,v):
        self.xTickFormat = v

    def GetXTickFormat():
        return self.xTickFormat

    def SetYTickFormat(self,v):
        self.yTickFormat = v

    def GetYTickFormat():
        return self.yTickFormat

    def SetTimeAxes(self,timeAxes):
        """ timeAxes is a tuple, first element is for X axis and second is for Y axis. If an element
        is False, time labels are not used. If an element is True, local time labels are used.
        For finer control, an element may itself be a tuple (offset,utc_flag) where offset is a signed
        offset in hours relative to either local time (utc_flag = False) or UTC (utc_flag = True).

        e.g. ((-8.0,True),False) uses time zone UTC-08:00 for X axis
        """
        if type(timeAxes) != tuple:
            raise TypeError, 'timeAxes must be a tuple.'
        self._timeAxes = timeAxes

    def _getTextExtent(self,dc,label):
        lines = label.split("\n")
        te = [dc.GetTextExtent(l) for l in lines]
        w = max([x for x,y in te])
        h = reduce(lambda x,y:x+y, [y for x,y in te])
        return (w,h)

    def _drawText(self,dc,label,leftX,topY):
        lines = label.split("\n")
        dy = 0
        for l in lines:
            dc.DrawText(l,leftX,topY+dy)
            dy += dc.GetTextExtent(l)[1]

    # We do not use scrollbars
    def SetShowScrollbars(self,value):
        plot.PlotCanvas.SetShowScrollbars(self,False)

    def SetGraphBackgroundColour(self,value):
        self.GraphBackgroundColour = value

    def GetGraphBackgroundColour(self):
        if self.GraphBackgroundColour == None: return self.GetBackgroundColour()
        else: return self.GraphBackgroundColour

    def Draw(self, graphics, xAxis = None, yAxis = None, dc = None):
        """Wrapper around _Draw, which handles log axes"""
        
        graphics.setLogScale(self.getLogScale())
        
        if xAxis is not None: xAxis = tuple(xAxis)
        if yAxis is not None: yAxis = tuple(yAxis)
        # check Axis is either tuple or none
        if type(xAxis) not in [type(None),tuple]:
            raise TypeError, "xAxis should be None or (minX,maxX)"+str(type(xAxis))
        if type(yAxis) not in [type(None),tuple]:
            raise TypeError, "yAxis should be None or (minY,maxY)"+str(type(xAxis))

        # check case for axis = (a,b) where a==b caused by improper zooms
        if xAxis != None:
            if xAxis[0] == xAxis[1]:
                return
        if yAxis != None:
            if yAxis[0] == yAxis[1]:
                return
        self._Draw(graphics, xAxis, yAxis, dc)
        
    def _Draw(self, graphics, xAxis = None, yAxis = None, dc = None):
        """\
        Draw objects in graphics with specified x and y axis.
        graphics- instance of PlotGraphics with list of PolyXXX objects
        xAxis - tuple with (min, max) axis range to view
        yAxis - same as xAxis
        dc - drawing context - doesn't have to be specified.
        If it's not, the offscreen buffer is used
        """
        if xAxis is not None:
            if xAxis[0] == xAxis[1]:
                self.Reset()
                return
        if yAxis is not None:
            if yAxis[0] == yAxis[1]:
                self.Reset()
                return
            
        p1, p2 = graphics.boundingBox()
        if numpy.isnan(p1).any() or numpy.isnan(p2).any():
            return
            
        if self._hasDragged: return
        if dc == None:
            # sets new dc and clears it
            dc = wx.BufferedDC(wx.ClientDC(self.canvas), self._Buffer)
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()

        dc.BeginDrawing()
        # dc.Clear()

        # set font size for every thing but title and legend
        dc.SetFont(self._getFont(self._fontSizeAxis))
        dc.SetTextForeground(self.GetForegroundColour())
        dc.SetTextBackground(self.GetBackgroundColour())

        # sizes axis to axis type, create lower left and upper right corners of plot
        if xAxis == None or yAxis == None:
            # One or both axis not specified in Draw
            p1, p2 = graphics.boundingBox()     # min, max points of graphics
            if xAxis == None:
                xAxis = self._axisInterval(self._xSpec, p1[0], p2[0]) # in user units
            if yAxis == None:
                yAxis = self._axisInterval(self._ySpec, p1[1], p2[1])
            # Adjust bounding box for axis spec
            p1[0],p1[1] = xAxis[0], yAxis[0]     # lower left corner user scale (xmin,ymin)
            p2[0],p2[1] = xAxis[1], yAxis[1]     # upper right corner user scale (xmax,ymax)
        else:
            # Both axis specified in Draw
            p1= numpy.array([xAxis[0], yAxis[0]])    # lower left corner user scale (xmin,ymin)
            p2= numpy.array([xAxis[1], yAxis[1]])     # upper right corner user scale (xmax,ymax)
            

        self.last_draw = (graphics, numpy.array(xAxis), numpy.array(yAxis))       # saves most recient values
        # Get ticks and textExtents for axis if required
        if numpy.isfinite(xAxis[0]) and numpy.isfinite(xAxis[1]) and self._xSpec is not 'none':
            xticks = self._xticks(xAxis[0], xAxis[1])
            xTextExtent = self._getTextExtent(dc,xticks[-1][1])# w h of x axis text last number on axis
        else:
            xticks = None
            xTextExtent= (0,0) # No text for ticks
        if numpy.isfinite(yAxis[0]) and numpy.isfinite(yAxis[1]) and self._ySpec is not 'none':
            yticks = self._yticks(yAxis[0], yAxis[1])
            if self.getLogScale()[1]:
                yTextExtent = self._getTextExtent(dc,'-2e-2')
            else:
                yTextExtentBottom = self._getTextExtent(dc,yticks[0][1])
                yTextExtentTop = self._getTextExtent(dc,yticks[-1][1])
                yTextExtent= (max(yTextExtentBottom[0],yTextExtentTop[0]),
                              max(yTextExtentBottom[1],yTextExtentTop[1]))
        else:
            yticks = None
            yTextExtent= (0,0) # No text for ticks

        # TextExtents for Title and Axis Labels
        titleWH, xLabelWH, yLabelWH= self._titleLablesWH(dc, graphics)

        # TextExtents for Legend
        legendBoxWH, legendSymExt, legendTextExt = self._legendWH(dc, graphics)

        # room around graph area
        scrollBarWidth = 20
        ylabelPadding  = 10
        rhsW= max(xTextExtent[0]//2, legendBoxWH[0]) # use larger of number width or legend width
        lhsW= yTextExtent[0] + yLabelWH[1] + ylabelPadding
        bottomH= max(xTextExtent[1], yTextExtent[1]/2.)+ xLabelWH[1]+scrollBarWidth
        topH= yTextExtent[1]/2. + titleWH[1]
        textSize_scale= numpy.array([rhsW+lhsW,bottomH+topH]) # make plot area smaller by text size
        textSize_shift= numpy.array([lhsW, bottomH])          # shift plot area by this amount

        # drawing title and labels text
        dc.SetFont(self._getFont(self._fontSizeTitle))
        titlePos= (self.plotbox_origin[0]+ lhsW + (self.plotbox_size[0]-lhsW-rhsW)/2.- titleWH[0]/2.,
                 self.plotbox_origin[1]- self.plotbox_size[1])
        dc.DrawText(graphics.getTitle(),titlePos[0],titlePos[1])
        dc.SetFont(self._getFont(self._fontSizeAxis))
        xLabelPos= (self.plotbox_origin[0]+ lhsW + (self.plotbox_size[0]-lhsW-rhsW)/2.- xLabelWH[0]/2.,
                 self.plotbox_origin[1]- xLabelWH[1])
        dc.DrawText(graphics.getXLabel(),xLabelPos[0],xLabelPos[1])
        yLabelPos= (self.plotbox_origin[0],
                 self.plotbox_origin[1]- bottomH- (self.plotbox_size[1]-bottomH-topH)/2.+ yLabelWH[0]/2.)
        if graphics.getYLabel():  # bug fix for Linux
            dc.DrawRotatedText(graphics.getYLabel(),yLabelPos[0],yLabelPos[1],90)

        # drawing legend makers and text
        if self._legendEnabled:
            self._drawLegend(dc,graphics,rhsW,topH,legendBoxWH, legendSymExt, legendTextExt)

        # allow for scaling and shifting plotted points
        scale = (self.plotbox_size-textSize_scale) / (p2-p1)* numpy.array((1,-1))
        shift = -p1*scale + self.plotbox_origin + textSize_shift * numpy.array((1,-1))
        self._pointScale= scale  # make available for mouse events
        self._pointShift= shift

        # Fill the center of the plotting region with another colour

        brush = dc.GetBrush()
        dc.SetBrush(wx.Brush(self.GetGraphBackgroundColour()))
        ptx,pty,rectWidth,rectHeight= self._point2ClientCoord(p1, p2)
        dc.DrawRectangle(ptx,pty,rectWidth,rectHeight)
        dc.SetBrush(brush)

        self._drawAxes(dc, p1, p2, scale, shift, xticks, yticks)

        graphics.scaleAndShift(scale, shift)
        graphics.setPrinterScale(self.printerScale)  # thicken up lines and markers if printing

        # set clipping area so drawing does not occur outside axis box
        #ptx,pty,rectWidth,rectHeight= self._point2ClientCoord(p1, p2)
        dc.SetClippingRegion(ptx,pty,rectWidth,rectHeight)
        # Draw the lines and markers
        #start = _time.clock()
        graphics.draw(dc)
        # print "entire graphics drawing took: %f second"%(_time.clock() - start)
        # remove the clipping region
        dc.DestroyClippingRegion()
        dc.EndDrawing()

        self._adjustScrollbars()


    def _drawAxes(self, dc, p1, p2, scale, shift, xticks, yticks):

        penWidth= self.printerScale        # increases thickness for printing only
        dc.SetPen(wx.Pen(self._gridColour, penWidth))

        yTickLength= 5 * self.printerScale  # lengthens lines for printing
        xTickLength= 5 * self.printerScale

        # set length of tick marks--long ones make grid
        if self._gridEnabled:
            xmin, xmax = p1[0],p2[0]
            ymin, ymax = p1[1],p2[1]
            for x, label in xticks:
                pt1 = scale*numpy.array([x, ymin])+shift
                pt2 = scale*numpy.array([x, ymax])+shift
                dc.DrawLine(pt1[0],pt1[1],pt2[0],pt2[1]) # draws tick mark d units
            for y, label in yticks:
                pt1 = scale*numpy.array([xmin, y])+shift
                pt2 = scale*numpy.array([xmax, y])+shift
                dc.DrawLine(pt1[0],pt1[1],pt2[0],pt2[1]) # draws tick mark d units
        dc.SetPen(wx.Pen(self.GetForegroundColour(), 2*penWidth))

        if self._xSpec is not 'none':
            lower, upper = p1[0],p2[0]
            text = 1
            for y, d in [(p1[1], -xTickLength), (p2[1], xTickLength)]:   # miny, maxy and tick lengths
                a1 = scale*numpy.array([lower, y])+shift
                a2 = scale*numpy.array([upper, y])+shift
                dc.DrawLine(a1[0],a1[1],a2[0],a2[1])  # draws upper and lower axis line
                for x, label in xticks:
                    pt = scale*numpy.array([x, y])+shift
                    dc.DrawLine(pt[0],pt[1],pt[0],pt[1] + d) # draws tick mark d units
                    if text:
                        te = self._getTextExtent(dc,label)
                        self._drawText(dc,label,pt[0]-te[0]//2,pt[1]+4)
                text = 0  # axis values not drawn on top side

        if self._ySpec is not 'none':
            lower, upper = p1[1],p2[1]
            text = 1
            for x, d in [(p1[0], -yTickLength), (p2[0], yTickLength)]:
                a1 = scale*numpy.array([x, lower])+shift
                a2 = scale*numpy.array([x, upper])+shift
                dc.DrawLine(a1[0],a1[1],a2[0],a2[1])
                for y, label in yticks:
                    pt = scale*numpy.array([x, y])+shift
                    dc.DrawLine(pt[0],pt[1],pt[0]-d,pt[1])
                    if text:
                        te = self._getTextExtent(dc,label)
                        self._drawText(dc,label,pt[0]-te[0]-4,pt[1]-0.5*te[1])
                text = 0    # axis values not drawn on right side

    # Allow XSpec and YSpec to be a callable object which computes the desired axis limits
    #  from the graphics bounding box
    def _axisInterval(self, spec, lower, upper):
        if callable(spec):
            return spec(lower,upper)
        else:
            return plot.PlotCanvas._axisInterval(self, spec, lower, upper)

    def _xticks(self, *args):
        if self._logscale[0]:
            return self._logticks(*args)
        elif self._timeAxes[0]:
            xTimeAxis = self._timeAxes[0]
            offsetTime = 0.0
            utcTime = False
            if isinstance(xTimeAxis,tuple):
                offsetTime = xTimeAxis[0]
                utcTime = xTimeAxis[1]
            return self._timeticks(*args,
                                   **dict(utcTime=utcTime,offsetTime=offsetTime,format=self.xTickFormat))
        else:
            return self._ticks(*args,**dict(format=self.xTickFormat))

    def _yticks(self, *args):
        if self._logscale[1]:
            return self._logticks(*args)
        elif self._timeAxes[1]:
            yTimeAxis = self._timeAxes[1]
            offsetTime = 0.0
            utcTime = False
            if isinstance(yTimeAxis,tuple):
                offsetTime = yTimeAxis[0]
                utcTime = yTimeAxis[1]
            return self._timeticks(*args,
                                   **dict(utcTime=utcTime,offsetTime=offsetTime,format=self.yTickFormat))
        else:
            return self._ticks(*args,**dict(format=self.yTickFormat))

    def _timeticks(self,lower,upper,ndiv=7,utcTime=True,offsetTime=0,format=None):
        if format is None:
            format="%H:%M:%S\n%d-%b-%Y"
        if utcTime:
            to_tm = lambda t: time.gmtime(max(0,t+3600*offsetTime))
            from_tm = lambda tm: calendar.timegm(tm)-3600*offsetTime
        else:
            to_tm = lambda t: time.localtime(max(0,t+3600*offsetTime))
            from_tm = lambda tm: time.mktime(tm)-3600*offsetTime
        duration = upper-lower
        ideal = duration/ndiv
        if ideal >= 0.4:
            dis = _getBestIncr(ideal)
            label_list = []
            time_list = []
            cur = lower
            tm = _getNiceTm(to_tm(cur),dis)
            while True:
                cur = from_tm(tm)
                if cur > upper: break
                label_list.append(time.strftime(format,tm))
                time_list.append(cur)
                temp = list(tm)
                temp[dis.field] += dis.field_incr
                tm = _normalize(temp)
            return zip(time_list,label_list)
        else:
            result = []
            for t,l in self._ticks(lower,upper,timeTicks=True):
                fmtfrac = format.replace("%S","%S."+("%s"%(l.split(".")[-1],)))
                label = time.strftime(fmtfrac,to_tm(int(t)))
                result.append((t,label))
            return result

    def _ticks(self, lower, upper, format=None, timeTicks = False):
        ideal = (upper-lower)/7.
        log = numpy.log10(ideal)
        power = numpy.floor(log)
        fraction = log-power
        factor = 1.
        error = fraction
        for f, lf in self._multiples:
            e = numpy.abs(fraction-lf)
            if e < error:
                error = e
                factor = f
        grid = factor * 10.**power
        if format is None:
            if (power > 4 or power < -4) and not timeTicks:
                format = '%+7.1e'
            elif power >= 0:
                digits = max(1, int(power))
                format = '%' + `digits`+'.0f'
            else:
                digits = -int(power)
                format = '%'+`digits+2`+'.'+`digits`+'f'
        ticks = []
        t = -grid*numpy.floor(-lower/grid)
        tickCounter = 0
        while t <= upper and tickCounter < 20:
            ticks.append( (t, format % (t,)) )
            t = t + grid
            tickCounter += 1
        return ticks

    _multiples = [(2., numpy.log10(2.)), (5., numpy.log10(5.))]


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

year = 0
month = 1
day = 2
hour = 3
min = 4
sec = 5

class NiceDateTimeIncrement(object):
    def __init__(self,incr_s,field,field_incr):
        self.incr_s = incr_s
        self.field  = field
        self.field_incr = field_incr
    def __str__(self):
        key = ['year', 'month', 'day', 'hour', 'minute', 'second']
        s = ""
        if self.field_incr != 1: s = 's'
        return "%d %s%s" % (self.field_incr,key[self.field],s,)

_incrList = [
    NiceDateTimeIncrement(1.0, sec, 1),
    NiceDateTimeIncrement(2.0, sec, 2),
    NiceDateTimeIncrement(5.0, sec, 5),
    NiceDateTimeIncrement(10.0, sec, 10),
    NiceDateTimeIncrement(30.0, sec, 30),
    NiceDateTimeIncrement(60.0, min, 1),
    NiceDateTimeIncrement(120.0, min, 2),
    NiceDateTimeIncrement(300.0, min, 5),
    NiceDateTimeIncrement(900.0, min, 15),
    NiceDateTimeIncrement(1800.0, min, 30),
    NiceDateTimeIncrement(3600.0, hour, 1),
    NiceDateTimeIncrement(3*3600.0, hour, 3),
    NiceDateTimeIncrement(6*3600.0, hour, 6),
    NiceDateTimeIncrement(12*3600.0, hour, 12),
    NiceDateTimeIncrement(24*3600.0, day, 1),
    NiceDateTimeIncrement(48*3600.0, day, 2),
    NiceDateTimeIncrement(120*3600.0, day, 5),
    NiceDateTimeIncrement(240*3600.0, day, 10),
    NiceDateTimeIncrement(30*24*3600.0, month, 1),
    NiceDateTimeIncrement(91*24*3600.0, month, 3),
    NiceDateTimeIncrement(182*24*3600.0, month, 6),
    NiceDateTimeIncrement(365*24*3600.0, year, 1),
    NiceDateTimeIncrement(2*365*24*3600.0, year, 2),
    NiceDateTimeIncrement(5*365*24*3600.0, year, 5),
    NiceDateTimeIncrement(10*365*24*3600.0, year, 10),
    NiceDateTimeIncrement(25*365*24*3600.0, year, 25)]

def _normalize(tm):
    """
    Returns a time tuple in standard format
    >>> tm = (2007, 2, 4, 0, 53, 20, 6, 35, 0)
    >>> _normalize(tm)
    (2007, 2, 4, 0, 53, 20, 6, 35, 0)

    Only the first six fields are important
    >>> _normalize(tm[:6])
    (2007, 2, 4, 0, 53, 20, 6, 35, 0)

    Overflowing the seconds should increment the minute
    >>> tm = (2007, 2, 4, 0, 53, 80)
    >>> _normalize(tm)
    (2007, 2, 4, 0, 54, 20, 6, 35, 0)

    Overflowing the minute should increment the hour
    >>> tm = (2007, 2, 4, 0, 75, 20)
    >>> _normalize(tm)
    (2007, 2, 4, 1, 15, 20, 6, 35, 0)

    Overflowing the hour should increment the day
    >>> tm = (2007, 2, 4, 25, 53, 20)
    >>> _normalize(tm)
    (2007, 2, 5, 1, 53, 20, 0, 36, 0)

    Overflowing the day should increment the month
    >>> tm = (2007, 2, 31, 1, 53, 20)
    >>> _normalize(tm)
    (2007, 3, 3, 1, 53, 20, 5, 62, 0)

    Overflowing the month should increment the year
    >>> tm = (2007, 14, 6, 1, 53, 20)
    >>> _normalize(tm)
    (2008, 2, 6, 1, 53, 20, 2, 37, 0)

    Overflowing Dec 31st should increment the year
    >>> tm = (2007, 12, 33, 1, 53, 20)
    >>> _normalize(tm)
    (2008, 1, 2, 1, 53, 20, 2, 2, 0)
    """
    # Handle months separately, since the usual time functions give errors
    temp = list(tm)
    if temp[month] > 12:
        temp[month] -= 12
        temp[year] += 1
    tm1 = list(time.gmtime(calendar.timegm(tuple(temp))))
    tm1[8] = temp[8] # Preserve daylight time flag
    return tuple(tm1)

def _fieldBase(field):
    if field == month or field == day: return 1
    return 0

def _getNiceTm(current_tm,discretization,after=True):
    """Using the specified discretization (expressed as a NiceDateTimeIncrement),
    return the closest "nice time" which
    1) occurs at or after "current_tm", if after  is True
    2) occurs at or before "current_tm", if after is False

    >>> dis = _incrList[1] # Choose 2s discretization
    >>> tm = (2007, 2, 4, 1, 53, 9.4)
    >>> _getNiceTm(tm,dis)
    (2007, 2, 4, 1, 53, 10, 6, 35, 0)
    >>> _getNiceTm(tm,dis,False)
    (2007, 2, 4, 1, 53, 8, 6, 35, 0)
    >>> tm = (2007, 2, 4, 1, 53, 8.1)
    >>> _getNiceTm(tm,dis)
    (2007, 2, 4, 1, 53, 10, 6, 35, 0)
    >>> _getNiceTm(tm,dis,False)
    (2007, 2, 4, 1, 53, 8, 6, 35, 0)
"""
    assert(isinstance(discretization,NiceDateTimeIncrement))
    b = _fieldBase(discretization.field)
    i = discretization.field_incr
    nice = list(current_tm)
    if after:
        nice[sec] += 1 # Kludge since fractional seconds are not in a tm
        for z in range(discretization.field,sec):
            if nice[z+1] != _fieldBase(z+1):
                nice[discretization.field] += 1
                break
        offset = nice[discretization.field]-b
        nice[discretization.field] = b+i*((offset+i-1)//i)
    else:
        offset = nice[discretization.field]-b
        nice[discretization.field] = b+i*(offset//i)

    for z in range(discretization.field,sec): nice[z+1] = _fieldBase(z+1)
    return _normalize(nice)

def _getBestIncr(interval):
    incr = None
    for dis in _incrList:
        if interval < dis.incr_s:
            return dis

if __name__ == "__main__":
    import doctest
    doctest.testmod()
