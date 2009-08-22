import wx
import matplotlib
from FigureInteraction import FigureInteraction
import matplotlib.pyplot
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import *
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
import sys
import threading

from cStringIO import StringIO
from numpy import *
from tables import *
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.wx.editor import Editor
from enthought.traits.ui.basic_editor_factory import BasicEditorFactory
from enthought.traits.ui.menu import *
from Host.autogen.interface import *
from thermalAnalysis2 import *

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
    systemResp = Instance(Plot2D,()) 
    setpointResp = Instance(Plot2D,())
    disturbanceResp = Instance(Plot2D,())
    K = CFloat(100.0)
    Ti = CFloat(1000.0)
    Td = CFloat(0.1)
    N = CFloat(1000.0)
    h = CFloat(0.2)
    b = CFloat(1.0)
    c = CFloat(1.0)
    Nsamp = CInt(500)
    
    def __init__(self,*a,**k):
        HasTraits.__init__(self,*a,**k)
        self.lock = threading.RLock()
    
    def process(self,fname,inputStream,outputStream):
        h5f = openFile(fname,"r")
        table = h5f.root.sensors
        y = table.readWhere("(streamNum == %d)" % outputStream)
        x = table.readWhere("(streamNum == %d)" % inputStream)
        h5f.close()
        # Obtain data on a common timebase
        tMin = max(x['time'][0],y['time'][0])
        tMax = min(x['time'][-1],y['time'][-1])
        filt = (x['time']>=tMin) & (x['time']<=tMax)
        t = x['time'][filt]
        x = x['value'][filt]
        y = y['value'][(y['time']>=tMin) & (y['time']<=tMax)]
        
        #fp = file("data.dat","wa")
        #for t1,x1,y1 in zip(t,x,y):
        #    print>>fp, "%s %s %s" % (t1,x1,y1)
        #fp.close()
        
        num,den,res,rank,sv,mock = find_ARMA(x,y,range(1,16),range(1,16),1)
        # Transfer functions as ratios of polynomials in z^-1
        step = ones(self.Nsamp,dtype=float)
        self.sysG = Ltid.fromNumDen(num,den)
        self.sysGinv = Ltid.fromNumDen(den,num)

    def findResponse(self):
        p = self.Td/(self.Td + self.N*self.h)
        denC =  array([1.0,-(1.0+p),p])
        numCp = array([0,1.0,-(1.0+p),p])
        numCi = array([0,1.0,-p,0.0])
        numCd = array([0,1.0,-2.0,1.0])
        numC = -self.K*(numCp + (self.h/self.Ti)*numCi + self.N*p*numCd)
        numCw = -self.K*(self.b*numCp + (self.h/self.Ti)*numCi + self.c*self.N*p*numCd)
        #
        sysC = Ltid.fromNumDen(numC,denC)
        self.sysD = self.sysG.feedback(sysC)
        self.sysE = Ltid.fromNumDen(numCw,denC)
        self.sysH = self.sysD.cascade(self.sysE)
        #
        idSys = Ltid([0],[1],[0],[1])
        sysGC = self.sysG.cascade(sysC)
        self.sysU = idSys.feedback(sysGC).cascade(self.sysE)
                
        self.Dnum, self.Dden = self.sysD.toNumDen()
        self.Hnum, self.Hden = self.sysH.toNumDen()
        self.Gnum, self.Gden = self.sysG.toNumDen()
        self.Unum, self.Uden = self.sysU.toNumDen()

        #
        step = ones(self.Nsamp,dtype=float)

        y0 = lfilter(self.Unum,self.Uden,step)
        self.systemResp.plotData(y0)

        y1 = lfilter(self.Dnum,self.Dden,step)
        self.disturbanceResp.plotData(y1)
        #
        y2 = lfilter(self.Hnum,self.Hden,step)
        self.setpointResp.plotData(y2)
        
    def _K_fired(self):
        self.findResponse()
    def _Ti_fired(self):
        self.findResponse()
    def _Td_fired(self):
        self.findResponse()
    def _N_fired(self):
        self.findResponse()
    def _b_fired(self):
        self.findResponse()
    def _c_fired(self):
        self.findResponse()
    def _Nsamp_fired(self):
        self.findResponse()
    
if __name__ == "__main__":
    fname = "../Host/Driver/Sensors_20090821_153336.h5"
    inputStream = STREAM_Laser3Tec
    outputStream = STREAM_Laser3Temp
    viewer = Viewer()
    viewer.process(fname,inputStream,outputStream)
    
    myView = View(Item("systemResp",style="custom",show_label=False),
                  Item("disturbanceResp",style="custom",show_label=False),
                  Item("setpointResp",style="custom",show_label=False),
                  Item("K",editor=RangeEditor(low=1.0,high=10000.0,auto_set=False,enter_set=True,mode='xslider')),
                  Item("Ti",editor=RangeEditor(low=0.1,high=10.0,auto_set=False,enter_set=True,mode='xslider')),
                  Item("Td",editor=RangeEditor(low=0.0,high=10.0,auto_set=False,enter_set=True,mode='xslider')),
                  Item("N",editor=RangeEditor(low=1.0,high=1000.0,auto_set=False,enter_set=True,mode='xslider')),
                  Item("b",editor=RangeEditor(low=0.0,high=1.0,auto_set=False,enter_set=True,mode='xslider')),
                  Item("c",editor=RangeEditor(low=0.0,high=1.0,auto_set=False,enter_set=True,mode='xslider')),
                  Item("Nsamp",editor=RangeEditor(low=1,high=10000,auto_set=False,enter_set=True,mode='xslider')),
                  width=800,height=800,resizable=True,buttons=NoButtons,title="Thermal Analyser"
                  )
    viewer.configure_traits(view=myView)
