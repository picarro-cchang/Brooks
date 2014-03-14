'''
ringdownplot.py -- The ringdownplot module contains the RingdownPlotController 
class. This class will display an XY plot of data from the 
BROADCAST_PORT_RDRESULTS.

The interactive UI allows for selection of up to 4 XY plots of data from the 
source.

The interactive UI allows user selection for graph markers and marker colors.

The interactive UI displays the selected graph

This module can run interactively or in batch. In batch mode it 
will export (save) a graph as its normal output:

Interactive mode USAGE: 
ringdownplot.py [ -h ] [ -s ] [ --help ] [ --skip-layout ] [ ctl_file_name ]
  
OPTIONS
  -h, --help                Show usage information
      
  -s, --skip-layout         Skip using last layout (start off with the default 
                            tab layout)

ARGUMENTS 
  ctl_file_name             Name of the ctl_file to use to restore the last 
                            saved parameters.

                            ini file format:
                            LAST POINTS: last_points
                            LAST P1TYPE: plot_type
                            LAST P2TYPE: plot_type
                            LAST P3TYPE: plot_type
                            LAST P4TYPE: plot_type
                            LAST COMBINE DATA: yn

                            last_points is the number of X data points in the 
                            plot (an integer).
                            
                            plot_type is the type of plot
                            
                            yn is 'Yes' or 'No'

EXAMPLES
    ringdownplot.py --skip-layout
        This would run the live plot but skip restoring the last tab layout. 
        
    ringdownplot.py some_new_ctl_file.ini
        This would run the live plot and use data in some_new_ctl_file.ini to 
        fill the parameters

'''
import os
import sys
import getopt
import datetime, time, random

import wx
import wx.lib.agw.pybusyinfo as PBI

from postprocessdefn import *
from postprocesscontrol import PostProcessController, EntryControls
from ringdownplotmodel import RingdownPlotModel


class RingdownPlotController(PostProcessController):
    '''
    RingdownPlot Controller Class
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if not "ctl_file" in kwargs:
            kwargs["ctl_file"] = "ringdownplot.ctl"

        PostProcessController.__init__(self, *args, **kwargs)

        # About Info
        self.about_name = "RingdownPlot Controller"
        self.about_version = "1.0.0"
        self.about_copyright = "(c) 2010 Picarro Inc."
        self.about_description = "Graphic plot of analyzer output."
        self.about_website = "http://www.picarro.com"
        
        self.allow_fi = True
        
        msg = "Processing the parameters."
        msg += "\nThis may take some time..."
        self._busy_msg = msg                

    def _do_control_configuration(self):
        '''
        set up all specific configurations for the class
        '''
        self._model = RingdownPlotModel(
                                        cntls_obj = self.cntls_obj,
                                        fig_act = self.fig_act
                                        )

        self._model._plot_canvas = self._plot_pnl
        self.plot_facecolor = self._model.plot_facecolor
        
        fmt_str = "%a, %b %d, %Y, %H:%M:%S"
        fmt2_str = "%Y%m%d%H%M%S"
        
        self._title = "RingdownPlot - %s" % (self._dt.strftime(fmt_str))
        self._title_filename = "RingdownPlot_%s" % (
                                                   self._dt.strftime(fmt2_str)
                                                       )

        self._layout_name = "ringdownplot"
        self._frame_title = "Picarro Post Processing - Ringdown Plot"
        self._sz = ((900, 600))
        self._layout = None
        #self._layout = "4cbc73200000000000000002=3,1|4cbc733a0000001900000003=+0,5|4cbc73780000005700000007=4|4cbc73920000007100000007=2@layout2|name=dummy;caption=;state=67372030;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=180;besth=180;minw=180;minh=180;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=4cbc73200000000000000002;caption=;state=67372028;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=200;besth=200;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=4cbc733a0000001900000003;caption=;state=67372028;dir=4;layer=0;row=1;pos=0;prop=100000;bestw=442;besth=255;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=4cbc73780000005700000007;caption=;state=67372028;dir=3;layer=0;row=1;pos=0;prop=40292;bestw=180;besth=180;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=4cbc73920000007100000007;caption=;state=67372028;dir=3;layer=0;row=1;pos=1;prop=126824;bestw=180;besth=180;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=202|dock_size(4,0,1)=212|dock_size(3,0,1)=129|"

        self.hidden_names = []
        
        self.parm_cntl = {}
        self.name_fld_dict = {}

        self.parameter_defn_column_count = 1
        
        self.selection_defn_column_count = 1

        self.cntls_len = {}
        
        for name, cntlobj in self.cntls_obj.control_list.iteritems():
            setattr(self, "%s_cntlobj" % (name), cntlobj)
            if not cntlobj.location in self.cntls_len.keys():
                self.cntls_len[cntlobj.location] = 0
            
            self.cntls_len[cntlobj.location] += 1
            

        self.cntls_cols = {
                           #PANEL: (nbr_of_columns, size_factor),
                           PARAMETER: (1, 100), 
                           PLOT0: (1, 20),
                           PLOT1: (1, 20),
                           PLOT2: (1, 20),
                           MOD0: (2, 100),
                           MOD1: (2, 100),
                           }


        self.timers_defn_dict = {
                                  "CUST1": (HTML, 
                                            "self._plot_pnl", 
                                            025, 
                                            True
                                            ),
                                  "CUST2": (HTML, 
                                            "", 
                                            1000, 
                                            True
                                            ),
                                  "CUST3": (HTML, 
                                            "self._plot_pnl", 
                                            1000, 
                                            True
                                            ),
                                  }
        
        self.button_size = 100
        self.buttons_defn_dict = {
                                  SOURCE: None,
                                  "CUST1": (HTML, "Export All PNG", None, None),
                                  "CUST2": (HTML, "Export All PDF", None, None),
                                  #"CUST1": (HTML, "Start Data", None, None),
                                  #"CUST2": (HTML, "Stop Data", None, None),
                                  "CUST19": (HTML, "Refresh All", None, None),
                                  "CUST20": (HTML, "Apply", None, None),
                                  "CUST21": (HTML, "Save to MFG DB", None, None),
                                  "CUST22": (HTML, "Controls", None, None),
                                  }
        
        self.buttons_ord_list = [
                                 "CUST22", 
                                 "CUST1", 
                                 "CUST2", 
                                 "CUST19", 
                                 "CUST20",
                                 "CUST21",
                                 ]
        
        self.pbutton_size = 90
        self.pbuttons_defn_dict = {
                                  "CUST3": (PLOT0, "Refresh", None, None),
                                  "CUST4": (PLOT1, "Refresh", None, None),
                                  "CUST5": (PLOT2, "Refresh", None, None),
                                  #"CUST6": (PLOT3, "Refresh", None, None),
                                  "CUST7": (PLOT0, "Freeze", None, None),
                                  "CUST8": (PLOT1, "Freeze", None, None),
                                  "CUST9": (PLOT2, "Freeze", None, None),
                                  #"CUST10": (PLOT3, "Freeze", None, None),
                                  "CUST11": (PLOT0, "Export PNG", None, None),
                                  "CUST12": (PLOT0, "Export PDF", None, None),
                                  "CUST13": (PLOT1, "Export PNG", None, None),
                                  "CUST14": (PLOT1, "Export PDF", None, None),
                                  "CUST15": (PLOT2, "Export PNG", None, None),
                                  "CUST16": (PLOT2, "Export PDF", None, None),
                                  #"CUST17": (PLOT3, "Export PNG", None, None),
                                  #"CUST18": (PLOT3, "Export PDF", None, None),
                                  }

        self.pbuttons_ord_list = [
                                 "CUST3", 
                                 "CUST4", 
                                 "CUST5", 
                                 "CUST7", 
                                 "CUST8",
                                 "CUST9",
                                 "CUST10",
                                 "CUST11",
                                 "CUST12",
                                 "CUST13",
                                 "CUST14",
                                 "CUST15",
                                 "CUST16",
                                 ]

               
        self.custom1_routine_data = {DIROPEN: True,
                                     OPEN_MSG: "Please select folder location for saved Image Files"}

        self.custom2_routine_data = {DIROPEN: True,
                                     OPEN_MSG: "Please select folder location for saved PDF Files"}

        self.custom11_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.png" % (self._title_filename, "plot0"),
                                     WILDCARD: "*.png",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom12_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.pdf" % (self._title_filename, "plot0"),
                                     WILDCARD: "*.pdf",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom13_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.png" % (self._title_filename, "plot1"),
                                     WILDCARD: "*.png",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom14_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.pdf" % (self._title_filename, "plot1"),
                                     WILDCARD: "*.pdf",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom15_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.png" % (self._title_filename, "plot2"),
                                     WILDCARD: "*.png",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom16_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.pdf" % (self._title_filename, "plot2"),
                                     WILDCARD: "*.pdf",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom17_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.png" % (self._title_filename, "plot3"),
                                     WILDCARD: "*.png",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom18_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s_%s.pdf" % (self._title_filename, "plot3"),
                                     WILDCARD: "*.pdf",
                                     GOOD_MSG: "Image has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }


        self.custom21_routine_data = {MODAL_WIN: True,
                                     "idx": 0,
                                     "pause_timer": True,
                                     }


        self.custom22_routine_data = {MODAL_WIN: True,
                                     "idx": 1,
                                     "pause_timer": True,
                                     
                                     }


        self.panels_defn_dict = {PLOT: 3, HTML: 1, MOD: 2}       

        self._html = {0: "", 
                      }
        
        self._html_title = {0: "Log", 
                           } 
        
        self.initial_frame_process = [
                                      {BUTTON: "CUST22"},
                                      {PROCESS: True},
                                      ]
                                       
                                      
#        self._plot_figure = {0: None, 
#                      1: None,
#                      2: None, 
#                      3: None} 
        
        self._plot_figure = None


        self._next_frame = HTML
        
        self._max_source_lines = 100
        
        self._outdir = ""

        self._brief_html = None


        #activate following when you need to save the layout to an external
        #file - for example, you need to change the default layout string
        #and you need to capture the layout
        #self._save_external_layout_file = "ringdownplot.layout"
        
        self._model.after_config_init()


    def reset_selection_values(self, values_dict = None):
        '''
        reset selection values to default (or passed in values)
            values_dict["combine_data"], 
            values_dict["p1_type"], 
        '''
        if not values_dict:
            values_dict = {}
        
        for kname, control in self.cntls_obj.control_list.iteritems():
            if kname in values_dict.keys():
                value = values_dict[kname]
            else:
                value = control.default
            
            control.set_value(value)
        
        return 


    def do_post_ctl_processing(self, last_values_dict):
        self.reset_selection_values(last_values_dict)


    def generate_chart(self, savefile=None, datavals=None):
        
        if datavals:
            sel_vals = datavals
        else:
            sel_vals = self.retrieve_values_from_controls()
                
        self._plot_figure = {}
        self._plot_data = {}
        exptfile = None
        
        #self._resolve_selection()
        
        export_data = None
        
        sel_vals["export_data"] = export_data
        self._model.generate_plot(
                                  sel_vals,
                                  self._notebook,
                                  self._plot_page_tidx
                                )

        if "plot_fig" in self._model.process_parms.keys():
            self._plot_figure = self._model.process_parms["plot_fig"]
            if "plot_data" in self._model.process_parms.keys():
                self._plot_data = self._model.process_parms["plot_data"]

        return True

        
    def save_file(self, btn):
        routine_data = getattr(self, "custom%s_routine_data" % (btn))
        if STEP in routine_data.keys():
            if routine_data[STEP] == 1:
                if RTN_OUTFILE in routine_data.keys():
                    routine_data[INFO_MSG] = "%s: %s" % (
                                                 routine_data[GOOD_MSG], 
                                                 routine_data[RTN_OUTFILE]
                                                         )
                    
                    if btn in (11, 12):
                        idx = 0
                    elif btn in (13, 14):
                        idx = 1
                    elif btn in (15, 16):
                        idx = 2
                    else:
                        return False
                    
                    self._save_plot_data(idx, routine_data[RTN_OUTFILE])
                    #self._plot_figure[idx].savefig(routine_data[RTN_OUTFILE])
            
            return True
        
        return None
    

    def _save_plot_data(self, plotidx, savefile):
        '''
        save the plot to requested location, and also save the data.
        '''
        self._model.save_fig(plotidx, savefile)
        #self._plot_figure[plotidx].savefig(savefile)

    def resize_process(self):
        '''
        custom timer 1 for refreshing plot
        '''
        self.refresh_the_plots = True
        return None

    def refresh_routine_data(self, idx=None):
        if idx in (11, 12, 13, 14, 15, 16, 17, 18):
            dt = datetime.datetime.now()
            fmt2_str = "%Y%m%d%H%M%S"
            if idx in (11, 12):
                pidx = 0
            elif idx in (13, 14):
                pidx = 1
            elif idx in (15, 16):
                pidx = 2
            else:
                pidx = 3
            filename = "%s_%s" % (self._model.plot_name[pidx], 
                                  dt.strftime(fmt2_str)
                                  )
            #print "filename", filename
            routine_data = getattr(self, "custom%s_routine_data" % (idx))
            routine_data[OUTFILE] = filename

            #print "refreshing the routine_data for ", idx
        return None


    def process_ok(self, dlg=None):
        '''
        stub process from ok (and reload) button
        '''
        msg = "Processing request."
        msg += "\nThis may take some time."
        msg += " Please wait..."
        dlg = wx.BusyInfo(msg)

        self._model.process_source(self._file_source, self._brief_html)
        if self._model.process_parms[STATUS] == OK:

            rtn_val = self._model.control_the_analyzer()

            if rtn_val == "OK":
                self.generate_chart()

        del dlg
            
        return
        

    def custom1_btn_process(self, parm=None):
        #print "parm", parm
        dt = datetime.datetime.now()
        fmt2_str = "%Y%m%d%H%M%S"
        for idx in self._plot_figure.keys():
            filename = "%s_%s.png" % (self._model.plot_name[idx], 
                                  dt.strftime(fmt2_str)
                                  )
            
            path = os.path.join(parm, filename)
            self._save_plot_data(idx, path)
            #self._plot_figure[idx].savefig(path)
            
            
        
        self._next_frame = None
        return

    def custom2_btn_process(self, parm=None):
        dt = datetime.datetime.now()
        fmt2_str = "%Y%m%d%H%M%S"
        for idx in self._plot_figure.keys():
            filename = "%s_%s.pdf" % (self._model.plot_name[idx], 
                                  dt.strftime(fmt2_str)
                                  )
            
            path = os.path.join(parm, filename)
            self._save_plot_data(idx, path)
            #self._plot_figure[idx].savefig(path)
        
        self._next_frame = None
        return

    def custom3_btn_process(self, parm=None):
        #print "refresh plot 0!!"
        self._refresh_plot(0)
        self._next_frame = None
        return

    def custom4_btn_process(self, parm=None):
        #print "refresh plot 1!!"
        self._refresh_plot(1)
        self._next_frame = None
        return

    def custom5_btn_process(self, parm=None):
        #print "refresh plot 2!!"
        self._refresh_plot(2)
        self._next_frame = None
        return

    def custom6_btn_process(self, parm=None):
        #print "refresh plot 3!!"
        self._refresh_plot(3)
        self._next_frame = None
        return

    def _refresh_plot(self, idx):
        sel_vals = self.retrieve_values_from_controls()
        self._rlock.acquire()
        rtn_val = self._model.next_from_buffer_process(
                                             self._notebook, 
                                             self._plot_page_tidx, 
                                             self._plot_pnl, 
                                             idx,
                                             self.refresh_the_plots,
                                             self.fig_act,
                                             sel_vals
                                             )
        self._rlock.release()

    def custom7_btn_process(self, parm=None):
        #print "refresh plot 3!!"
        if self._model.freeze[0]:
            self._model.freeze[0] = None
        else:
            self._model.freeze[0] = True

        self._next_frame = None
        return

    def custom8_btn_process(self, parm=None):
        #print "refresh plot 3!!"
        if self._model.freeze[1]:
            self._model.freeze[1] = None
        else:
            self._model.freeze[1] = True

        self._next_frame = None
        return

    def custom9_btn_process(self, parm=None):
        #print "refresh plot 3!!"
        if self._model.freeze[2]:
            self._model.freeze[2] = None
        else:
            self._model.freeze[2] = True

        self._next_frame = None
        return

    def custom10_btn_process(self, parm=None):
        #print "refresh plot 3!!"
        if self._model.freeze[3]:
            self._model.freeze[3] = None
        else:
            self._model.freeze[3] = True

        self._next_frame = None
        return


    def custom11_btn_process(self, parm=None):
        self._next_frame = None
        return


    def custom12_btn_process(self, parm=None):
        self._next_frame = None
        return


    def custom13_btn_process(self, parm=None):
        self._next_frame = None
        return


    def custom14_btn_process(self, parm=None):
        self._next_frame = None
        return


    def custom15_btn_process(self, parm=None):
        self._next_frame = None
        return


    def custom16_btn_process(self, parm=None):
        self._next_frame = None
        return


    def custom19_btn_process(self, parm=None):
        #print "refresh plot 0!!"
        self._refresh_plot("all")
        self._next_frame = None
        return

    def custom20_btn_process(self, parm=None):
        sel_vals = self.retrieve_values_from_controls()
        #print " apply button sel_vals", sel_vals
        if not self._model._status == "working":
            self._rlock.acquire()
            self._model.macro_mode_active = None
            self._model.next_from_buffer_process(
                                                 self._notebook, 
                                                 self._plot_page_tidx, 
                                                 self._plot_pnl, 
                                                 None,
                                                 self.refresh_the_plots,
                                                 self.fig_act,
                                                 sel_vals
                                                 )
            self._rlock.release()
        
        #print "in custom20"
        if "plot_fig" in self._model.process_parms.keys():
            self._plot_figure = self._model.process_parms["plot_fig"]
            if "plot_data" in self._model.process_parms.keys():
                self._plot_data = self._model.process_parms["plot_data"]

        self._next_frame = None


    def custom21_btn_process(self, parm=None):
        self._next_frame = None
        return


    def custom22_btn_process(self, parm=None):
        self._next_frame = None
        return


    def pre_modal_process(self, routine_data):
        testname = self._get_default_testname()
        if "idx" in routine_data.keys():
            idx = routine_data["idx"]
            if idx == 0:
                self._load_save_to_db_values(testname)
                self._model.preserve_plot_values()
                #routine_data["release_timer"] = True
                routine_data["title"] = "Save Buildstation Data to MFG Database"
            elif idx == 1:
                routine_data["title"] = "Submit control request to analyzer"
        
        return
    
    def _get_default_testname(self):
        dt = datetime.datetime.now()
        fmt2_str = "%Y%m%d%H%M%S"
        testname = "%s_%s" % (self._model.station_id, 
                              dt.strftime(fmt2_str)
                              )
        
        return testname
    
    def post_modal_process(self, rtn=None, routine_data=None):
        #print "!! HERE IN POST MODAL !!"
        if not rtn == wx.ID_OK:
            return
        
        if "idx" in routine_data.keys():
            idx = routine_data["idx"]
            if idx == 0:
                msg = "Sending data to the MFG database."
                msg += "\nThis may take some time."
                msg += " Please wait..."
                dlg = wx.BusyInfo(msg)
            
                rtn_val = self._model.save_to_database()
                self._load_modal_to_parm_values()

                del dlg
                
                if rtn_val == "OK":
                    msg = "Data sucessfully saved into MFG database."
                    routine_data[POST_BTN_MSG] = msg
                else:
                    routine_data[POST_BTN_ERROR_MSG] = rtn_val
                    
            elif idx == 1:
                msg = "Submitting control request to analyzer."
                msg += "\nThis may take some time."
                msg += "Please wait..."
                dlg = wx.BusyInfo(msg)
                
                print "!!!!!!! Control !!!!!!!"
                rtn_val = self._model.control_the_analyzer(
                                                 self._notebook, 
                                                 self._plot_page_tidx, 
                                                 self._plot_pnl, 
                                                           )
                #self._load_modal_to_parm_values()

                del dlg
                
                print "BACK FROM CONTROL"
                
                if rtn_val == "OK":
                    msg = "Analyzer control request was submitted."
                    routine_data[POST_BTN_MSG] = msg
                else:
                    routine_data[POST_BTN_ERROR_MSG] = rtn_val
                    
        return
    

    def _load_save_to_db_values(self, testname=None):
        '''
        load relevant data from the parameter controls to the modal
        dialog screen
        '''
        for cv_pair in self._model.cntl_to_modal_pairs:
            mname, cname = cv_pair
            mcontrol = self.cntls_obj.control_list[mname]
            ccontrol = self.cntls_obj.control_list[cname]
            
            mcontrol.set_value(ccontrol.get_value())
        
        if testname:
            self.cntls_obj.control_list["mdl_test_id"].set_value(testname)

        dt = datetime.datetime.now()
        fmt_str = "%m/%d/%Y %H:%M:%S"
        self.cntls_obj.control_list["mdl_date"].set_value(dt.strftime(fmt_str))


        
    def _load_modal_to_parm_values(self):
        '''
        load relevant data from the parameter controls to the modal
        dialog screen
        '''
        for cv_pair in self._model.cntl_to_modal_pairs:
            mname, cname = cv_pair
            if mname in (
                         "mdl_mirror_id", 
                         "mdl_lot_id", 
                         "mdl_user_id",
                         "mdl_cavity_id",
                         "mdl_cavity_sn"
                         ):
                mcontrol = self.cntls_obj.control_list[mname]
                ccontrol = self.cntls_obj.control_list[cname]
                
                ccontrol.set_value(mcontrol.get_value())
        

    def custom1_timer_process(self, restart=None, canvasdict=None):
        '''
        custom timer 1 for refreshing plot
        '''
        self._model._plot_canvas = self._plot_pnl

        if not self._model._status == "working":
            if not self._model.ringdown_plot_active:
                self._rlock.acquire()
                rtn_val = self._model.next_from_buffer_process(
                                                     self._notebook, 
                                                     self._plot_page_tidx, 
                                                     canvasdict, 
                                                     restart,
                                                     self.refresh_the_plots,
                                                     self.fig_act
                                                     )
                self._rlock.release()
                if self.refresh_the_plots:
                    self.refresh_the_plots = None
                    
                return rtn_val
            
        return None
    
    def custom2_timer_process(self, restart=None, canvasdict=None):
        '''
        custom timer 2 for refreshing log messages to html tab
        '''
        self._model._plot_canvas = self._plot_pnl

        if 0 in self._model.process_parms["html_source"]:
            before_len = len(self._model.process_parms["html_source"][0])
            self._model.refresh_html()
            after_len = len(self._model.process_parms["html_source"][0])
            
            if not before_len == after_len:
                self._html[0] = self._model.process_parms["html_source"][0]
                return {"html.0": "refresh"}

        return None
    
    def custom3_timer_process(self, restart=None, canvasdict=None):
        '''
        custom timer 3 for refreshing ringdowns
        '''
        self._model._plot_canvas = self._plot_pnl

        if not self._model._status == "working":
            if self._model.ringdown_plot_active:
                self._rlock.acquire()
                rtn_val = self._model.next_from_buffer_process(
                                                     self._notebook, 
                                                     self._plot_page_tidx, 
                                                     canvasdict, 
                                                     restart,
                                                     self.refresh_the_plots,
                                                     self.fig_act
                                                     )
                self._rlock.release()
                if self.refresh_the_plots:
                    self.refresh_the_plots = None
                    
                return rtn_val
            
        return None
    
    def next_frame(self):
        '''
        next frame stub:
        '''
        skip_layout = None
        
        if self._next_frame:
            self._model.process_source(self._file_source, self._brief_html)
            if self._model.process_parms[STATUS] == OK:
                self.generate_chart()
        else:
            skip_layout = True
        
        return self._next_frame, skip_layout


    def save_ctl(self):
        '''
        save last_used values into ctl file
        '''
        try:
            ctl_f = open(self._ctl_file, "w")
            if ctl_f:
                str = ""
                for name, control in self.cntls_obj.control_list.iteritems():
                    if control.ctl_name:
                        # Force to always start up in Ringdown mode
                        if name == "rd_mode":
                            save_term = "%s: %s\n" % (
                                                control.ctl_name,
                                                "Ringdown"
                                                    )
                        else:
                            save_term = "%s: %s\n" % (
                                                control.ctl_name,
                                                control.get_value()
                                                    )

                        str += save_term
                        

                ctl_f.write(str)
        except:
            pass

        return

    def frame_color_init(self):
        '''
        stub to modify frame colors. Return None or a dictionary. 
        Valid dictionary keys are:
        mainBackgroundColor
        controlBackgroundColor
        plotBackgroundColor
        
        example:
                return {"mainBackgroundColor": MAIN_BACKGROUNDCOLOR,
                        "controlBackgroundColor": CONTROL_BACKGROUNDCOLOR,
                        "plotBackgroundColor": PLOT_FACECOLOR}

        '''
        return {"plotBackgroundColor": self.plot_facecolor}
    


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], 
                                       "hs", 
                                       ["help", 
                                        "skip-layout",]
                                       )
        except getopt.error, msg:
             raise Usage(msg)

        for o, a in opts:
            if o in ("-h", "--help"):
                raise Usage(__doc__) 

        parm_dict = {
                     "skip_layout": None,
                     "ctl_file": None,
                     "batch_type": None,
                     "save_loc": None,
                     "save_name": None,
                    }

        _get_opts_and_args(parm_dict, opts)
        _setup_and_validate_parms(parm_dict, args)    
            
        ctl_file = None
        batch_type = None
        save_loc = None
        save_name = None
        
        if parm_dict["ctl_file"]:
            c = RingdownPlotController(ctl_file=parm_dict["ctl_file"]) 
        else:
            c = RingdownPlotController() 

        if parm_dict["skip_layout"]:
            c.skip_layout = True
    
        if parm_dict["batch_type"]:
            if parm_dict["batch_type"] in ("pdf", "png"):
                c.process_source_file()
                #datavals = c.build_selection_dict()
                
                if not parm_dict["save_name"]:
                    parm_dict["save_name"] = c._title_filename
                    
                if parm_dict["save_loc"]:
                    rtn_outfile = os.path.join(
                                           parm_dict["save_loc"], 
                                           "%s.%s" % (parm_dict["save_name"], 
                                                      parm_dict["batch_type"])
                                               )
                else:
                    rtn_outfile = "%s.%s" % (
                                             parm_dict["save_name"], 
                                             parm_dict["batch_type"]
                                             )
                
                c.generate_chart(rtn_outfile, datavals)
            else:
                raise Usage(__doc__)
        else:
            c.show_main_gui()
            
        # more code, unchanged
    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "for help use --help"
        return 2

def _get_opts_and_args(parm_dict, opts):
    '''
    get passed in options and arguments
    '''
    for user_opt, user_arg in opts:
        if user_opt in ("-h", "--help"):
            raise Usage(__doc__) 
        if user_opt in ("-s", "--skip-layout"):
            parm_dict["skip_layout"] = True

def _setup_and_validate_parms(parm_dict, args):
    '''
    setup parms from passed in arguments
    '''
    all_ok = True

    if len(args) == 1:
        parm_dict["ctl_file"] = args[0]

    if 2 <= len(args):
        parm_dict["batch_type"] = args[1]
    if 3 <= len(args):
        parm_dict["save_loc"] = args[2]
    if 4 <= len(args):
        parm_dict["save_name"] = args[3]
    
        
    if not all_ok:
        raise Usage(__doc__) 


if __name__ == '__main__':
    sys.exit(main())
