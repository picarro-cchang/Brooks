#!/usr/bin/python
#
# File Name: TestRcbCast.py
# Purpose: Diagnostic script for initiating dump of ringdown capture buffer and plotting result
#
# Notes:
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header

import sys
if ".." not in sys.path: sys.path.append("..")
from scipy.signal import lfilter, butter

import wx
import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

import socket
import time
from ctypes import *
from tables import *

# Host takes precedence over local, if the first fails it's likely the others will too
try:
    from Host.autogen.interface import *
    from Host.Common import CmdFIFO, SharedTypes
    from Host.Common.SharedTypes import RPC_PORT_DRIVER
except:
    from interface import *
    import CmdFIFO
    from SharedTypes import RPC_PORT_DRIVER

import threading
from numpy import *
from tables import *
from enthought.traits.api import *
from enthought.traits.api import File as EnthoughtFile
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import *
from enthought.traits.ui.wx.editor import Editor
from enthought.traits.ui.table_column import *
from traceback import format_exc
from numpy.linalg import solve
from FigureInteraction import FigureInteraction

def doFit(data,tSamp):
    """Perform exponential fitting to data, sampled at intervals tSamp"""
    x = array(data,dtype=double)
    y = cumsum(x)
    n = len(x)
    t = arange(n)
    sx = sum(x)
    stx = sum(t*x)
    sy = sum(y)
    sty = sum(t*y)
    syx = sum(y*x)
    syy = sum(y**2)
    A = n
    B = 0.5*n*(n-1)
    C = sy
    D = (n/6.0)*(n-1)*(2*n-1)
    E = sty
    F = syy
    G = sx
    H = stx
    I = syx
    a,b,s = solve(array([[n,B,sy],[B,D,sty],[sy,sty,syy]]),array([sx,stx,syx]))
    b = -b/s
    a = a/(1-s)-b
    f = 1/(1-s)
    return a,b,f

def doImprove(data,tSamp,start,nIter):
    x = array(data,dtype=double)
    a,b,f = start
    n = len(data)
    for k in range(nIter):
        v1 = f**arange(n)
        v2 = ones(n)
        v3 = a*arange(n)*tSamp * v1
        A = sum(v1**2)
        B = sum(v1*v2)
        C = sum(v1*v3)
        D = sum(v2**2)
        E = sum(v2*v3)
        F = sum(v3**2)
        res = x - (a*v1 + b)
        G = sum(v1*res)
        H = sum(v2*res)
        I = sum(v3*res)
        
        da,db,dal = solve(array([[A,B,C],[B,D,E],[C,E,F]]),array([G,H,I]))
        a += da
        b += db
        f *= exp(+dal*tSamp)
    return a,b,f    
    
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
            
    def autoscale(self):
        self.axes.relim()
        self.axes.autoscale_view()
        self.figureInteraction.autoscale[self.axes] = True

class RingdownGrabber(HasTraits):
    a = CFloat
    b = CFloat
    tau = CFloat
    loss = CFloat
    tSamp = CFloat(1.0/12.5e6)
    fitStart = CInt(10)
    fitEnd = CInt(4096)
    thresholdPercent = CFloat(80.0)
    lowerThreshold = CFloat(13000.0)
    
    traits_view = View(VGroup(Item("loss"),
                              Item("a"),
                              Item("b"),
                              Item("fitStart"),
                              Item("fitEnd"),
                              Item("thresholdPercent"),
                              Item("lowerThreshold")))

    def __init__(self):
        self.driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER,
                                    "", IsDontCareConnection = False)
    
    def getData(self):
        self.driverRpc.wrDasReg(SPECT_CNTRL_STATE_REGISTER,SPECT_CNTRL_PausedState)
        time.sleep(0.2)
        data, meta, params = self.driverRpc.rdRingdown(0)
        self.driverRpc.wrDasReg(SPECT_CNTRL_STATE_REGISTER,SPECT_CNTRL_RunningState)
        time.sleep(0.05)
        self.rd = asarray(data) & 0x3FFF
        self.t = self.tSamp*arange(len(self.rd))
        return self.t, self.rd

    def fitExp(self):
        c = 3e8
        minVal = min(self.rd[self.fitStart:self.fitEnd])
        maxVal = max(self.rd[self.fitStart:self.fitEnd])
        frac = 0.01*self.thresholdPercent
        thresh = min(frac*maxVal + (1.0-frac)*minVal,self.lowerThreshold)
        # Scan starting from position of maximum to find point which is below thresh
        istart = self.fitStart + argmax(self.rd[self.fitStart:self.fitEnd])
        while self.rd[istart]>thresh: 
            istart += 1
        self.a,self.b,f = doFit(self.rd[istart:self.fitEnd],self.tSamp)
        self.tau = -self.tSamp/log(f)
        self.loss = 1.0e4/(c*self.tau)
        self.tres = self.t[istart:self.fitEnd]
        self.res = self.rd[istart:self.fitEnd] - (self.a*exp(-(self.tres-self.tres[0])/self.tau)+self.b)
        return self.a, self.b, self.tau, self.loss, self.tres, self.res

class Waveform(IsDescription):
    index = Int16Col()
    value = Int16Col()
    
class Main(HasTraits):
    plot2d = Instance(Plot2D)
    instrument = Instance(RingdownGrabber)
    resScale = CFloat(200.0)
    run = CBool(True)
    showRes = CBool(True)
    showAvg = CBool(False)
    nPoints = CInt(0)
    meanLoss = CFloat
    stdLoss = CFloat
    shotToShot = CFloat
    resetStats = Button
    nAverage = CInt(0)
    resetAverage = Button
    outputFile = EnthoughtFile("",filter=["*.h5"])
    fCutoff = CFloat(500000.0)
    aFilt = CArray(value=[1.0,0.0,0.0])
    bFilt = CArray(value=[1.0,0.0,0.0])
    def __init__(self):
        self.plot2d = Plot2D(title="Ringdown",xLabel="Time (us)",yLabel="Voltage")
        self.instrument = RingdownGrabber()
        self.instrument.set(fitStart=10,fitEnd=4096)
        threading.Timer(1.0,self.doPlot).start()
        self.h5f = None
        self.sumLoss = 0
        self.sumSqLoss = 0
        self.sumBufferLength = None
        self.sumBuffer = None
        self._fCutoff_changed()
        self.plotHandles = self.plot2d.plotData([],[],'b-',[],[],'g-',[],[],'r-')

    def _fCutoff_changed(self):
        self.bFilt, self.aFilt = butter(3,2*self.instrument.tSamp*self.fCutoff) 
    
    def _outputFile_changed(self,old,new):
        if self.h5f != None:
            self.h5f.close()
            self.h5f = None
        h5f = openFile(self.outputFile,"w")
        filters = Filters(complevel=1,fletcher32=True)
        self.table = h5f.createTable(h5f.root,"ringdown",Waveform,filters=filters)
        self.table.attrs.sample_time = self.instrument.tSamp
        self.table.attrs.next_index = 0
        self.h5f = h5f
        
    def doPlot(self):
        if self.run:
            t, rd = self.instrument.getData()
            t = t[:self.instrument.fitEnd]
            rd = rd[:self.instrument.fitEnd]
            if self.sumBufferLength is None: 
                self.sumBufferLength = len(t)-400
                self.sumBuffer = zeros(self.sumBufferLength,dtype=float)
            if self.h5f:
                for v in rd:
                    entry = self.table.row
                    entry["index"] = self.table.attrs.next_index
                    entry["value"] = v
                    entry.append()
                self.table.attrs.next_index += 1    
                self.table.flush()
            try:
                a, b, tau, loss, tres, res = self.instrument.fitExp()
                res = lfilter(self.bFilt,self.aFilt,res)
                # print self.sumBuffer.shape, res[:self.sumBufferLength].shape
                self.sumBuffer += res[:self.sumBufferLength]
                self.nAverage += 1
                self.plot2d.updateData(self.plotHandles[0],1e6*t,rd)
                if self.showRes: 
                    self.plot2d.updateData(self.plotHandles[1],1e6*tres,self.resScale*res)
                else:
                    self.plot2d.updateData(self.plotHandles[1],[0],[0])
                if self.showAvg: 
                    self.plot2d.updateData(self.plotHandles[2],1e6*t[:self.sumBufferLength],self.resScale*self.sumBuffer/self.nAverage)
                else:
                    self.plot2d.updateData(self.plotHandles[2],[0],[0])
                self.sumLoss += loss
                self.sumSqLoss += loss**2
                self.nPoints += 1
                self.meanLoss = self.sumLoss/self.nPoints
                self.stdLoss = sqrt(self.sumSqLoss/self.nPoints - self.meanLoss**2)
                self.shotToShot = 100.0*self.stdLoss/self.meanLoss
            except:
                print format_exc()
        threading.Timer(0.2,self.doPlot).start()

    def _resetStats_fired(self):
        self.nPoints = 0
        self.sumLoss = 0
        self.sumSqLoss = 0

    def _resetAverage_fired(self):
        self.nAverage = 0
        self.sumBuffer = 0.0
        
if __name__ == "__main__":
    m =  Main()
    viewer = View(
        HGroup(Item("plot2d",style="custom",show_label=False),
               VGroup(Item("instrument",style="custom",show_label=False),
                      VGroup(Item("outputFile"),
                             HGroup(Item("run"),Item("showRes"),Item("showAvg")),
                             Item("fCutoff",editor=TextEditor(auto_set=False,enter_set=True)),
                             Item("resScale"),
                             Item("nPoints",style="readonly"),
                             Item("meanLoss",style="readonly",format_str="%.4f"),
                             Item("stdLoss",style="readonly",format_str="%.5f"),
                             Item("shotToShot",style="readonly",format_str="%.4f"),
                             Item("resetStats",show_label=False),
                             Item("nAverage",style="readonly"),
                             Item("resetAverage",show_label=False)
              ))),
        width=700,height=600,resizable=True,buttons=NoButtons,title="Examine Ringdowns") 
    m.configure_traits(view = viewer)
