import wx
import matplotlib
from Host.MfgUtilities.FigureInteraction import FigureInteraction
import matplotlib.pyplot
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import *
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import sys
import threading

from configobj import ConfigObj
from cStringIO import StringIO
from numpy import *
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.wx.editor import Editor
from enthought.traits.ui.basic_editor_factory import BasicEditorFactory
from enthought.traits.ui.menu import *
from Host.autogen.interface import *

class _MPLFigureEditor(Editor):
    scrollable = True

    def init(self,parent):
        self.control = self._create_canvas(parent)
        self.object.figureInteraction = FigureInteraction(self.object.plot2dFigure,self.object.lock)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self,parent):
        panel = wx.Panel(parent,-1,style=wx.CLIP_CHILDREN)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)
        mpl_control = FigureCanvas(panel,-1,self.value)
        sizer.Add(mpl_control,1,wx.LEFT|wx.TOP|wx.GROW)
        self.value.canvas.SetMinSize((10,10))
        return panel

class MPLFigureEditor(BasicEditorFactory):
    klass = _MPLFigureEditor

class Plot2D(HasTraits):
    plot2dFigure = Instance(Figure,(),{"facecolor":"lightgrey","edgecolor":"black","linewidth":2})
    figureInteraction = Instance(FigureInteraction)
    xLabel = CStr
    yLabel = CStr
    title = CStr
    sharex = Instance(matplotlib.axes.Axes)
    sharey = Instance(matplotlib.axes.Axes)
    traits_view = View(Item("plot2dFigure",editor=MPLFigureEditor(),show_label=False),width=700,height=600,resizable=True)
    lock = Instance(threading.RLock,())

    def plotData(self,*a,**k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        share = {}
        if self.sharex: share['sharex'] = self.sharex
        if self.sharey: share['sharey'] = self.sharey
        self.axes = self.plot2dFigure.add_subplot(111,**share)
        handles = self.axes.plot(*a,**k)
        self.axes.grid(True)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        self.axes.set_title(self.title)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()
        return handles

    def plotTimeSeries(self,t,*a,**k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        self.tz = k.get("tz",pytz.timezone("UTC"))
        formatter = matplotlib.dates.DateFormatter('%H:%M:%S\n%Y/%m/%d',self.tz)
        if len(t)>0:
            dt = datetime.datetime.fromtimestamp(t[0],tz=self.tz)
            t0 = matplotlib.dates.date2num(dt)
            tbase = t0 + (t-t[0])/(24.0*3600.0)
        else:
            tbase = []
        share = {}
        if self.sharex: share['sharex'] = self.sharex
        if self.sharey: share['sharey'] = self.sharey
        self.axes = self.plot2dFigure.add_subplot(111,**share)
        handles = self.axes.plot_date(tbase,*a,**k)
        self.axes.grid(True)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        self.axes.set_title(self.title)
        self.axes.xaxis.set_major_formatter(formatter)
        self.axes.xaxis.set_major_locator( MaxNLocator(8) )
        labels = self.axes.get_xticklabels()
        for l in labels:
            l.set(rotation=0, fontsize=10)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()
        return handles

    def addText(self,*a,**k):
        self.lock.acquire()
        handle = self.axes.text(*a,**k)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()
        return handle

    def updateData(self,handle,newX,newY,linkedPlots=None):
        self.lock.acquire()
        handle.set_data(newX,newY)
        autoscale = True
        try:
            autoscale &= self.figureInteraction.autoscale.values()[0]
        except:
            pass
        if linkedPlots:
            for p in linkedPlots:
                try:
                    autoscale &= p.figureInteraction.autoscale.values()[0]
                except:
                    pass
        if autoscale:
            self.autoscale()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()

    def updateTimeSeries(self,handle,newX,newY,linkedPlots=None):
        self.lock.acquire()
        t = newX
        if len(t)>0:
            dt = datetime.datetime.fromtimestamp(t[0],tz=self.tz)
            t0 = matplotlib.dates.date2num(dt)
            tbase = t0 + (t-t[0])/(24.0*3600.0)
        else:
            tbase = []
        handle.set_data(tbase,newY)
        autoscale = True
        try:
            autoscale &= self.figureInteraction.autoscale.values()[0]
        except:
            pass
        if linkedPlots:
            for p in linkedPlots:
                try:
                    autoscale &= p.figureInteraction.autoscale.values()[0]
                except:
                    pass
        if autoscale:
            self.autoscale()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()

    def  redraw(self):
        self.lock.acquire()
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()
        self.lock.release()

    def autoscale(self):
        self.axes.relim()
        self.axes.autoscale_view()
        self.figureInteraction.autoscale[self.axes] = True

class Viewer(HasTraits):
    current = Instance(Plot2D,())
    original = Instance(Plot2D,())
    configFile = File(filter=["*.ini"])

    def __init__(self,*a,**k):
        HasTraits.__init__(self,*a,**k)

    def _configFile_fired(self):
        config = ConfigObj(self.configFile)
        current = config["VIRTUAL_CURRENT_1"]
        currentValues = array([float(current[k]) for k in current])
        original = config["VIRTUAL_ORIGINAL_1"]
        originalValues = array([float(original[k]) for k in original])
        self.current.plotData(currentValues)
        self.original.plotData(originalValues)

if __name__ == "__main__":
    viewer = Viewer()

    myView = View(
        Item("current",style="custom",show_label=False),
        Item("original",style="custom",show_label=False),
        Item("configFile"),
        width=800,height=800,resizable=True,buttons=NoButtons,title="Warm Box Calibration Viewer")
    viewer.configure_traits(view=myView)