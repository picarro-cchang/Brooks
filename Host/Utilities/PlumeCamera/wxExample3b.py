import wx

import matplotlib
from matplotlib.figure import Figure
import matplotlib.font_manager as font_manager
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from FigureInteraction import FigureInteraction
import psutil as p
import threading 

TIMER_ID = wx.NewId()
POINTS = 300

class PlotFigure(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,wx.ID_ANY,title="CPU Usage Monitor",size=(600,400))
        self.fig = Figure((6,4),100)
        self.canvas = FigureCanvas(self,wx.ID_ANY,self.fig)
        self.ax = self.fig.add_subplot(1,1,1)
        self.ax.set_ylim([0,100])
        self.ax.set_xlim([0,POINTS])
        self.ax.set_autoscale_on(False)
        # self.ax.set_xticks([])
        self.ax.set_yticks(range(0,101,10))
        self.ax.grid(True)
        
        self.user = [None] * POINTS
        self.nice = [None] * POINTS
        self.sys  = [None] * POINTS
        self.idle = [None] * POINTS
        
        self.l_user, = self.ax.plot(range(POINTS),self.user,label='User %')
        self.l_nice, = self.ax.plot(range(POINTS),self.nice,label='Nice %')
        self.l_sys,  = self.ax.plot(range(POINTS),self.sys, label='Sys %')
        self.l_idle, = self.ax.plot(range(POINTS),self.idle,label='Idle %')
        
        self.ax.legend(loc='upper center', ncol=4, prop=font_manager.FontProperties(size=10))
        self.canvas.draw()
        
        self.before = self.prepare_cpu_usage()
        self.k = 0
        self.bg = None
        self.Bind(wx.EVT_SIZE,self.onSize)
        wx.EVT_TIMER(self,TIMER_ID,self.onTimer)
        
    def prepare_cpu_usage(self):
        t = p.cpu_times()
        if hasattr(t,'nice'):
            return [t.user, t.nice, t.system, t.idle]
        else:
            return [t.user, 0, t.system, t.idle]
        
    def get_cpu_usage(self):
        now = self.prepare_cpu_usage()
        delta = [now[i]-self.before[i] for i in range(len(now))]
        total = sum(delta)
        self.before = now
        return [(100.0*dt)/total for dt in delta]
    
    def onSize(self,event):
        self.bg = None
        empty = [None] * POINTS
        self.l_user.set_ydata(empty)
        self.l_nice.set_ydata(empty)
        self.l_sys.set_ydata(empty)
        self.l_idle.set_ydata(empty)
        self.ax.draw_artist(self.l_user)
        self.ax.draw_artist(self.l_nice)
        self.ax.draw_artist(self.l_sys)
        self.ax.draw_artist(self.l_idle)
        self.canvas.blit(self.ax.bbox)
        event.Skip()
        
    def onTimer(self, evt):
        if self.bg is None:
            self.bg = self.canvas.copy_from_bbox(self.ax.bbox)
        tmp = self.get_cpu_usage()
        self.canvas.restore_region(self.bg)
        self.user = self.user[1:] + [tmp[0]]
        self.nice = self.nice[1:] + [tmp[1]]
        self.sys  = self.sys[1:]  + [tmp[2]]
        self.idle = self.idle[1:] + [tmp[3]]
        # self.ax.set_xlim([self.k,self.k+POINTS])
        self.l_user.set_xdata(range(self.k,self.k+POINTS))
        self.l_nice.set_xdata(range(self.k,self.k+POINTS))
        self.l_sys.set_xdata(range(self.k,self.k+POINTS))
        self.l_idle.set_xdata(range(self.k,self.k+POINTS))
        self.k += 1
        self.l_user.set_ydata(self.user)
        self.l_nice.set_ydata(self.nice)
        self.l_sys.set_ydata(self.sys)
        self.l_idle.set_ydata(self.idle)
        self.ax.draw_artist(self.l_user)
        self.ax.draw_artist(self.l_nice)
        self.ax.draw_artist(self.l_sys)
        self.ax.draw_artist(self.l_idle)
        # self.canvas.blit(self.ax.bbox)
        self.ax.relim()
        self.ax.autoscale(enable=True, axis='both', tight=True)
        self.canvas.draw()
        
if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = PlotFigure()
    fi = FigureInteraction(frame.fig,threading.RLock())
    t = wx.Timer(frame,TIMER_ID)
    t.Start(50)
    frame.Show()
    app.MainLoop()
    
    