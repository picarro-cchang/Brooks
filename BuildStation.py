APP_NAME = "BuildStation"

import sys
import wx
import time
import datetime
from collections import deque
from Queue import Queue, Empty
import inspect
from numpy import *
import types
from RingdownAnalyzer import RingdownAnalyzer
from ModeAnalyzer import ModeAnalyzer
from BuildStationGUI import BuildStationGUI
from Host.Common import timestamp
from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.configobj import ConfigObj
from Host.Common.Listener import Listener
from Host.Common.GraphPanel import Series
from Host.Common.Listener import Listener
from Host.Common.TextListener import TextListener
from Host.Common.SharedTypes import ctypesToDict, RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER, BROADCAST_PORT_RD_RECALC
from Host.Common.SharedTypes import RPC_PORT_SPECTRUM_COLLECTOR 
from Host.autogen import interface
from BuildStationCommon import _value, setFPGAbits, Driver, FreqConverter, SpectrumCollector

from TravellerDataPush import TravellerDataPush

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
            
class BuildStationFrame(BuildStationGUI):
    configName = 'BuildStationSettings.ini'
    scriptConfigName = 'BuildStationScript.ini'
    guiSave = {'text_ctrl':['graph_points', 'rd_threshold','min_1','max_1','min_2','max_2',
                            'serial_number', 'rejection_window', 'rejection_scale',
                            'laser_temperature', 'laser_current', 'num_average'],
               'combo_box':['action','laser'],
               'checkbox':['autoscale_1','autoscale_2','dither_enable']}
    cast = {'text_ctrl':str,
            'combo_box':str,
            'checkbox': lambda x:x == 'True'}
    def __init__(self,*args,**kwargs):
        BuildStationGUI.__init__(self,*args,**kwargs)
        self.handlers = {}
        self.timer = wx.Timer(self)
        self.rdAnalyzer = RingdownAnalyzer(self,ConfigObj(self.scriptConfigName))
        self.modeAnalyzer = ModeAnalyzer(self,ConfigObj(self.scriptConfigName))
        self.oldVisiblePages = None
        self.scriptEnvironment = {}
        self.processScriptIni(self.scriptConfigName)
        self.restoreGuiSettings()
        self.setupFromGui()
        self.text_ctrl_graph_points.Bind(wx.EVT_KILL_FOCUS, self.onGraphPointsEnter)
        self.text_ctrl_rd_threshold.Bind(wx.EVT_KILL_FOCUS, self.onRdThresholdEnter)
        self.text_ctrl_laser_temperature.Bind(wx.EVT_KILL_FOCUS, self.onLaserTemperatureEnter)
        self.text_ctrl_laser_current.Bind(wx.EVT_KILL_FOCUS, self.onLaserCurrentEnter)
        self.text_ctrl_num_average.Bind(wx.EVT_KILL_FOCUS, self.onNumAverageEnter)
        self.text_ctrl_rejection_window.Bind(wx.EVT_KILL_FOCUS, self.onRejectionWindowEnter)
        self.text_ctrl_rejection_scale.Bind(wx.EVT_KILL_FOCUS, self.onRejectionScaleEnter)
        self.text_ctrl_min_1.Bind(wx.EVT_KILL_FOCUS, self.onMin1Enter)
        self.text_ctrl_max_1.Bind(wx.EVT_KILL_FOCUS, self.onMax1Enter)
        self.text_ctrl_min_2.Bind(wx.EVT_KILL_FOCUS, self.onMin2Enter)
        self.text_ctrl_max_2.Bind(wx.EVT_KILL_FOCUS, self.onMax2Enter)
        self.button_pause.Show(False)
        #self.button_save.Show(False)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)        
        self.performAction()

    def startTimer(self,interval):
        self.timer.Start(interval)
        
    def stopTimer(self):
        self.timer.Stop()
    
    def registerObserver(self,handler,observer):
        name = handler if isinstance(handler,types.StringType) else handler.__name__
        if name not in self.handlers:
            self.handlers[name] = []
        if observer not in self.handlers[name]:
            self.handlers[name].append(observer)

    def deregisterObserver(self,handler,observer):
        name = handler if isinstance(handler,types.StringType) else handler.__name__
        if name in self.handlers:
            if observer in self.handlers[name]:
                self.handlers[name].remove(observer)
        
    def dispatcher(self):
        funcName = inspect.stack()[1][3]
        if funcName in self.handlers:
            for obs in self.handlers[funcName]: obs(self)

    def restoreGuiSettings(self):
        cfg = ConfigObj(self.configName)
        for c in cfg:
            if c in self.guiSave:
                for i in cfg[c]:
                    if i in self.guiSave[c]:
                        name = '%s_%s' % (c,i)
                        getattr(eval('self.' + name),'SetValue')(self.cast[c](cfg[c][i]))
    
    def saveGuiSettings(self):
        cfg = ConfigObj(self.configName)
        for c in self.guiSave:
            if c not in cfg: cfg[c] = {}
            for i in self.guiSave[c]:
                name = '%s_%s' % (c,i)
                cfg[c][i] = getattr(eval('self.' + name),'GetValue')()
        cfg.write()
        
    def processScriptIni(self,fname):
        self.actions = {}
        fp = file(fname,'r')
        self.scriptConfig = ConfigObj(fp,list_values=True,raise_errors=True)
        fp.close()
        self.laserSelection = self.scriptConfig['_Laser Selection']
        self.actionNames = [secName for secName in self.scriptConfig if not secName.startswith('_')]
        for a in self.actionNames:
            self.actions[a] = self.scriptConfig[a]["action"]
        self.combo_box_laser.SetItems([self.laserSelection[laser] for laser in self.laserSelection])
        self.combo_box_laser.SetSelection(0)
        self.combo_box_action.SetItems(self.actionNames)
        self.combo_box_action.SetSelection(0)
        self.scriptEnvironment.update({
           "__builtins__": __builtins__,
           "self": self,
           "interface": interface,
           "Driver": Driver,
           "SpectrumCollector": SpectrumCollector,
           "FreqConverter": FreqConverter,
           "setFPGAbits": setFPGAbits,
           "_value": _value
           })
        if '_Macro Environment' in self.scriptConfig:
            action = self.scriptConfig['_Macro Environment']['action']
            exec action in self.scriptEnvironment

    def screenDump(self):
        ##print 'saving the traveller push ctl file'
        save_ts = datetime.datetime.now()
        png_name = 'bstn_%s.png' % (save_ts.strftime("%Y%m%d%H%M%S"))
        dfile_name = 'bstn_%s.ctl' % (save_ts.strftime("%Y%m%d%H%M%S"))
        
        ## for now we are building a csv.  But we should build an H5 once
        ## we learn the proper format
        h5file_name = 'bstn_%s.h5' % (save_ts.strftime("%Y%m%d%H%M%S"))
        csvplotfile_name = 'bstn_%s.csv' % (save_ts.strftime("%Y%m%d%H%M%S"))
        dump_data = {}
        parm_data = {}
        lsrsel = self.combo_box_laser.GetString(
                                                self.combo_box_laser.GetCurrentSelection()
                                                )
        optnum, sep, las_sel = lsrsel.partition('-')
        las_sel = las_sel.strip()
        laser_str, sep, suffix = las_sel.partition(' ')
        dump_data['rdmdoc_wavelength'] = laser_str.strip()
        dump_data['rdmdoc_rd_time'] = self.text_ctrl_rd_time.GetValue()
        dump_data['rdmdoc_s2s_pct'] = self.text_ctrl_s2s.GetValue()
        dump_data['cavity_sn'] = self.text_ctrl_serial_number.GetValue()
        
        ctl_f = open(dfile_name, "w")
        str = "[cavity_traveller]\n"
        for kv in dump_data:
            str += "%s: %s\n" % (kv, dump_data[kv])
        
        try:
            xvals = self.rdAnalyzer.graph1Waveform.GetX() 
            yvals = self.rdAnalyzer.graph1Waveform.GetY()
        except:
            xvals = []
            yvals = []
        
        if len(xvals) == len(yvals):
            dta_f = open(csvplotfile_name, 'w')
            dstr = ''
            for x, y in zip(xvals, yvals):
                dstr += '%s,%s\n' % (x, y)
            
            dta_f.write(dstr)
            
        ctl_f.write(str)
        
        context = wx.WindowDC(self)
        memory = wx.MemoryDC( )
        x,y = self.GetSizeTuple()
        bitmap = wx.EmptyBitmap( x,y, -1 )
        memory.SelectObject( bitmap )
        memory.Blit( 0,0,x,y, context, 0,0)
        memory.SelectObject( wx.NullBitmap )
        bitmap.SaveFile( png_name, wx.BITMAP_TYPE_PNG )  

        parm_data['image_file'] = png_name
        parm_data['plot_file'] = csvplotfile_name
        
        try:
            if self.last_userid:
                dump_data['userid'] = self.last_userid
        except:
            self.last_userid = None
        
        ## Wrapped in a try so as not to kill the buildstation if there
        ## is some issuw with the Traveller Push
        try:
            c = TravellerDataPush(data_dict=dump_data,parm_dict=parm_data)
            self.last_userid = c.last_userid 
            del c
        except:
            pass 
        
    def setupFromGui(self):
        self.onMin1Enter()
        self.onMax1Enter()
        self.onAutoscale1()
        self.onMin2Enter()
        self.onMax2Enter()
        self.onAutoscale2()
        self.onGraphPointsEnter()
            
    def performAction(self):
        dlg = wx.BusyInfo('Configuring analyzer, please wait')
        exec self.actions[self.combo_box_action.GetValue()] in self.scriptEnvironment
        del dlg
        
    def onLaserSelect(self,evt):
        self.performAction()
        if evt: evt.Skip()

    def onActionSelect(self,evt):
        self.performAction()
        if evt: evt.Skip()
        
    def notebook_setup(self,visiblePages):
        if self.oldVisiblePages == visiblePages: return
        pages = [(self.notebook_graphs_ringdowns,"Ringdowns"),
                 (self.notebook_graphs_mode_scan,"Mode Scan"),
                 (self.notebook_graphs_mode_amplitudes,"Mode Amplitudes"),
                 (self.notebook_graphs_ripple_analysis,"Ripple Analysis")]
        # Clear out notebook
        self.notebook_graphs.Show(False) # Hide while making changes, this speeds up screen update
        while (self.notebook_graphs.GetPageCount() > 0):
            self.notebook_graphs.RemovePage(0)
        for p,s in pages:
            if p in visiblePages:
                p.Show(True)
                self.notebook_graphs.AddPage(p,s)
            else:
                p.Show(False)
        self.notebook_graphs.SetSelection(0)
        self.notebook_graphs.Show(True)
        self.SetAutoLayout(True)
        self.Layout()
        self.oldVisiblePages = visiblePages
        
    def onAutoscale1(self, evt=None):
        if self.checkbox_autoscale_1.IsChecked():
            self.graph_panel_1.SetGraphProperties(YSpec="auto")
        else:
            self.graph_panel_1.SetGraphProperties(YSpec=(float(self.text_ctrl_min_1.GetValue()),float(self.text_ctrl_max_1.GetValue())))
        if evt: evt.Skip()

    def onMin1Enter(self,evt=None):
        if not self.checkbox_autoscale_1.IsChecked():
            self.graph_panel_1.SetGraphProperties(YSpec=(float(self.text_ctrl_min_1.GetValue()),float(self.text_ctrl_max_1.GetValue())))
        if evt: evt.Skip()
        
    def onMax1Enter(self,evt=None):
        if not self.checkbox_autoscale_1.IsChecked():
            self.graph_panel_1.SetGraphProperties(YSpec=(float(self.text_ctrl_min_1.GetValue()),float(self.text_ctrl_max_1.GetValue())))
        if evt: evt.Skip()
        
    def onAutoscale2(self, evt=None):
        if self.checkbox_autoscale_2.IsChecked():
            self.graph_panel_2.SetGraphProperties(YSpec="auto")
        else:
            self.graph_panel_2.SetGraphProperties(YSpec=(float(self.text_ctrl_min_2.GetValue()),float(self.text_ctrl_max_2.GetValue())))
        if evt: evt.Skip()
        
    def onMin2Enter(self,evt=None):
        if not self.checkbox_autoscale_2.IsChecked():
            self.graph_panel_2.SetGraphProperties(YSpec=(float(self.text_ctrl_min_2.GetValue()),float(self.text_ctrl_max_2.GetValue())))
        if evt: evt.Skip()
        
    def onMax2Enter(self,evt=None):
        if not self.checkbox_autoscale_2.IsChecked():
            self.graph_panel_2.SetGraphProperties(YSpec=(float(self.text_ctrl_min_2.GetValue()),float(self.text_ctrl_max_2.GetValue())))
        if evt: evt.Skip()
    
    def onGraphPointsEnter(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()

    def onRdThresholdEnter(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()

    def onLaserTemperatureEnter(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()

    def onLaserCurrentEnter(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()

    def onNumAverageEnter(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()

    def onRejectionWindowEnter(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()
        
    def onRejectionScaleEnter(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()
        
    def onTimer(self,evt=None):
        interval = self.timer.GetInterval()
        self.timer.Stop()
        self.dispatcher()
        self.timer.Start(interval)
        if evt: evt.Skip()

    def onDitherEnable(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()
    
    def onClear(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()

    def onPause(self,evt=None):
        self.dispatcher()
        if evt: evt.Skip()
        
    def onSave(self,evt=None):
        self.dispatcher()
        self.screenDump()
        if evt: evt.Skip()
        
    def onClose(self,evt=None):
        self.dispatcher()
        self.timer.Stop()
        self.saveGuiSettings()
        if evt: evt.Skip()
    
    def onQuit(self,evt=None):
        self.dispatcher()
        self.Close()
        if evt: evt.Skip()
        
if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = BuildStationFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()