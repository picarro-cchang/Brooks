import wx
import matplotlib
from Host.MfgUtilities.FigureInteraction import FigureInteraction
import matplotlib.pyplot
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import *
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import os
import sys
import time
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

def sortByName(top,nameList):
    nameList.sort()
    return nameList

def sortByMtime(top,nameList):
    """Sort a list of files by modification time"""
    # Decorate with the modification time of the file for sorting
    fileList = [(os.path.getmtime(os.path.join(top,name)),name) for name in nameList]
    fileList.sort()
    return [name for t,name in fileList]

def walkTree(top,onError=None,sortDir=None,sortFiles=None):
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
        fullName = os.path.join(top,name)
        if not os.path.islink(fullName):
            if os.path.isdir(fullName):
                dirs.append(name)
            else:
                nondirs.append(name)
    # Sort the directories and nondirectories (in-place)
    if sortDir is not None:
        dirs = sortDir(top,dirs)
    if sortFiles is not None:
        nondirs = sortFiles(top,nondirs)
    # Recursively call walkTree on directories
    for dir in dirs:
        for x in walkTree(os.path.join(top,dir),onError,sortDir,sortFiles):
            yield x
    # Yield up files
    for file in nondirs:
        yield 'file', os.path.join(top,file)
    # Yield up the current directory
    yield 'dir', top

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

class ContourfPlot(HasTraits):
    plot2dFigure  = Instance(Figure,(),{"facecolor":"lightgrey","edgecolor":"black","linewidth":2})
    axes = Instance(matplotlib.axes.Axes)
    xMinVal = CFloat
    xMaxVal = CFloat
    yMinVal = CFloat
    yMaxVal = CFloat
    xLabel = CStr
    yLabel = CStr
    title = CStr
    replot = Button
    traits_view = View(Item("plot2dFigure",editor=MPLFigureEditor(),show_label=False),width=700,height=600,resizable=True)
    lock = Instance(threading.RLock,())

    def scaleAxes(self):
        xAuto = self.xMinVal == self.xMaxVal
        yAuto = self.yMinVal == self.yMaxVal
        self.axes.autoscale_view(xAuto,yAuto)
        if not xAuto: self.axes.set_xlim(xmin=self.xMinVal,xmax=self.xMaxVal)
        if not yAuto: self.axes.set_ylim(ymin=self.yMinVal,ymax=self.yMaxVal)
        self.axes.set_xlabel(self.xLabel)
        self.axes.set_ylabel(self.yLabel)
        self.axes.set_title(self.title)
        if self.plot2dFigure.canvas and not self.figureInteraction.isActive():
            self.plot2dFigure.canvas.draw()

    def contourData(self,*a,**k):
        self.lock.acquire()
        self.plot2dFigure.clf()
        self.axes = self.plot2dFigure.add_subplot(111)
        pl = self.axes.contourf(*a,**k)
        self.plot2dFigure.colorbar(pl,fraction=0.05)
        self.scaleAxes()
        self.lock.release()
        return pl

class WarmBoxCalExplorer(HasTraits):
    current = Instance(Plot2D,())
    virtualLaserNumber = CInt(1)
    configFile = File(filter=["*.ini"])
    corrSurf = Instance(ContourfPlot,(),dict(title="Correction Surface"))
    calDirectory = Directory()

    def __init__(self,*a,**k):
        HasTraits.__init__(self,*a,**k)

    def _configFile_fired(self):
        config = ConfigObj(self.configFile)
        current = config["VIRTUAL_CURRENT_1"]
        currentValues = array([float(current[k]) for k in current])
        original = config["VIRTUAL_ORIGINAL_1"]
        originalValues = array([float(original[k]) for k in original])
        self.current.plotData(currentValues)
        x = linspace(-3,3,31)
        y = linspace(-4,4,41)
        xx, yy = meshgrid(x,y)
        zz = exp(-0.5*(xx**2 + yy**2))
        self.corrSurf.contourData(x,y,zz)
        # self.original.plotData(originalValues)

    def _calDirectory_fired(self):
        currentValues = []
        originalValues = []
        when = []
        progress = 0
        for what,name in walkTree(self.calDirectory,sortDir=sortByName,sortFiles=sortByName):
            if what == "file" and os.path.splitext(name)[1]==".ini":
                if not progress:
                    d = wx.ProgressDialog("Reading calibration data","%s" % os.path.split(name)[1],style=wx.PD_APP_MODAL)
                when.append(time.mktime(time.strptime(os.path.split(name)[1][-19:-4],"%Y%m%d_%H%M%S")))
                config = ConfigObj(name)
                current = config["VIRTUAL_CURRENT_%d" % self.virtualLaserNumber]
                currentValues.append(array([float(current[k]) for k in current]))
                original = config["VIRTUAL_ORIGINAL_%d" % self.virtualLaserNumber]
                originalValues.append(array([float(original[k]) for k in original]))
            d.Pulse("%s" % os.path.split(name)[1])
            progress += 1
        currentValues = array(currentValues)
        originalValues = array(originalValues)
        d.Update(100,newmsg = "Done. Close box to view results")
        m,n = currentValues.shape
        self.corrSurf.contourData(arange(n),when,currentValues-originalValues)


if __name__ == "__main__":
    warmBoxCalExplorer = WarmBoxCalExplorer()

    myView = View(
        Item("current",style="custom",show_label=False),
        Item("corrSurf",style="custom",show_label=False),
        Item("virtualLaserNumber"),
        Item("calDirectory"),
        width=800,height=800,resizable=True,buttons=NoButtons,title="Warm Box Calibration Viewer")
    warmBoxCalExplorer.configure_traits(view=myView)