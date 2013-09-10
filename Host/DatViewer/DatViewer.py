oldSum = sum
import wx
import matplotlib
matplotlib.use('WXAgg')
import pytz
import matplotlib.pyplot
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import *
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import datetime
#import logging
import os
import time
import threading
#import traceback
import sys
import zipfile
import tempfile

#from cStringIO import StringIO
from numpy import *
from tables import *
from scipy.signal import lfilter
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.wx.editor import Editor
from enthought.traits.ui.basic_editor_factory import BasicEditorFactory
from enthought.traits.ui.menu import *
#from traceback import format_exc
from configobj import ConfigObj

Button1 = Button   # This is overwritten by pylab import
######################################################
#################  FigureInteraction  ##########################
######################################################
from pylab import *


# cursors
class Cursors:  # namespace
    HAND, POINTER, SELECT_REGION, MOVE, MAGNIFIER = range(5)
cursors = Cursors()
# Dictionary for mapping cursor names to wx cursor names
cursord = {
    cursors.MOVE: wx.CURSOR_HAND,
    cursors.HAND: wx.CURSOR_HAND,
    cursors.POINTER: wx.CURSOR_ARROW,
    cursors.SELECT_REGION: wx.CURSOR_CROSS,
    cursors.MAGNIFIER: wx.CURSOR_MAGNIFIER}


# Decorator to protect access to matplotlib figure from several threads
#  self.lock should be a recursive lock
def checkLock(func):
    def wrapper(self, *a, **k):
        try:
            self.lock.acquire()
            return func(self, *a, **k)
        finally:
            self.lock.release()
    return wrapper


class FigureInteraction(object):
    def __init__(self, fig, lock):
        self.fig = fig
        self.lock = lock
        self.canvas = fig.canvas
        w = self.canvas

        # Find the nearest top-level window
        while w and not w.IsTopLevel():
            w = w.GetParent()
        self.topLevel = {self.canvas: w}
        self.lastTime = 0
        self.lastButton = 0
        self._button_pressed = None
        self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)
        self._active = ""
        self._idle = True
        self._xypress = []
        self._lastCursor = None
        self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.mpl_connect('button_release_event', self.onRelease)
        self.canvas.mpl_connect('key_press_event', self.onKeyDown)
        self.canvas.mpl_connect('key_release_event', self.onKeyUp)
        self.canvas.mpl_connect('figure_enter_event', self.onEnterFigure)
        #self.canvas.mpl_connect('figure_leave_event', self.onLeaveFigure)
        #self.canvas.mpl_connect('axes_enter_event', self.onEnterAxes)
        #self.canvas.mpl_connect('axes_leave_event', self.onLeaveAxes)

        # Get all the subplots within the figure
        self.subplots = fig.axes
        self.autoscale = {}
        for s in self.subplots:
            self.autoscale[s] = True

    @checkLock
    def isActive(self):
        return self._active
        
    @checkLock
    def onEnterFigure(self, event):
        w = wx.Window.FindFocus()
        if w not in self.topLevel:
            p = w
            while p and not p.IsTopLevel():
                p = p.GetParent()
            self.topLevel[w] = p
        if self.topLevel[w] == self.topLevel[event.canvas]:
            event.canvas.SetFocus()

    @checkLock
    def onLeaveFigure(self, event):
        print "Leaving figure", event.canvas.figure

    @checkLock
    def onEnterAxes(self, event):
        print "Entering axes", event.inaxes

    @checkLock
    def onLeaveAxes(self, event):
        print "Leaving axes", event.inaxes

    @checkLock
    def onKeyDown(self, event):
        if self._active:
            return
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        elif event.key == "shift":
            self.setCursor(cursors.MOVE)

    @checkLock
    def onKeyUp(self, event):
        if self._active:
            return
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        elif event.key == "shift":
                self.setCursor(cursors.MAGNIFIER)

    @checkLock
    def draw(self):
        'redraw the canvases, update the locators'
        for a in self.fig.get_axes():
            xaxis = getattr(a, 'xaxis', None)
            yaxis = getattr(a, 'yaxis', None)
            locators = []
            if xaxis is not None:
                locators.append(xaxis.get_major_locator())
                locators.append(xaxis.get_minor_locator())
            if yaxis is not None:
                locators.append(yaxis.get_major_locator())
                locators.append(yaxis.get_minor_locator())

            for loc in locators:
                loc.refresh()
        self.canvas.draw()

    @checkLock
    def onRelease(self, event):
        # Get the axes within which the point falls
        if self._active == "ZOOM":
            self.release_zoom(event)
        elif self._active == "PAN":
            self.release_pan(event)
        self._active = ""

    @checkLock
    def release_zoom(self, event):
        if not self._xypress:
            return
        last_a = []

        for cur_xypress in self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, ind, lim, trans = cur_xypress

            # ignore singular clicks - 5 pixels is a threshold
            if abs(x-lastx) < 5 or abs(y-lasty) < 5:
                self._xypress = None
                self.draw()
                return

            x0, y0, x1, y1 = lim.extents

            # zoom to rect
            inverse = a.transData.inverted()
            lastx, lasty = inverse.transform_point((lastx, lasty))
            x, y = inverse.transform_point((x, y))
            Xmin, Xmax = a.get_xlim()
            Ymin, Ymax = a.get_ylim()

            # detect twinx,y axes and avoid double zooming
            twinx, twiny = False, False
            if last_a:
                for la in last_a:
                    if a.get_shared_x_axes().joined(a, la):
                        twinx = True
                    if a.get_shared_y_axes().joined(a, la):
                        twiny = True
            last_a.append(a)

            if twinx:
                x0, x1 = Xmin, Xmax
            else:
                if Xmin < Xmax:
                    if x < lastx:
                        x0, x1 = x, lastx
                    else:
                        x0, x1 = lastx, x

                    if x0 < Xmin:
                        x0 = Xmin
                    if x1 > Xmax:
                        x1 = Xmax
                else:
                    if x > lastx:
                        x0, x1 = x, lastx
                    else:
                        x0, x1 = lastx, x

                    if x0 > Xmin:
                        x0 = Xmin
                    if x1 < Xmax:
                        x1 = Xmax

            if twiny:
                y0, y1 = Ymin, Ymax
            else:
                if Ymin < Ymax:
                    if y < lasty:
                        y0, y1 = y, lasty
                    else:
                        y0, y1 = lasty, y

                    if y0 < Ymin:
                        y0 = Ymin
                    if y1 > Ymax:
                        y1 = Ymax
                else:
                    if y > lasty:
                        y0, y1 = y, lasty
                    else:
                        y0, y1 = lasty, y

                    if y0 > Ymin:
                        y0 = Ymin
                    if y1 < Ymax:
                        y1 = Ymax

            if self._button_pressed == 1:
                a.set_xlim((x0, x1))
                a.set_ylim((y0, y1))

            elif self._button_pressed == 3:
                if a.get_xscale() == 'log':
                    alpha = np.log(Xmax/Xmin)/np.log(x1/x0)
                    rx1 = pow(Xmin/x0, alpha)*Xmin
                    rx2 = pow(Xmax/x0, alpha)*Xmin
                else:
                    alpha = (Xmax-Xmin)/(x1-x0)
                    rx1 = alpha*(Xmin-x0)+Xmin
                    rx2 = alpha*(Xmax-x0)+Xmin

                if a.get_yscale() == 'log':
                    alpha = np.log(Ymax/Ymin)/np.log(y1/y0)
                    ry1 = pow(Ymin/y0, alpha)*Ymin
                    ry2 = pow(Ymax/y0, alpha)*Ymin
                else:
                    alpha = (Ymax-Ymin)/(y1-y0)
                    ry1 = alpha*(Ymin-y0)+Ymin
                    ry2 = alpha*(Ymax-y0)+Ymin
                a.set_xlim((rx1, rx2))
                a.set_ylim((ry1, ry2))

        self.draw()
        self._xypress = None
        self._button_pressed = None
        try:
            del self.lastrect
        except AttributeError:
            pass

    @checkLock
    def onClick(self, event):
        # Get the axes within which the point falls
        print "click", event.button
        self._active = "ACTIVE"
        axes = event.inaxes
        if axes not in self.subplots:
            return
        now, button = time.time(), event.button
        delay = now - self.lastTime
        self.lastTime, self.lastButton = now, button

        if button == self.lastButton and delay < 0.3:
            for a in self.fig.get_axes():
                if a.in_axes(event):
                    a.relim()
                    a.autoscale_view()
                    print "double click"
                    self.autoscale[a] = True
            self.draw()
            return

        if event.key is None:
            self._active = "ZOOM"
            self.press_zoom(event)
        elif event.key == "shift":
            self._active = "PAN"
            self.press_pan(event)
        else:
            return

    @checkLock
    def press_zoom(self, event):
        if event.button == 1:
            self._button_pressed = 1
        elif event.button == 3:
            self._button_pressed = 3
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y
        self._xypress = []
        for i, a in enumerate(self.fig.get_axes()):
            if x is not None and y is not None and a.in_axes(event) \
                    and a.get_navigate() and a.can_zoom():
                self.autoscale[a] = False
                self._xypress.append((x, y, a, i, a.viewLim.frozen(), a.transData.frozen()))

    @checkLock
    def setCursor(self, cursor):
        if self._lastCursor != cursor:
            self.set_cursor(cursor)
            self._lastCursor = cursor

    @checkLock
    def onMouseMove(self, event):
        if not event.inaxes:
            self.setCursor(cursors.POINTER)
        else:
            if self._active == 'ZOOM':
                self.setCursor(cursors.MAGNIFIER)
                if self._xypress:
                    x, y = event.x, event.y
                    lastx, lasty, a, ind, lim, trans = self._xypress[0]
                    self.draw_rubberband(event, x, y, lastx, lasty)
            elif self._active == 'PAN':
                self.setCursor(cursors.MOVE)
            else:
                if event.key is None:
                    self.setCursor(cursors.MAGNIFIER)
                elif event.key == "shift":
                    self.setCursor(cursors.MOVE)
                else:
                    self.setCursor(cursors.POINTER)

    @checkLock
    def draw_rubberband(self, event, x0, y0, x1, y1):
        'adapted from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/189744'
        canvas = self.canvas
        dc = wx.ClientDC(canvas)

        # Set logical function to XOR for rubberbanding
        dc.SetLogicalFunction(wx.XOR)

        # Set dc brush and pen
        # Here I set brush and pen to white and grey respectively
        # You can set it to your own choices

        # The brush setting is not really needed since we
        # dont do any filling of the dc. It is set just for
        # the sake of completion.

        wbrush = wx.Brush(wx.Colour(255, 255, 255), wx.TRANSPARENT)
        wpen = wx.Pen(wx.Colour(200, 200, 200), 1, wx.SOLID)
        dc.SetBrush(wbrush)
        dc.SetPen(wpen)

        dc.ResetBoundingBox()
        dc.BeginDrawing()
        height = self.canvas.figure.bbox.height
        y1 = height - y1
        y0 = height - y0

        if y1 < y0:
            y0, y1 = y1, y0
        if x1 < y0:
            x0, x1 = x1, x0

        w = x1 - x0
        h = y1 - y0

        rect = int(x0), int(y0), int(w), int(h)
        try:
            lastrect = self.lastrect
        except AttributeError:
            pass
        else:
            dc.DrawRectangle(*lastrect)  # erase last

        self.lastrect = rect
        dc.DrawRectangle(*rect)
        dc.EndDrawing()

    @checkLock
    def press_pan(self, event):
        'the press mouse button in pan/zoom mode callback'

        if event.button == 1:
            self._button_pressed = 1
        elif event.button == 3:
            self._button_pressed = 3
        else:
            self._button_pressed = None
            return

        x, y = event.x, event.y

        self._xypress = []
        for i, a in enumerate(self.canvas.figure.get_axes()):
            if x is not None and y is not None and a.in_axes(event) and a.get_navigate():
                a.start_pan(x, y, event.button)
                self.autoscale[a] = False
                self._xypress.append((a, i))
                self.canvas.mpl_disconnect(self._idDrag)
                self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.drag_pan)

    @checkLock
    def release_pan(self, event):
        'the release mouse button callback in pan/zoom mode'
        self.canvas.mpl_disconnect(self._idDrag)
        self._idDrag = self.canvas.mpl_connect('motion_notify_event', self.onMouseMove)
        for a, ind in self._xypress:
            a.end_pan()
        if not self._xypress:
            return
        self._xypress = []
        self._button_pressed = None
        self.draw()

    @checkLock
    def drag_pan(self, event):
        'the drag callback in pan/zoom mode'

        for a, ind in self._xypress:
            #safer to use the recorded button at the press than current button:
            #multiple button can get pressed during motion...
            a.drag_pan(self._button_pressed, event.key, event.x, event.y)
        self.dynamic_update()

    @checkLock
    def dynamic_update(self):
        d = self._idle
        self._idle = False
        if d:
            self.canvas.draw()
            self._idle = True

    @checkLock
    def set_cursor(self, cursor):
        cursor = wx.StockCursor(cursord[cursor])
        self.canvas.SetCursor(cursor)


###############################################################################
#############################  Allan variance routines   ######################
###############################################################################
class AllanVar(object):
    """ Class for computation of Allan Variance of a data series. Variances are computed over sets of
  size 1,2,...,2**(nBins-1). In order to process a new data point call processDatum(value). In order
  to recover the results, call getVariances(). In order to reset the calculation, call reset(). """

    def __init__(self, nBins):
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

    def processDatum(self, value):
        """ Process a value for the Allan variance calculation """
        for bin in self.bins:
            bin.process(value)
        self.counter += 1

    def getVariances(self):
        """ Get the result of the Allan variance calculation as (count,(var1,var2,var4,...)) """
        return (self.counter, tuple([bin.allanVar for bin in self.bins]))


class AllanBin(object):
    """ Internal class for Allan variance calculation """
    def __init__(self, averagingLength):
        self.averagingLength = averagingLength
        self.reset()

    def reset(self):
        self.sum, self.sumSq = 0, 0
        self.sumPos, self.numPos = 0, 0
        self.sumNeg, self.numNeg = 0, 0
        self.nPairs, self.allanVar = 0, 0

    def process(self, value):
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
###############################################################################


def sortByName(top, nameList):
    nameList.sort()
    return nameList


def sortByMtime(top, nameList):
    """Sort a list of files by modification time"""
    # Decorate with the modification time of the file for sorting
    fileList = [(os.path.getmtime(os.path.join(top, name)), name) for name in nameList]
    fileList.sort()
    return [name for t, name in fileList]


def walkTree(top, onError=None, sortDir=None, sortFiles=None):
    """Generator which traverses a directory tree rooted at "top" in bottom to top order (i.e., the children are visited
    before the parent, and directories are visited before files.) The order of directory traversal is determined by
    "sortDir" and the order of file traversal is determined by "sortFiles". If "onError" is defined, exceptions during
    directory listings are passed to this function. When the function yields a result, it is either the pair
    ('file',fileName)  or ('dir',directoryName)"""
    try:
        names = os.listdir(top)
    except OSError, err:
        if onError is not None:
            onError(err)
        return
    # Obtain lists of directories and files which are not links
    dirs, nondirs = [], []
    for name in names:
        fullName = os.path.join(top, name)
        if not os.path.islink(fullName):
            if os.path.isdir(fullName):
                dirs.append(name)
            else:
                nondirs.append(name)
    # Sort the directories and nondirectories (in-place)
    if sortDir is not None:
        dirs = sortDir(top, dirs)
    if sortFiles is not None:
        nondirs = sortFiles(top, nondirs)
    # Recursively call walkTree on directories
    for dir in dirs:
        for x in walkTree(os.path.join(top, dir), onError, sortDir, sortFiles):
            yield x
    # Yield up files
    for file in nondirs:
        yield 'file', os.path.join(top, file)
    # Yield up the current directory
    yield 'dir', top

ORIGIN = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)
UNIXORIGIN = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)


def datetimeToTimestamp(t):
    td = t - ORIGIN
    return (td.days*86400 + td.seconds)*1000 + td.microseconds//1000


def getTimestamp():
    """Returns 64-bit millisecond resolution timestamp for instrument"""
    return datetimeToTimestamp(datetime.datetime.utcnow())


def timestampToUtcDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to UTC datetime"""
    return ORIGIN + datetime.timedelta(microseconds=1000*timestamp)


def timestampToLocalDatetime(timestamp):
    """Converts 64-bit millisecond resolution timestamp to local datetime"""
    offset = datetime.datetime.now() - datetime.datetime.utcnow()
    return timestampToUtcDatetime(timestamp) + offset


def formatTime(dateTime):
    ms = dateTime.microsecond//1000
    return dateTime.strftime("%Y/%m/%d %H:%M:%S") + (".%03d" % ms)


def unixTime(timestamp):
    dt = (ORIGIN-UNIXORIGIN)+datetime.timedelta(microseconds=1000*timestamp)
    return 86400.0*dt.days + dt.seconds + 1.e-6*dt.microseconds


class _MPLFigureEditor(Editor):
    scrollable = True

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.object.figureInteraction = FigureInteraction(self.object.plot2dFigure, self.object.lock)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self, parent):
        panel = wx.Panel(parent, -1, style=wx.CLIP_CHILDREN)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        mpl_control = FigureCanvas(panel, -1, self.value)
        sizer.Add(mpl_control, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.value.canvas.SetMinSize((10, 10))
        return panel


class MPLFigureEditor(BasicEditorFactory):
    klass = _MPLFigureEditor


class Plot2D(HasTraits):
    plot2dFigure = Instance(Figure, (), {"facecolor": "lightgrey", "edgecolor": "black", "linewidth": 2})
    figureInteraction = Instance(FigureInteraction)
    xScale = CStr('linear')
    yScale = CStr('linear')
    xLabel = CStr
    yLabel = CStr
    title = CStr
    sharex = Instance(matplotlib.axes.Axes)
    sharey = Instance(matplotlib.axes.Axes)
    traits_view = View(Item("plot2dFigure", editor=MPLFigureEditor(), show_label=False), width=700, height=600, resizable=True)
    lock = Instance(threading.RLock, ())
    autoscaleOnUpdate = CBool(False)

    def plotData(self, *a, **k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        share = {}
        if self.sharex:
            share['sharex'] = self.sharex
        if self.sharey:
            share['sharey'] = self.sharey
        self.axes = self.plot2dFigure.add_subplot(111, **share)
        handles = self.axes.plot(*a, **k)
        self.axes.grid(True)
        self.axes.set_xscale(self.xScale)
        self.axes.set_yscale(self.yScale)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        self.axes.set_title(self.title)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()
        return handles

    def plotTimeSeries(self, t, *a, **k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        self.tz = k.get("tz", pytz.timezone("UTC"))
        formatter = matplotlib.dates.DateFormatter('%H:%M:%S\n%Y/%m/%d', self.tz)
        if len(t) > 0:
            dt = datetime.datetime.fromtimestamp(t[0], tz=self.tz)
            t0 = matplotlib.dates.date2num(dt)
            tbase = t0 + (t-t[0])/(24.0*3600.0)
        else:
            tbase = []
        share = {}
        if self.sharex:
            share['sharex'] = self.sharex
        if self.sharey:
            share['sharey'] = self.sharey
        self.axes = self.plot2dFigure.add_subplot(111, **share)
        handles = self.axes.plot_date(tbase, *a, **k)
        self.axes.grid(True)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        self.axes.set_title(self.title)
        self.axes.xaxis.set_major_formatter(formatter)
        self.axes.xaxis.set_major_locator(MaxNLocator(8))
        labels = self.axes.get_xticklabels()
        for l in labels:
            l.set(rotation=0, fontsize=10)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()
        return handles

    def addText(self, *a, **k):
        self.lock.acquire()
        handle = self.axes.text(*a, **k)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()
        return handle

    def updateData(self, handle, newX, newY, linkedPlots=None):
        self.lock.acquire()
        handle.set_data(newX, newY)
        if self.autoscaleOnUpdate:
            self.autoscale()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()

    def updateTimeSeries(self, handle, newX, newY, linkedPlots=None):
        self.lock.acquire()
        t = newX
        if len(t) > 0:
            dt = datetime.datetime.fromtimestamp(t[0], tz=self.tz)
            t0 = matplotlib.dates.date2num(dt)
            tbase = t0 + (t-t[0])/(24.0*3600.0)
        else:
            tbase = []
        handle.set_data(tbase, newY)
        if self.autoscaleOnUpdate:
            self.autoscale()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()

    def redraw(self):
        self.lock.acquire()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()

    def autoscale(self):
        self.axes.relim()
        self.axes.autoscale_view()
        if self.figureInteraction:
            self.figureInteraction.autoscale[self.axes] = True


class XyViewerHandler(Handler):
    def init(self, info):
        info.object.parent.uiSet.add(info.ui)
        Handler.init(self, info)

    def close(self, info, is_ok):
        info.object.parent.uiSet.discard(info.ui)
        info.ui.dispose()


class XyViewer(HasTraits):
    plot = Instance(Plot2D, ())
    xArray = CArray
    yArray = CArray
    xMin = CFloat
    xMax = CFloat
    yMin = CFloat
    yMin = CFloat
    xScale = CStr('linear')
    yScale = CStr('linear')
    xLabel = CStr
    yLabel = CStr
    mode = CInt(1)  # 1 for line of best fit, 2 for Allan Std Dev
    parent = Instance(object)
    traits_view = View(Item("plot", style="custom", show_label=False), width=800, height=600,
                       resizable=True, handler=XyViewerHandler())

    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        self.dataHandle, self.fitHandle = self.plot.plotData([], [], '.', [], [], '-')
        self.plot.axes.callbacks.connect("xlim_changed", self.notify)
        self.plot.axes.callbacks.connect("ylim_changed", self.notify)
        self.xlim = None
        self.ylim = None
        self.xData = None
        self.yData = None
        self.poly = None

    def update(self):
        self.plot.updateData(self.dataHandle, self.xArray, self.yArray)
        self.plot.axes.set_xscale(self.xScale)
        self.plot.axes.set_yscale(self.yScale)
        self.plot.axes.set_xlim((self.xMin, self.xMax))
        self.plot.axes.set_ylim((self.yMin, self.yMax))
        self.plot.axes.set_xlabel(self.xLabel)
        self.plot.axes.set_ylabel(self.yLabel)
    
    def notify(self, ax):
        self.xLim = ax.get_xlim()
        self.yLim = ax.get_ylim()
        self.xData, self.yData = self.dataHandle.get_data()
        self.sel = (self.xData >= self.xLim[0]) & (self.xData <= self.xLim[1])
        boxsel = self.sel & (self.yData >= self.yLim[0]) & (self.yData <= self.yLim[1])
        if self.mode == 1 and any(boxsel):
            self.poly = polyfit(self.xData[boxsel], self.yData[boxsel], 1)
            self.plot.axes.set_title("Best fit line: y = %s * x + %s" % (self.poly[0], self.poly[1]))
            self.fitHandle.set_data(self.xLim, polyval(self.poly, self.xLim))
        elif self.mode == 2:
            y = self.yData[0]/sqrt(self.xData/self.xData[0])
            self.fitHandle.set_data(self.xData, y)


class DatViewer(HasTraits):
    refAxes = []
    plot = Instance(Plot2D, ())
    dataFile = CStr
    dataSetNameList = ListStr
    dataSetName = CStr
    varNameList = ListStr
    varName = CStr
    transform = Str(editor=TextEditor(enter_set=False, auto_set=False))
    commands = Button1
    autoscaleY = CBool
    showPoints = CBool
    mean = CFloat
    stdDev = CFloat
    peakToPeak = CFloat
    nAverage = CInt(1)
    doAverage = Button1
    parent = Instance(object)
    nLines = CInt(3)
    
    traits_view = View(
        Group(
            Item("plot", style="custom", show_label=False),
            Item("dataSetName", editor=EnumEditor(name="dataSetNameList")),
            Item("varName", editor=EnumEditor(name="varNameList")),
            Item("transform")
        ))

    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        self.dataHandles = self.plot.plotTimeSeries([], zeros((0, self.nLines)), '-', tz=k.get("tz", pytz.timezone("UTC")))
        self.ip = None
        self.plot.axes.callbacks.connect("xlim_changed", self.notify)
        self.xlim = None
        self.ylim = None
        self.xData = None
        self.yData = None
        self.transform = "lambda(x):x"

    def notify(self, ax):
        self.xLim = ax.get_xlim()
        self.xData = [h.get_xdata() for h in self.dataHandles]
        self.yData = [h.get_ydata() for h in self.dataHandles]
        if self.autoscaleY:
            ymin, ymax = None, None
            for xv, yv in zip(self.xData, self.yData):
                self.sel = (xv >= self.xLim[0]) & (xv <= self.xLim[1])
                if any(self.sel):
                    ymin = min(ymin, min(yv[self.sel])) if ymin is not None else min(yv[self.sel])
                    ymax = max(ymax, max(yv[self.sel])) if ymax is not None else max(yv[self.sel])
            if ymin is not None and ymax is not None:
                ax.set_ylim(ymin, ymax)

        self.yLim = ax.get_ylim()
        # For means and standard deviations, use the first time series only
        self.sel = (self.xData[0] >= self.xLim[0]) & (self.xData[0] <= self.xLim[1])
        boxsel = self.sel & (self.yData[0] >= self.yLim[0]) & (self.yData[0] <= self.yLim[1])
        #
        if self.showPoints:
            for h in self.dataHandles:
                h.set_marker('o')
                h.set_linestyle('None')
        else:
            for h in self.dataHandles:
                h.set_marker('None')
                h.set_linestyle('-')
        
        if any(boxsel):
            self.mean = oldSum(self.yData[0][boxsel])/sum(boxsel)
            self.stdDev = sqrt(oldSum((self.yData[0][boxsel]-self.mean)**2)/sum(boxsel))
            self.peakToPeak = ptp(self.yData[0][boxsel])
        if self.parent.listening:
            wx.CallAfter(self.parent.notify, self, self.xLim, self.yLim)

    def _dataFile_changed(self):
        # Figure out the tree of tables and arrays
        if self.ip is not None:
            self.ip.close()
            self.ip = None
        self.dataSetNameList = []
        self.dataSetName = ""
        self.varName = ""
        if self.dataFile:
            self.ip = openFile(self.dataFile)
            for n in self.ip.walkNodes("/"):
                if isinstance(n, Table):
                    self.dataSetNameList.append(n._v_pathname)
            if 1 == len(self.dataSetNameList):
                self.dataSetName = self.dataSetNameList[0]

    def _dataSetName_changed(self):
        if self.dataSetName:
            self.table = self.ip.getNode(self.dataSetName)
            self.varNameList = [""] + self.table.colnames
        else:
            self.varNameList = []
        self.varName = ""

    def _varName_changed(self):
        self.plot.autoscaleOnUpdate = not self.parent.xlimSet
        for h in self.dataHandles:
            self.plot.updateTimeSeries(h, [], [])
        try:
            if not self.varName:
                self.mean = 0.0
                self.stdDev = 0.0
                self.peakToPeak = 0.0
            else:
                try:
                    dateTime = self.table.col("DATE_TIME")
                except:
                    try:
                        dateTime = array([unixTime(int(t)) for t in self.table.col("timestamp")])
                    except:
                        dateTime = array([unixTime(int(t)) for t in self.table.col("time")])
                    
                values = self.table.col(self.varName)
                values = eval(self.transform)(values)
                p = argsort(dateTime)
                if values.ndim > 1:
                    for i in range(values.shape[1]):
                        self.plot.updateTimeSeries(self.dataHandles[i], dateTime[p], [v[i] for v in values[p]])
                else:
                    self.plot.updateTimeSeries(self.dataHandles[0], dateTime[p], values[p])
            self.autoscaleY = True
            self.notify(self.plot.axes)
        except Exception, e:
            d = wx.MessageDialog(None, "%s" % e, "Error while displaying", style=wx.OK | wx.ICON_ERROR)
            d.ShowModal()
        self.parent.xlimSet = True

    def _transform_changed(self):
        if self.varName:
            self._varName_changed()

    def _autoscaleY_changed(self):
        if self.autoscaleY:
            self.notify(self.plot.axes)

    def _showPoints_changed(self):
        self.notify(self.plot.axes)
        
    def _doAverage_fired(self):
        try:
            dateTime = self.table.col("DATE_TIME")
        except:
            try:
                dateTime = array([unixTime(int(t)) for t in self.table.col("timestamp")])
            except:
                dateTime = array([unixTime(int(t)) for t in self.table.col("time")])
            
        values = self.table.col(self.varName)
        values = eval(self.transform)(values)
        p = argsort(dateTime)
        fKernel = ones(self.nAverage, dtype=float)/self.nAverage
        fTime = lfilter(fKernel, [1], dateTime[p])[self.nAverage-1:]
        if values.ndim > 1:
            for i in range(values.shape[1]):
                fData = lfilter(fKernel, [1], asarray([v[i] for v in values[p]]))[self.nAverage-1:]
                self.plot.updateTimeSeries(self.dataHandles[i], fTime, fData)
        else:
            fData = lfilter(fKernel, [1], values[p])[self.nAverage-1:]
            self.plot.updateTimeSeries(self.dataHandles[0], fTime, fData)
        self.notify(self.plot.axes)
            
    def getYDataAndLimInWindow(self):
        return self.table.col(self.varName)


class Dat2h5(HasTraits):
    datFileName = CStr
    h5FileName = CStr
    
    def fixed_width(self, text, width):
        start = 0
        result = []
        while True:
            atom = text[start:start+width].strip()
            if not atom:
                return result
            result.append(atom)
            start += width

    def convert(self):
        fp, d, h5f = None, None, None
        try:
            fp = open(self.datFileName, "r")
            root, ext = os.path.splitext(self.datFileName)
            self.h5FileName = ".".join([root, "h5"])
            d = wx.ProgressDialog("Convert DAT file to H5 format", "Converting %s" % (os.path.split(self.datFileName)[-1],),
                                  style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
            h5f = openFile(self.h5FileName, "w")
            filters = Filters(complevel=1, fletcher32=True)
            headings = []
            table = None
            for i, line in enumerate(fp):
                atoms = line.split()
                if len(atoms) < 2:
                    break
                if not headings:
                    headings = [a.replace(" ", "_") for a in atoms]
                    colDict = {"DATE_TIME": Time64Col()}
                    for h in headings:
                        if h not in ["DATE", "TIME"]:
                            colDict[h] = Float32Col()
                    TableType = type("TableType", (IsDescription,), colDict)
                    table = h5f.createTable(h5f.root, "results", TableType, filters=filters)
                else:
                    minCol = 0
                    if headings[0] == "DATE" and headings[1] == "TIME":
                        minCol = 2
                        # atoms[0] is date, atoms[1] is time
                        dateTimeString = " ".join(atoms[0:2])
                        dp = dateTimeString.find(".")
                        if dp >= 0:
                            fracSec = float(dateTimeString[dp:])
                            dateTimeString = dateTimeString[:dp]
                        else:
                            fracSec = 0.0
                        try:
                            when = time.mktime(time.strptime(dateTimeString, "%m/%d/%y %H:%M:%S")) + fracSec
                        except:
                            when = time.mktime(time.strptime(dateTimeString, "%Y-%m-%d %H:%M:%S")) + fracSec
                    entry = table.row
                    for h, a in zip(headings, atoms)[minCol:]:
                        try:
                            entry[h] = float(a)
                            if h == "EPOCH_TIME":
                                when = float(a)
                        except:
                            entry[h] = NaN
                    entry["DATE_TIME"] = when
                    entry.append()
                if i % 100 == 0:
                    d.Pulse()
            table.flush()
            d.Update(100, newmsg="Done. Output is %s" % (os.path.split(self.h5FileName)[-1]))
        finally:
            if h5f is not None:
                h5f.close()
            if d is not None:
                d.Destroy()
            if fp is not None:
                fp.close()


class h52Dat(HasTraits):
    h5FileName = CStr
    datFileName = CStr

    def convert(self):
        d, ip, dat = None, None, None
        try:
            root, ext = os.path.splitext(self.h5FileName)
            self.datFileName = ".".join([root, "dat"])
            d = wx.ProgressDialog("Convert H5 file to DAT format", "Converting %s" % (os.path.split(self.h5FileName)[-1],),
                                  style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
            ip = openFile(self.h5FileName, "r")
            try:
                resultsTable = ip.root.results
            except:
                resultsTable = ip.root.results_0
            dataRows = resultsTable.read()
            colNames = resultsTable.colnames
            numCols = len(colNames)
            timeMode = "DATE_TIME"
            if "DATE_TIME" in colNames:
                dateTimeIndex = colNames.index("DATE_TIME")
                colNames.remove("DATE_TIME")
            elif "time" in colNames:
                dateTimeIndex = colNames.index("time")
                colNames.remove("time")
                timeMode = "time"
            else:
                dateTimeIndex = colNames.index("timestamp")
                colNames.remove("timestamp")
                timeMode = "timestamp"
                
            ip.close()
            headingFormat = "%-26s" * (numCols-1) + "\n"
            dataFormat = "%-26f" * (numCols-1) + "\n"
            headings = headingFormat % tuple(colNames)
            linesToBeWritten = ["%-26s%-26s" % ("DATE", "TIME") + headings]
            for i, row in enumerate(dataRows):
                if timeMode in ["timestamp", "time"]:
                    timestamp = unixTime(row[dateTimeIndex])
                else:
                    timestamp = row[dateTimeIndex]
                dateTimeField = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                fracSec = timestamp - int(timestamp)
                dateTimeField += (".%02d" % round(100*fracSec))
                dateTimeCols = "%-26s%-26s" % tuple(dateTimeField.split(" "))
                row = list(row)
                row.remove(row[dateTimeIndex])
                data = dateTimeCols + (dataFormat % tuple(row))
                linesToBeWritten.append(data)
                if i % 100 == 0:
                    d.Pulse()
            dat = open(self.datFileName, "w")
            dat.writelines(linesToBeWritten)
            dat.close()
            d.Update(100, newmsg="Done. Output is %s" % (os.path.split(self.datFileName)[-1]))
        finally:
            if dat is not None:
                dat.close()
            if d is not None:
                d.Destroy()
            if ip is not None:
                ip.close()


class Window(HasTraits):
    pass


class SeriesWindowHandler(Handler):
    def init(self, info):
        info.object.parent.uiSet.add(info.ui)
        Handler.init(self, info)

    def close(self, info, is_ok):
        info.object.parent.uiSet.discard(info.ui)
        info.ui.dispose()


class SeriesWindow(Window):
    dataFile = CStr
    viewers = List(DatViewer)
    traits_view = Instance(View)
    nViewers = CInt(3)
    width = CInt(1024)
    height = CInt(768)
    resizable = CBool(True)
    parent = Any()
    xlimSet = CBool(False)
    
    def __init__(self, *a, **k):
        Window.__init__(self, *a, **k)
        self.tz = k.get("tz", pytz.timezone("UTC"))
        for n in range(self.nViewers):
            self.viewers.append(DatViewer(parent=self, tz=self.tz))
        self.listening = True
        a = []
        self.cDict = {}
        w = 150
        for i, fr in enumerate(self.viewers):
            a.append(
                HGroup(
                    Item("plot", object="h%d" % i, style="custom", show_label=False, springy=True),
                    VGroup(
                        Item("dataSetName", object="h%d" % i, editor=EnumEditor(name="dataSetNameList"), width=w),
                        Item("varName", object="h%d" % i, editor=EnumEditor(name="varNameList"), width=w),
                        HGroup(Item("autoscaleY", object="h%d" % i), Item("showPoints", object="h%d" % i)),
                        Item("transform", object="h%d" % i, width=w),
                        Item("mean", object="h%d" % i, width=w),
                        Item("stdDev", object="h%d" % i, width=w),
                        Item("peakToPeak", object="h%d" % i, width=w),
                        HGroup(Item("nAverage", object="h%d" % i), Item("doAverage", object="h%d" % i, show_label=False))
                    )))
            self.cDict["h%d" % i] = fr

        tGroup = Group(*a, **dict(layout="split"))
        self.cDict["object"] = self
        self.traits_view = View(VGroup(tGroup),
                                buttons=NoButtons, title="Time Series Viewer",
                                width=800, height=600, resizable=True, handler=SeriesWindowHandler())

    def notify(self, child, xlim, ylim):
        self.listening = False
        for v in self.viewers:
            v.plot.axes.set_xlim(xlim)
            v.plot.redraw()
        self.listening = True

    def _dataFile_changed(self):
        for v in self.viewers:
            v.set(dataFile=self.dataFile)


class CorrelationWindowHandler(Handler):
    def init(self, info):
        info.object.parent.uiSet.add(info.ui)
        Handler.init(self, info)

    def close(self, info, is_ok):
        info.object.parent.uiSet.discard(info.ui)
        info.ui.dispose()


class CorrelationWindow(Window):
    dataFile = CStr
    viewers = List(DatViewer)
    traits_view = Instance(View)
    width = CInt(1024)
    height = CInt(768)
    resizable = CBool(True)
    parent = Instance(object)
    correlate = Button1
    xlimSet = CBool(False)
    nAverage = CInt(1)
    doAverage = Button1

    def __init__(self, *a, **k):
        Window.__init__(self, *a, **k)
        self.nViewers = 2
        self.tz = k.get("tz", pytz.timezone("UTC"))
        for n in range(self.nViewers):
            self.viewers.append(DatViewer(parent=self, tz=self.tz))
        self.listening = True
        a = []
        self.cDict = {}
        w = 150
        for i, fr in enumerate(self.viewers):
            a.append(
                HGroup(
                    Item("plot", object="h%d" % i, style="custom", show_label=False, springy=True),
                    VGroup(
                        Item("dataSetName", object="h%d" % i, editor=EnumEditor(name="dataSetNameList"), width=w),
                        Item("varName", object="h%d" % i, editor=EnumEditor(name="varNameList"), width=w),
                        HGroup(Item("autoscaleY", object="h%d" % i), Item("showPoints", object="h%d" % i)),
                        Item("transform", object="h%d" % i, width=w),
                        Item("mean", object="h%d" % i, width=w),
                        Item("stdDev", object="h%d" % i, width=w),
                        Item("peakToPeak", object="h%d" % i, width=w),
                    )))
            self.cDict["h%d" % i] = fr
        tGroup = Group(*a, **dict(layout="split"))
        self.cDict["object"] = self
        self.traits_view = View(VGroup(tGroup,
                                       HGroup(Item("nAverage"),
                                              Item("doAverage", show_label=False),
                                              Item('correlate', show_label=False, label='Show correlation', springy=True),
                                              )
                                       ),
                                buttons=NoButtons, title="Correlation Viewer",
                                width=800, height=600, resizable=True, handler=SeriesWindowHandler())

    def notify(self, child, xlim, ylim):
        self.listening = False
        for v in self.viewers:
            v.plot.axes.set_xlim(xlim)
            v.plot.redraw()
        self.listening = True

    def _dataFile_changed(self):
        for v in self.viewers:
            v.set(dataFile=self.dataFile)

    def _correlate_fired(self):
        viewer = XyViewer(parent=self.parent)
        xV = self.viewers[0]
        yV = self.viewers[1]
        try:
            if not (len(xV.yData[0][xV.sel]) > 0 and len(yV.yData[0][yV.sel]) > 0):
                raise ValueError
            viewer.set(xArray=xV.yData[0][xV.sel], yArray=yV.yData[0][yV.sel],
                       xLabel=xV.varName, yLabel=yV.varName,
                       xMin=xV.yLim[0], xMax=xV.yLim[1], yMin=yV.yLim[0], yMax=yV.yLim[1])
            viewer.update()
            viewer.trait_view().set(title=self.dataFile)
            viewer.edit_traits()
        except Exception, e:
            print "An exception occurred: %s\n" % e
            wx.MessageBox("No or incompatible data for correlation plot within window (check averaging)")
            raise

    def _doAverage_fired(self):
        for v in self.viewers:
            v.set(nAverage=self.nAverage)
        for v in self.viewers:
            v.set(doAverage=True)


class AllanWindowHandler(Handler):
    def init(self, info):
        info.object.parent.uiSet.add(info.ui)
        Handler.init(self, info)

    def close(self, info, is_ok):
        info.object.parent.uiSet.discard(info.ui)
        info.ui.dispose()


class AllanWindow(Window):
    dataFile = CStr
    viewers = List(DatViewer)
    traits_view = Instance(View)
    width = CInt(1024)
    height = CInt(768)
    resizable = CBool(True)
    parent = Instance(object)
    plotAllan = Button1
    xlimSet = CBool(False)

    def __init__(self, *a, **k):
        Window.__init__(self, *a, **k)
        self.nViewers = 1
        self.tz = k.get("tz", pytz.timezone("UTC"))
        for n in range(self.nViewers):
            self.viewers.append(DatViewer(parent=self, tz=self.tz))
        self.listening = True
        a = []
        self.cDict = {}
        w = 150
        for i, fr in enumerate(self.viewers):
            a.append(
                HGroup(
                    Item("plot", object="h%d" % i, style="custom", show_label=False, springy=True),
                    VGroup(
                        Item("dataSetName", object="h%d" % i, editor=EnumEditor(name="dataSetNameList"), width=w),
                        Item("varName", object="h%d" % i, editor=EnumEditor(name="varNameList"), width=w),
                        HGroup(Item("autoscaleY", object="h%d" % i), Item("showPoints", object="h%d" % i)),
                        Item("transform", object="h%d" % i, width=w),
                        Item("mean", object="h%d" % i, width=w),
                        Item("stdDev", object="h%d" % i, width=w),
                        Item("peakToPeak", object="h%d" % i, width=w),
                    )))
            self.cDict["h%d" % i] = fr
        tGroup = Group(*a, **dict(layout="split"))
        self.cDict["object"] = self
        self.traits_view = View(VGroup(tGroup,
                                       Item('plotAllan', show_label=False, label='Show Allan standard deviation')),
                                buttons=NoButtons, title="Allan Standard Deviation Viewer",
                                width=800, height=600, resizable=True, handler=SeriesWindowHandler())
        
    def notify(self, child, xlim, ylim):
        self.listening = False
        for v in self.viewers:
            v.plot.axes.set_xlim(xlim)
            v.plot.redraw()
        self.listening = True

    def _dataFile_changed(self):
        for v in self.viewers:
            v.set(dataFile=self.dataFile)

    def _plotAllan_fired(self):
        viewer = XyViewer(parent=self.parent, mode=2)
        xV = self.viewers[0]
        try:
            n = len(xV.yData[0][xV.sel])
            if not n > 0:
                raise ValueError
            # Find conversion from points to a time axis
            slope, offset = polyfit(arange(n), xV.xData[0][xV.sel], 1)
                
            npts = int(floor(log(n)/log(2)))
            av = AllanVar(int(npts))
            for y in xV.yData[0][xV.sel]:
                av.processDatum(y)
            v = av.getVariances()
            sdev = sqrt(asarray(v[1]))
            viewer.set(xArray=2**arange(npts)*slope*24*3600, yArray=sdev, xLabel='Time (s)', yLabel='Allan Std Dev',
                       xMin=1, xMax=2**npts, yMin=sdev.min(), yMax=sdev.max(), xScale='log', yScale='log')
            viewer.update()
            viewer.trait_view().set(title=self.dataFile)
            viewer.edit_traits()
        except Exception, e:
            print "An exception occurred: %s\n" % e
            wx.MessageBox("No data for Allan standard deviation within window")
            raise


class NotebookHandler(Handler):
    datDirName = CStr

    def onOpen(self, info):
        d = wx.FileDialog(None, "Open HDF5 file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            info.object.dataFile = d.GetPath()
            info.ui.title = "Viewing [" + info.object.dataFile + "]"
        d.Destroy()

    def onOpenZip(self, info):
        # first let the user choose the .zip archive
        dz = wx.FileDialog(None, "Open .zip HDF5 file archive", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="zip files (*.zip)|*.zip")
        if dz.ShowModal() == wx.ID_OK:
            zipname = dz.GetPath()

            if os.path.splitext(zipname)[1] == ".zip" and zipfile.is_zipfile(zipname):
                # use the .zip filename to initialize a .h5 output filename
                # path is same as the .zip archive
                fname = os.path.splitext(zipname)[0] + ".h5"

                # give the user a chance to change it and warn about overwrites
                fd = wx.FileDialog(None, "Output file", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR, defaultFile=fname, wildcard="h5 files (*.h5)|*.h5")
                if fd.ShowModal() == wx.ID_OK:
                    fname = fd.GetPath()
                    if not self.datDirName:
                        self.datDirName = os.path.split(fname)[0]
                    try:
                        op = openFile(fname, "w")
                    except:
                        wx.MessageBox("Cannot open %s. File may be in use." % fname)
                        fd.Destroy()
                        dz.Destroy()
                        return

                    self.datDirName = fname
                    progress = 0
                    allData = []

                    # Note: openFile is tables.file.openFile() which imports the .h5 data.
                    #       It cannot read the files directly from the archive, so we must
                    #       unpack them first.

                    # open zip archive
                    zipArchive = zipfile.ZipFile(zipname, 'r')
                    tmpDir = tempfile.gettempdir()

                    try:
                        zipfiles = zipArchive.namelist()
                        # enumerate files in the .zip archive
                        for zfname in zipfiles:

                            # look for .h5 files
                            if os.path.splitext(zfname)[1] == ".h5":
                                # create a modal progress dialog if not created yet
                                if not progress:
                                    pd = wx.ProgressDialog("Concatenating files", "%s" % os.path.split(zfname)[1], style=wx.PD_APP_MODAL)

                                # extract the .h5 file from the zip archive into the temp dir
                                zf = zipArchive.extract(zfname, tmpDir)

                                # not sure why we have to stick on a .h5 extension since
                                # we already checked for it but using same code as above...
                                ip = openFile(zf[:-3]+".h5", "r")
                                try:
                                    # append the data from this .h5 file
                                    allData.append(ip.root.results.read())
                                finally:
                                    # clean up
                                    ip.close()
                                    os.remove(zf)  # delete the extracted temp file

                                # update the progress dialog with this filename
                                pd.Pulse("%s" % os.path.split(zfname)[1])
                                progress += 1

                    finally:
                        # close the .zip archive
                        zipArchive.close()

                    try:
                        # check whether any .h5 data files were found and concatenated
                        if progress == 0:
                            wx.MessageBox("No .h5 files found!")
                            return

                        pd.Pulse("Writing output file")

                        # Concatenate everything together and sort by time of data
                        dtypes = array([dt.dtype for dt in allData])
                        u = array(len(dtypes)*[True])
                        filters = Filters(complevel=1, fletcher32=True)

                        # Concatenate by unique data type
                        j = 0
                        for i, t in enumerate(dtypes):
                            if u[i]:
                                match = (dtypes == t)
                                u[match] = False
                                data = concatenate([dm for dm, c in zip(allData, match) if c])
                                try:
                                    perm = argsort(data['DATE_TIME'])
                                except:
                                    perm = argsort(data['timestamp'])
                                data = data[perm]
                                table = op.createTable(op.root, "results_%d" % j, data, filters=filters)
                                j += 1
                                table.flush()

                        info.object.dataFile = fname
                        info.ui.title = "Viewing [" + info.object.dataFile + "]"
                        pd.Update(100, newmsg="Done. Close box to view results")
                    finally:
                        # close the output file
                        op.close()

                info.object.dataFile = fname
                info.ui.title = "Viewing [" + info.object.dataFile + "]"

                # destroy the file save dialog
                fd.Destroy()

            else:
                wx.MessageBox("%s is not a .zip archive!" % os.path.split(zipname)[1])

        # destroy the file open dialog
        dz.Destroy()

    def onConcatenate(self, info):
        fname = time.strftime("DatViewer_%Y%m%d_%H%M%S.h5", time.localtime())
        fd = wx.FileDialog(None, "Output file", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR, defaultFile=fname, wildcard="h5 files (*.h5)|*.h5")
        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            if not self.datDirName:
                self.datDirName = os.path.split(fname)[0]
            try:
                op = openFile(fname, "w")
            except:
                wx.MessageBox("Cannot open %s. File may be in use." % fname)
                return
            try:
                d = wx.DirDialog(None, "Select directory tree with individual .h5 and/or zipped .h5 files", style=wx.DD_DEFAULT_STYLE, defaultPath=self.datDirName)
                if d.ShowModal() == wx.ID_OK:
                    path = d.GetPath()
                    self.datDirName = path
                    progress = 0
                    allData = []

                    for what, name in walkTree(path, sortDir=sortByName, sortFiles=sortByName):
                        if what == "file" and os.path.splitext(name)[1] == ".h5" and os.path.splitext(name)[0].split(".")[-1] not in fname:
                            if not progress:
                                pd = wx.ProgressDialog("Concatenating files", "%s" % os.path.split(name)[1], style=wx.PD_APP_MODAL)
                            ip = openFile(name[:-3]+".h5", "r")
                            try:
                                allData.append(ip.root.results.read())
                            finally:
                                ip.close()

                            pd.Pulse("%s" % os.path.split(name)[1])
                            progress += 1

                        elif what == "file" and os.path.splitext(name)[1] == ".zip" and zipfile.is_zipfile(name):
                            # Note: openFile is tables.file.openFile() which imports the .h5 data.
                            #       It cannot read the files directly from the archive, so we must
                            #       unpack them first.

                            # open zip archive
                            zipArchive = zipfile.ZipFile(name, 'r')
                            tmpDir = tempfile.gettempdir()

                            try:
                                zipfiles = zipArchive.namelist()
                                # enumerate files in the .zip archive
                                for zfname in zipfiles:

                                    # look for .h5 files
                                    if os.path.splitext(zfname)[1] == ".h5":
                                        # create a modal progress dialog if not created yet
                                        if not progress:
                                            pd = wx.ProgressDialog("Concatenating files", "%s" % os.path.split(zfname)[1], style=wx.PD_APP_MODAL)

                                        # extract the .h5 file from the zip archive into the temp dir
                                        zf = zipArchive.extract(zfname, tmpDir)

                                        # not sure why we have to stick on a .h5 extension since
                                        # we already checked for it but using same code as above...
                                        ip = openFile(zf[:-3]+".h5", "r")
                                        try:
                                            # append the data from this .h5 file
                                            allData.append(ip.root.results.read())
                                        finally:
                                            # clean up
                                            ip.close()
                                            os.remove(zf)  # delete the extracted temp file

                                        # update the progress dialog with this filename
                                        pd.Pulse("%s" % os.path.split(zfname)[1])
                                        progress += 1

                            finally:
                                # close this .zip archive
                                zipArchive.close()

                    # check whether any .h5 data files were found and concatenated
                    if progress == 0:
                        wx.MessageBox("No .h5 files found!")
                        return

                    pd.Pulse("Writing output file")

                    # Concatenate everything together and sort by time of data
                    dtypes = array([dt.dtype for dt in allData])
                    u = array(len(dtypes)*[True])
                    filters = Filters(complevel=1, fletcher32=True)

                    # Concatenate by unique data type
                    j = 0
                    for i, t in enumerate(dtypes):
                        if u[i]:
                            match = (dtypes == t)
                            u[match] = False
                            data = concatenate([dm for dm, c in zip(allData, match) if c])
                            try:
                                perm = argsort(data['DATE_TIME'])
                            except:
                                perm = argsort(data['timestamp'])
                            data = data[perm]
                            table = op.createTable(op.root, "results_%d" % j, data, filters=filters)
                            j += 1
                            table.flush()

                    info.object.dataFile = fname
                    info.ui.title = "Viewing [" + info.object.dataFile + "]"
                    pd.Update(100, newmsg="Done. Close box to view results")
            finally:
                op.close()
        
    def onBatchConvertDatToH5(self, info):
        d = wx.DirDialog(None, "Open directory with .dat files", style=wx.DD_DEFAULT_STYLE)
        if d.ShowModal() == wx.ID_OK:
            path = d.GetPath()
            #progress = 0
            for what, name in walkTree(path, sortDir=sortByName, sortFiles=sortByName):
                if what == "file" and os.path.splitext(name)[1] == ".dat":
                    c = Dat2h5(datFileName=name)
                    try:
                        c.convert()
                    except Exception, e:
                        print "Error converting %s: %s" % (name, e)
        d.Destroy()

    def onBatchConvertH5ToDat(self, info):
        d = wx.DirDialog(None, "Open directory with .h5 files", style=wx.DD_DEFAULT_STYLE)
        if d.ShowModal() == wx.ID_OK:
            path = d.GetPath()
            #progress = 0
            for what, name in walkTree(path, sortDir=sortByName, sortFiles=sortByName):
                if what == "file" and os.path.splitext(name)[1] == ".h5":
                    c = h52Dat(h5FileName=name)
                    try:
                        c.convert()
                    except Exception, e:
                        print "Error converting %s: %s" % (name, e)
        d.Destroy()

    def onConvertDatToH5(self, info):
        d = wx.FileDialog(None, "Open DAT file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="dat files (*.dat)|*.dat")
        if d.ShowModal() == wx.ID_OK:
            c = Dat2h5(datFileName=d.GetPath())
            d.Destroy()
            try:
                c.convert()
                info.object.dataFile = c.h5FileName
                info.ui.title = "Viewing [" + info.object.dataFile + "]"
            except Exception, e:
                d = wx.MessageDialog(None, "%r" % e, "Error in conversion", style=wx.OK | wx.ICON_ERROR)
                d.ShowModal()
                info.ui.title = "HDF5 File Viewer"
        else:
            d.Destroy()

    def onConvertH5ToDat(self, info):
        d = wx.FileDialog(None, "Open H5 file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            c = h52Dat(h5FileName=d.GetPath())
            d.Destroy()
            try:
                c.convert()
            except Exception, e:
                d = wx.MessageDialog(None, "%r" % e, "Error in conversion", style=wx.OK | wx.ICON_ERROR)
                d.ShowModal()
        else:
            d.Destroy()
            
    def onSeries(self, info, nFrames):
        if not info.object.dataFile:
            wx.MessageBox("Please open or convert a file first")
            return
        window = SeriesWindow(nViewers=nFrames, tz=info.object.tz, parent=info.object)
        window.set(dataFile=info.object.dataFile)
        window.traits_view.set(title=info.object.dataFile)
        window.edit_traits(view=window.traits_view, context=window.cDict)

    def onSeries1(self, info):
        return self.onSeries(info, 1)

    def onSeries2(self, info):
        return self.onSeries(info, 2)
        
    def onSeries3(self, info):
        return self.onSeries(info, 3)

    def onCorrelation(self, info):
        if not info.object.dataFile:
            wx.MessageBox("Please open or convert a file first")
            return
        window = CorrelationWindow(tz=info.object.tz, parent=info.object)
        window.set(dataFile=info.object.dataFile)
        window.traits_view.set(title=info.object.dataFile)
        window.edit_traits(view=window.traits_view, context=window.cDict)
        
    def onAllanPlot(self, info):
        if not info.object.dataFile:
            wx.MessageBox("Please open or convert a file first")
            return
        window = AllanWindow(tz=info.object.tz, parent=info.object)
        window.set(dataFile=info.object.dataFile)
        window.traits_view.set(title=info.object.dataFile)
        window.edit_traits(view=window.traits_view, context=window.cDict)

    def onExit(self, info):
        self.close(info, True)
        sys.exit(0)

    def close(self, info, is_ok):
        for ui in info.object.uiSet:
            ui.dispose()
        info.ui.dispose()


class ViewNotebook(HasTraits):
    dataFile = CStr("")
    config = Instance(ConfigObj)
    tzString = CStr("UTC")

    def __init__(self, *a, **k):
        HasTraits.__init__(self, *a, **k)
        if self.config:
            if "Config" in self.config:
                config = self.config["Config"]
                self.tzString = config.get("tz", self.tzString)
        self.tz = pytz.timezone(self.tzString)
        self.uiSet = set()

        openAction = Action(name="Open H5...", action="onOpen")
        openZipAction = Action(name="Concatenate H5 ZIP archive...", action="onOpenZip")
        concatenateAction = Action(name="Concatenate H5...", action="onConcatenate")
        convertDatAction = Action(name="Convert DAT to H5...", action="onConvertDatToH5")
        convertH5Action = Action(name="Convert H5 to DAT...", action="onConvertH5ToDat")
        batchConvertDatAction = Action(name="BatchConvert DAT to H5...", action="onBatchConvertDatToH5")
        batchConvertH5Action = Action(name="BatchConvert H5 to DAT...", action="onBatchConvertH5ToDat")
        exitAction = Action(name="Exit", action="onExit")
        series1Action = Action(name="1 frame", action="onSeries1")
        series2Action = Action(name="2 frames", action="onSeries2")
        series3Action = Action(name="3 frames", action="onSeries3")
        xyViewAction = Action(name="Correlation Plot", action="onCorrelation")
        allanAction = Action(name="Allan Standard Deviation Plot", action="onAllanPlot")

        # Curiously, with separators in the menu the exit item needs to be
        # put in first so it ends up at the bottom of the menu.
        self.traits_view = View(Item("dataFile", style="readonly", show_label=False),
                                buttons=NoButtons, title="HDF5 File Viewer",
                                menubar=MenuBar(Menu(exitAction,
                                                     Separator(),
                                                     openAction,
                                                     openZipAction,
                                                     concatenateAction,
                                                     Separator(),
                                                     convertDatAction,
                                                     batchConvertDatAction,
                                                     convertH5Action,
                                                     batchConvertH5Action,
                                                     name='File'),
                                                Menu(Menu(series1Action, series2Action, series3Action,
                                                name="Time Series Plot"), xyViewAction, allanAction, name='New')),
                                handler=NotebookHandler(), width=800, resizable=True)

_DEFAULT_CONFIG_NAME = "DatViewer.ini"
HELP_STRING = """\
DatViewer.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different config file.  Default = "datViewer.ini"

View/analyze data in an HDF5 file
"""


def printUsage():
    print HELP_STRING


def handleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    #executeTest = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit(0)

    #Start with option defaults...
    configFile = _DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    return configFile

if __name__ == "__main__":
    configFile = handleCommandSwitches()
    config = ConfigObj(configFile)
    viewNotebook = ViewNotebook(config=config)
    viewNotebook.configure_traits(view=viewNotebook.traits_view)
