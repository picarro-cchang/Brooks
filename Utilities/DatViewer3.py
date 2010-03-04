import wx
import matplotlib
import pytz
from FigureInteraction import FigureInteraction
import matplotlib.pyplot
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import *
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import datetime
import logging
import os
import time
import threading
import traceback
import sys

from cStringIO import StringIO
from numpy import *
from tables import *
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.wx.editor import Editor
from enthought.traits.ui.basic_editor_factory import BasicEditorFactory
from enthought.traits.ui.menu import *
from traceback import format_exc
from configobj import ConfigObj
import datetime

ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
UNIXORIGIN = datetime.datetime(1970,1,1,0,0,0,0)

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
        if self.figureInteraction:
            self.figureInteraction.autoscale[self.axes] = True


class XyViewerHandler(Handler):
    def init(self,info):
        info.object.parent.uiSet.add(info.ui)
        Handler.init(self,info)
    def close(self,info,is_ok):
        info.object.parent.uiSet.discard(info.ui)
        info.ui.dispose()

class XyViewer(HasTraits):
    plot = Instance(Plot2D,())
    xArray = CArray
    yArray = CArray
    xMin = CFloat
    xMax = CFloat
    yMin = CFloat
    yMin = CFloat
    xLabel = CStr
    yLabel = CStr
    parent = Instance(object)
    traits_view = View(Item("plot",style="custom",show_label=False),width=800,height=600,
                        resizable=True,handler=XyViewerHandler())

    def __init__(self,*a,**k):
        HasTraits.__init__(self,*a,**k)
        self.dataHandle, self.fitHandle = self.plot.plotData([],[],'.',[],[],'-')
        self.plot.axes.callbacks.connect("xlim_changed",self.notify)
        self.plot.axes.callbacks.connect("ylim_changed",self.notify)
        self.xlim = None
        self.ylim = None
        self.xData = None
        self.yData = None
        self.poly = None

    def update(self):
        self.plot.updateData(self.dataHandle,self.xArray,self.yArray)
        self.plot.axes.set_xlim((self.xMin,self.xMax))
        self.plot.axes.set_ylim((self.yMin,self.yMax))
        self.plot.axes.set_xlabel(self.xLabel)
        self.plot.axes.set_ylabel(self.yLabel)
    
    def notify(self,ax):
        self.xLim = ax.get_xlim()
        self.yLim = ax.get_ylim()
        self.xData, self.yData = self.dataHandle.get_data()
        self.sel = (self.xData>=self.xLim[0]) & (self.xData<=self.xLim[1])
        boxsel = self.sel & (self.yData>=self.yLim[0]) & (self.yData<=self.yLim[1])
        if any(boxsel):
            self.poly = polyfit(self.xData[boxsel],self.yData[boxsel],1)
            self.plot.axes.set_title("Best fit line: y = %s * x + %s" % (self.poly[0],self.poly[1]))
            self.fitHandle.set_data(self.xLim,polyval(self.poly,self.xLim))
            
class DatViewer(HasTraits):
    refAxes = []
    plot = Instance(Plot2D,())
    dataFile = CStr
    dataSetNameList = ListStr
    dataSetName = CStr
    varNameList = ListStr
    varName = CStr
    commands = Button
    autoscaleY = CBool
    mean = CFloat
    stdDev = CFloat
    parent = Instance(object)

    traits_view = View(
        Group(
            Item("plot",style="custom",show_label=False),
            Item("dataSetName",editor=EnumEditor(name="dataSetNameList")),
            Item("varName",editor=EnumEditor(name="varNameList"))
        ))

    def __init__(self,*a,**k):
        HasTraits.__init__(self,*a,**k)
        self.dataHandle = self.plot.plotTimeSeries([],[],'-',tz=k.get("tz",pytz.timezone("UTC")))[0]
        self.ip = None
        self.plot.axes.callbacks.connect("xlim_changed",self.notify)
        self.xlim = None
        self.ylim = None
        self.xData = None
        self.yData = None

    def notify(self,ax):
        self.xLim = ax.get_xlim()
        self.xData, self.yData = self.dataHandle.get_data()
        if self.autoscaleY:
            self.sel = (self.xData>=self.xLim[0]) & (self.xData<=self.xLim[1])
            if any(self.sel):
                ax.set_ylim((min(self.yData[self.sel]),max(self.yData[self.sel])))
        self.yLim = ax.get_ylim()
        self.sel = (self.xData>=self.xLim[0]) & (self.xData<=self.xLim[1])
        boxsel = self.sel & (self.yData>=self.yLim[0]) & (self.yData<=self.yLim[1])
        if any(boxsel):
            self.mean = mean(self.yData[boxsel])
            self.stdDev = std(self.yData[boxsel])
        if self.parent.listening:
            wx.CallAfter(self.parent.notify,self,self.xLim,self.yLim)

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
                if isinstance(n,Table):
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
        try:
            if not self.varName:
                self.plot.updateTimeSeries(self.dataHandle,[],[])
                self.mean = 0.0
                self.stdDev = 0.0
            else:
                try:
                    dateTime = self.table.col("DATE_TIME")
                except:
                    dateTime = array([unixTime(int(t)) for t in self.table.col("timestamp")])
                    
                values = self.table.col(self.varName)
                self.plot.updateTimeSeries(self.dataHandle,dateTime,values)
        except Exception, e:
            d = wx.MessageDialog(None,"%s" % e,"Error while displaying", style=wx.OK|wx.ICON_ERROR)
            d.ShowModal()
        
    def  _autoscaleY_changed(self):
        if self.autoscaleY:
            self.notify(self.plot.axes)

    def getYDataAndLimInWindow(self):
        return self.table.col(self.varName)

class Dat2h5(HasTraits):
    datFileName = CStr
    h5FileName = CStr
    
    def fixed_width(self,text,width):
        start = 0
        result = []
        while True:
            atom = text[start:start+width].strip()
            if not atom: return result
            result.append(atom)
            start += width

    def convert(self):
        fp, d, h5f = None, None, None
        try:
            fp = open(self.datFileName,"r")
            root,ext = os.path.splitext(self.datFileName)
            self.h5FileName = ".".join([root,"h5"])
            d = wx.ProgressDialog("Convert DAT file to H5 format","Converting %s" % (os.path.split(self.datFileName)[-1],), 
                style=wx.PD_APP_MODAL)
            h5f = openFile(self.h5FileName,"w")
            filters = Filters(complevel=1,fletcher32=True)
            headings = []
            table = None
            for i,line in enumerate(fp):
                atoms = self.fixed_width(line,26)
                if not headings:
                    headings = [a.replace(" ","_") for a in atoms]
                    colDict = { "DATE_TIME":Time64Col() }
                    for h in headings:
                        if h not in ["DATE","TIME"]:
                            colDict[h]=Float32Col()
                    TableType = type("TableType",(IsDescription,),colDict)
                    table = h5f.createTable(h5f.root,"results",TableType,filters=filters)
                else:
                    # atoms[0] is date, atoms[1] is time
                    dateTimeString = " ".join(atoms[0:2])
                    dp = dateTimeString.find(".")
                    if dp >= 0:
                        fracSec = float(dateTimeString[dp:])
                        dateTimeString = dateTimeString[:dp]
                    else:
                        fracSec = 0.0
                    try:
                        when = time.mktime(time.strptime(dateTimeString,"%m/%d/%y %H:%M:%S")) + fracSec
                    except:
                        when = time.mktime(time.strptime(dateTimeString,"%Y-%m-%d %H:%M:%S")) + fracSec
                    entry = table.row
                    entry["DATE_TIME"] = when
                    for h,a in zip(headings,atoms)[2:]:
                        try:
                            entry[h] = float(a)
                        except:
                            entry[h] = NaN
                    entry.append()
                if i%100 == 0: d.Pulse()
            table.flush()
            d.Update(100,newmsg = "Done. Output is %s" % (os.path.split(self.h5FileName)[-1]))
        finally:
            if h5f is not None: h5f.close()
            if d is not None: d.Destroy()
            if fp is not None: fp.close()
        
class Window(HasTraits):
    pass

class SeriesWindowHandler(Handler):
    def init(self,info):
        info.object.parent.uiSet.add(info.ui)
        Handler.init(self,info)
    def close(self,info,is_ok):
        info.object.parent.uiSet.discard(info.ui)
        info.ui.dispose()
    
class SeriesWindow(Window):
    dataFile = CStr
    viewers = List(DatViewer)
    traits_view = Instance(View)
    nViewers = CInt(3)
    width = CInt(1024)
    height  = CInt(768)
    resizable = CBool(True)
    parent = Any()

    def __init__(self,*a,**k):
        Window.__init__(self,*a,**k)
        self.tz = k.get("tz",pytz.timezone("UTC"))
        for n in range(self.nViewers):
            self.viewers.append(DatViewer(parent=self,tz=self.tz))
        self.listening = True
        a = []
        self.cDict = {}
        w = 150
        for i,fr in enumerate(self.viewers):
            a.append(HGroup(
                        Item("plot",object="h%d"%i,style="custom",show_label=False,springy=True),
                        VGroup(
                            Item("dataSetName",object="h%d"%i,editor=EnumEditor(name="dataSetNameList"),width=w),
                            Item("varName",object="h%d"%i,editor=EnumEditor(name="varNameList"),width=w),
                            Item("autoscaleY",object="h%d"%i,width=w),
                            Item("mean",object="h%d"%i,width=w),
                            Item("stdDev",object="h%d"%i))
                    ))
            self.cDict["h%d"%i] = fr
        tGroup = Group(*a,**dict(layout="split"))
        self.cDict["object"] = self
        self.traits_view = View(VGroup(tGroup),
                                    buttons=NoButtons,title="Time Series Viewer",
                                    width=800,height=600,resizable=True,handler=SeriesWindowHandler())
        
    def  notify(self,child,xlim,ylim):
        self.listening = False
        for v in self.viewers:
            v.plot.axes.set_xlim(xlim)
            v.plot.redraw()
        self.listening = True

    def _dataFile_changed(self):
        for v in self.viewers:
            v.set(dataFile = self.dataFile)
            
class CorrelationWindowHandler(Handler):
    def init(self,info):
        info.object.parent.uiSet.add(info.ui)
        Handler.init(self,info)
    def close(self,info,is_ok):
        info.object.parent.uiSet.discard(info.ui)
        info.ui.dispose()

class CorrelationWindow(Window):
    dataFile = CStr
    viewers = List(DatViewer)
    traits_view = Instance(View)
    width = CInt(1024)
    height  = CInt(768)
    resizable = CBool(True)
    parent = Instance(object)
    correlate = Button

    def __init__(self,*a,**k):
        Window.__init__(self,*a,**k)
        self.nViewers = 2
        self.tz = k.get("tz",pytz.timezone("UTC"))
        for n in range(self.nViewers):
            self.viewers.append(DatViewer(parent=self,tz=self.tz))
        self.listening = True
        a = []
        self.cDict = {}
        w = 150
        for i,fr in enumerate(self.viewers):
            a.append(HGroup(
                        Item("plot",object="h%d"%i,style="custom",show_label=False,springy=True),
                        VGroup(
                            Item("dataSetName",object="h%d"%i,editor=EnumEditor(name="dataSetNameList"),width=w),
                            Item("varName",object="h%d"%i,editor=EnumEditor(name="varNameList"),width=w),
                            Item("autoscaleY",object="h%d"%i,width=w),
                            Item("mean",object="h%d"%i,width=w),
                            Item("stdDev",object="h%d"%i))
                    ))
            self.cDict["h%d"%i] = fr
        tGroup = Group(*a,**dict(layout="split"))
        self.cDict["object"] = self
        self.traits_view = View(VGroup(tGroup,
                                       Item('correlate',show_label=False,label='Show correlation')),
                                buttons=NoButtons,title="Correlation Viewer",
                                width=800,height=600,resizable=True,handler=SeriesWindowHandler())
        
    def  notify(self,child,xlim,ylim):
        self.listening = False
        for v in self.viewers:
            v.plot.axes.set_xlim(xlim)
            v.plot.redraw()
        self.listening = True

    def _dataFile_changed(self):
        for v in self.viewers:
            v.set(dataFile = self.dataFile)

    def _correlate_fired(self):
        viewer = XyViewer(parent=self.parent)
        xV = self.viewers[0]
        yV = self.viewers[1]
        try:
            if not (len(xV.yData[xV.sel])>0 and len(yV.yData[yV.sel])>0):
                raise ValueError
            viewer.set(xArray=xV.yData[xV.sel],yArray=yV.yData[yV.sel],
                       xLabel=xV.varName,yLabel=yV.varName,
                       xMin=xV.yLim[0],xMax=xV.yLim[1],yMin=yV.yLim[0],yMax=yV.yLim[1])
            viewer.update()
            viewer.trait_view().set(title=self.dataFile)
            viewer.edit_traits()
        except Exception,e:
            wx.MessageBox("No data for correlation plot within window" )
            raise
            return
        
    
class NotebookHandler(Handler):
    def onOpen(self,info):
        d = wx.FileDialog(None,"Open HDF5 file",style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            info.object.dataFile = d.GetPath()
            info.ui.title = "Viewing [" + info.object.dataFile + "]"
        d.Destroy()
        
    def onConvert(self,info):
        d = wx.FileDialog(None,"Open DAT file",style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,wildcard="dat files (*.dat)|*.dat")
        if d.ShowModal() == wx.ID_OK:
            c = Dat2h5(datFileName = d.GetPath())
            d.Destroy()
            try:
                c.convert()
                info.object.dataFile = c.h5FileName
                info.ui.title = "Viewing [" + info.object.dataFile + "]"
            except Exception, e:
                d = wx.MessageDialog(None,"%s" % e,"Error in conversion", style=wx.OK|wx.ICON_ERROR)
                d.ShowModal()
                info.ui.title = "HDF5 File Viewer"
        else:
            d.Destroy()
    
    def onSeries(self,info,nFrames):
        if not info.object.dataFile:
            wx.MessageBox("Please open or convert a file first")
            return
        window = SeriesWindow(nViewers=nFrames,tz=info.object.tz,parent=info.object)
        window.set(dataFile=info.object.dataFile)
        window.traits_view.set(title=info.object.dataFile)
        window.edit_traits(view=window.traits_view,context=window.cDict)

    def onSeries1(self,info):
        return self.onSeries(info,1)

    def onSeries2(self,info):
        return self.onSeries(info,2)
        
    def onSeries3(self,info):
        return self.onSeries(info,3)
    
    def onCorrelation(self,info):
        if not info.object.dataFile:
            wx.MessageBox("Please open or convert a file first")
            return
        window = CorrelationWindow(tz=info.object.tz,parent=info.object)
        window.set(dataFile=info.object.dataFile)
        window.traits_view.set(title=info.object.dataFile)
        window.edit_traits(view=window.traits_view,context=window.cDict)

    def onExit(self,info):
        self.close(info,True)
        
    def close(self,info,is_ok):
        for ui in info.object.uiSet:
            ui.dispose()
        info.ui.dispose()
    
class ViewNotebook(HasTraits):
    dataFile = CStr("")
    config = Instance(ConfigObj)
    tzString = CStr("UTC")
    
    def  __init__(self,*a,**k):
        HasTraits.__init__(self,*a,**k)
        if self.config:
            if "Config" in self.config:
                config = self.config["Config"]
                self.tzString = config.get("tz",self.tzString)
        self.tz = pytz.timezone(self.tzString)
        self.uiSet = set()

        openAction = Action(name="Open...",action="onOpen")
        convertAction = Action(name="Convert...",action="onConvert")
        exitAction = Action(name="Exit",action="onExit")
        series1Action = Action(name="1 frame",action="onSeries1")
        series2Action = Action(name="2 frames",action="onSeries2")
        series3Action = Action(name="3 frames",action="onSeries3")
        xyViewAction = Action(name="Correlation Plot",action="onCorrelation")
        self.traits_view = View(Item("dataFile",style="readonly",show_label=False),
                                    buttons=NoButtons,title="HDF5 File Viewer",
                                    menubar=MenuBar(Menu(openAction,convertAction,exitAction,name='File'),
                                                    Menu(Menu(series1Action,series2Action,series3Action,
                                                    name="Time Series Plot"),xyViewAction,name='New')),
                                    handler=NotebookHandler(),width=800,resizable=True)

_DEFAULT_CONFIG_NAME = "DatViewer.ini"
HELP_STRING = \
"""\
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

    executeTest = False
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

