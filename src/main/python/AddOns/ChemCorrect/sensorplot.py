'''
sensorplot.py -- The sensorplot module contains the SensorPlotController class.
This class will display an XY plot of data from the BROADCAST_PORT_SENSORSTREAM.

The interactive UI allows for selection of up to 4 Y columns of data from the 
source. X is points of data from the stream.

The interactive UI allows user selection for graph markers and marker colors.

The interactive UI displays the selected graph

This module can run interactively or in batch. In batch mode it 
will export (save) a graph as its normal output:

Interactive mode USAGE: 
sensorplot.py [ -h ] [ -s ] [ --help ] [ --skip-layout ] [ ctl_file_name ]
  
OPTIONS
  -h, --help                Show usage information
      
  -s, --skip-layout         Skip using last layout (start off with the default 
                            tab layout)

ARGUMENTS 
  ctl_file_name             Name of the ctl_file to use to restore the last 
                            saved parameters.

                            ini file format:
                            LAST POINTS: last_points
                            LAST Y1COL: column_name
                            LAST Y2COL: column_name
                            LAST Y3COL: column_name
                            LAST Y4COL: column_name
                            LAST COMBINE DATA: yn

                            last_points is the number of X data points in the 
                            plot (an integer).
                            
                            column_name is the Y column name for the plot
                            
                            yn is 'Yes' or 'No'

EXAMPLES
    sensorplot.py --skip-layout
        This would run the live plot but skip restoring the last tab layout. 
        
    sensorplot.py some_new_ctl_file.ini
        This would run the live plot and use data in some_new_ctl_file.ini to 
        fill the parameters

'''
import os
import sys
import getopt
import datetime, time, random

import wx

from postprocessdefn import *
from postprocesscontrol import PostProcessController, EntryControls
from sensorplotmodel import SensorPlotModel

from Host.autogen import interface

from Utilities import AppInfo


class SensorPlotController(PostProcessController):
    '''
    SensorPlot Controller Class
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if not "ctl_file" in kwargs:
            kwargs["ctl_file"] = "sensorplot.ctl"

        PostProcessController.__init__(self, *args, **kwargs)

        # version and about info
        about = AppInfo()
        self.about_version = about.getAppVer()
        self.about_name = "SensorPlot Controller"  #about.getAppName()
        self.about_copyright = about.getCopyright()
        self.about_description = "Graphic plot of analyzer output."  # about.getDescription()
        self.about_website = about.getWebSite()

        msg = "Processing the parameters."
        msg += "\nThis may take some time..."
        self._busy_msg = msg  

    def _do_control_configuration(self):
        '''
        set up all specific configurations for the class
        '''
        self._model = SensorPlotModel(
                                        cntls_obj = self.cntls_obj,
                                        fig_act = self.fig_act
                                        )

        fmt_str = "%a, %b %d, %Y, %H:%M:%S"
        fmt2_str = "%Y%m%d%H%M%S"
        
        self._title = "SensorPlot - %s" % (self._dt.strftime(fmt_str))
        self._title_filename = "SensorPlot_%s" % (
                                                   self._dt.strftime(fmt2_str)
                                                       )

        self._layout_name = "sensorplot"
        self._frame_title = "Picarro Post Processing - Sensor Plot"
        self._sz = ((900, 600))
        self._layout = "4cb5d8c00000000000000002=+0,1,2,3,4,5@layout2|\
        name=dummy;caption=;state=67372030;dir=3;layer=0;row=0;pos=0;\
        prop=100000;bestw=442;besth=255;minw=442;minh=255;maxw=-1;maxh=-1;\
        floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|\
        name=4cb5d8c00000000000000002;caption=;state=67372028;dir=5;layer=0;\
        row=0;pos=0;prop=100000;bestw=200;besth=200;minw=-1;minh=-1;maxw=-1;\
        maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;\
        transparent=255|dock_size(5,0,0)=202|"


        self.list_yes_no = []
        self.list_yes_no.append("No")
        self.list_yes_no.append("Yes")

        self.list_tabs = []
        self.list_tabs.append("Single Tab")
        self.list_tabs.append("Separate Tabs")
        self.list_tabs.append("Combine and Correlate")

        self.list_ychoice = []
        self.list_ychoice.append(CHOICE_NONE)
        for idx, mbr in interface.STREAM_MemberTypeDict.iteritems():
            val = mbr.replace("STREAM_", "")
            self.list_ychoice.append(val)
        
        self.parameter_names = [
                       ]
        
        self.hidden_names = []
        
        self.parm_cntl = {}
        self.name_fld_dict = {}

        self.parameter_defn_column_count = 1
        
        self.selection_defn_column_count = 1

        txt_len = 80
        cntl_len = 200
        tiny_len = 65
        ord = 0
        
        ord += 10
        self.cntls_obj.new_control(
                                   POINTS_PARM,
                                   order = ord,
                                   control_size = txt_len, #cntl size (on frame)
                                   label = "Points", #screen label
                                   ctl_name = "LAST POINTS", #cntl_file_entry
                                   type = TEXT_CNTL, #type of control
                                   location = PARAMETER, #location of control
                                   default = "1000"
                                   )
        
        ord += 10
        self.cntls_obj.new_control(
                                   "y1_col",
                                   order = ord,
                                   control_size = txt_len, #cntl size (on frame)
                                   label = "Y1 Column", #screen label
                                   ctl_name = "LAST Y1COL", #cntl_file_entry
                                   type = CHOICE_CNTL, #type of control
                                   location = PARAMETER, #location of control
                                   default = CHOICE_NONE,
                                   values_list = self.list_ychoice
                                   )
        
        ord += 10
        self.cntls_obj.new_control(
                                   "y2_col",
                                   order = ord,
                                   control_size = txt_len, 
                                   label = "Y2 Column", 
                                   ctl_name = "LAST Y2COL",
                                   type = CHOICE_CNTL, #type of control
                                   location = PARAMETER, #location of control
                                   default = CHOICE_NONE,
                                   values_list = self.list_ychoice
                                   )
        
        ord += 10
        self.cntls_obj.new_control(
                                   "y3_col",
                                   order = ord,
                                   control_size = txt_len, 
                                   label = "Y3 Column", 
                                   ctl_name = "LAST Y3COL",
                                   type = CHOICE_CNTL, #type of control
                                   location = PARAMETER, #location of control
                                   default = CHOICE_NONE,
                                   values_list = self.list_ychoice
                                   )
        
        ord += 10
        self.cntls_obj.new_control(
                                   "y4_col",
                                   order = ord,
                                   control_size = txt_len, 
                                   label = "Y4 Column", 
                                   ctl_name = "LAST Y4COL",
                                   type = CHOICE_CNTL, #type of control
                                   location = PARAMETER, #location of control
                                   default = CHOICE_NONE,
                                   values_list = self.list_ychoice
                                   )
        
        ord += 10
        self.cntls_obj.new_control(
                                   "combine_data",
                                   order = ord,
                                   control_size = txt_len, 
                                   label = "Plot View?", 
                                   ctl_name = "LAST COMBINE DATA",
                                   type = CHOICE_CNTL, #type of control
                                   location = PARAMETER, #location of control
                                   default = "Separate Tabs",
                                   values_list =  self.list_tabs,
                                   )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt1_spacer1",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "", 
                                    ctl_name = None,
                                    type = SPACER_CNTL, #type of control
                                    location = PLOT0, #location of control
                                    default = ""
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt1_auto",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Autosize?", 
                                    ctl_name = "LAST PLT1 AUTO",
                                    type = RADIO_CNTL, #type of control
                                    location = PLOT0, #location of control
                                    values_list = self.list_yes_no,
                                    default = "Yes"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt1_ymin",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Min", 
                                    ctl_name = "LAST PLT1 YMIN",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT0, #location of control
                                    default = "20.0"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt1_ymax",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Max", 
                                    ctl_name = "LAST PLT1 YMAX",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT0, #location of control
                                    default = "70.0"
                                   )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt2_spacer",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "", 
                                    ctl_name = None,
                                    type = SPACER_CNTL, #type of control
                                    location = PLOT1, #location of control
                                    default = ""
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt2_auto",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Autosize?", 
                                    ctl_name = "LAST PLT2 AUTO",
                                    type = RADIO_CNTL, #type of control
                                    location = PLOT1, #location of control
                                    values_list = self.list_yes_no,
                                    default = "Yes"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt2_ymin",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Min", 
                                    ctl_name = "LAST PLT2 YMIN",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT1, #location of control
                                    default = "20.0"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt2_ymax",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Max", 
                                    ctl_name = "LAST PLT2 YMAX",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT1, #location of control
                                    default = "70.0"
                                   )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt3_spacer",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "", 
                                    ctl_name = None,
                                    type = SPACER_CNTL, #type of control
                                    location = PLOT2, #location of control
                                    default = ""
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt3_auto",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Autosize?", 
                                    ctl_name = "LAST PLT3 AUTO",
                                    type = RADIO_CNTL, #type of control
                                    location = PLOT2, #location of control
                                    values_list = self.list_yes_no,
                                    default = "Yes"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt3_ymin",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Min", 
                                    ctl_name = "LAST PLT3 YMIN",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT2, #location of control
                                    default = "20.0"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt3_ymax",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Max", 
                                    ctl_name = "LAST PLT3 YMAX",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT2, #location of control
                                    default = "70.0"
                                   )
        
        ord += 10
        self.cntls_obj.new_control(
                                    "plt4_spacer",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "", 
                                    ctl_name = None,
                                    type = SPACER_CNTL, #type of control
                                    location = PLOT3, #location of control
                                    default = ""
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt4_auto",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Autosize?", 
                                    ctl_name = "LAST PLT4 AUTO",
                                    type = RADIO_CNTL, #type of control
                                    location = PLOT3, #location of control
                                    values_list = self.list_yes_no,
                                    default = "Yes"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt4_ymin",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Min", 
                                    ctl_name = "LAST PLT4 YMIN",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT3, #location of control
                                    default = "20.0"
                                  )

        ord += 10
        self.cntls_obj.new_control(
                                    "plt4_ymax",
                                    order = ord,
                                    control_size = tiny_len, 
                                    label = "Y Max", 
                                    ctl_name = "LAST PLT4 YMAX",
                                    type = TEXT_CNTL, #type of control
                                    location = PLOT3, #location of control
                                    default = "70.0"
                                   )
        

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
                           PLOT3: (1, 20),
                           }



        self.timers_defn_dict = {
                                  "CUST1": (HTML, 
                                            "self._plot_pnl", 
                                            0020, 
                                            True
                                            ),
                                  "CUST2": (HTML, 
                                            "", 
                                            1000, 
                                            True
                                            ),
                                  }
        
        self.button_size = 130
        self.buttons_defn_dict = {
                                  SOURCE: None,
                                  "CUST1": (HTML, "Export All PNG", None, None),
                                  "CUST2": (HTML, "Export All PDF", None, None),
                                  }
               
        self.pbutton_size = 90
        self.pbuttons_defn_dict = {
                                  "CUST3": (PLOT0, "Refresh", None, None),
                                  "CUST4": (PLOT1, "Refresh", None, None),
                                  "CUST5": (PLOT2, "Refresh", None, None),
                                  "CUST6": (PLOT3, "Refresh", None, None),
                                  "CUST7": (PLOT0, "Freeze", None, None),
                                  "CUST8": (PLOT1, "Freeze", None, None),
                                  "CUST9": (PLOT2, "Freeze", None, None),
                                  "CUST10": (PLOT3, "Freeze", None, None),
                                  "CUST11": (PLOT0, "Export PNG", None, None),
                                  "CUST12": (PLOT0, "Export PDF", None, None),
                                  "CUST13": (PLOT1, "Export PNG", None, None),
                                  "CUST14": (PLOT1, "Export PDF", None, None),
                                  "CUST15": (PLOT2, "Export PNG", None, None),
                                  "CUST16": (PLOT2, "Export PDF", None, None),
                                  "CUST17": (PLOT3, "Export PNG", None, None),
                                  "CUST18": (PLOT3, "Export PDF", None, None),
                                  }
               
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

        self.panels_defn_dict = {PLOT: 4, HTML: 1,}       

        self._html = {0: "", 
                      }
        
        self._html_title = {0: "Log", 
                           } 
        
        self._plot = {0: None, 
                      1: None,
                      2: None, 
                      3: None} 


        self._next_frame = HTML
        
        self._max_source_lines = 100
        
        self._outdir = ""

        self._brief_html = None

        
        self._model.after_config_init()

        #activate following when you need to save the layout to an external
        #file - for example, you need to change the default layout string
        #and you need to capture the layout
        #self._save_external_layout_file = "sensorplot.layout"


    def reset_selection_values(self, values_dict = None):
        '''
        reset selection values to default (or passed in values)
            values_dict["combine_data"], 
            values_dict["y1_col"], 
            values_dict["y2_col"], 
            values_dict["y3_col"], 
            values_dict["y4_col"], 
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
        self.reset_selection_values()

        if self.parameter_dict:
            self.process_source_file(None)

            self.load_value_to_control(last_values_dict)


    def generate_chart(self, savefile=None, datavals=None):
        
        if datavals:
            sel_vals = datavals
        else:
            sel_vals = self.retrieve_values_from_controls()
                
        self._plot = {}
        self._plot_data = {}
        exptfile = None
        
        #self._resolve_selection()
        
        export_data = None
        self._model.generate_plot(
                                  {
                      "combine_data_flag": sel_vals["combine_data"],
                      "y1_col": sel_vals["y1_col"],
                      "y2_col": sel_vals["y2_col"],
                      "y3_col": sel_vals["y3_col"],
                      "y4_col": sel_vals["y4_col"],
                      "points": sel_vals[POINTS_PARM],
                      "export_data": export_data
                                    },
                      self._notebook,
                      self._plot_page_tidx
                                        )

        if "plot_fig" in self._model.process_parms.keys():
            self._plot = self._model.process_parms["plot_fig"]
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
                    self._plot[0].savefig(routine_data[RTN_OUTFILE])
            
            return True
        
        return None
    

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
            print "filename", filename
            routine_data = getattr(self, "custom%s_routine_data" % (idx))
            routine_data[OUTFILE] = filename

            print "refreshing the routine_data for ", idx
        return None

    def custom1_btn_process(self, parm=None):
        #print "parm", parm
        for idx in self._plot.keys():
            dt = datetime.datetime.now()
            fmt2_str = "%Y%m%d%H%M%S"
            filename = "%s_%s.png" % (self._model.plot_name[idx], 
                                  dt.strftime(fmt2_str)
                                  )
            
            path = os.path.join(parm, filename)
            self._plot[idx].savefig(path)
            
            
        
        self._next_frame = None
        return

    def custom2_btn_process(self, parm=None):
        for idx in self._plot.keys():
            dt = datetime.datetime.now()
            fmt2_str = "%Y%m%d%H%M%S"
            filename = "%s_%s.pdf" % (self._model.plot_name[idx], 
                                  dt.strftime(fmt2_str)
                                  )
            
            path = os.path.join(parm, filename)
            self._plot[idx].savefig(path)
            
            
        
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
        self._model.next_from_buffer_process(
                                             self._notebook, 
                                             self._plot_page_tidx, 
                                             self._plot_pnl, 
                                             idx,
                                             self.refresh_the_plots,
                                             self.fig_act
                                             )

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
        print "cust11"
        return
    
        if parm:
            if SOURCE_PARM in self.name_fld_dict.keys():
                fld_id, fld_type = self.name_fld_dict[SOURCE_PARM]

                self.parm_cntl["pctrl"][fld_id].SetValue(parm)
                self.parameter_dict[SOURCE_PARM] = parm
                
                self.process_source_file(None)
                self.reset_selection_values()
                
        self._next_frame = None
        return

    def custom12_btn_process(self, parm=None):
        if parm:
            if SOURCE_PARM in self.name_fld_dict.keys():
                fld_id, fld_type = self.name_fld_dict[SOURCE_PARM]

                self.parm_cntl["pctrl"][fld_id].SetValue(parm)
                self.parameter_dict[SOURCE_PARM] = parm
                
                self.process_source_file(None)
                self.reset_selection_values()
                
        self._next_frame = None
        return


    def custom1_timer_process(self, restart=None, canvasdict=None):
        '''
        custom timer 1 for refreshing plot
        '''
        if not self._model._status == "working":
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

    
    def custom2_timer_process(self, restart=None, canvas=None):
        '''
        custom timer 2 for refreshing log messages to html tab
        '''
        if 0 in self._model.process_parms["html_source"]:
            before_len = len(self._model.process_parms["html_source"][0])
            self._model.refresh_html()
            after_len = len(self._model.process_parms["html_source"][0])
            
            if not before_len == after_len:
                self._html[0] = self._model.process_parms["html_source"][0]
                return {"html.0": "refresh"}

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
            c = SensorPlotController(ctl_file=parm_dict["ctl_file"]) 
        else:
            c = SensorPlotController() 

        if parm_dict["skip_layout"]:
            c.skip_layout = True
    
        if parm_dict["batch_type"]:
            if parm_dict["batch_type"] in ("pdf", "png"):
                c.process_source_file()
                datavals = c.build_selection_dict()
                
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
