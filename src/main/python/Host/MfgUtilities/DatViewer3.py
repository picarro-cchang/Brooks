import wx
import matplotlib
import pytz
from Host.MfgUtilities.FigureInteraction import FigureInteraction
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
    autoscaleOnUpdate = CBool(False)

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
        if self.autoscaleOnUpdate:
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
        if self.autoscaleOnUpdate:
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
    showPoints = CBool
    mean = CFloat
    stdDev = CFloat
    parent = Instance(object)
    nLines = CInt(3)

    traits_view = View(
        Group(
            Item("plot",style="custom",show_label=False),
            Item("dataSetName",editor=EnumEditor(name="dataSetNameList")),
            Item("varName",editor=EnumEditor(name="varNameList"))
        ))

    def __init__(self,*a,**k):
        HasTraits.__init__(self,*a,**k)
        self.dataHandles = self.plot.plotTimeSeries([],zeros((0,self.nLines)),'-',tz=k.get("tz",pytz.timezone("UTC")))
        self.ip = None
        self.plot.axes.callbacks.connect("xlim_changed",self.notify)
        self.xlim = None
        self.ylim = None
        self.xData = None
        self.yData = None

    def notify(self,ax):
        self.xLim = ax.get_xlim()
        self.xData = [h.get_xdata() for h in self.dataHandles]
        self.yData = [h.get_ydata() for h in self.dataHandles]
        if self.autoscaleY:
            ymin,ymax = None,None
            for xv,yv in zip(self.xData,self.yData):
                self.sel = (xv>=self.xLim[0]) & (xv<=self.xLim[1])
                if any(self.sel):
                    ymin = min(ymin,min(yv[self.sel])) if ymin!=None else min(yv[self.sel])
                    ymax = max(ymax,max(yv[self.sel])) if ymax!=None else max(yv[self.sel])
            if ymin!=None and ymax!=None:
                ax.set_ylim(ymin,ymax)
        self.yLim = ax.get_ylim()
        # For means and standard deviations, use the first time series only
        self.sel = (self.xData[0]>=self.xLim[0]) & (self.xData[0]<=self.xLim[1])
        boxsel = self.sel & (self.yData[0]>=self.yLim[0]) & (self.yData[0]<=self.yLim[1])
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
            self.mean = mean(self.yData[0][boxsel])
            self.stdDev = std(self.yData[0][boxsel])
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
        self.plot.autoscaleOnUpdate = not self.parent.xlimSet
        for h in self.dataHandles:
            self.plot.updateTimeSeries(h,[],[])
        try:
            if not self.varName:
                self.mean = 0.0
                self.stdDev = 0.0
            else:
                try:
                    dateTime = self.table.col("DATE_TIME")
                except:
                    try:
                        dateTime = array([unixTime(int(t)) for t in self.table.col("timestamp")])
                    except:
                        dateTime = array([unixTime(int(t)) for t in self.table.col("time")])

                values = self.table.col(self.varName)
                p = argsort(dateTime)
                if values.ndim > 1:
                    for i in range(values.shape[1]):
                        self.plot.updateTimeSeries(self.dataHandles[i],dateTime[p],[v[i] for v in values[p]])
                else:
                    self.plot.updateTimeSeries(self.dataHandles[0],dateTime[p],values[p])
            self.autoscaleY = True
            self.notify(self.plot.axes)
        except Exception, e:
            d = wx.MessageDialog(None,"%s" % e,"Error while displaying", style=wx.OK|wx.ICON_ERROR)
            d.ShowModal()
        self.parent.xlimSet = True

    def  _autoscaleY_changed(self):
        if self.autoscaleY:
            self.notify(self.plot.axes)

    def  _showPoints_changed(self):
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
                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
            h5f = openFile(self.h5FileName,"w")
            filters = Filters(complevel=1,fletcher32=True)
            headings = []
            table = None
            for i,line in enumerate(fp):
                atoms = self.fixed_width(line,26)
                if len(atoms) < 2: break
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
    xlimSet = CBool(False)

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
                            HGroup(Item("autoscaleY",object="h%d"%i),Item("showPoints",object="h%d"%i)),
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
    xlimSet = CBool(False)

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
            if not (len(xV.yData[0][xV.sel])>0 and len(yV.yData[0][yV.sel])>0):
                raise ValueError
            viewer.set(xArray=xV.yData[0][xV.sel],yArray=yV.yData[0][yV.sel],
                       xLabel=xV.varName,yLabel=yV.varName,
                       xMin=xV.yLim[0],xMax=xV.yLim[1],yMin=yV.yLim[0],yMax=yV.yLim[1])
            viewer.update()
            viewer.trait_view().set(title=self.dataFile)
            viewer.edit_traits()
        except Exception,e:
            wx.MessageBox("No data for correlation plot within window" )
            raise

class NotebookHandler(Handler):
    datDirName = CStr
    def onOpen(self,info):
        d = wx.FileDialog(None,"Open HDF5 file",style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,wildcard="h5 files (*.h5)|*.h5")
        if d.ShowModal() == wx.ID_OK:
            info.object.dataFile = d.GetPath()
            info.ui.title = "Viewing [" + info.object.dataFile + "]"
        d.Destroy()

    def onConcatenate(self,info):
        fname = time.strftime("DatViewer_%Y%m%d_%H%M%S.h5",time.localtime())
        fd = wx.FileDialog(None,"Output file",style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR,defaultFile=fname,wildcard="h5 files (*.h5)|*.h5")
        if fd.ShowModal() == wx.ID_OK:
            fname = fd.GetPath()
            if not self.datDirName:
                self.datDirName = os.path.split(fname)[0]
            try:
                op = openFile(fname,"w")
            except:
                wx.MessageBox("Cannot open %s. File may be in use." % fname)
                return
            try:
                d = wx.DirDialog(None,"Select directory tree with individual .h5 files",style=wx.DD_DEFAULT_STYLE,defaultPath=self.datDirName)
                if d.ShowModal() == wx.ID_OK:
                    path = d.GetPath()
                    self.datDirName = path
                    progress = 0
                    allData = []
                    for what,name in walkTree(path,sortDir=sortByName,sortFiles=sortByName):
                        if what == "file" and os.path.splitext(name)[1]==".h5":
                            if not progress:
                                pd = wx.ProgressDialog("Concatenating files","%s" % os.path.split(name)[1],style=wx.PD_APP_MODAL)
                            ip = openFile(name[:-3]+".h5","r")
                            try:
                                allData.append(ip.root.results.read())
                            finally:
                                ip.close()
                            pd.Pulse("%s" % os.path.split(name)[1])
                            progress += 1
                    pd.Pulse("Writing output file")
                    # Concatenate everything together and sort by time of data
                    dtypes = array([d.dtype for d in allData])
                    u = array(len(dtypes)*[True])
                    filters = Filters(complevel=1,fletcher32=True)
                    # Concatenate by unique data type
                    j = 0
                    for i,t in enumerate(dtypes):
                        if u[i]:
                            match = (dtypes == t)
                            u[match] = False
                            data = concatenate([d for d,c in zip(allData,match) if c])
                            try:
                                perm = argsort(data['DATE_TIME'])
                            except:
                                perm = argsort(data['timestamp'])
                            data = data[perm]
                            table = op.createTable(op.root,"results_%d" % j,data,filters=filters)
                            j += 1
                            table.flush()
                    info.object.dataFile = fname
                    info.ui.title = "Viewing [" + info.object.dataFile + "]"
                    pd.Update(100,newmsg = "Done. Close box to view results")
            finally:
                op.close()

    def onBatchConvert(self,info):
        d = wx.DirDialog(None,"Open directory with .dat files",style=wx.DD_DEFAULT_STYLE)
        if d.ShowModal() == wx.ID_OK:
            path = d.GetPath()
            progress = 0
            for what,name in walkTree(path,sortDir=sortByName,sortFiles=sortByName):
                if what == "file" and os.path.splitext(name)[1]==".dat":
                    c = Dat2h5(datFileName = name)
                    try:
                        c.convert()
                    except Exception,e:
                        print "Error converting %s: %s" % (name,e)
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

        openAction = Action(name="Open H5...",action="onOpen")
        concatenateAction = Action(name="Concatenate H5...",action="onConcatenate")
        convertAction = Action(name="Convert DAT...",action="onConvert")
        batchConvertAction = Action(name="BatchConvert DAT...",action="onBatchConvert")
        exitAction = Action(name="Exit",action="onExit")
        series1Action = Action(name="1 frame",action="onSeries1")
        series2Action = Action(name="2 frames",action="onSeries2")
        series3Action = Action(name="3 frames",action="onSeries3")
        xyViewAction = Action(name="Correlation Plot",action="onCorrelation")
        self.traits_view = View(Item("dataFile",style="readonly",show_label=False),
                                    buttons=NoButtons,title="HDF5 File Viewer",
                                    menubar=MenuBar(Menu(openAction,concatenateAction,convertAction,batchConvertAction,exitAction,name='File'),
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