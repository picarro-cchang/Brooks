'''
sensorplotmodel.py -- The sensorplot module contains the SensorPlotModel class.
This class will display an XY plot of data from the BROADCAST_PORT_SENSORSTREAM

'''
APP_NAME = "SensorPlotModel"
APP_DESCRIPTION = "SensorPlot Data Model"
__version__ = 1.0

# Set SIMULATE_DATA to true for testing where there is no drive
# random values will be used for the plots 
# the plot datum are meaningless during this time, but you are able
# to test the operation of the module
SIMULATE_DATA = True

import os
import time, datetime
import random
from Queue import Queue

from postprocessdefn import *

from matplotlib import pyplot
from matplotlib.figure import Figure
import matplotlib.font_manager as font_manager

from Host.Common.Listener import Listener
from Host.Common import CmdFIFO, SharedTypes, timestamp

from Host.autogen import interface

from Utilities import AppInfo


#from Host.Common.SharedTypes import RPC_PORT_COORDINATOR, \
#                                    RPC_PORT_DRIVER,  \
#                                    RPC_PORT_SPECTRUM_COLLECTOR

#from Host.autogen.interface import * 

#SpectrumCollector = CmdFIFO.CmdFIFOServerProxy(
#                        "http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR, 
#                        APP_NAME, IsDontCareConnection = False
#                        )


class SensorPlotModel(object):
    '''
    SensorPlot Model Class
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''

        # version and about info
        about = AppInfo()
        self.about_version = about.getAppVer()
        self.about_name = "Sensor Plot (Test Station)"  #about.getAppName()
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
        self._title = "Sensor Plot"
        self._max_source_lines = 100
        self._counter = 0
        
        self._message_array = {0: (datetime.datetime.now(), "Start plotting.")}
        
        self._plot_was_generated = None

        self.data_listener = SensorListener()
        
        self._init_process_parms()

    
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
        
        self.plot_name = {
                          0: "Plot 1",
                          1: "Plot 2",
                          2: "Plot 3",
                          3: "Plot 4",
                          }

        self.lock_yaxis = {
                           # (T/F, min_lim, max_lim)
                           0: (None, None, None),
                           1: (None, None, None),
                           2: (None, None, None),
                           3: (None, None, None),
                           }
        
        self._collecting = {
                          0: None,
                          1: None,
                          2: None,
                          3: None,
                            }

        self.stream_name_dict = {}
        self.ychoice_list = []
        for idx, mbr in interface.STREAM_MemberTypeDict.iteritems():
            val = mbr.replace("STREAM_", "")
            self.ychoice_list.append(val)
            self.stream_name_dict[val] = idx
            
        self._latest_ymax = {}
        self._latest_ymin = {}
        self._current_ymax = {}
        self._current_ymin = {}
        
        self.freeze = {
                        0: None,
                        1: None,
                        2: None,
                        3: None,
                        }
         
        self.auto_freeze = {
                        0: None,
                        1: None,
                        2: None,
                        3: None,
                        }
        
        self.ylim_dict = {
                           "degC_laser": (15,35),
                           "degC_warmbox": (30,60),
                           "degC_hotbox": (40,50),
                           "dgU_laser": (32000, 38000),
                           "dgU_warmbox": (40000, 45000),
                           "dgU_hotbox": (44000, 46000),
                           "mA_laser": (140, 190),
                           "tor_pressure": (772.40, 772.70)
                           
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
                           3: self.plt4_auto_cntlobj,
                           }
        self._ymin_cntl = {
                           0: self.plt1_ymin_cntlobj,
                           1: self.plt2_ymin_cntlobj,
                           2: self.plt3_ymin_cntlobj,
                           3: self.plt4_ymin_cntlobj,
                           }
        self._ymax_cntl = {
                           0: self.plt1_ymax_cntlobj,
                           1: self.plt2_ymax_cntlobj,
                           2: self.plt3_ymax_cntlobj,
                           3: self.plt4_ymax_cntlobj,
                           }
        self._auto_current = {
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
        self.process_parms["column_list"] = self.ychoice_list
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
              "combine_data_flag": combine_data_flag,
              "y1_col": y1_col,
              "y2_col": y2_col,
              "y3_col": y3_col,
              "y4_col": y4_col,
              "points": points
              "export_data": True_or_None, #optional
        '''
        self._bg = None

        self._ptype = {}
        self._ptype[0] = plot_parameters["y1_col"]
        self._ptype[1] = plot_parameters["y2_col"]
        self._ptype[2] = plot_parameters["y3_col"]
        self._ptype[3] = plot_parameters["y4_col"]
        
        self._combine_data_flag = "No"
        if plot_parameters["combine_data_flag"] == "Combine and Correlate":
            self._combine_data_flag = "Yes"
        elif plot_parameters["combine_data_flag"] == "Separate Tabs":
            self._combine_data_flag = "Tabs"
            
        points = int(plot_parameters["points"])
        self._points = points

        first_axes = None
        
        self.yval = {}
        self.xval = {}
        fig = {}
        ncol = 0
        self._axes = {}
        self._plot = {}

        self._initial_yval = [None] * points
        
        for cidx in range(0,4):
            self.yval[cidx] = [None] * points
            #self.xval[cidx] = [None] * points
            self.xval[cidx] = range(points)
            #self.yval[cidx] = [0.0]
            #self.xval[cidx] = [0.0]
            fig[cidx]=Figure(frameon=True,facecolor=PLOT_FACECOLOR)
                    
        if self._combine_data_flag == "Yes":
            self._axes[0] = fig[1].add_subplot(111)
            first_axes = self._axes[0]

            for cidx in range(0,4):
                if not self._ptype[cidx] == CHOICE_NONE:
                    self._plot[cidx] = self._do_plot(
                                                  self._axes[0], 
                                                  self.xval[cidx], 
                                                  self.yval[cidx], 
                                                  self._ptype[cidx],
                                                  True
                                                  )
                    ncol += 1
                
            self._axes[0].legend(
                                 loc='upper center', 
                                 ncol=ncol, 
                                 prop=font_manager.FontProperties(size=10)
                                 )
            self._axes[0].grid(
                               True, 
                               linestyle='-', 
                               which='major', 
                               color='lightgrey', 
                               alpha=0.5
                               )
            last_plot_idx = 0
        else:
            first_axes = None
            plot_cycle = 0
            num_plots = 0
            
            for cidx in range(0,4):
                if not self._ptype[cidx] == CHOICE_NONE:
                    num_plots += 1
                
            last_plot_idx = 0
            
            for cidx in range(0,4):
                if self._combine_data_flag == "Tabs":
                    cbidx = cidx
                else:
                    cbidx = 0
                    
                if not self._ptype[cidx] == CHOICE_NONE:
                    last_plot_idx = cidx
                    if self._combine_data_flag == "Tabs":
                        subplt = "111"
                    else:
                        subplt = "%s1%s" %(num_plots, plot_cycle + 1)

                    if plot_cycle == 0:
                        self._axes[cidx] = fig[cbidx].add_subplot(subplt)
                        first_axes = self._axes[cidx]
                    else:
                        #if self._combine_data_flag == "Tabs":
                        #    self._axes[cidx] = fig[cidx].add_subplot(subplt)
                        #else:
                        self._axes[cidx] = fig[cbidx].add_subplot(
                                                        subplt, 
                                                        sharex=first_axes
                                                                )
                        #self._axes[cidx] = fig[cidx].add_subplot(subplt)
                    
                    self._plot[cidx] = self._do_plot(
                                                  self._axes[cidx], 
                                                  self.xval[cidx], 
                                                  self.yval[cidx], 
                                                  self._ptype[cidx]
                                                  )
                    plot_cycle += 1
                

        
        if first_axes:
            if self._combine_data_flag == "Yes":
                first_axes.set_ylim([0,500])
                #first_axes.set_autoscaley_on(True)
            else:
                for cidx in range(0,4):
                    if not self._ptype[cidx] == CHOICE_NONE:
                        self._set_ylim(self._axes[cidx], self._ptype[cidx])
                    
                    if self._combine_data_flag == "Tabs":
                        if cidx in self._axes.keys(): 
                            self._axes[cidx].set_xticklabels(
                                                           self.xval[cidx], 
                                                           visible=True
                                                           )
                    
            first_axes.set_xlim([0,points])
            first_axes.set_autoscale_on(False)
            #first_axes.set_yticks(range(0,101,10))
            
            if not self._combine_data_flag == "Tabs":
                self._axes[last_plot_idx].set_xticklabels(
                                                         self.xval[0], 
                                                         visible=True
                                                         )

            if notebook:
                print "HERE notebook"
                if pltidx:
                    print "HERE pltidx"
                    for cidx in range(0,4):
                        if self._combine_data_flag == "Tabs":
                            self.plot_name[cidx] = self._ptype[cidx]
                            notebook.SetPageText(
                                                 pltidx[cidx], 
                                                 self._ptype[cidx]
                                                 )
                        else:
                            self.plot_name[cidx] = "Plot %s" % (cidx + 1)
                            notebook.SetPageText(
                                                 pltidx[cidx], 
                                                 "Plot %s" % (cidx + 1)
                                                )
                        
           
            self._bg = None
            self._get_data()
    
            for cidx in range(0,4):
                self.process_parms["plot_fig"][cidx] = fig[cidx]
                self.process_parms["plot_data"][cidx] = None
    
            self._plot_was_generated = True
        
        self._status = ""

    def _do_plot(self, plt, xval, yval, ycol, combine=None):
        '''
        Do the plot
        '''
        rtn_plot, = plt.plot(xval, yval,label=ycol)
        if not combine:
            plt.grid(
                     True, 
                     linestyle='-', 
                     which='major', 
                     color='lightgrey', 
                     alpha=0.5
                     )
            plt.set_xticklabels(xval, visible=False)
            plt.set_ylabel(ycol)
        return rtn_plot
                
    def _set_ylim(self, plt, col):
        '''
        set ylim based on selected column
        '''
        lw = 0
        hh = 100
        
        if col in (
                   "Laser1Temp",
                   "Laser2Temp",
                   "Laser3Temp",
                   "Laser4Temp",
                   ):
            lw, hh = self.ylim_dict["degC_laser"]
        elif col in (
                   "Laser1Tec",
                   "Laser2Tec",
                   "Laser3Tec",
                   "Laser4Tec",
                   ):
            lw, hh = self.ylim_dict["dgU_laser"]
        elif col in (
                   "Laser1Current",
                   "Laser2Current",
                   "Laser3Current",
                   "Laser4Current",
                   ):
            lw, hh = self.ylim_dict["mA_laser"]
        elif col in (
                    "EtalonTemp",
                    "WarmBoxTemp",
                    "WarmBoxHeatsinkTemp",
                    "DasTemp",
                   ):
            lw, hh = self.ylim_dict["degC_warmbox"]
        elif col in (
                    "CavityTemp",
                    "HotBoxHeatsinkTemp",
                   ):
            lw, hh = self.ylim_dict["degC_hotbox"]
        elif col in (
                    "WarmBoxTec",
                   ):
            lw, hh = self.ylim_dict["dgU_warmbox"]
        elif col in (
                    "HotBoxTec",
                   ):
            lw, hh = self.ylim_dict["dgU_hotbox"]

        elif col in (
                    "CavityPressure",
                   ):
            lw, hh = self.ylim_dict["tor_pressure"]

        plt.set_ylim([lw, hh])

#STREAM_CavityPressure = 20 # 


#STREAM_AmbientPressure = 21 # 

#STREAM_InletValve = 29 # 
#STREAM_OutletValve = 30 # 



        
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
        rtn_val = None
        
        if self._status == "working":
            return rtn_val
        
        need_to_draw = {
                        0: None,
                        1: None,
                        2: None,
                        3: None,
                        }
        
        if cntl_values:
            self._evaluate_control_changes()
            if self._regenerate_plot:
                self.generate_plot(cntl_values, notebook, pltidx)
                for cidx in range(0,4):
                    need_to_draw[cidx] = True
                    
                rtn_val = {"plot": "layout"}
        else:
            do_minmax = None        
            for cidx in range(0,4):
                if cidx in self._auto_current.keys():
                    if not self._auto_current[cidx] == self._auto_cntl[cidx].get_value():
                        self._auto_current[cidx] = self._auto_cntl[cidx].get_value()
                        do_minmax = True
            if do_minmax:
                self._plot_minmax_switch()
            
        if self._plot_was_generated:
            if canvas:
                # Save the initial background canvas region(s)
                if refresh_layout or self._bg is None:
                    self._bg = {}
                    for i in self._axes.keys():
                        self._bg[i] = None
                    
                for i in self._axes.keys():
                    if not self._bg[i]:
                        if self._combine_data_flag == "Tabs":
                            cbidx = i
                        else:
                            cbidx = 0
                        
                        # draw if the notebook has been defined
                        if refresh_layout:
                            if not self._ptype[i] == CHOICE_NONE:
                                self._plot[i].set_ydata(self._initial_yval)
                                canvas[cbidx].draw()
                        
                        elif notebook:
                            if pltidx:
                                canvas[cbidx].draw()

                        self._bg[i] = canvas[cbidx].copy_from_bbox(
                                                           self._axes[i].bbox
                                                                   )
    
                # restore the background
                for i in self._axes.keys():
                    if self._combine_data_flag == "Tabs":
                        cbidx = i
                    else:
                        cbidx = 0
                    
                    canvas[cbidx].restore_region(self._bg[i])
            
            if restart:
                for cidx in range(0,4):
                    self.yval[cidx] = [None] * self._points
                    
            else:
                self._load_plot_values()

            comb_miny = None
            comb_maxy = None
            
            # plot the new values (onto the restored background)
            for cidx in range(0,4):
                if not self._ptype[cidx] == CHOICE_NONE:
                    self._plot[cidx].set_ydata(self.yval[cidx])
                    

                    #self._plot[cidx].set_xdata(self.xval[cidx])
                    #if cidx == 1:
                    #    print "x", self.xval[cidx]

                if self._combine_data_flag == "Yes":
                    if not self._ptype[cidx] == CHOICE_NONE:
                        if self._latest_ymax[cidx]:
                            if self._latest_ymin[cidx]:
                                if comb_miny:
                                    if self._latest_ymin[cidx] <= comb_miny:
                                        comb_miny = self._latest_ymin[cidx]
                                else:
                                    comb_miny = self._latest_ymin[cidx]

                                if comb_maxy:
                                    if self._latest_ymin[cidx] >= comb_maxy:
                                        comb_maxy = self._latest_ymax[cidx]
                                else:
                                    comb_maxy = self._latest_ymax[cidx]
                                        

                        self._axes[0].draw_artist(self._plot[cidx])
                else:
                    if not self._ptype[cidx] == CHOICE_NONE:
                        if self._latest_ymax[cidx]:
                            if self._latest_ymin[cidx]:
                                cmin, cmax = self._axes[cidx].get_ylim()
                                newmin, newmax = self._calc_new_minmax(
                                                        self._latest_ymin[cidx],
                                                        self._latest_ymax[cidx]
                                                                        )
                                if ((not newmin == cmin)
                                    or (not newmax == cmax)):

                                    need_to_draw[cidx] = True
                                    self._axes[cidx].set_ylim(newmin, newmax)

                        try:
                            self._axes[cidx].draw_artist(self._plot[cidx])
                        except AttributeError:
                            pass
                        except AssertionError:
                            pass
                            
            
            if self._combine_data_flag == "Yes":
                if comb_miny:
                    if comb_maxy:
                        cmin, cmax = self._axes[0].get_ylim()
                        newmin, newmax = self._calc_new_minmax(
                                                            comb_miny,
                                                            comb_maxy
                                                               )
                        
                        if ((not newmin == cmin)
                            or (not newmax == cmax)):

                            need_to_draw[1] = True
                            self._axes[0].set_ylim(newmin, newmax)

            if canvas:
                for i in self._axes.keys():
                    if self._combine_data_flag == "Tabs":
                        cbidx = i
                    else:
                        cbidx = 0
                    canvas[cbidx].blit(self._axes[i].bbox)
                    
                    if need_to_draw[i]:
                        canvas[cbidx].draw()
            

    def _calc_new_minmax(self, ymin, ymax):
        '''
        calculate new min/max values
        '''
        buff = ((ymax - ymin) / 3 )
        newmin = ymin - buff
        newmax = ymax + buff
        
        return newmin, newmax
                                

    def _load_plot_values(self):
        '''
        load plot y array from queue
        '''
        tmp = self._get_data()
        
        yv = {}
        xv = {}
        numelm = {}

        # There are up to 4 plots 1-4.
        # And tmp contains up to 4 return values (also 1-4)
        # for each of the 4
        # build array of return data (2nd of the return tuple from tmp)
        # then append the new return data to end of current yval array
        # but retain the current size of yval array
        # SO.... if yval starts with .... 1,2,3,4
        # AND rtn contains ..  5,6
        # the END value will be...  3,4,5,6
        # returning values push out earlier values.
        for cidx in range(0,4):
            yv[cidx] = []
            xv[cidx] = []
            self._latest_ymax[cidx] = None
            self._latest_ymin[cidx] = None
            numelm[cidx] = len(tmp[cidx])
            for vv in range(0, numelm[cidx]):
                if len(tmp[cidx][vv]) > 0:
                    #print "tmp[1][vv]", tmp[1][vv]
                    tm,va = tmp[cidx][vv]
                    yv[cidx].append(va)
                    xv[cidx].append(tm)

            if len(yv[cidx]) > 0:
                self.yval[cidx] = self.yval[cidx][numelm[cidx]:] + yv[cidx]
                for va in self.yval[cidx]:
                    if va:
                        if self._latest_ymax[cidx]:
                            if va >= self._latest_ymax[cidx]:
                                #print "max change:", va
                                self._latest_ymax[cidx] = va
                        else:
                            self._latest_ymax[cidx] = va
                        
                        if self._latest_ymin[cidx]:
                            if va <= self._latest_ymin[cidx]:
                                #print "min change:", va
                                self._latest_ymin[cidx] = va
                        else:
                            self._latest_ymin[cidx] = va
                #self.xval[cidx] = self.xval[cidx][numelm[cidx]:] + xv[cidx]
            

    def refresh_html(self):
        self._counter += 1
        if self._counter > 10:
            self.process_parms["html_source"][0] = self._build_html()
        
    def _get_data(self):
        '''
        get and return from queues
        '''
        if SIMULATE_DATA:
            new_data = self._get_simulated_data()
        else:
            new_data = self.data_listener.get_data()
        
        now = {}
        for cidx in range(0,4):
            now[cidx] = []
            if not self._ptype[cidx] == CHOICE_NONE:
                if self.stream_name_dict[self._ptype[cidx]] in new_data.keys():
                    now[cidx] = new_data[self.stream_name_dict[self._ptype[cidx]]]

        self._before = now
        #print "now", now
        return now


    def _get_simulated_data(self):
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
        

    def _log(self, msg):
        ii = len(self._message_array)
        self._message_array[ii] = (datetime.datetime.now(), msg)


    def _plot_minmax_switch(self):
        for cidx in self._ptype.keys():
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
                            #print "ymin: %s  ymax: %s" % (ymin, ymax)



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
            #print "seems the queue is NOT empty"
            try:
                data = self.queue.get()
                #print "data", data.streamNum,
                #print data.timestamp,
                #print data.value
                #print
                utime = timestamp.unixTime(data.timestamp)
    
                if data.streamNum == interface.STREAM_Ratio1:
                    rtn[data.streamNum].append((utime, data.value/32768.0))
                elif data.streamNum == interface.STREAM_Ratio2:
                    rtn[data.streamNum].append((utime, data.value/32768.0))
                else:
                    rtn[data.streamNum].append((utime, data.value))
                
            except: # Queue.Empty:
                #print "empty queue"
                break
                
        #print "rtn", rtn
        return rtn
        

        
if __name__ == '__main__':
    msg = "liveplotmodel.py"
    msg += " defines a class which cannot be run as a stand-alone process."
    raise RuntimeError, msg