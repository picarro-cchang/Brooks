'''
ringdownplotmodel.py -- The ringdownplot module contains the RingdownPlotModel 
class. This class will display an XY plot of data from the 
BROADCAST_PORT_RDRESULTS

'''
APP_NAME = "RingdownPlotModel"
APP_DESCRIPTION = "RingdownPlot Data Model"
__version__ = 1.0

# Set SIMULATE_DATA to true for testing where there is no drive
# random values will be used for the plots 
# the plot datum are meaningless during this time, but you are able
# to test the operation of the module
SIMULATE_DATA = True

from pylab import *
            



import os
import time, datetime
import random

import tables
from collections import deque

from configobj import ConfigObj

from Queue import Queue

from postprocessdefn import *

from matplotlib.figure import Figure
from matplotlib.dates import date2num, YearLocator, MonthLocator, DateFormatter
from matplotlib.ticker import FormatStrFormatter

import matplotlib.font_manager as font_manager

from Host.Common.Listener import Listener
from Host.Common import CmdFIFO, SharedTypes, timestamp

from Host.autogen import interface

from ctypes import c_ubyte, c_byte, c_uint, c_int, c_ushort, c_short
from ctypes import c_longlong, c_float, c_double, Structure, Union, sizeof

import numpy
from Host.Common.SharedTypes import ctypesToDict, RPC_PORT_DRIVER, RPC_PORT_SPECTRUM_COLLECTOR, RPC_PORT_FREQ_CONVERTER

import xmlrpclib

from Utilities import AppInfo


Driver = CmdFIFO.CmdFIFOServerProxy(
                        "http://localhost:%d" % RPC_PORT_DRIVER, 
                        APP_NAME, IsDontCareConnection = False
                        )

SpectrumDriver = CmdFIFO.CmdFIFOServerProxy(
                        "http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR, 
                        APP_NAME, IsDontCareConnection = False
                        )

FreqConverter = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_FREQ_CONVERTER,
                                     APP_NAME, IsDontCareConnection = False)

class RingdownListener(SharedTypes.Singleton):
    def __init__(self, latency=None):
        self.queue = Queue()
        self.latency = latency
        self.listener = Listener(queue=self.queue,
                            port = SharedTypes.BROADCAST_PORT_RDRESULTS,
                            elementType = interface.RingdownEntryType,
                            #streamFilter = self.filter,
                            retry = True,
                            name = "RingdownPlotModel ringdown stream listener",
                            ) #logFunc = Log)

    def get_data(self):
        if self.latency:
            until_ts = timestamp.getTimestamp() - self.latency
            
        rtn = []
        while not self.queue.empty():
            try:
                data = self.queue.get()
                rtn.append(data)
                
                if self.latency:
                    if data.timestamp > until_ts:
                        break
                        
            except:
                break
        
        return rtn


class RingdownListenerWLM(SharedTypes.Singleton):
    '''
    This is for listening with a WLM
    '''
    def __init__(self, latency=None):
        self.queue = Queue()
        self.latency = latency
        self.listener = Listener(queue=self.queue,
                            port = SharedTypes.BROADCAST_PORT_RD_RECALC,
                            elementType = interface.ProcessedRingdownEntryType,
                            #streamFilter = self.filter,
                            retry = True,
                            name = "RingdownPlotModel ringdown stream listener",
                            ) #logFunc = Log)

    def get_data(self):
        if self.latency:
            until_ts = timestamp.getTimestamp() - self.latency
            
        rtn = []
        while not self.queue.empty():
            try:
                data = self.queue.get()
                rtn.append(data)

                if self.latency:
                    if data.timestamp > until_ts:
                        break
                        
            except:
                break

        return rtn


class SensorListener(SharedTypes.Singleton):
    def __init__(self):
        self.queue = Queue()
        self.listener = Listener(queue=self.queue,
                            port = SharedTypes.BROADCAST_PORT_SENSORSTREAM,
                            elementType = interface.SensorEntryType,
                            #streamFilter = self.filter,
                            retry = True,
                            name = "SensorPlotModel sensor stream listener",
                            ) #logFunc = Log)
    
    def get_data(self):
        rtn = {}
        for ii in interface.STREAM_MemberTypeDict.keys():
            rtn[ii] = []
        
        while not self.queue.empty():
            try:
                data = self.queue.get()
                utime = timestamp.unixTime(data.timestamp)
    
                if data.streamNum == interface.STREAM_Ratio1:
                    rtn[data.streamNum].append((utime, data.value/32768.0))
                elif data.streamNum == interface.STREAM_Ratio2:
                    rtn[data.streamNum].append((utime, data.value/32768.0))
                else:
                    rtn[data.streamNum].append((utime, data.value))
                
            except: # Queue.Empty:
                #print datetime.datetime.now(), "empty queue"
                break
                
        return rtn
        


class RingdownPlotModel(object):
    '''
    RingdownPlot Model Class
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''

        #Temporary code
        self.count_of_rows = []
        self.debug_fig = None
        self._debug_plt = None

        # version and about info
        about = AppInfo()
        self.about_version = about.getAppVer()
        self.about_name = "Ringdown Plot (Test Station)"  #about.getAppName()
        self.about_copyright = about.getCopyright()
        self.about_description = "Graphic plot of live analyzer output."  # about.getDescription()
        self.about_website = about.getWebSite()

        if "cntls_obj" in kwargs:
            self.cntls_obj = kwargs["cntls_obj"]
            del kwargs["cntls_obj"]
        else:
            self.cntls_obj = None

        if "fig_act" in kwargs:
            self.fig_act = kwargs["fig_act"]
            del kwargs["fig_act"]
        else:
            self.fig_act = None

        self._status = ""
        self._title = "Ringdown Plot"
        self._max_source_lines = 100
        self._counter = 0
        self.lbl_rotate = 0
        self.s2s_size = 400
        self.smooth_size = 0
        self.pctr = 0
        self.initial_ts = timestamp.getTimestamp()
        self.plot_ts = self.initial_ts
        self.last_s2s_ts = self.initial_ts
        self.rdfilter_ts = self.initial_ts
        self.last_stats_ts = self.initial_ts

        self.rdstats = []
        self.number_ringdowns = 0
        self.rdt_sum = 0
        self.avg_timer = 0
        self.last_rd_ts = self.initial_ts
        
        self._last_data_len = 0
        self.show_time = True
        self._plot_canvas = None
        self.SHOW_MEASURE = None
        self.macro_mode_active = None
        self.macro_laser_active = None
        self.macro_debug = None
        self.macro_initialization = None
        self.macro_environment = {}
        
        #measurement of code
        self.last_time = timestamp.getTimestamp()
                
        self._message_array = {0: (datetime.datetime.now(), "Start plotting.")}
        
        self._plot_was_generated = None
        self._regenerate_plot = None
        self.ringdown_plot_active = None        
        
        self.using_wlm = None
        self.collecting_data = None
        
        self._get_buildstation_ctl()
        self._get_buildstation_ini()
        self._init_process_parms()
        self._init_cntl_objs()


    def _get_buildstation_ctl(self):
        '''
        get data from buildstation ctl_file
        '''
        f_data = None
        skip_queue = ""
        use_wlm = ""
        show_measure = ""
        latency = ""
        facecolor = ""
        macro_debug = ""

        try:
            ctl_f = open("buildstation.ctl", "rw")
            if ctl_f:
                f_data = ctl_f.readline()
                while f_data:
                    
                    for ckey in (
                                 "STATION ID", 
                                 "MFG URI", 
                                 "USE WLM", 
                                 "SKIP QUEUE",
                                 "SHOW MEASURE",
                                 "LATENCY",
                                 "PLOT FACE COLOR",
                                 "MACRO DEBUG",
                                 ):
                        #search_term = "%s: " % (self.cntls_defn[ckey][3])
                        search_term = "%s: " % (ckey)
                        if search_term in f_data:

                            slen = len(search_term)
                            val = f_data[slen:].strip()
                            
                            if ckey == "STATION ID":
                                self.station_id = val

                            if ckey == "MFG URI":
                                self.mfg_uri = val

                            if ckey == "USE WLM":
                                use_wlm = val
                            
                            if ckey == "SKIP QUEUE":
                                skip_queue = val
                            
                            if ckey == "SHOW MEASURE":
                                show_measure = val
                                
                            if ckey == "LATENCY":
                                latency = val
                                
                            if ckey == "PLOT FACE COLOR":
                                facecolor = val
                            
                            if ckey == "MACRO DEBUG":
                                macro_debug = val
                                
                    f_data = ctl_f.readline()
            
        except:
            msg = "buildstation.ctl file is missing or cannot be found."
            msg += "\nThis file must be in the same path as the program."
            raise RuntimeError, msg

        try:
            self.latency = int(latency)
        except:
            self.latency = None
       
        self.plot_facecolor = PLOT_FACECOLOR
        if facecolor:
            self.plot_facecolor = facecolor 
      
        
        if show_measure.upper() in ("YES", "Y", "T", "TRUE"):
            self.SHOW_MEASURE = True
            print datetime.datetime.now(), "SHOW MEASURE", show_measure
        

        if macro_debug.upper() in ("YES", "Y", "T", "TRUE"):
            self.macro_debug = True
            print datetime.datetime.now(), "MACRO DEBUG", macro_debug
        

        if skip_queue.upper() in ("YES", "Y", "T", "TRUE"):
            self.no_listener_queue = True
            if use_wlm.upper() in ("YES", "Y", "T", "TRUE"):
    
                self.using_wlm = True
                #self.data_listener = RingdownListenerWLM()
                self.listener = Listener(
                                    queue=None,
                                    port = SharedTypes.BROADCAST_PORT_RD_RECALC,
                                    elementType = interface.ProcessedRingdownEntryType,
                                    streamFilter = self.rdfilter,
                                    retry = True,
                                    name = "RingdownPlotModel ringdown stream listener",
                                    ) #logFunc = Log)
            else:
                #self.data_listener = RingdownListener()
                self.listener = Listener(
                                    queue=None,
                                    port = SharedTypes.BROADCAST_PORT_RDRESULTS,
                                    elementType = interface.RingdownEntryType,
                                    streamFilter = self.rdfilter,
                                    retry = True,
                                    name = "RingdownPlotModel ringdown stream listener",
                                    ) #logFunc = Log)


        else:
            self.no_listener_queue = None
            
            if use_wlm.upper() in ("YES", "Y", "T", "TRUE"):
    
                self.using_wlm = True
                self.data_listener = RingdownListenerWLM(self.latency)
            else:
                self.data_listener = RingdownListener(self.latency)


        self.sensor_data_listener = SensorListener()
    
    def _get_buildstation_ini(self):
        '''
        '''
        self.macro_dict = {}
        self.macro_order = []
        self.laser_sel_order = []
        try:
            config = ConfigObj("buildstation.ini", 
                               list_values=True, 
                               raise_errors=True)
            good_file = True
        except:
            good_file = False
            
        if good_file:
            for sect in config.keys():
                #print "sect:", sect, type(config[sect])
                if sect not in ("Laser Selection", "Macro Environment", ):
                    self.macro_order.append(sect)

                self.macro_dict[sect] = {}
                if type(config[sect]) == type("this is a string"):
                    #print "None", sect, config[sect]
                    contiue
                else:
                    for keyword in config[sect]:
                        val = config[sect][keyword]
                        #print "keyword", sect, keyword, val
                        self.macro_dict[sect][keyword] = val
                        
                        if sect == "Laser Selection":
                            self.laser_sel_order.append(val)
        else:
            #print "found error"
            print "No Macros Found"
        
    
    def rdfilter(self, data):
        '''
        ringdown data filter 
        '''
        if not self.collecting_data:
            return
        
        localDict = ctypesToDict(data)
        #print datetime.datetime.now(), "localDict", localDict
        
        self._measure_system("rdfilter")   
             
        now = {}
        for cidx in range(0,3):
            now[cidx] = []

        now["stats"] = []
        
        start_time = None
        end_time = None
        dt = None
        rdt_sum = 0.0
        
        if data.uncorrectedAbsorbance == 0.0:
            return
        
        try:
            #utime = timestamp.unixTime(data.timestamp)
            ltime = timestamp.timestampToLocalDatetime(data.timestamp)
        except:
            return

        if data.timestamp < self.initial_ts:
            return
            
        self._last_data_len += 1

        dt = ltime
        #dt = datetime.datetime.fromtimestamp(plot_time)

        if not start_time:
            start_time = dt
            
        numtime = date2num(dt)
        
        rdt = 0.0
        if not data.uncorrectedAbsorbance == 0.0:
            rdt = 1.0 / (0.029979245800 * data.uncorrectedAbsorbance)
            
        for cidx in range(0,3):
            if self._ptype[cidx] in ("Ringdowns", ):
                continue
            
            if not self._ptype[cidx] == CHOICE_NONE:
                x,y = self.ptype_dict[self._ptype[cidx]]
                if x == "timestamp":
                    xval = numtime
                else:
                    xval = getattr(data, x)
                if y == "shot2shot":
                    y = "uncorrectedAbsorbance"
                yval = getattr(data, y)
                
                if y == "uncorrectedAbsorbance":
                    yval = rdt
                    
                now[cidx].append((xval, yval))

#        if start_time:
#            end_time = dt
        self.number_ringdowns += 1
        self.rdt_sum += rdt
        
        rd_ts = timestamp.getTimestamp()
        
        elapsed_time = rd_ts - self.last_rd_ts

        self.last_rd_ts = rd_ts
        
        self.avg_timer += elapsed_time
        
        self.rdstats.append((dt, rdt))
        
        if self.avg_timer > 999:            
            avg_rdt = self.rdt_sum / self.number_ringdowns
            
            now["stats"] = self.rdstats
            
            now["start_time"] = rd_ts - self.avg_timer
            now["end_time"] = rd_ts
            now["number_ringdowns"] = self.number_ringdowns
            now["avg_ringdown"] = avg_rdt
            
            self.number_ringdowns = 0
            self.rdt_sum = 0
            self.avg_timer = 0
            self.rdstats = []
            
        self._load_plot_values(now)
        if self._plot_canvas:
            self._set_and_draw(1, fig_act, self._plot_canvas)

        
    def _init_cntl_objs(self):
        '''
        Initialize the control objects (define the controls for the panels)
        '''
        self.list_of_plots = []
        self.list_of_plots.append(CHOICE_NONE)
        for name in self.ptype_list:
            self.list_of_plots.append(name)

        self.list_of_smooth = []
        self.list_of_smooth.append(CHOICE_NONE)
        for i in range(1,10):
            self.list_of_smooth.append("%s" % (i) )
        for i in range(1,10):
            self.list_of_smooth.append("%s0" % (i) )
        for i in range(1,10):
            self.list_of_smooth.append("%s00" % (i) )

        self.list_yes_no = []
        self.list_yes_no.append("No")
        self.list_yes_no.append("Yes")

        self.list_spect = []
        for ns in range(32):
            self.list_spect.append("%s" % (ns+1,))

        self.list_norm_smooth = []
        self.list_norm_smooth.append("Both")
        self.list_norm_smooth.append("Normal")
        self.list_norm_smooth.append("Smooth")

        self.list_tabs = []
        self.list_tabs.append("Single Tab")
        self.list_tabs.append("Separate Tabs")
        #self.list_tabs.append("Combine and Correlate")

        self.list_lasers = []
        self.list_lasers.append("1")
        self.list_lasers.append("2")
        self.list_lasers.append("3")
        self.list_lasers.append("4")

        self.list_rdtypes = []
        self.list_rdtypes.append("Constant laser temp")  
        self.list_rdtypes.append("Laser temp sweep")
        if self.using_wlm:
            self.list_rdtypes.append("Use sequence")

        self.list_pltypes = []
        self.list_pltypes.append("Plot against time")  #constant laser temp, laser temp sweep, use sequence (SPECT_CNTRL_SchemeMultipleMode)
        self.list_pltypes.append("Plot against laser temp")
        if self.using_wlm:
            self.list_pltypes.append("Plot against wave number")



        self.list_rdmodes = []
        self.list_rdmodes.append("Ringdown")
        self.list_rdmodes.append("Continuous")

        self.list_mirror_loc = []
        self.list_mirror_loc.append("Top")
        self.list_mirror_loc.append("Center")
        self.list_mirror_loc.append("Bottom")
        self.list_mirror_loc.append("Left")
        self.list_mirror_loc.append("Right")

        self.list_wavelength_loc = []
        self.list_wavelength_loc.append("1325nm")
        self.list_wavelength_loc.append("1392nm")
        self.list_wavelength_loc.append("1575nm")
        self.list_wavelength_loc.append("1601nm")
        
        self.list_align_type = []
        self.list_align_type.append("Front")
        self.list_align_type.append("Rear")

        dflt_macro = self.macro_order[0]
        dflt_laser_sel = self.laser_sel_order[0]



        txt_len = 80
        txt_len_smed = 110
        txt_len_long = 200
        txt_len_med = 150
        txt_len_note = 1024
        cntl_len = 200
        tiny_len = 65

        parameter_cols = [
        ("laser_sel", txt_len_smed, "Select Laser", CHOICE_CNTL, self.laser_sel_order, dflt_laser_sel, True),
        ("pl_macro", txt_len_smed, "Process", CHOICE_CNTL, self.macro_order, dflt_macro, True),
        (POINTS_PARM, txt_len, "Points", TEXT_CNTL, None, "5000", True),
        ("p1_type", cntl_len, "Plot 1", CHOICE_CNTL, self.list_of_plots, CHOICE_NONE, True),
            
        ("rd_time", txt_len_smed, "RD Time", TEXT_CNTL_DSP, None, None, None),
        ("rd_sec", txt_len_smed, "RD/s", TEXT_CNTL_DSP, None, None, None),
        ("s2s_pct", txt_len_smed, "S2S Pct", TEXT_CNTL_DSP, None, None, None),
        ("cav_pressure", txt_len_smed, "Pressure", TEXT_CNTL_DSP, None, None, None),

        ("rd_mode", txt_len_smed, "Mode", RADIO_CNTL, self.list_rdmodes, "Continuous", True),
        ("dither_flag", txt_len_smed, "Enable dither?", RADIO_CNTL, self.list_yes_no, "Yes", True),
        ("rd_threshold", txt_len, "RD Threshold", TEXT_CNTL, None, "16350", True),

        ("cntl_spacer4", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("lot_id", txt_len, "Lot", TEXT_CNTL, None, "", True),
        ("mirror_id", txt_len, "Mirror", TEXT_CNTL, None, "", True),
        ("cavity_id", txt_len, "Cavity ID", TEXT_CNTL, None, "", True),
        ("cavity_sn", txt_len, "Cavity S/N", TEXT_CNTL, None, "", True),
        ]
    
        # data columns for PLOT0 panel
        plot0_cols = [
        #(name, len, label, type, vlist, default, cname)
        ("plt1_spacer", tiny_len, "", SPACER_CNTL, None, None, None),
        ("plt1_auto", txt_len, "Autosize?", RADIO_CNTL, self.list_yes_no, "Yes", True),
        ("plt1_ymin", tiny_len, "Y Min", TEXT_CNTL, None, "20.0", True),
        ("plt1_ymax", tiny_len, "Y Max", TEXT_CNTL, None, "70.0", True),
        ]
        
        # data columns for PLOT1 panel
        plot1_cols = [
        #(name, len, label, type, vlist, default, cname)
        ("plt2_spacer", tiny_len, "", SPACER_CNTL, None, None, None),
        ("plt2_auto", txt_len, "Autosize?", RADIO_CNTL, self.list_yes_no, "Yes", True),
        ("plt2_ymin", tiny_len, "Y Min", TEXT_CNTL, None, "20.0", True),
        ("plt2_ymax", tiny_len, "Y Max", TEXT_CNTL, None, "70.0", True),
        ]
        
        # data columns for PLOT2 panel
        plot2_cols = [
        #(name, len, label, type, vlist, default, cname)
        ("plt3_spacer", tiny_len, "", SPACER_CNTL, None, None, None),
        ("plt3_auto", txt_len, "Autosize?", RADIO_CNTL, self.list_yes_no, "Yes", True),
        ("plt3_ymin", tiny_len, "Y Min", TEXT_CNTL, None, "20.0", True),
        ("plt3_ymax", tiny_len, "Y Max", TEXT_CNTL, None, "70.0", True),
        ("plt3_spacer2",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("s2s_show", tiny_len, "Show plot", CHOICE_CNTL, self.list_norm_smooth, "Both", True),
        ("s2s_smooth",tiny_len, "Smooth\nSize", CHOICE_CNTL, self.list_of_smooth, "40", True),
        ("s2s_size", tiny_len, "S2S Size", TEXT_CNTL, None, "200", True),
        ]
        
        # data columns for MOD0 panel
        mod0_cols = [
        #(name, len, label, type, vlist, default, cname)
        ("mdl_spacer",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl_date",txt_len_med, "Save Date", TEXT_CNTL_DSP, None, None, None),
        ("mdl_passwd", txt_len, "Password", PASSWD_CNTL, None, None, None),
        ("mdl_spacer2",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl_lot_id", txt_len,"Lot", TEXT_CNTL, None, None, None),
        ("mdl_mirror_id", txt_len, "Mirror", TEXT_CNTL, None, None, None),
        ("mdl_mirror_loc",tiny_len,"Mirror Location", CHOICE_CNTL, self.list_mirror_loc,"Center", None),
        ("mdl_spacer21",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl_cavity_id", txt_len, "Cavity ID", TEXT_CNTL, None, None, None),
        ("mdl_cavity_sn", txt_len, "Cavity S/N", TEXT_CNTL, None, None, None),
        ("mdl_spacer21",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl_spacer21",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl_test_id",txt_len_long, "Test ID", TEXT_CNTL, None, None, None),
        ("mdl_user_id",txt_len,"User ID", TEXT_CNTL, None, None, None),
        ("mdl_align_type", txt_len, "Cavity Align Document", CHOICE_CNTL, self.list_align_type, "Front", None),
        ("mdl_spacer22",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl_vert", txt_len, "Vertical Align", TEXT_CNTL, None, None, None),
        ("mdl_horiz", txt_len, "Horiz Align",TEXT_CNTL, None, None, None),
        ("mdl_wavelength", txt_len, "Wavelength", CHOICE_CNTL, self.list_wavelength_loc, "1601nm", None),
        ("mdl_vpzt", txt_len,"Vpzt", TEXT_CNTL, None, None, None),
        ("mdl_note", (450,100),"Note", NOTE_CNTL, None, None, None),
        ("mdl_spacer3", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl_rd_time", txt_len_smed,"RD Time", TEXT_CNTL_DSP, None, None, None),
        ("mdl_rd_sec", txt_len_smed,"RD/s", TEXT_CNTL_DSP, None, None, None),
        ("mdl_s2s_pct", txt_len_smed, "S2S Pct", TEXT_CNTL_DSP, None, None, None),
        ("mdl_cav_pressure", txt_len_smed, "Pressure", TEXT_CNTL_DSP, None, None, None),
        ("mdl_spacer4", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ]

        # data columns for MOD0 panel
        mod1_cols = [
        #(name, len, label, type, vlist, default, cname)
        ("mdl1_spacer", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("mdl1_spacer2",tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("rd_type", txt_len_med, "Scan type", CHOICE_CNTL, self.list_rdtypes, "Constant laser temp", True),
        ("pl_type", txt_len_med, "Plot type", CHOICE_CNTL, self.list_pltypes, "Plot against time", True),
        ("mdl1_spacer4", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("sweep_min", txt_len, "Sweep Min", TEXT_CNTL, None, "15", True),
        ("sweep_max", txt_len, "Sweep Max",TEXT_CNTL, None, "30", True),
        ("sweep_incr", txt_len, "Sweep Incr", TEXT_CNTL, None, "0.05", True),
        ("spect_sequence", txt_len, "Spectrum Sequence", CHOICE_CNTL, self.list_spect, "1", True),
        ("mdl1_spacer3", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("laser_pwr", txt_len, "Laser Pwr?", CHOICE_CNTL, self.list_yes_no, "Yes", True),
        ("laser_num", txt_len, "Laser Number", CHOICE_CNTL, self.list_lasers, "1", True),
        ("setpoint", txt_len, "Setpoint", TEXT_CNTL, None, "26.0", True),
        ("mdl1_spacer5", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("rd_sample_size", txt_len, "RD Sample Size", TEXT_CNTL, None, "2200", True),
        ("mdl1_spacer6", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ]
        
        ord = 0
        for ploc, clist in [  
                          (PARAMETER, parameter_cols),
                          (PLOT0, plot0_cols), 
                          (PLOT1, plot1_cols), 
                          (PLOT2, plot2_cols),
                          (MOD0, mod0_cols),
                          (MOD1, mod1_cols),
                          ]:

            ord = self._load_cols(ploc, clist, ord)
        
        self.cntls_obj.control_list["rd_time"].font_attr = "bigbold"
        self.cntls_obj.control_list["rd_sec"].font_attr = "bigbold"
        self.cntls_obj.control_list["s2s_pct"].font_attr = "bigbold"
        self.cntls_obj.control_list["cav_pressure"].font_attr = "bigbold"

        self.cntls_obj.control_list["mdl_rd_time"].font_attr = "bigbold"
        self.cntls_obj.control_list["mdl_rd_sec"].font_attr = "bigbold"
        self.cntls_obj.control_list["mdl_s2s_pct"].font_attr = "bigbold"
        self.cntls_obj.control_list["mdl_cav_pressure"].font_attr = "bigbold"
        
        self.cntls_obj.control_list["rd_mode"].font_attr = "bigbold"
        self.cntls_obj.control_list["dither_flag"].font_attr = "bigbold"
            
        self._controls_for_mfg = { 
                      #col_name: (name_in_mfg, type_in_mfg),
                      "mdl_passwd": ("passwd", "char"),
                      "mdl_user_id": ("user", "char"),
                      "mdl_test_id": ("identifier", "char"),
                      "mdl_lot_id": ("bdoc_lot_id", "char"),
                      "mdl_mirror_id": ("bdoc_mirror_id", "char"), 
                      "mdl_mirror_loc": ("bdoc_mirror_loc", "char"), 
                      "mdl_note": ("bdoc_station_note", "char"), 
                      "mdl_rd_time": ("bdoc_rd_time", "float"), 
                      "mdl_rd_sec": ("bdoc_rd_per_sec", "float"), 
                      "mdl_s2s_pct": ("bdoc_shot2shot_pct", "float"),
                      "mdl_cav_pressure": ("bdoc_test_pressure", "float"),
                      "mdl_cavity_id": ("bdoc_cavity_id", "float"),
                      "mdl_cavity_sn": ("bdoc_cavity_sn", "float"),
                      "mdl_vert": ("bdoc_initial_vert", "float"),
                      "mdl_horiz": ("bdoc_initial_horiz", "float"),
                      "mdl_wavelength": ("bdoc_initial_wavelength", "float"),
                      "mdl_vpzt": ("bdoc_initial_vpzt", "int"),
                      "mdl_align_type": ("bdoc_align_type", "char"),
                                  }

        # list of control value to modal dialog control names    
        self.cntl_to_modal_pairs = [
                                    #("mdl_user_id", "user_id"),
                                    ("mdl_lot_id", "lot_id"),
                                    ("mdl_mirror_id", "mirror_id"),
                                    ("mdl_rd_time", "rd_time"),
                                    ("mdl_rd_sec", "rd_sec"),
                                    ("mdl_s2s_pct", "s2s_pct"),
                                    ("mdl_cav_pressure", "cav_pressure"),
                                    ("mdl_cavity_id", "cavity_id"),
                                    ("mdl_cavity_sn", "cavity_sn"),
                                     ]

        
    def _load_cols(self, ploc, clist, ord):
        for val in clist:
#            if val[0] in ("sweep_min", "sweep_max", "sweep_incr"):
#                if self.using_wlm:
#                    continue
#            
            if val[0] in ("spect_sequence", ):
                if not self.using_wlm:
                    continue
        
            ord += 10
    
            if val[3] in (CHOICE_CNTL, RADIO_CNTL):
                vlist = val[4]
                vdft = val[5]
            else:
                vlist = None
                vdft = val[5]
            
            ctl_name = None
            if val[6] == True:
                nme = val[0].upper().replace("_", " ")
                nme = nme.replace("/", "")
                ctl_name = "LAST %s" % (nme)
            elif val[6]:
                ctl_name = val[6]
                
            self.cntls_obj.new_control(
                                        val[0],
                                        order = ord,
                                        control_size = val[1], 
                                        label = val[2], 
                                        ctl_name = ctl_name,
                                        type = val[3], 
                                        location = ploc,
                                        values_list = vlist,
                                        default = vdft
                                      )
        return ord
        
        
    def _init_process_parms(self):
        '''
        initialize process_parms
        '''
        self.process_parms = {
                              "column_list": None,
                              "html_source": {},
                              "plot_fig": {},
                              "plot_data": {},
                              }
        
        self.ptype_dict = {}
        self.ptype_list = []
        self._ptype = {}
        
        self.plot_name = {
                          0: "Plot 1",
                          1: "Plot 2",
                          2: "Plot 3",
                          }

        self.lock_yaxis = {
                           # (T/F, min_lim, max_lim)
                           0: (None, None, None),
                           1: (None, None, None),
                           2: (None, None, None),
                           }
        
        self._collecting = {
                          0: None,
                          1: None,
                          2: None,
                            }
        
        self._cur_values = {}
        self._cur_values["laser_num"] = 0
        self._cur_values["laser_pwr"] = "No"
        self._cur_values["main_plot"] = None
        self._cur_values["analyzer_status"] = None
        self._cur_values["rd_mode"] = None
        self._cur_values["rd_type"] = None
        self._cur_values["pl_type"] = None
        self._cur_values["dither_flag"] = None
        self._cur_values["setpoint"] = None
        self._cur_values["sweep_min"] = None
        self._cur_values["sweep_max"] = None
        self._cur_values["sweep_incr"] = None
        self._cur_values["spect_sequence"] = None
        self._cur_values["rd_threshold"] = None
        
        self._driver_cntl_list = [
                                    "laser_num", 
                                    "laser_pwr", 
                                    "rd_type", 
                                    "pl_type", 
                                    "setpoint", 
                                    "sweep_min", 
                                    "sweep_max", 
                                    "sweep_incr", 
                                    ]
        if self.using_wlm:
            self._driver_cntl_list.append("spect_sequence")
            
            
        self._fitting_requests = {
            #keyname: (current_value, register),
            "rd_sample_size": (
                               None, 
                               interface.RDFITTER_NUMBER_OF_POINTS_REGISTER
                               ),
#            "rd_threshold": (
#                             None, 
#                             interface.SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER
#                             ),
                                      }
        
        self._plots_with_mean = []   
        self._plots_with_yloss = []
        
        if self.using_wlm:
            name = "ringdown time vs waveNumber"
            xy = ("waveNumber", "uncorrectedAbsorbance")
            self.ptype_list.append(name)
            self.ptype_dict[name] = xy
            self._plots_with_yloss.append(name)

        name = "ringdown time vs temperature"
        xy = ("laserTemperature", "uncorrectedAbsorbance")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
        self._plots_with_yloss.append(name)
            
        name = "ringdown time vs time"
        xy = ("timestamp", "uncorrectedAbsorbance")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
        self._plots_with_mean.append(name)
        self._plots_with_yloss.append(name)
        self._cur_values["main_plot"] = name
            
        name = "ringdown time vs ratio1"
        xy = ("ratio1", "uncorrectedAbsorbance")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
        self._plots_with_yloss.append(name)
            
        name = "ringdown time vs ratio2"
        xy = ("ratio2", "uncorrectedAbsorbance")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
        self._plots_with_yloss.append(name)


        if self.using_wlm:
            name = "ratio1 vs waveNumber"
            xy = ("waveNumber", "ratio1")
        else:
            name = "ratio1 vs laserTemperature"
            xy = ("laserTemperature", "ratio1")

        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
            
        if self.using_wlm:
            name = "tunerValue vs waveNumber"
            xy = ("waveNumber", "tunerValue")
        else:
            name = "tunerValue vs laserTemperature"
            xy = ("laserTemperature", "tunerValue")

        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
            
        name = "tunerValue vs timestamp"
        xy = ("timestamp", "tunerValue")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
        self._plots_with_mean.append(name)

        name = "tunerValue vs ratio1"
        xy = ("ratio1", "tunerValue")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
            
        name = "tunerValue vs ratio2"
        xy = ("ratio2", "tunerValue")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
            
        if self.using_wlm:
            name = "waveNumber vs timestamp"
            xy = ("timestamp", "waveNumber")
        else:
            name = "waveNumber vs timestamp"
            xy = ("timestamp", "waveNumber")

        self.ptype_list.append(name)
        self.ptype_dict[name] = xy

        self._plots_with_mean.append(name)

        if self.using_wlm:
            name = "fineLaserCurrent vs waveNumber"
            xy = ("waveNumber", "fineLaserCurrent")
        else:
            name = "fineLaserCurrent vs waveNumber"
            xy = ("waveNumber", "fineLaserCurrent")

        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
            
        name = "fineLaserCurrent vs timestamp"
        xy = ("timestamp", "fineLaserCurrent")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
            
        self._plots_with_mean.append(name)

        name = "Ringdowns"
        xy = ("point", "ringdown")
        self.ptype_list.append(name)
        self.ptype_dict[name] = xy
        
        name = "Shot to Shot"
        xy = ("timestamp", "shot2shot")
        #self.ptype_list.append(name)
        self.ptype_dict[name] = xy
        
        self.freeze = {
                        0: None,
                        1: None,
                        2: None,
                        }
         
        self.auto_freeze = {
                        0: None,
                        1: None,
                        2: None,
                        }
        

        self._running_stats_refresh_count = 1000
        self._running_stats_current_count = 0
        self._running_stats_dict = {}
        for ii in interface.STREAM_MemberTypeDict.keys():
            self._running_stats_dict[ii] = {
                                           "avg": None,
                                           "min": None,
                                           "max": None,
                                           "curr_array": None,
                                           }
    
        self._fig = {}
        self._axes = {}
        self._plot = {}
        
    def after_config_init(self):
        '''
        any follow up configuration after controller initialization
        '''
        for name, cntlobj in self.cntls_obj.control_list.iteritems():
            setattr(self, "%s_cntlobj" % (name), cntlobj)


        self._auto_cntl = {
                           0: self.plt1_auto_cntlobj,
                           1: self.plt2_auto_cntlobj,
                           2: self.plt3_auto_cntlobj,
                           }
        self._ymin_cntl = {
                           0: self.plt1_ymin_cntlobj,
                           1: self.plt2_ymin_cntlobj,
                           2: self.plt3_ymin_cntlobj,
                           }
        self._ymax_cntl = {
                           0: self.plt1_ymax_cntlobj,
                           1: self.plt2_ymax_cntlobj,
                           2: self.plt3_ymax_cntlobj,
                           }
        self._auto_current = {
                           0: None,
                           1: None,
                           2: None,
                           }
        self._ymin_current = {
                           0: None,
                           1: None,
                           2: None,
                           }
        self._ymax_current = {
                           0: None,
                           1: None,
                           2: None,
                           }
        self.ymean_smooth_ctl = {
                                 0: (None,0),
                                 1: (None,0),
                                 2: (None,0),
                                 }
        
        self._initial_plot = {
                               0: None,
                               1: None,
                               2: None,
                               }
        

        return
           
    def process_source(self, source_file=None, brief_html = None):
        '''
        process the passed source file - Not required for Live
        '''
        self._status = "working"
        self._init_process_parms()
        self.process_parms["html_source"][0] = self._build_html()
        self.process_parms["column_list"] = self.ptype_list
        self.process_parms[STATUS] = OK
        self._status = ""
                

    def _build_html(self, brief_html = None):
        '''
        build the html source file
        '''
        line = "<HTML><BODY bgcolor='%s'>" % (MAIN_BACKGROUNDCOLOR)
        line += "<H2 align='center'>%s</H2>" % (self._title)
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                    '98%', 
                                                    PNL_TBL_BACKGROUNDCOLOR
                                                                )
        line += "</table>"
        line += "</td></tr>"
        line += "<tr><td><p></td><tr/>"
        line += "</table>"

        line += "<tr><td align='center'>"
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                        '98%', 
                                                        PNL_TBL_BORDERCOLOR
                                                                )

        line += "<th bgcolor='%s'><b>" %(PNL_TBL_HEADINGCOLOR)
        line += "time"
        line += "</b></th>"

        line += "<th bgcolor='%s'><b>" %(PNL_TBL_HEADINGCOLOR)
        line += "message"
        line += "</b></th>"
        
        for ii in range(len(self._message_array), 0, -1):
            tme, msg = self._message_array[ii - 1]

            line += "<tr>"
            line += "<td bgcolor='%s' width='%s'>" % (
                                                      PNL_TBL_BACKGROUNDCOLOR,
                                                      '20%'
                                                      )
            line += "%s" % (tme.strftime("%a, %b %d, %Y, %H:%M:%S")) 
            line += "</td>"
            
            line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)
            line += "%s" % (msg) 
            line += "</td>"
            line += "</tr>"
            
        line += "</table>"
        line += "</td></tr>"
        
        line += "<table><tr><td align='right'>&copy; 2010 Picarro Inc.</td></tr></table>"
        line += "</BODY></HTML>"
        
        return line
        
    def generate_plot(self, plot_parameters, notebook=None, pltidx=None):
        '''
        generate a live plot 
          plot_parameters 
              "combine_data": combine_data,
              "p1_type": p1_type,
              "p2_type": p2_type,
              "p3_type": p3_type,
              "p4_type": p4_type,
              "points": points
              "export_data": True_or_None, #optional
        '''
        self._status = "working"
        
        self._bg = None
        self._regenerate_plot = None
        self.ringdown_plot_active = None
        #self._current_xmean_small = {}
        self._current_xmean_large = {}
        self._current_ymean_small = {}
        self._current_ymean_large = {}
        self._old_title = {
                           0: None,
                           1: None,
                           2: None,
                           }        
        self.ymean_smooth_ctl = {
                                 0: (None,0),
                                 1: (None,0),
                                 2: (None,0),
                                 }
        
        self.current_number_ringdowns = 0
        self.current_rdt = 0.0
        self.current_rd_second = None
        self.current_start_time = None
        self.first_start_time = None
        self.latest_end_time = None
        self.current_s2s = None
        self.stats_array = []


        self._ptype = {}
        self._ptype[0] = self.p1_type_cntlobj.get_value()
        self._ptype[1] = self._cur_values["main_plot"]
        self._ptype[2] = "Shot to Shot"

        self._plot_minmax_switch()
        
        self.ringdown_plot_active = None
        self._regenerate_plot = None

        try:
            s2s_size = int(plot_parameters["s2s_size"])
        except:
            s2s_size = 200
            
        self.s2s_size = s2s_size
        
        try:    
            points = int(self.points_cntlobj.get_value())
        except:
            points = 5000
            
            
        self._points = points
        
        self.points_cntlobj.set_value("%s" % (points))
        self.s2s_size_cntlobj.set_value("%s" % (s2s_size))
        
        
        first_axes = None
        
        self.yval = {}
        self.xval = {}

        self.yval_s2s = {}

        self.ymean_small_yval = {}
        self.ymean_small_xval = {}

        self.ymean_smooth_yval = {}
        self.ymean_smooth_xval = {}

        ncol = 0
        self._initial_yval = numpy.array([])
        self._initial_xval = numpy.array([])
        
        for cidx in range(0,3):
            self._reset_plot_arrays(cidx)
            if self._ptype[cidx] == "Ringdowns":
                self.ringdown_plot_active = True
            

        if not self.no_listener_queue:
            if not self._load_plot_values():
                print datetime.datetime.now(), "NO VALUES!!! WHY???"
            #self._status = ""
            #return

        for cidx in range(0,3):
            if not cidx in self._fig.keys():
                self._fig[cidx]=Figure(frameon=True,facecolor=self.plot_facecolor)
                self._fig[cidx].subplots_adjust(left=0.125,right=0.98)

            else:
                if self._ptype[cidx] == CHOICE_NONE:
                    if cidx in self._axes.keys():
                        self._axes[cidx].cla()
                    self._fig[cidx].clf()
                    
        first_axes = None
        plot_cycle = 0
        num_plots = 0
        
        for cidx in range(0,3):
            self._initial_plot[cidx] = True
            #print "setting initial_plot to true for cidx", cidx
            if not self._ptype[cidx] == CHOICE_NONE:
                num_plots += 1
                
                # when not using the queue, initialize xy values
                # if we have not yet started collecting any data
                if self.no_listener_queue:
                    if not self.collecting_data:
                        x,y = self.ptype_dict[self._ptype[cidx]]
                        if x == "timestamp":
                            xval = date2num(datetime.datetime.now())
                        else:
                            xval = 0
                        yval = 0
                        
                        self.xval[cidx] = [xval]
                        self.yval[cidx] = [yval]
                else:
                    x,y = self.ptype_dict[self._ptype[cidx]]
                    if x == "timestamp":
                        xval = date2num(datetime.datetime.now())
                    else:
                        xval = 0
                    yval = 0
                    
                    self.xval[cidx] = [xval]
                    self.yval[cidx] = [yval]
                    
        last_plot_idx = 0
        
        for cidx in range(0,3):
            cbidx = cidx
                
            if not self._ptype[cidx] == CHOICE_NONE:
                last_plot_idx = cidx
                subplt = "111"

                if not cidx in self._axes.keys():
                    if plot_cycle == 0:
                        self._axes[cidx] = self._fig[cbidx].add_subplot(subplt)
                        first_axes = self._axes[cidx]
                    else:
                        self._axes[cidx] = self._fig[cidx].add_subplot(subplt)

                self._plot[cidx] = self._do_plot(
                                              self._axes[cidx], 
                                              self.xval[cidx], 
                                              self.yval[cidx], 
                                              self._ptype[cidx]
                                              )
                
                if self._ptype[cidx] in self._plots_with_mean:
                    self._plot[cidx+10] = self._do_plot(
                                              self._axes[cidx], 
                                              self.xval[cidx][0:1], 
                                              self.ymean_small_yval[cidx],
                                              self._ptype[cidx],
                                              None,
                                              "mean"
                                                  )
                elif self._ptype[cidx] == "Shot to Shot":
                    self._plot[cidx+10] = self._do_plot(
                                              self._axes[cidx], 
                                              self.xval[cidx][0:1], 
                                              self.ymean_small_yval[cidx],
                                              self._ptype[cidx],
                                              None,
                                              "s2s"
                                                  )
                    
                
                plot_cycle += 1
                
        if notebook:
            if pltidx:
                for cidx in range(0,3):
                    if not self._ptype[cidx] == CHOICE_NONE:
                        self.plot_name[cidx] = self._ptype[cidx]
                        notebook.SetPageText(
                                             pltidx[cidx], 
                                             self._ptype[cidx]
                                             )
                        #print "setting the name", self._ptype[cidx]
                    else:
                        self.plot_name[cidx] = "Plot%s" % (cidx + 1)
                        notebook.SetPageText(
                                             pltidx[cidx], 
                                             self.plot_name[cidx]
                                             )
                        #print "unsetting the name", self._ptype[cidx]
       
        self._bg = None
        self.collecting_data = True

        if not self.no_listener_queue:
            self._get_data()

        for cidx in range(0,3):
            self.process_parms["plot_fig"][cidx] = self._fig[cidx]
            self.process_parms["plot_data"][cidx] = None

        self._plot_was_generated = True
        
        self._status = ""
    
    def _do_plot(self, plt, xval, yval, ptype, combine=None, extra=None):
        '''
        Do the plot
        '''
        if extra == "mean":
            marker = "%s%s" %( 
                              MARKER_COLORS_DICT["blue"],
                              MARKER_POINTS_DICT["solid line"]
                              )
        elif extra == "s2s":
            marker = "%s%s" %( 
                              MARKER_COLORS_DICT["blue"],
                              MARKER_POINTS_DICT["circle marker"]
                              )
        else:
            marker = "%s%s" %( 
                              MARKER_COLORS_DICT["red"],
                              MARKER_POINTS_DICT["point marker"]
                              )

        x,y = self.ptype_dict[ptype]

        if not combine:
            if not extra == "mean":
                
                if x == "timestamp":
                    if self.show_time:
                        plt.set_xticklabels(xval, visible=True, size="medium")
                else:
                    plt.set_xticklabels(xval, visible=True, size="medium")
                
        if x == "timestamp":
            #rtn_plot, = plt.plot_date(xval, yval, marker, label=ptype)
            if self.show_time:
                plt.xaxis.set_major_formatter(
                     DateFormatter('%H:%M:%S\n%Y/%m/%d', 
                                            tz=None)
                                                    )
            else:
                #xval = range(len(yval))
                plt.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
                
        elif ptype == "Ringdowns":
            plt.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        else:
            plt.xaxis.set_major_formatter(FormatStrFormatter('%.5f'))

        if ptype == "Ringdowns":
            plt.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        else:
            plt.yaxis.set_major_formatter(FormatStrFormatter('%.5f'))

        for tl in plt.get_yticklabels():
            tl.set_fontsize('medium')
        
        if not len(xval) == len(yval):
            xval = numpy.array([])
            yval = numpy.array([])
        rtn_plot, = plt.plot(xval, yval, marker, label=ptype, markeredgecolor='black')
        
        return rtn_plot
                
    def save_fig(self, plotidx, savefile):
        '''
        save the plot figure into savefile (a pdf or png file)
        '''
        if plotidx in self._fig.keys():
            if plotidx in self._plot.keys():
                self._fig[plotidx].savefig(savefile)
                xydata = self._plot[plotidx].get_xydata()
    
    def preserve_plot_values(self):
        '''
        in preparation for save_to_db, get the XY values from the plot figure 
        '''
        self._preserve_xy = {}
        for cidx in range(0,3):
            self._preserve_xy[cidx] = None
            if cidx in self._ptype:
                if not self._ptype[cidx] in (CHOICE_NONE, ):
                    self._preserve_xy[cidx] = self._plot[cidx].get_xydata()
        
        
    def save_to_database(self):
        '''
        save buildstation state and plot to mfg database
        '''  
        rtn_code = "OK"
        
        mfg_parm_dict = {}
        
        for cname, dbinfo in self._controls_for_mfg.iteritems():
            control = self.cntls_obj.control_list[cname]
            mfgname, mfgtype = dbinfo
            
            mfgvalue = None
            if mfgtype == "float":
                val = control.get_value()
                if cname == "mdl_cav_pressure":
                    val = val.rstrip("torr")
                    
                try:
                    mfgvalue = float(val)
                except:
                    mfgvalue = None
            elif mfgtype == "int":
                val = control.get_value()
                try:
                    mfgvalue = int(val)
                except:
                    mfgvalue = None
            else:
                mfgvalue = control.get_value()
            
            if mfgvalue:   
                mfg_parm_dict[mfgname] = mfgvalue

        str = ""
        for cname, control in self.cntls_obj.control_list.iteritems():
            if (control.location == PARAMETER 
                and control.ctl_name):
                
                str+= "%s: %s\n" % (control.ctl_name, control.get_value())
                
        if not str == "":
            mfg_parm_dict["bdoc_station_info"] = str
            
            
        mfg_parm_dict["bdoc_doc_name"] = "%s Mirror Data" % (
                                             mfg_parm_dict["bdoc_align_type"]
                                                                         )
        mfg_parm_dict["bdoc_station_id"] = "buildstation 4"
        
        for cidx in range(0,3):
            if not self._ptype[cidx] in (CHOICE_NONE, ):
                mfg_parm_dict["segment_name"] = self._ptype[cidx]
                xynumpy = self._preserve_xy[cidx]
                xy_array = []
                for nx, ny in xynumpy:
                    xval = float(nx)
                    yval = float(ny)
                    xy_array.append((xval, yval))
                    
                mfg_parm_dict["xy_narray"] = None
                mfg_parm_dict["xy_narray"] = xy_array
                #mfg_parm_dict["xy_narray"] = None
                #mfg_parm_dict["xy_narray"] = self._preserve_xy[cidx]
                #xynarray = xmlrpclib.Binary(self._preserve_xy[cidx])

                x,y = self.ptype_dict[self._ptype[cidx]]
                mfg_parm_dict["x_label"] = x
                mfg_parm_dict["y_label"] = y
                
                uri_type, sep, uri_host = self.mfg_uri.rpartition("://")
                full_uri = "%s%s%s:%s@%s" % (
                                         uri_type,
                                         sep,
                                         self.mdl_user_id_cntlobj.get_value(),
                                         self.mdl_passwd_cntlobj.get_value(),
                                         uri_host
                                             ) 
                
                self.XMLProxy = xmlrpclib.ServerProxy(full_uri)

                try:
                    rtn_value = self.XMLProxy.add_buildstation_test_data(
                                                                     mfg_parm_dict
                                                                         )
                except:
                    msg = "MFG Database is currently not available."
                    msg += "\nPlease try again later."
                    return msg
                
                if not rtn_value == "OK":
                    print datetime.datetime.now(), "return", rtn_value
                    
                    rtn_code = "Error while saving to the MFG Database. " 
                    rtn_code += "This data was not saved."
                    try:
                        if "error" in rtn_value.keys():
                            rtn_code += "\n%s" % (rtn_value["error"])
                            if "missing" in rtn_value.keys():
                                rtn_code += "\n%s" % (rtn_value["missing"])
                    except:
                        rtn_code = "Error while saving to the MFG Database. "
                        rtn_code += "This data was not saved."
                    
        
        return rtn_code
        
    def next_from_buffer_process(self, 
                                 notebook=None, 
                                 pltidx=None, 
                                 canvas=None, 
                                 restart=None,
                                 refresh_layout=None,
                                 fig_act=None,
                                 cntl_values=None):
        '''
        next usage from buffer
        '''
        self._measure_system("entry")
        rtn_val = None
        
        if self._status == "working":
            self._measure_system("exit")
            return rtn_val
        
        #Check for macro
        if self._check_and_run_macro():
            if self._regenerate_plot:
                print "time to regenerate!!"
                control_dict = {}
                for key in self._driver_cntl_list:
                    control_dict[key] = self.cntls_obj.control_list[key].get_value()
                self.generate_plot(control_dict, notebook, pltidx)
                for cidx in range(0,3):
                    self._reset_plot_arrays(cidx)
                    if canvas:
                        try:
                            canvas[cidx].draw()
                        except:
                            pass

            return rtn_val
        
        
        #Check/process dither requests
        self._dither_test()
        
        #Check/process dither requests
        self._rd_threshold_test()
        
        #Check/process mode requests
        self._mode_test()
        
        #Check/process changes in controls
        if cntl_values:
            self._evaluate_control_changes()
            if self._regenerate_plot:
                print "time to regenerate!!"
                self.generate_plot(cntl_values, notebook, pltidx)
                for cidx in range(0,3):
                    self._reset_plot_arrays(cidx)
                    if canvas:
                        try:
                            canvas[cidx].draw()
                        except:
                            pass
        
        #if reset flag sent, reset the requested plot array
        if restart == "all":
            for cidx in range(0,3):
                self._reset_plot_arrays(cidx)
        else:
            if not restart == None:
                cidx = restart
                self._reset_plot_arrays(cidx)

        #get data
        if not self.no_listener_queue:
            if not self._load_plot_values():
                self._measure_system("exit_empty")
                return rtn_val

        # Shot 2 shot is the third plot. We only update it about every 1 second
        self.plot_ts = timestamp.getTimestamp()
        pctr = self.plot_ts - self.last_s2s_ts
        pmax = 2
        pstart = 1
        if pctr >= 1000:
            self.last_s2s_ts = self.plot_ts
            pmax = 3
            pstart = 0
            self._plot_smooth()

        #plot data
        for cidx in range(pstart,pmax):
            self._set_and_draw(cidx, fig_act, canvas)
        
        #return
        self._measure_system("exit")
        return rtn_val


    def _set_and_draw(self, cidx, fig_act, canvas):
        '''
        set xy data, and draw the plot
        '''
        if self._ptype[cidx] == CHOICE_NONE:
            return
        
        if fig_act:
            if cidx in fig_act.keys(): 
                auto = fig_act[cidx].autoscale.values()
                if not auto or auto[0]:
                    self._autoscale(cidx, fig_act[cidx]) 
                    if self.auto_freeze[cidx]:
                        self.auto_freeze[cidx] = None
                else:
                    self.auto_freeze[cidx] = True

        else:
            self._autoscale(cidx, None)

        if self.freeze[cidx] or self.auto_freeze[cidx]:
            return
        
        self._plot[cidx].set_ydata(self.yval[cidx])
        self._plot[cidx].set_xdata(self.xval[cidx])

        self._minmax_switch(cidx)
        
        #show Averages in the title
        if not self._ptype[cidx] == "Ringdowns":
            self._show_averages(cidx)

        #show mean as second plot within figure
        if self._ptype[cidx] in self._plots_with_mean:
            self._show_mean(cidx)

        #show smooth as second plot within figure
        if self._ptype[cidx] == "Shot to Shot":
            self._show_smooth(cidx)
        
        if canvas:
            try:
                canvas[cidx].draw()
            except:
                pass


    def _measure_system(self, req=None):
        if req == "entry":
            self.entry_ts = timestamp.getTimestamp()
            
        if req == "exit":
            self.exit_ts = timestamp.getTimestamp()
            if self.SHOW_MEASURE:
                print datetime.datetime.now(), "data: %s  estart: %s  eprocess: %s" % (
                                                  self._last_data_len,
                                                  self.entry_ts - self.last_time,
                                                  self.exit_ts - self.entry_ts,
                                                  )
                self._last_data_len = 0
            
            
        if req == "exit_empty":
            self.exit_ts = timestamp.getTimestamp()
            if self.SHOW_MEASURE:
                print datetime.datetime.now(), "no data  estart: %s  eprocess: %s" % (
                                                  self.entry_ts - self.last_time,
                                                  self.exit_ts - self.entry_ts
                                                  )
            
            self.last_time = timestamp.getTimestamp()

       
        if req == "rdfilter":
            old_rdfilter_ts = self.rdfilter_ts
            self.rdfilter_ts = timestamp.getTimestamp()
            if self.SHOW_MEASURE:
                print datetime.datetime.now(), "data: %s  rdprocess: %s" % (
                                                  self._last_data_len,
                                                  self.rdfilter_ts - old_rdfilter_ts,
                                                  )
                self._last_data_len = 0
            
    
    def _show_averages(self, cidx):
        '''
        show averages in the title area of the plot
        '''
        new_title = "Avg 1000: %.5f   Avg 100: %.5f" % (
                          self._current_ymean_large[cidx],
                          self._current_ymean_small[cidx],
                                                      )

        if not new_title == self._old_title[cidx]:
            self._old_title[cidx] = new_title
            self._axes[cidx].set_title(
                                       new_title, 
                                       visible=True,
                                       size="small"
                                       )

    def _show_mean(self, cidx):
        '''
        show mean as second plot
        '''
        if len(self.ymean_small_yval[cidx]) > 0:
            if (cidx+10) in self._plot.keys():
                self._plot[cidx+10].set_ydata(
                              self.ymean_small_yval[cidx]
                                              )
                self._plot[cidx+10].set_xdata(
                              self.ymean_small_xval[cidx]
                                          )

    
    def _show_smooth(self, cidx):
        '''
        show smooth as second plot
        '''
        cursmooth, curcount = self.ymean_smooth_ctl[2]
        if self.s2s_show_cntlobj.get_value() in ("Both", "Normal"):
            self._plot[cidx].set_visible(True)
        else:
            self._plot[cidx].set_visible(False)
        
        if self.s2s_show_cntlobj.get_value() in ("Both", "Smooth"):
            self._plot[cidx+10].set_visible(True)
        else:
            self._plot[cidx+10].set_visible(False)
        
        
        if len(self.ymean_smooth_yval[cidx]) > 0:
            if (cidx+10) in self._plot.keys():
                self._plot[cidx+10].set_ydata(
                              self.ymean_smooth_yval[cidx]
                                              )
                
                self._plot[cidx+10].set_xdata(
                              self.ymean_smooth_xval[cidx]
                                                )
        
    def _reset_plot_arrays(self, cidx):
        self.yval[cidx] = numpy.array([])
        self.xval[cidx] = numpy.array([])
        self.yval_s2s[cidx] = numpy.array([])
        
        self.ymean_small_yval[cidx] = numpy.array([])
        self.ymean_small_xval[cidx] = numpy.array([])

        self.ymean_smooth_yval[cidx] = numpy.array([])
        self.ymean_smooth_xval[cidx] = numpy.array([])
        
        self._current_ymean_small[cidx] = 0
        self._current_xmean_large[cidx] = 0
        self._current_ymean_large[cidx] = 0
        

    def _autoscale(self, cidx, fig_act):
        if not self._collecting[cidx]:
            return

        if fig_act:
            fig_act.autoscale[self._axes[cidx]] = True
        
        xmin = 0.0
        xmax = 0.0

        x,y = self.ptype_dict[self._ptype[cidx]]

#        if ((not self.show_time)
#             and (x == "timestamp")):
#            newmin = -1
#            newmax = len(self.yval[cidx]) + 1
#        else:
        if len(self.xval[cidx]) > 0:
            xmin = numpy.min(self.xval[cidx])
            xmax = numpy.max(self.xval[cidx])

        newmin, newmax = self._calc_new_minmax(
                                            xmin,
                                            xmax,
                                            100.0
                                                )

        self._axes[cidx].set_xlim(newmin, newmax)
        
        
        try:
            self._setup_ticklabels(
                               self._axes[cidx], 
                               self._ptype[cidx], 
                               self.xval[cidx]
                               )
        except:
            pass

        lock, ymin, ymax = self.lock_yaxis[cidx]
        if lock == "start" or lock == None:
            
            #ymin = 0.0
            #ymax = 0.0
            
            if ymin == None or lock == None:
                if len(self.yval[cidx]) > 0:
                    ymin = numpy.min(self.yval[cidx])
                
            if ymax == None or lock == None:
                if len(self.yval[cidx]) > 0:
                    ymax = numpy.max(self.yval[cidx])

            
            if ymin:
                if ymax:
                    newmin, newmax = self._calc_new_minmax(
                                                        ymin,
                                                        ymax,
                                                        20.0
                                                            )
                    
                    if self._ptype[cidx] == "Ringdowns":
                        if newmax > 16385:
                            newmax = 16385
                            
                    #if cidx == 2:
                    #    print newmin, newmax
                    
                    self._axes[cidx].set_ylim(newmin, newmax)
                    lock = "locked"

    def _setup_ticklabels(self, axes, ptype, xval):
        axes.grid(
                 True, 
                 linestyle='-', 
                 which='major', 
                 color='lightgrey', 
                 alpha=0.5
                 )

        x,y = self.ptype_dict[ptype]

        if x == "timestamp":
            if self.show_time:
                axes.set_xticklabels(
                                            xval, 
                                            visible=True,
                                            rotation=self.lbl_rotate,
                                            size="medium"
                                                )
        else:
            axes.set_xticklabels(
                                        xval, 
                                        visible=True,
                                        rotation=self.lbl_rotate,
                                        size="medium"
                                            )
            
        if x == "timestamp":
#            pass
            if self.show_time:
                axes.xaxis.set_major_formatter(
                     DateFormatter('%H:%M:%S\n%Y/%m/%d', 
                                            tz=None)
                                                    )
            else:
                axes.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
                
        elif ptype == "Ringdowns":
            axes.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
            
        else:
            axes.xaxis.set_major_formatter(FormatStrFormatter('%.5f'))

        if ptype == "Ringdowns":
            axes.yaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        else:
            axes.yaxis.set_major_formatter(FormatStrFormatter('%.5f'))

        for tl in axes.get_yticklabels():
            tl.set_fontsize('medium')
        
        
    def _calc_new_minmax(self, ymin, ymax, factor=3.0):
        '''
        calculate new min/max values
        '''
        buff = ((ymax - ymin) / factor )
        newmin = ymin - buff
        newmax = ymax + buff
        
        return newmin, newmax
                                

    def _load_plot_values(self, tmp=None):
        '''
        load plot xy array from queue
        '''
        if not tmp:
            tmp = self._get_data()
        
        if len(tmp[0]) == 0:
            if len(tmp[1]) == 0:
                if len(tmp[2]) == 0:
                    return None

        yv = {}
        xv = {}
        numelm = {}

        pv_now_ts = timestamp.getTimestamp()
        
        for cidx in range(0,3):
            if self._ptype[cidx] == "Ringdowns":
                self._collecting[cidx] = True
                data = self._get_rd_waveform()
                self.yval[cidx] = numpy.array(data)
                self.xval[cidx] = numpy.array(range(len(self.yval[cidx])))
                continue
            
            dctr = 0
             
            for xval, yval in tmp[cidx]:
                if self._ptype[cidx] == "Shot to Shot":
                    self.yval_s2s[cidx] = numpy.append(self.yval_s2s[cidx], [yval])
                    self._collecting[cidx] = None
                    #if len(self.yval_s2s[cidx]) > self.s2s_size:
                    self._collecting[cidx] = True
                    if self.s2s_size >= self._points:
                        startp = 0
                    else:
                        startp = len(self.yval_s2s[cidx]) - self.s2s_size
                    
                    mean_s2s = numpy.mean(self.yval_s2s[cidx][startp:])
                    #std_s2s = numpy.std(self.yval_s2s[cidx][startp:], ddof=1)
                    std_s2s = numpy.std(self.yval_s2s[cidx][startp:])
                    s2s = std_s2s / mean_s2s * 100
                    self.current_s2s = s2s
                   
                    self.yval[cidx] = numpy.append(self.yval[cidx], [s2s])
                    self.xval[cidx] = numpy.append(self.xval[cidx], [xval])

                else:
                    self._collecting[cidx] = True
                    
                    self.yval[cidx] = numpy.append(self.yval[cidx], [yval])
                    self.xval[cidx] = numpy.append(self.xval[cidx], [xval])
                
                if self._initial_plot[cidx]:
                    self._initial_plot[cidx] = None
                    self.xval[cidx] = self.xval[cidx][1:]
                    self.yval[cidx] = self.yval[cidx][1:]
                    #print "skipping first for cidx", cidx
                
                if len(self.xval[cidx]) > self._points:
                    startp = len(self.xval[cidx]) - self._points
                    tmp_array = self.xval[cidx][startp:]
                    self.xval[cidx] = numpy.array(tmp_array)
                    
                    tmp_array = self.yval[cidx][startp:]
                    self.yval[cidx] = numpy.array(tmp_array)
                    
                    if self._ptype[cidx] == "Shot to Shot":
                        tmp_array = self.yval_s2s[cidx][startp:]
                        self.yval_s2s[cidx] = numpy.array(tmp_array)

                if self._ptype[cidx] == "Shot to Shot":
                    smsize, smcount = self.ymean_smooth_ctl[cidx]
                    if smsize:
                        if smcount > smsize:
                            smcount = 0
                            
                            if len(self.yval[cidx]) > smsize:
                                startp2 = len(self.yval[cidx]) - smsize
                                smooth_mean = numpy.mean(numpy.mean(self.yval[cidx][startp2:]))
                            else:
                                smooth_mean = self._current_ymean_small[cidx]
                            
                            self.ymean_smooth_xval[cidx] = numpy.append(
                                                              self.ymean_smooth_xval[cidx], 
                                                              [xval]
                                                                       )
                            self.ymean_smooth_yval[cidx] = numpy.append(
                                                          self.ymean_smooth_yval[cidx], 
                                                          [smooth_mean]
                                                                      )                
                            
                            
                            if len(self.ymean_smooth_yval[cidx]) > self._points:
                               startp = len(self.ymean_smooth_yval[cidx]) - self._points
                            
                               tmp_array = self.ymean_smooth_yval[cidx][startp:]
                               self.ymean_smooth_yval[cidx] = numpy.array(tmp_array)

                               tmp_array = self.ymean_smooth_xval[cidx][startp:]
                               self.ymean_smooth_xval[cidx] = numpy.array(tmp_array)
                             
                        else:
                            smcount += 1
                        
                        self.ymean_smooth_ctl[cidx] = (smsize, smcount)

            if len(self.xval[cidx]) > 100:
                startp = len(self.xval[cidx]) - 100
                #self._current_xmean_small[cidx] = numpy.mean(self.xval[cidx][startp:])
                self._current_ymean_small[cidx] = numpy.mean(self.yval[cidx][startp:])

                
                self.ymean_small_xval[cidx] = numpy.append(
                                                   self.ymean_small_xval[cidx], 
                                                   [xval]
                                                            )
                self.ymean_small_yval[cidx] = numpy.append(
                                               self.ymean_small_yval[cidx], 
                                               [self._current_ymean_small[cidx]]
                                                           )                

                if len(self.ymean_small_yval[cidx]) > self._points:
                    startp = len(self.ymean_small_yval[cidx]) - self._points
                    
                    tmp_array = self.ymean_small_yval[cidx][startp:]
                    self.ymean_small_yval[cidx] = numpy.array(tmp_array)

                    tmp_array = self.ymean_small_xval[cidx][startp:]
                    self.ymean_small_xval[cidx] = numpy.array(tmp_array)
                    
            if len(self.xval[cidx]) > 1000:
                startp = len(self.xval[cidx]) - 1000
                self._current_xmean_large[cidx] = numpy.mean(self.xval[cidx][startp:])
                self._current_ymean_large[cidx] = numpy.mean(self.yval[cidx][startp:])

        if "start_time" in tmp:
            self._load_stats(tmp["stats"])
            if not self.first_start_time:
                self.first_start_time = tmp["start_time"]

            if not self.current_start_time:
                self.current_start_time = tmp["start_time"]
            
            self.latest_end_time = tmp["end_time"]
            self.current_number_ringdowns += tmp["number_ringdowns"]
            self.current_rdt = tmp["avg_ringdown"]
            
            if self.no_listener_queue:
                self.show_stats(tmp)
            else:
                elapsed_time = pv_now_ts - self.last_stats_ts
                if elapsed_time >= 1000:
                    self.last_stats_ts = pv_now_ts
                    self.show_stats(tmp)
                
        return True

    def show_stats(self, tmp):
        '''
        show rd stats on the panel
        '''
        self.current_rd_second = self._calc_rd_per_second()
        self.current_number_ringdowns = 0
        self.current_start_time = tmp["start_time"]
        
        self.rd_time_cntlobj.set_value("%.5f" % (self.current_rdt) )
        self.rd_sec_cntlobj.set_value("%.2f" % (self.current_rd_second) )
        self.s2s_pct_cntlobj.set_value("%.5f" % (self.current_s2s) )
        
        sensor_data = self._get_sensor_data()
        if sensor_data:
            if interface.STREAM_CavityPressure in sensor_data.keys():
                if len(sensor_data[interface.STREAM_CavityPressure]) > 0:
                    (tm, val) = sensor_data[interface.STREAM_CavityPressure].pop()
                    self.cav_pressure_cntlobj.set_value("%.3f torr" % (val))
                    
                   
    def refresh_html(self):
        self._counter += 1
        if self._counter > 10:
            self.process_parms["html_source"][0] = self._build_html()
     
    
    def _load_stats(self, stats):
        for val in stats:
            self.stats_array.append(val)
        
         
    def _calc_rd_per_second(self):
        rd_per_sec = 0.0
        start_time, rd = self.stats_array[0]
        number_of_rds = len(self.stats_array)
        end_time, rd2 = self.stats_array[number_of_rds - 1]        
        elapsed_time = end_time - start_time
        elapsed_time = 24*3600*elapsed_time.days + elapsed_time.seconds + 1.0e-6*elapsed_time.microseconds
        
        if elapsed_time > 0:
            rd_per_sec = number_of_rds / elapsed_time

        if number_of_rds > 20:
            st = number_of_rds - 20
            self.stats_array = self.stats_array[st:]
            
        return rd_per_sec
        
    
    
    def _get_data(self):
        '''
        get and return from queues
        '''
        if SIMULATE_DATA:
            new_data = self._get_simulated_data()
        else:
            new_data = self.data_listener.get_data()
        
        now = {}
        for cidx in range(0,3):
            now[cidx] = []

        now["stats"] = []
        
        start_time = None
        end_time = None
        dt = None
        rdt_sum = 0.0
        
        self._last_data_len = len(new_data)
        for data in new_data:
            if data.uncorrectedAbsorbance == 0.0:
                continue
            
            try:
                #utime = timestamp.unixTime(data.timestamp)
                ltime = timestamp.timestampToLocalDatetime(data.timestamp)
            except:
                continue

            if data.timestamp < self.initial_ts:
                continue
            
            dt = ltime
            #dt = datetime.datetime.fromtimestamp(plot_time)

            if not start_time:
                start_time = dt
                
            numtime = date2num(dt)
            
            rdt = 0.0
            if not data.uncorrectedAbsorbance == 0.0:
                rdt = 1.0 / (0.029979245800 * data.uncorrectedAbsorbance)
                
            rdt_sum += rdt

            for cidx in range(0,3):
                if self._ptype[cidx] in ("Ringdowns", ):
                    continue
                
                if not self._ptype[cidx] == CHOICE_NONE:
                    x,y = self.ptype_dict[self._ptype[cidx]]
                    if x == "timestamp":
                        xval = numtime
                    else:
                        xval = getattr(data, x)
                    if y == "shot2shot":
                        y = "uncorrectedAbsorbance"
                    yval = getattr(data, y)
                    
                    if y == "uncorrectedAbsorbance":
                        yval = rdt
                        
                    now[cidx].append((xval, yval))
            
            now["stats"].append((dt, rdt))

        if start_time:
            end_time = dt
            number_ringdowns = len(now["stats"])
            avg_rdt = rdt_sum / number_ringdowns
            
            now["start_time"] = start_time
            now["end_time"] = end_time
            now["number_ringdowns"] = number_ringdowns
            now["avg_ringdown"] = avg_rdt
        
        return now


    def _do_instrument_data(self):
        ii = 0
        for inst in self.instrument_dict.keys():
            ii += 1
            sval = "%s.%s" %(ii, random.randint(0, 9))
            self.instrument_dict[inst] = float(sval)
            
        
    def _get_simulated_data(self):
        class RingdownEntryType(Structure):
            _fields_ = [
            ("timestamp",c_longlong),
            ("wlmAngle",c_float),
            ("waveNumber",c_double),
            ("uncorrectedAbsorbance",c_float),
            ("correctedAbsorbance",c_float),
            ("status",c_ushort),
            ("count",c_ushort),
            ("tunerValue",c_ushort),
            ("pztValue",c_ushort),
            ("lockerOffset",c_ushort),
            ("laserUsed",c_ushort),
            ("ringdownThreshold",c_ushort),
            ("subschemeId",c_ushort),
            ("schemeTable",c_ushort),
            ("schemeRow",c_ushort),
            ("ratio1",c_ushort),
            ("ratio2",c_ushort),
            ("fineLaserCurrent",c_ushort),
            ("coarseLaserCurrent",c_ushort),
            ("laserTemperature",c_float),
            ("etalonTemperature",c_float),
            ("cavityPressure",c_float),
            ("lockerError",c_short),
            ("padToCacheLine",c_ushort)
            ]
        
        def ran_tiny_float():  
            rnd = random.randint(-300,300)
            rnddec = random.randint(7000,8000)
            val = "%s.%s" % (0, rnddec)
            return float(val)
              
        def ran_float():  
            rnd = random.randint(-300,300)
            rnddec = random.randint(0,30)
            val = "%s.%s" % (rnd, rnddec)
            return float(val)
              
        def ran_double():  
            rnd = random.randint(-300,300)
            rnddec = random.randint(0,30)
            val = "%s.%s" % (rnd, rnddec)
            return float(val)
              
        def ran_short():  
            rnd = random.randint(-30,30)
            return rnd
              
        def ran_ushort():  
            rnd = random.randint(0,30)
            return rnd
              
        rtndata = RingdownEntryType()
        rtndata.timestamp = timestamp.getTimestamp()
        rtndata.wlmAngle = ran_float()
        rtndata.waveNumber = ran_double()
        rtndata.uncorrectedAbsorbance = ran_tiny_float()
        rtndata.correctedAbsorbance = ran_float()
        rtndata.status = ran_ushort()
        rtndata.count = ran_ushort()
        rtndata.tunerValue = ran_ushort()
        rtndata.pztValue = ran_ushort()
        rtndata.lockerOffset = ran_ushort()
        rtndata.laserUsed = ran_ushort()
        rtndata.ringdownThreshold = ran_ushort()
        rtndata.subschemeId = ran_ushort()
        rtndata.schemeTable = ran_ushort()
        rtndata.schemeRow = ran_ushort()
        rtndata.ratio1 = ran_ushort()
        rtndata.ratio2 = ran_ushort()
        rtndata.fineLaserCurrent = ran_ushort()
        rtndata.coarseLaserCurrent = ran_ushort()
        rtndata.laserTemperature = ran_float()
        rtndata.etalonTemperature = ran_float()
        rtndata.cavityPressure = ran_float()
        rtndata.lockerError = ran_short()
        rtndata.padToCacheLine = ran_ushort()
        
        rtn = []
        loop = random.randint(0,10)
        for iii in range(loop):
            rtn.append(rtndata)
            
            rtndata = None
            rtndata = RingdownEntryType()
            
            rtndata.timestamp = timestamp.getTimestamp()
            rtndata.wlmAngle = ran_float()
            rtndata.uncorrectedAbsorbance = ran_tiny_float()
            rtndata.correctedAbsorbance = ran_float()
            rtndata.status = ran_ushort()
            rtndata.count = ran_ushort()
            rtndata.tunerValue = ran_ushort()
            rtndata.pztValue = ran_ushort()
            rtndata.lockerOffset = ran_ushort()
            rtndata.laserUsed = ran_ushort()
            rtndata.ringdownThreshold = ran_ushort()
            rtndata.subschemeId = ran_ushort()
            rtndata.schemeTable = ran_ushort()
            rtndata.schemeRow = ran_ushort()
            rtndata.ratio1 = ran_ushort()
            rtndata.ratio2 = ran_ushort()
            rtndata.fineLaserCurrent = ran_ushort()
            rtndata.coarseLaserCurrent = ran_ushort()
            rtndata.laserTemperature = ran_float()
            rtndata.etalonTemperature = ran_float()
            rtndata.cavityPressure = ran_float()
            rtndata.lockerError = ran_short()
            rtndata.padToCacheLine = ran_ushort()
            
        return rtn
        
    def _get_rd_waveform(self):
        if SIMULATE_DATA:
            data = []
            max = 500
            min = 450
            for i in range(4096):
                data.append(random.randint(min,max))
                max = max - random.randint(0,4)
                min = min - random.randint(0,4)
                if max < 0:
                    max = 1
                if min < 0:
                    min = 0
                if max <= min:
                    max = min + 1
                
            return data
        
        data = None
        self._change_das_value(
                        interface.SPECT_CNTRL_STATE_REGISTER,
                        interface.SPECT_CNTRL_PausedState
                        )
        time.sleep(0.05)
        data, meta, params = Driver.rdRingdown(0)
        self._change_das_value(
                        interface.SPECT_CNTRL_STATE_REGISTER,
                        interface.SPECT_CNTRL_RunningState
                        )
        time.sleep(0.05)
        return data

    def _evaluate_control_changes(self):
        try:    
            points = int(self.points_cntlobj.get_value())
        except:
            points = 5000
            
        if not self._points == points:
            self._points = points

        try:
            s2s_size = int(self.s2s_size_cntlobj.get_value())
        except:
            s2s_size = 200
        
        self.s2s_size = s2s_size
        
        try:
            new_points = int(self.points_cntlobj.get_value())
        except:
            new_points = self._points
        
        if not self._ptype[0] == self.p1_type_cntlobj.get_value():
            self._ptype[0] = self.p1_type_cntlobj.get_value()
            self._regenerate_plot = True
          
        self._plot_minmax_switch()
        self._evaluate_driver_requests()
            
    def _plot_smooth(self):
        if not self.s2s_smooth_cntlobj.get_value() == CHOICE_NONE:
            try:
                smooth_size = int(self.s2s_smooth_cntlobj.get_value())
            except:
                smooth_size = None
        else:
            smooth_size = None

        cursmooth, curcount = self.ymean_smooth_ctl[2]
        if not smooth_size == cursmooth:
            self.ymean_smooth_ctl[2] = (smooth_size, curcount)
          
                
    def _minmax_switch(self, cidx):
        self._auto_current[cidx] = self._auto_cntl[cidx].get_value()
        self._ymin_current[cidx] = self._ymin_cntl[cidx].get_value()
        self._ymax_current[cidx] = self._ymax_cntl[cidx].get_value()

        #restore new values back to control
        self._auto_cntl[cidx].set_value(self._auto_current[cidx])
        self._ymin_cntl[cidx].set_value(self._ymin_current[cidx])
        self._ymax_cntl[cidx].set_value(self._ymax_current[cidx])

        if cidx in self._auto_cntl.keys():
            curlock, curmin, curmax = self.lock_yaxis[cidx]
            
            changed = None
            if curlock in ("start", "locked",):
                if not self._auto_cntl[cidx].get_value() == "No":
                    changed = True
                
                if not (curmin == self._ymin_cntl[cidx].get_value()):
                    changed = True

                if not (curmax == self._ymax_cntl[cidx].get_value()):
                    changed = True
            else:
                if not self._auto_cntl[cidx].get_value() == "Yes":
                    changed = True
            
            if changed:
                self.lock_yaxis[cidx] = (None, None, None)
                if self._auto_cntl[cidx].get_value() == "No":
                    bad_minmax = None
                    try:
                        ymin = float(self._ymin_cntl[cidx].get_value())
                    except:
                        bad_minmax = True

                    try:
                        ymax = float(self._ymax_cntl[cidx].get_value())
                    except:
                        bad_minmax = True
                    
                    if not bad_minmax:   
                        self.lock_yaxis[cidx] = ("start", ymin, ymax)

    def _plot_minmax_switch(self):
        for cidx in self._ptype.keys():
            self._minmax_switch(cidx)


    def _check_and_run_macro(self):
        '''
        get the requested macro (from entry control) and run it.
        '''
        new_laser = self.laser_sel_cntlobj.get_value()
        if new_laser == CHOICE_NONE:
            new_laser = None
            
        new_mode = self.pl_macro_cntlobj.get_value()
        if new_mode == CHOICE_NONE:
            new_mode = None
            
        if ((new_mode == self.macro_mode_active)
            and new_laser == self.macro_laser_active):
            
            return None
        
        if (new_mode
            or new_laser):
            
            if not self.macro_initialization:
                self.macro_environment.update({
                                               "__builtins__": __builtins__,
                                               "self": self,
                                               "interface": interface,
                                               "Driver": Driver,
                                               "SpectrumDriver": SpectrumDriver,
                                               "FreqConverter": FreqConverter,
                                               })
                
                if "Macro Environment" in self.macro_dict.keys():
                    macro = "Macro Environment"
                    if "action" in self.macro_dict[macro]:
                        action = self.macro_dict[macro]["action"]
                        if self.macro_debug:
                            print "process code to execute:"
                            print self.macro_dict[macro]["action"]
                            exec self.macro_dict[macro]["action"] in self.macro_environment
                        else:
                            try:
                                print "process code to execute:"
                                print self.macro_dict[macro]["action"]
                                exec self.macro_dict[macro]["action"] in self.macro_environment
                            except:
                                msg = "Error when trying to run Analyzer macro %s" % (
                                                                          macro
                                                                                      )
                                print datetime.datetime.now(), msg

                self.macro_initialization = True
            
        
            if self.macro_debug:
                print "process code to execute:"
                print self.macro_dict[new_mode]["action"]
                exec self.macro_dict[new_mode]["action"] in self.macro_environment
            else:
                try:
                    print "process code to execute:"
                    print self.macro_dict[new_mode]["action"]
                    exec self.macro_dict[new_mode]["action"] in self.macro_environment
                except:
                    msg = "Error when trying to run Analyzer macro %s" % (
                                                              self.macro_mode_active
                                                                          )
                    print datetime.datetime.now(), msg
                    self.macro_mode_active = None
                    self.pl_macro_cntlobj.set_value(CHOICE_NONE)
        else:
            # unprotect any keys previously protected by the old macro
            self._enable_entry(self.cntls_obj.control_list.keys())            

        self.macro_mode_active = new_mode
        self.macro_laser_active = new_laser
        
        return new_mode
        
                
        
    def control_the_analyzer(self,
                             notebook=None, 
                             pltidx=None, 
                             canvas=None, 
                             ):
        '''
        grab values from the controls, and process Analyzer
        '''
        rtn_code = "OK"
        
        print datetime.datetime.now(), "controlling the analyzer"

        cntl_values = self._evaluate_driver_requests()
        if self._regenerate_plot:
            self.generate_plot(cntl_values, notebook, pltidx)
            for cidx in range(0,3):
                self._reset_plot_arrays(cidx)
                if canvas:
                    try:
                        canvas[cidx].draw()
                    except:
                        pass

        return rtn_code

    def _dither_test(self):
#        if self.macro_mode_active:
#            return

        dither_flag = self.dither_flag_cntlobj.get_value()
        
        if not dither_flag == self._cur_values["dither_flag"]:
            print datetime.datetime.now(), "dither_flag request", dither_flag
            print datetime.datetime.now(), "changing the dither from: ", self._cur_values["dither_flag"]
            self._switch_mode_dither(dither_flag)
        
        self.dither_flag_cntlobj.set_value(dither_flag)
        self._cur_values["dither_flag"] = dither_flag


    def _rd_threshold_test(self):
#        if self.macro_mode_active:
#            return

        rd_threshold = self.rd_threshold_cntlobj.get_value()
        
        if not rd_threshold == self._cur_values["rd_threshold"]:
            print datetime.datetime.now(), "rd_threshold request", rd_threshold
            print datetime.datetime.now(), "changing the rd_threshold from: ", self._cur_values["rd_threshold"]
            self._set_rd_threshold(rd_threshold)
        
        self.rd_threshold_cntlobj.set_value(rd_threshold)
        self._cur_values["rd_threshold"] = rd_threshold


    def _mode_test(self):
#        if self.macro_mode_active:
#            return

        rd_mode = self.rd_mode_cntlobj.get_value()
        
        if not rd_mode == self._cur_values["rd_mode"]:
            print datetime.datetime.now(), "rd_mode request", rd_mode
            print datetime.datetime.now(), "changing the rd_mode from: ", self._cur_values["rd_mode"]
            self._switch_modes(rd_mode)
        
        self.rd_mode_cntlobj.set_value(rd_mode)
        self._cur_values["rd_mode"] = rd_mode
        
            
    def _evaluate_driver_requests(self):
        self._evaluate_fitting()
        
        control_dict = {}
        for key in self._driver_cntl_list:
            control_dict[key] = self.cntls_obj.control_list[key].get_value()

        self._analyzer_control(control_dict)
        return control_dict


    def _evaluate_fitting(self):
        for name in self._fitting_requests.keys():
            if name in self.cntls_obj.control_list.keys():
                cval = self.cntls_obj.control_list[name].get_value()
                if not self._fitting_requests[name][0] == cval:
                    try:
                        new_value = int(cval)
                        self._change_das_value(
                                        self._fitting_requests[name][1],
                                        new_value
                                                 )
                        self._fitting_requests[name][0] = cval
                    except:
                        pass
                                

    def _disable_entry(self, control_list=None):
        '''
        lock the requested controls from entry
        '''
        if not control_list:
            return
        
        for name in control_list:
            if name in self.cntls_obj.control_list.keys():
                self.cntls_obj.control_list[name].set_disable()
                print "disable", name

        
    def _enable_entry(self, control_list=None):
        '''
        unlock requested controls and allow entry
        '''
        if not control_list:
            return
        
        for name in control_list:
            if name in self.cntls_obj.control_list.keys():
                self.cntls_obj.control_list[name].set_enable()
                print "enable", name
 
        
    def _analyzer_control(self, control_dict=None):
        '''
        Send various control requests to the Analyzer
        '''
        if not control_dict:
            return
        
        control_change_requested = None
        
        laser_switch = None
        rd_type_switch = None
        setpoint_switch = None
        sweep_switch = None
        spect_sequence = None
        
        
        #get the analyzer control values
        if "laser_num" in control_dict.keys():
            laser_num = control_dict["laser_num"]
        else:
            laser_num = self._cur_values["laser_num"]
            
        if "laser_pwr" in control_dict.keys():
            laser_pwr = control_dict["laser_pwr"]
        else:
            laser_pwr = self._cur_values["laser_pwr"]
            
        if "rd_type" in control_dict.keys():
            rd_type = control_dict["rd_type"]
        else:
            rd_type = self._cur_values["rd_type"]
            
        if "pl_type" in control_dict.keys():
            pl_type = control_dict["pl_type"]
        else:
            pl_type = self._cur_values["pl_type"]
            
        if "setpoint" in control_dict.keys():
            setpoint = control_dict["setpoint"]
        else:
            setpoint = self._cur_values["setpoint"]
            
        if "sweep_min" in control_dict.keys():
            sweep_min = control_dict["sweep_min"]
        else:
            sweep_min = self._cur_values["sweep_min"]
            
        if "sweep_max" in control_dict.keys():
            sweep_max = control_dict["sweep_max"]
        else:
            sweep_max = self._cur_values["sweep_max"]
            
        if "sweep_incr" in control_dict.keys():
            sweep_incr = control_dict["sweep_incr"]
        else:
            sweep_incr = self._cur_values["sweep_incr"]
            
        
        if self.using_wlm:
            if "spect_sequence" in control_dict.keys():
                spect_sequence = control_dict["spect_sequence"]
            else:
                spect_sequence = self._cur_values["spect_sequence"]


        #test values to see which have changed
        if not laser_num == self._cur_values["laser_num"]:
            control_change_requested = True
            print datetime.datetime.now(), "laser_num request", laser_num
            laser_switch = True

        if not laser_pwr == self._cur_values["laser_pwr"]:
            control_change_requested = True
            print datetime.datetime.now(), "laser_pwr request", laser_pwr
            laser_switch = True

        if not rd_type == self._cur_values["rd_type"]:
            control_change_requested = True
            print datetime.datetime.now(), "rd_type request", rd_type
            rd_type_switch = True
            
        if not setpoint == self._cur_values["setpoint"]:
            control_change_requested = True
            print datetime.datetime.now(), "setpoint request", setpoint
            setpoint_switch = True

        if not sweep_min == self._cur_values["sweep_min"]:
            control_change_requested = True
            print datetime.datetime.now(), "sweep_min request", sweep_min
            sweep_switch = True

        if not sweep_max == self._cur_values["sweep_max"]:
            control_change_requested = True
            print datetime.datetime.now(), "sweep_max request", sweep_max
            sweep_switch = True

        if not sweep_incr == self._cur_values["sweep_incr"]:
            control_change_requested = True
            print datetime.datetime.now(), "sweep_incr request", sweep_incr
            sweep_switch = True

        if self.using_wlm:
            if not spect_sequence == self._cur_values["spect_sequence"]:
                control_change_requested = True
                print datetime.datetime.now(), "spect_sequence request", spect_sequence
                rd_type_switch = True

        if not pl_type == self._cur_values["pl_type"]:
            self._regenerate_plot = True
            print datetime.datetime.now(), "pl_type request", pl_type
            self._cur_values["pl_type"] = pl_type
            
            if self._cur_values["pl_type"] == "Plot against laser temp":
                self._cur_values["main_plot"] = "ringdown time vs temperature"
            elif self._cur_values["pl_type"] == "Plot against wave number":
                self._cur_values["main_plot"] = "ringdown time vs waveNumber"
            else:
                self._cur_values["main_plot"] = "ringdown time vs time"
        
        #send the values back to the screen control
        self.laser_num_cntlobj.set_value(laser_num)
        self.laser_pwr_cntlobj.set_value(laser_pwr)
        self.rd_type_cntlobj.set_value(rd_type)
        self.pl_type_cntlobj.set_value(pl_type)
        self.setpoint_cntlobj.set_value(setpoint)
        self.sweep_min_cntlobj.set_value(sweep_min)
        self.sweep_max_cntlobj.set_value(sweep_max)
        self.sweep_incr_cntlobj.set_value(sweep_incr)
        
        if self.using_wlm:
            self.spect_sequence_cntlobj.set_value(spect_sequence)

        # Unconditionally select the correct laser
        
        self._select_laser(laser_num)

        if not control_change_requested:
            return

        # store the new changed values as "current" values
        self._cur_values["laser_pwr"] = laser_pwr
        self._cur_values["laser_num"] = laser_num
        self._cur_values["rd_type"] = rd_type
        self._cur_values["setpoint"] = setpoint
        self._cur_values["sweep_min"] = sweep_min
        self._cur_values["sweep_max"] = sweep_max
        self._cur_values["sweep_incr"] = sweep_incr

        
        if self.using_wlm:
            self._cur_values["spect_sequence"] = spect_sequence


        #Start the analzer if not yet started
        if (not self._cur_values["analyzer_status"]):
            print datetime.datetime.now(), "starting analyzer engine"
                
            self._start_up_analyzer()
            self._cur_values["analyzer_status"] = True
            
            time.sleep(1.0)

        #print datetime.datetime.now(), "rd_type", self._cur_values["rd_type"]
        
        #Do the requested changes
        if setpoint_switch:
            print datetime.datetime.now(), "changing the setpoint to: ", self._cur_values["setpoint"]
            self._adjust_setpoint(self._cur_values["laser_num"], self._cur_values["setpoint"])

        if sweep_switch:
            print datetime.datetime.now(), "changing the sweep to: ", self._cur_values["sweep_min"], self._cur_values["sweep_max"], self._cur_values["sweep_incr"]
            self._adjust_sweep(
                                  self._cur_values["laser_num"], 
                                  self._cur_values["sweep_min"],
                                  self._cur_values["sweep_max"],
                                  self._cur_values["sweep_incr"],
                                  )
        
        
        # changing sequence and starting ringdowns is always
        if rd_type_switch:
            if self._cur_values["rd_type"] == "Use sequence":
                print datetime.datetime.now(), "changing the rd_type / spect_seq to: %s / %s " % (
                                                         self._cur_values["rd_type"], 
                                                         self._cur_values["spect_sequence"]
                                                                     )
            else:
                print datetime.datetime.now(), "changing the rd_type to: ", self._cur_values["rd_type"]
            
        # Start acquisition if laser is on
                
        if not self._cur_values["laser_pwr"] == "Yes":
            self.stop_acquisition()
            time.sleep(0.5)
            self._stop_all_laser()
        else:
            self._start_all_laser()
            time.sleep(0.5)
            self.start_acquisition()
        
        
        return True
                    
    def start_acquisition(self):
        self._start_ringdowns(self._cur_values["laser_num"], self._cur_values["rd_type"])
        
    def stop_acquisition(self):
        self._change_das_value(
                        interface.SPECT_CNTRL_STATE_REGISTER, 
                        interface.SPECT_CNTRL_IdleState
                                 )
    
    def _set_laser_locking(self,enable):
        oldVal = Driver.rdFPGA(interface.FPGA_RDMAN,interface.RDMAN_OPTIONS)
        bitpos = 1<<interface.RDMAN_OPTIONS_LOCK_ENABLE_B
        fieldMask = (1<<interface.RDMAN_OPTIONS_LOCK_ENABLE_W)-1
        optMask = bitpos*fieldMask
        optNew  = bitpos*int(bool(enable))
        newVal = ((~optMask) & oldVal) | optNew
        self._change_fpga_value(interface.FPGA_RDMAN,interface.RDMAN_OPTIONS,newVal)

    def _stop_all_laser(self):
        lsr_register = {}
        lsr_register[1] = interface.LASER1_CURRENT_CNTRL_STATE_REGISTER
        lsr_register[2] = interface.LASER2_CURRENT_CNTRL_STATE_REGISTER
        lsr_register[3] = interface.LASER3_CURRENT_CNTRL_STATE_REGISTER
        lsr_register[4] = interface.LASER4_CURRENT_CNTRL_STATE_REGISTER
        
        for ls in lsr_register.keys():
            reg = lsr_register[ls]
            #print datetime.datetime.now(), "reg", reg   
            self._change_das_value(
                            reg,
                            interface.LASER_CURRENT_CNTRL_DisabledState
                            )

        return True

    
    def _start_all_laser(self):
        lsr_register = {}
        lsr_register[1] = interface.LASER1_CURRENT_CNTRL_STATE_REGISTER
        lsr_register[2] = interface.LASER2_CURRENT_CNTRL_STATE_REGISTER
        lsr_register[3] = interface.LASER3_CURRENT_CNTRL_STATE_REGISTER
        lsr_register[4] = interface.LASER4_CURRENT_CNTRL_STATE_REGISTER
        
        for ls in lsr_register.keys():
            reg = lsr_register[ls]
            #print datetime.datetime.now(), "reg", reg   
            self._change_das_value(
                            reg,
                            interface.LASER_CURRENT_CNTRL_ManualState
                            )
        return True


    def _get_laser_current_state(self, lsr):
        '''
        Get the laser state for laserNum (0-index)
        '''
        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None
        
        if lsr_id in (1, 2, 3, 4):
            lsr_register = {}
            lsr_register[1] = interface.LASER1_CURRENT_CNTRL_STATE_REGISTER
            lsr_register[2] = interface.LASER2_CURRENT_CNTRL_STATE_REGISTER
            lsr_register[3] = interface.LASER3_CURRENT_CNTRL_STATE_REGISTER
            lsr_register[4] = interface.LASER4_CURRENT_CNTRL_STATE_REGISTER
        else:
            return None
        
        reg = lsr_register[lsr_id]
        curr_state = Driver.rdDasReg(reg)

        return curr_state


    def _get_laser_temp_state(self, lsr):
        '''
        Get the laser state for laserNum (0-index)
        '''
        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None
        
        if lsr_id in (1, 2, 3, 4):
            lsr_register = {}
            lsr_register[1] = interface.LASER1_TEMP_CNTRL_STATE_REGISTER
            lsr_register[2] = interface.LASER2_TEMP_CNTRL_STATE_REGISTER
            lsr_register[3] = interface.LASER3_TEMP_CNTRL_STATE_REGISTER
            lsr_register[4] = interface.LASER4_TEMP_CNTRL_STATE_REGISTER
        else:
            return None
        
        reg = lsr_register[lsr_id]
        curr_state = Driver.rdDasReg(reg)

        return curr_state


    def _disable_laser_current(self, lsr):
        '''
        Turn off laser current for laserNum (0-index)
        '''
        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None
        
        laserNum = lsr_id - 1
        
        if laserNum<0 or laserNum>=interface.MAX_LASERS:
            raise ValueError("Invalid laser number in enableLaserCurrent")
        enableSource = 1 << (interface.INJECT_CONTROL_LASER_CURRENT_ENABLE_B + laserNum)
        removeShort  = 1 << (interface.INJECT_CONTROL_MANUAL_LASER_ENABLE_B + laserNum)
        injControl = Driver.rdFPGA("FPGA_INJECT","INJECT_CONTROL")
        injControl &= ~(enableSource |removeShort)
        #Driver.wrFPGA("FPGA_INJECT","INJECT_CONTROL",injControl)
        self._change_fpga_value("FPGA_INJECT", "INJECT_CONTROL", newBits)

    
    def _select_laser(self, lsr):
        '''
        Select laser for laserNum (0-index)
        '''
        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None
        
        
        laserNum = lsr_id - 1
        print datetime.datetime.now(), "lsr_id/laserNum", lsr_id, laserNum
        
        if laserNum<0 or laserNum>=interface.MAX_LASERS:
            raise ValueError("Invalid laser number in _select_laser")

        currentBits = Driver.rdFPGA("FPGA_INJECT","INJECT_CONTROL") 
        mask = 0x3 << interface.INJECT_CONTROL_LASER_SELECT_B 
        newBits = (laserNum) << interface.INJECT_CONTROL_LASER_SELECT_B 
        newBits = newBits | (currentBits & (~mask))
        
        self._change_fpga_value("FPGA_INJECT", "INJECT_CONTROL", newBits)
        

    def _set_rd_threshold(self, rd_threshold):
        '''
        set the rd_threshold
        '''
        #change rd_threshold value
        self._change_das_value(
                        interface.SPECT_CNTRL_DEFAULT_THRESHOLD_REGISTER, 
                        rd_threshold
                                 )


    def _switch_modes(self, new_mode):
        '''
        Switching between ringdown moda and continuous modes
        '''
        if new_mode == "Ringdown":
            self._switch_mode_ringdown()
        elif new_mode == "Continuous":
            self._switch_mode_continuous()
        
        
    def _switch_mode_ringdown(self):
        '''
        switch to ringdown mode
        '''
        if SIMULATE_DATA:
            return
        
        currentBits = Driver.rdFPGA("FPGA_RDMAN", "RDMAN_OPTIONS") 
        print datetime.datetime.now(), "switch_mode_ringdown before bits %x " %(currentBits)

        upSlopeBit = 1 << interface.RDMAN_OPTIONS_UP_SLOPE_ENABLE_B 
        downSlopeBit = 1 << interface.RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B 
        newBits = currentBits | upSlopeBit & (~downSlopeBit) 
        #Driver.wrFPGA("FPGA_RDMAN", "RDMAN_OPTIONS", newBits)
        self._change_fpga_value("FPGA_RDMAN", "RDMAN_OPTIONS", newBits)
        
        currentBits = Driver.rdFPGA("FPGA_RDMAN", "RDMAN_OPTIONS") 
        print datetime.datetime.now(), "switch_mode_ringdown after bits %x " %(currentBits)
        self.start_acquisition()


    def _switch_mode_continuous(self):
        '''
        switch to continuous mode
        '''
        if SIMULATE_DATA:
            return
        
        currentBits = Driver.rdFPGA("FPGA_RDMAN", "RDMAN_OPTIONS") 
        print datetime.datetime.now(), "switch_mode_continuous before bits %x " %(currentBits)

        upSlopeBit = 1 << interface.RDMAN_OPTIONS_UP_SLOPE_ENABLE_B 
        downSlopeBit = 1 << interface.RDMAN_OPTIONS_DOWN_SLOPE_ENABLE_B 
        newBits = currentBits & (~upSlopeBit) & (~downSlopeBit) 
        #Driver.wrFPGA("FPGA_RDMAN", "RDMAN_OPTIONS", newBits)
        self._change_fpga_value("FPGA_RDMAN", "RDMAN_OPTIONS", newBits)
        
        currentBits = Driver.rdFPGA("FPGA_RDMAN", "RDMAN_OPTIONS") 
        print datetime.datetime.now(), "switch_mode_continuous after bits %x " %(currentBits)
        self.stop_acquisition()

    def _switch_mode_dither(self, switch_flag):
        '''
        switch to continuous mode
        '''
        if SIMULATE_DATA:
            return
        
        currentBits = Driver.rdFPGA("FPGA_RDMAN", "RDMAN_OPTIONS") 
        print datetime.datetime.now(), "_switch_mode_dither to %s before bits %x " %(switch_flag, currentBits)

        ditherBit = 1 << interface.RDMAN_OPTIONS_DITHER_ENABLE_B 
        if switch_flag == "Yes":
            newBits = currentBits | ditherBit
        else:
            newBits = currentBits & (~ditherBit)
        
        #Driver.wrFPGA("FPGA_RDMAN", "RDMAN_OPTIONS", newBits)
        self._change_fpga_value("FPGA_RDMAN", "RDMAN_OPTIONS", newBits)
        
        currentBits = Driver.rdFPGA("FPGA_RDMAN", "RDMAN_OPTIONS")
        print datetime.datetime.now(), "_switch_mode_dither to %s after bits %x " %(switch_flag, currentBits)
        
        
        
    def _start_up_analyzer(self):
        '''
        call Driver.startEngine() to start temperature control of all lasers.
        '''
        if SIMULATE_DATA:
            return

        Driver.stopScan()

        if self.using_wlm:
            FreqConverter.loadWarmBoxCal()
            FreqConverter.loadHotBoxCal()
            FreqConverter.centerTuner(32768)
        
        Driver.startEngine()
        
    def _start_ringdowns(self, lsr, rd_type):
        '''
        Switching between ringdown mode and continuous modes
        '''
        if rd_type == "Constant laser temp":
            self._start_ringdowns_constant_temp(lsr)

        elif rd_type == "Laser temp sweep":
            self._start_ringdowns_sweep_temp(lsr)

        elif rd_type == "Use sequence":
            self._start_ringdowns_use_sequence()
        
        
    def _start_ringdowns_constant_temp(self, lsr):
        '''
        Start ringdowns for constant temp
        '''
        print datetime.datetime.now(), "start_ringdowns_constant_temp"

        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None

        if lsr_id in (1, 2, 3, 4):
            lsr_register = {}
            lsr_register[1] = interface.LASER1_TEMP_CNTRL_STATE_REGISTER
            lsr_register[2] = interface.LASER2_TEMP_CNTRL_STATE_REGISTER
            lsr_register[3] = interface.LASER3_TEMP_CNTRL_STATE_REGISTER
            lsr_register[4] = interface.LASER4_TEMP_CNTRL_STATE_REGISTER
        else:
            return None
        
        reg = lsr_register[lsr_id]

        #set to idle
        self.stop_acquisition()
        
        time.sleep(0.5)
        self._set_laser_locking(False)
        
        self._change_das_value(
                        reg, 
                        interface.TEMP_CNTRL_EnabledState
                                 )

        #change the mode
        self._change_das_value(
                        interface.SPECT_CNTRL_MODE_REGISTER, 
                        interface.SPECT_CNTRL_ContinuousManualTempMode
                                 )

        #change to starting
        self._change_das_value(
                        interface.SPECT_CNTRL_STATE_REGISTER, 
                        interface.SPECT_CNTRL_StartManualState
                                 )

        time.sleep(0.5)
        
        return True


    def _start_ringdowns_sweep_temp(self, lsr):
        '''
        Start ringdowns for temp sweep
        '''
        print datetime.datetime.now(), "start_ringdowns_sweep_temp"

        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None

        if lsr_id in (1, 2, 3, 4):
            lsr_register = {}
            lsr_register[1] = interface.LASER1_TEMP_CNTRL_STATE_REGISTER
            lsr_register[2] = interface.LASER2_TEMP_CNTRL_STATE_REGISTER
            lsr_register[3] = interface.LASER3_TEMP_CNTRL_STATE_REGISTER
            lsr_register[4] = interface.LASER4_TEMP_CNTRL_STATE_REGISTER
        else:
            return None
        
        reg = lsr_register[lsr_id]

        #set to idle
        self.stop_acquisition()
        
        time.sleep(0.5)
        self._set_laser_locking(False)

        self._change_das_value(
                        reg, 
                        interface.TEMP_CNTRL_SweepingState
                                )

        time.sleep(0.5)

        #change the mode
        self._change_das_value(
                        interface.SPECT_CNTRL_MODE_REGISTER, 
                        interface.SPECT_CNTRL_ContinuousManualTempMode
                                 )

        #change to starting
        self._change_das_value(
                        interface.SPECT_CNTRL_STATE_REGISTER, 
                        interface.SPECT_CNTRL_StartManualState
                                 )

        time.sleep(0.5)
        return True
    
    
    def _start_ringdowns_use_sequence(self):
        '''
        Start ringdowns with spectral scan WLM mode
        '''
        print datetime.datetime.now(), "start_ringdowns_use_sequence"

        if SIMULATE_DATA:
            return
        
        #set to idle
        self.stop_acquisition()
        
        time.sleep(0.5)
        self._set_laser_locking(True)
        #change the mode
        self._change_das_value(
                        interface.SPECT_CNTRL_MODE_REGISTER, 
                        interface.SPECT_CNTRL_SchemeMultipleMode
                                 )

        time.sleep(0.5)
        
        #change to starting
        SpectrumDriver.startSequence(self.spect_sequence_cntlobj.get_value())

        return True

    
    def _adjust_setpoint(self, lsr, setpoint):
        '''
        Adjust laser temp setpoint
        '''
        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None

        if lsr_id in (1, 2, 3, 4):
            lsr_register = {}
            lsr_register[1] = interface.LASER1_TEMP_CNTRL_USER_SETPOINT_REGISTER
            lsr_register[2] = interface.LASER2_TEMP_CNTRL_USER_SETPOINT_REGISTER
            lsr_register[3] = interface.LASER3_TEMP_CNTRL_USER_SETPOINT_REGISTER
            lsr_register[4] = interface.LASER4_TEMP_CNTRL_USER_SETPOINT_REGISTER
        else:
            return None
        
        reg = lsr_register[lsr_id]
        self._change_das_value(
                                reg, 
                                setpoint
                                 )
        
        return True
    
    
    def _adjust_sweep(self, lsr, min, max, incr):
        '''
        adjust laser sweep range
        '''   
        if SIMULATE_DATA:
            return
        
        try:
            lsr_id = int(lsr)
        except:
            return None

        if lsr_id in (1, 2, 3, 4):
            lsr_max_register = {}
            lsr_max_register[1] = interface.LASER1_TEMP_CNTRL_SWEEP_MAX_REGISTER
            lsr_max_register[2] = interface.LASER2_TEMP_CNTRL_SWEEP_MAX_REGISTER
            lsr_max_register[3] = interface.LASER3_TEMP_CNTRL_SWEEP_MAX_REGISTER
            lsr_max_register[4] = interface.LASER4_TEMP_CNTRL_SWEEP_MAX_REGISTER

            lsr_min_register = {}
            lsr_min_register[1] = interface.LASER1_TEMP_CNTRL_SWEEP_MIN_REGISTER
            lsr_min_register[2] = interface.LASER2_TEMP_CNTRL_SWEEP_MIN_REGISTER
            lsr_min_register[3] = interface.LASER3_TEMP_CNTRL_SWEEP_MIN_REGISTER
            lsr_min_register[4] = interface.LASER4_TEMP_CNTRL_SWEEP_MIN_REGISTER

            lsr_incr_register = {}
            lsr_incr_register[1] = interface.LASER1_TEMP_CNTRL_SWEEP_INCR_REGISTER
            lsr_incr_register[2] = interface.LASER2_TEMP_CNTRL_SWEEP_INCR_REGISTER
            lsr_incr_register[3] = interface.LASER3_TEMP_CNTRL_SWEEP_INCR_REGISTER
            lsr_incr_register[4] = interface.LASER4_TEMP_CNTRL_SWEEP_INCR_REGISTER
        else:
            return None

        regincr = lsr_incr_register[lsr_id]
        regmax = lsr_max_register[lsr_id]
        regmin = lsr_min_register[lsr_id]

        self._change_das_value(regmin, min)
        self._change_das_value(regmax, max)
        self._change_das_value(regincr, incr)
        
        return True

    
    def _change_das_value(self, reg, value):
        '''
        write value into register
        '''
        if SIMULATE_DATA:
            return
        
        current_val = Driver.rdDasReg(reg)
        if not value == current_val:
            Driver.wrDasReg(reg, value)
            print datetime.datetime.now(), "das change: %s: %s" % (reg, value)

        return True
    
    
    def _change_fpga_value(self, base, reg, value):
        '''
        write value into register
        '''
        if SIMULATE_DATA:
            return
        
        current_val = Driver.rdFPGA(base, reg)
        if not value == current_val:
            Driver.wrFPGA(base, reg, value)
            print datetime.datetime.now(), "fpga change: %s %s: %s" % (base, reg, value)

        return True
    
    
    def _change_spectrum_driver_value(self, reg, value):
        '''
        write value into register
        '''
        if SIMULATE_DATA:
            return
        
        current_val = Driver.rdDasReg(reg)
        if not value == current_val:
            SpectrumDriver.wrDasReg(
                            reg, 
                            value
                            )

        return True
     
        
    def _log(self, msg):
        ii = len(self._message_array)
        self._message_array[ii] = (datetime.datetime.now(), msg)

    def _get_sensor_data(self):
        '''
        get and return from queues
        '''
        if SIMULATE_DATA:
            new_data = self._get_sensor_simulated_data()
            #print datetime.datetime.now(), "new_data", new_data
        else:
            new_data = self.sensor_data_listener.get_data()
        
        return new_data


    def _get_sensor_simulated_data(self):
        rtn = {}
        for ii in interface.STREAM_MemberTypeDict.keys():
            rtn[ii] = []
        loop = random.randint(0,10)
        for iii in range(loop):
            
            for ii in interface.STREAM_MemberTypeDict.keys():
                rndval = random.randint(0,30)
                tm = 0.0
                rtn[ii].append((tm, rndval))
            
        return rtn
        


        
if __name__ == '__main__':
    msg = "liveplotmodel.py"
    msg += " defines a class which cannot be run as a stand-alone process."
    raise RuntimeError, msg