'''
thresholdviewercontrol.py -- The thresholdviewer module contains the 
ThresholdViewerController class. This class will display custom XY plot of data 
from up to 5 source files in specialized Threshold Integration step format.

This format is 5 columns of data as
column1: value1 column2: value2 column3: value3...
The column names are:
Threshold, Ringdown rate, Shot-to-shot, Mean loss, Mean wavenumber.
Rows not in that format and not including the listed columns are ignored.

The interactive UI allows for selection of the X and Y columns of data from the 
source threshold text file.

The interactive UI allows user selection for graph markers and marker colors.

The interactive UI displays the selected graph

This module can run interactively or in batch. In batch mode it 
will export (save) a graph as its normal output:

Interactive mode USAGE: 
thresholdviewercontrol.py [ -h ] [ -s ] [ --help ] [ --skip-layout ] 
[ ctl_file_name ]

Batch mode USAGE:
thresholdviewercontrol.py ctl_file_name type dest_dir name

OPTIONS
  -h, --help                Show usage information
      
  -s, --skip-layout         Skip using last layout (start off with the default 
                            tab layout)

ARGUMENTS 
  ctl_file_name             Name of the ctl_file to use to restore the last 
                            saved parameters.

                            ini file format:
                            LAST SOURCE1: source_file_name
                            LAST SOURCE2: source_file_name
                            LAST SOURCE3: source_file_name
                            LAST SOURCE4: source_file_name
                            LAST SOURCE5: source_file_name
                            LAST GRAPHY1: column_name 
                            LAST GRAPHY2: column_name 
                            LAST MARKER1: m
                            LAST MARKER2: m
                            LAST COLOR1: c
                            LAST COLOR3: c
                            LAST COLOR2: c
                            LAST COLOR5: c
                            LAST COLOR4: c
                            LAST COMBINE DATA: yn
                            LAST LEGEND LOC: loc
                            
                            source_file_name is the path and name for the 
                            source csv file.
                            
                            column_name is the name of the column 
                            (from the source csv file) to plot.
                            
                            m is marker type
                                'solid line'
                                'dashed line'
                                'dash-dot'
                                'dotted line'
                                'point marker'
                                'pixel marker'
                                'circle marker'
                            
                            c is marker color
                                'blue'
                                'green'
                                'red'
                                'cyan'
                                'magenta'
                                'yellow'
                                'black'
                                'white'

                            yn is 'Yes' or 'No'
                            
                            loc is legend location
                                'best'
                                'upper right'
                                'upper left'
                                'lower left'
                                'lower right'
                                'right'
                                'center left'
                                'center right'
                                'lower center'
                                'upper center'
                                'center'                  
                            

  type                      'png' or 'pdf' type of graph export
  
  dest_dir                 Destination directory for the export graph.
  
  name                     The export graph name. Note the system will append 
                           '.png' or '.pdf' appropriately. 
  
EXAMPLES
    thresholdviewercontrol.py --skip-layout
        This would run the xy plot but skip restoring the last tab layout. 
        
    thresholdviewercontrol.py some_new_ctl_file.ini
        This would run the xy plot and use data in some_new_ctl_file.ini to 
        fill the parameters

    thresholdviewercontrol.py some_new_ctl_file.ini png ./ thresholdviewerexpt
        This would run the xy plot in batch, using data in some_new_ctl_file.ini
        to fill the parameters, and place the created plot in a file named
        thresholdviewerexpt.png


'''
import os
import sys
import getopt
import datetime, time, random

import wx

from postprocessdefn import *
from postprocesscontrol import PostProcessController, ThreadedWorker
from thresholdviewermodel import ThresholdViewerModel

from Utilities import AppInfo


class ThresholdViewerController(PostProcessController):
    '''
    ThresholdViewer Controller Class
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if not "ctl_file" in kwargs:
            kwargs["ctl_file"] = "thresholdviewer.ctl"

        PostProcessController.__init__(self, *args, **kwargs)

        # version and about info
        about = AppInfo()
        self.about_version = about.getAppVer()
        self.about_name = "Threshold Viewer"  #about.getAppName()
        self.about_copyright = about.getCopyright()
        descr = "Display Threshold Viewer from selected columns in Picarro Threshold "
        descr += "data files."
        self.about_description = descr  # about.getDescription()
        self.about_website = about.getWebSite()

        msg = "Processing the parameters."
        msg += "\nThis may take some time..."
        self._busy_msg = msg                

    def _do_control_configuration(self):
        '''
        set up all specific configurations for the class
        '''
        self._model = ThresholdViewerModel(
                                cntls_obj = self.cntls_obj,
                                fig_act = self.fig_act
                                  )

        fmt_str = "%a, %b %d, %Y, %H:%M:%S"
        fmt2_str = "%Y%m%d%H%M%S"
        
        self._title = "ThresholdViewer - %s" % (self._dt.strftime(fmt_str))
        self._title_pre = "ThresholdViewer"
        self._title_filename = "%s_%s" % (
                                          self._title_pre,
                                          self._dt.strftime(fmt2_str)
                                          )

        self._layout_name = "thresholdviewer"
        self._frame_title = "Picarro Post Processing - Threshold Viewer"
        self._sz = ((900, 600))
        self._layout = None
        '''
        self._layout = "4c96d5b10000000000000002=1,2|4c96d5bd0000000c00000003=+\
        0@layout2|name=dummy;caption=;state=67372030;dir=3;layer=0;row=0;pos=0;\
        prop=100000;bestw=180;besth=180;minw=180;minh=180;maxw=-1;maxh=-1;\
        floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|\
        name=4c96d5b10000000000000002;caption=;state=67372028;dir=5;layer=0;\
        row=0;pos=0;prop=100000;bestw=200;besth=200;minw=-1;minh=-1;maxw=-1;\
        maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;\
        transparent=255|name=4c96d5bd0000000c00000003;caption=;state=67372028;\
        dir=4;layer=0;row=1;pos=0;prop=100000;bestw=438;besth=253;minw=-1;\
        minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;\
        notebookid=-1;transparent=255|dock_size(5,0,0)=202|\
        dock_size(4,0,1)=200|"
        '''
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
                           }


        self.timers_defn_dict = {}
        
        self.button_size = 90
        self.buttons_defn_dict = {
                                  SOURCE: None,                                  
                                  "CUST1": (HTML, "Source 1", None, None),                                  
                                  "CUST2": (HTML, "Source 2", None, None),                                  
                                  "CUST3": (HTML, "Source 3", None, None),                                  
                                  "CUST4": (HTML, "Source 4", None, None),                                  
                                  "CUST5": (HTML, "Source 5", None, None),                                  
                                  "CUST6": (HTML, "Export PNG", None, None),
                                  "CUST7": (HTML, "Export PDF", None, None),
                                  }

        self.pbutton_size = 90
        self.pbuttons_defn_dict = {
            #std_btn_name: std_btn_parameter,
            #cst_btn_name: (panel_name, label, menu_location_name, menu_name),
        }
        
        self.custom1_routine_data = {FILEOPEN: True, 
                                     WILDCARD: "*.txt",
                                     OPEN_MSG: "Choose Source File 1",
                                     "skey": SOURCE_PARM,
                                     }

        self.custom2_routine_data = {FILEOPEN: True, 
                                     WILDCARD: "*.txt",
                                     OPEN_MSG: "Choose Source File 2",
                                     "skey": SOURCE_PARM2,
                                     }

        self.custom3_routine_data = {FILEOPEN: True, 
                                     WILDCARD: "*.txt",
                                     OPEN_MSG: "Choose Source File 3",
                                     "skey": SOURCE_PARM3,
                                     }

        self.custom4_routine_data = {FILEOPEN: True, 
                                     WILDCARD: "*.txt",
                                     OPEN_MSG: "Choose Source File 4",
                                     "skey": SOURCE_PARM4,
                                     }

        self.custom5_routine_data = {FILEOPEN: True, 
                                     WILDCARD: "*.txt",
                                     OPEN_MSG: "Choose Source File 5",
                                     "skey": SOURCE_PARM5,
                                     }

        self.custom6_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s.png" % (self._title_filename),
                                     WILDCARD: "*.png",
                                     GOOD_MSG: "Image has been saved as",
                                     OUTFILE2: "%s.txt" % (self._title_filename),
                                     WILDCARD2: "*.txt",
                                     GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.custom7_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s.pdf" % (self._title_filename),
                                     WILDCARD: "*.pdf",
                                     GOOD_MSG: "Image has been saved as",
                                     OUTFILE2: "%s.txt" % (self._title_filename),
                                     WILDCARD2: "*.txt",
                                     GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.panels_defn_dict = {PLOT: 1, HTML: 1, MOD: 0}       

        self._html = {0: "", 
                      }
        
        self._html_title = {0: "Source", 
                           } 
        
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
        #self._save_external_layout_file = "thresholdviewer.layout"
        
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
#        for vkey, value in last_values_dict.iteritems():
#            print vkey, value
            
        self._setup_source(last_values_dict)
        self.reset_selection_values(last_values_dict)
        

    def _setup_source(self, last_values_dict):
        list_of_columns = self._model.collist_from_source(last_values_dict)
        
        for cname in (
                      "graphy1",
                      "graphy2",
                      ):
            
            self.cntls_obj.control_list[cname].set_choice_list(list_of_columns)
            if not self.cntls_obj.control_list[cname].get_value():
                self.cntls_obj.control_list[cname].default = CHOICE_NONE
                self.cntls_obj.control_list[cname].set_value(CHOICE_NONE)

    def generate_chart(self):
        
        self._model.generate_plot()

        if "plot_fig" in self._model.process_parms.keys():
            self._plot_figure = self._model.process_parms["plot_fig"]
            if "plot_data" in self._model.process_parms.keys():
                self._plot_data = self._model.process_parms["plot_data"]

        if "html_source" in self._model.process_parms.keys():
            self._html = self._model.process_parms["html_source"]

        return True


    def save_file(self, btn):
        routine_data = getattr(self, "custom%s_routine_data" % (btn))
        if STEP in routine_data.keys():
            export_data_flag = self.cntls_obj.control_list[
                                                           "expt_data"
                                                           ].get_value()
            
            if routine_data[STEP] == 1:
                if RTN_OUTFILE in routine_data.keys():
                    routine_data[INFO_MSG] = "%s: %s" % (
                                                 routine_data[GOOD_MSG], 
                                                 routine_data[RTN_OUTFILE]
                                                         )

                    self._save_plot_fig(routine_data[RTN_OUTFILE])
                    
                    if export_data_flag == "Yes":
                        routine_data[SKIPOUT_2] = False
                    else:
                        routine_data[SKIPOUT_2] = True
            
            if routine_data[STEP] == 2:
                if export_data_flag == "Yes":

                    self._save_plot_data(routine_data[RTN_OUTFILE2])
            
                    routine_data[INFO_MSG] = "%s: %s" % (
                                                 routine_data[GOOD_MSG2], 
                                                 routine_data[RTN_OUTFILE2]
                                                         )
            return True
        
        return None

    

    def _save_plot_fig(self, savefile, batch=None):
        '''
        save the plot to requested location, and also save the data.
        '''
        if batch:
            self._model.save_fig_batch(savefile)
        else:
            self._model.save_fig(savefile)
        #self._plot_figure[plotidx].savefig(savefile)

    def _save_plot_data(self, savefile):
        '''
        save the plot to requested location, and also save the data.
        '''
        self._model.save_data(savefile)


    def refresh_routine_data(self, idx=None):
        if idx in (1, 2, 3, 4, 5):
            routine_data = getattr(self, "custom%s_routine_data" % (idx))
            source = self._model._source[routine_data["skey"]]
            if source:
                left, sep, suffix = source.rpartition(".")
                
            
        if idx in (6, 7,):
            if idx == 6:
                suffix = "png"
            else:
                suffix = "pdf"
                
            dt = datetime.datetime.now()
            fmt2_str = "%Y%m%d%H%M%S"
            filename = "%s_%s" % (
                                  self._title_pre, 
                                  dt.strftime(fmt2_str)
                                  )

            routine_data = getattr(self, "custom%s_routine_data" % (idx))
            routine_data[OUTFILE] = "%s.%s" % (filename, suffix)
            routine_data[OUTFILE2] = "%s.%s" % (filename, "txt")

        return None


    def process_ok(self, dlg=None):
        '''
        stub process from ok (and reload) button
        '''
        self._next_frame = HTML
        return
        

    def custom1_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[SOURCE_PARM].set_value(parm)
            self._setup_source({SOURCE_PARM: parm})
            
                
        self._next_frame = None
        return


    def custom2_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[SOURCE_PARM2].set_value(parm)
            self._setup_source({SOURCE_PARM2: parm})
            
                
        self._next_frame = None
        return


    def custom3_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[SOURCE_PARM3].set_value(parm)
            self._setup_source({SOURCE_PARM3: parm})
            
                
        self._next_frame = None
        return


    def custom4_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[SOURCE_PARM4].set_value(parm)
            self._setup_source({SOURCE_PARM4: parm})
            
                
        self._next_frame = None
        return


    def custom5_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[SOURCE_PARM5].set_value(parm)
            self._setup_source({SOURCE_PARM5: parm})
            
                
        self._next_frame = None
        return



    def custom6_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom7_btn_process(self, parm=None):
        self._next_frame = None
        return

    def next_frame(self):
        '''
        next frame stub:
        '''
        skip_layout = None
        
        if self._next_frame:
            self._model.process_source(self._brief_html)
            if self._model.process_parms[STATUS] == OK:
                self.generate_chart()
        
        return self._next_frame, skip_layout

class TestThreadedWorker(ThreadedWorker):
    def task(self):
        if "task" in self._workload.keys():
            task = self._workload["task"]
            wait = self._workload["wait"]
            time.sleep(wait)
            print "task", task
        else:
            print "invalid workload"

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
            c = ThresholdViewerController(ctl_file=parm_dict["ctl_file"]) 
        else:
            c = ThresholdViewerController() 

        if parm_dict["skip_layout"]:
            c.skip_layout = True
    
        if parm_dict["batch_type"]:
            if parm_dict["batch_type"] in ("pdf", "png"):
                if not parm_dict["save_name"]:
                    parm_dict["save_name"] = "%s.%s" % (
                                                        c._title_filename, 
                                                        parm_dict["batch_type"]
                                                        )
                    text_file_name = "%s.%s" % (
                                                c._title_filename, 
                                                "txt"
                                                )
                    
                if parm_dict["save_loc"]:
                    rtn_outfile = os.path.join(
                                           parm_dict["save_loc"], 
                                           "%s.%s" % (parm_dict["save_name"], 
                                                      parm_dict["batch_type"])
                                               )
                    text_file_name = os.path.join(
                                           parm_dict["save_loc"], 
                                           "%s.%s" % (parm_dict["save_name"], 
                                                      "txt")
                                               )
                else:
                    rtn_outfile = "%s.%s" % (
                                             parm_dict["save_name"], 
                                             parm_dict["batch_type"]
                                             )
                    text_file_name = "%s.%s" % (
                                                parm_dict["save_name"], 
                                                "txt"
                                                )
                
                c.generate_chart()
                c._save_plot_fig(parm_dict["save_name"], True)
                
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
