'''
configdiffviewer.py -- The configdiffviewer module contains the ConfigDiffViewer class.
This class will display an XY plot of data from the source CSV file (from 
coordinator).

The interactive UI allows for selection of the X and Y columns of data from the 
source CSV or H5 file.

The interactive UI allows user selection for graph markers and marker colors.

The interactive UI displays the selected graph

This module can run interactively or in batch. In batch mode it 
will export (save) a graph as its normal output:

Interactive mode USAGE: 
configdiffviewer.py [ -h ] [ -s ] [ --help ] [ --skip-layout ] [ ctl_file_name ]

Batch mode USAGE:
configdiffviewer.py ctl_file_name dest_dir name

OPTIONS
  -h, --help                Show usage information
      
  -s, --skip-layout         Skip using last layout (start off with the default 
                            tab layout)

ARGUMENTS 
  ctl_file_name             Name of the ctl_file to use to restore the last 
                            saved parameters.

                            ctl file format:
                            LAST SOURCE1: source_folder_name
                            LAST SOURCE2: source_folder_name
                            
                            source_folder_name is the path for the configuration
                            parent folder.
                            
  dest_dir                 Destination directory for the export spreadsheet.
  
  name                     The export spreadsheet name. Note the system will 
                           append '.xls'. 
  
EXAMPLES
    configdiffviewer.py --skip-layout
        This would run the viewer but skip restoring the last tab layout. 
        
    configdiffviewer.py some_new_ctl_file.ctl
        This would run the viewer and use data in some_new_ctl_file.ctl to 
        fill the parameters

    configdiffviewer.py some_new_ctl_file.ctl ./ configdiffviewerexpt
        This would run the viewer in batch, using data in some_new_ctl_file.ctl
        to fill the parameters, and place the created spreadsheet in a file 
        named configdiffviewerexpt.xls


'''
import os
import sys
import getopt
import datetime, time, random

import wx

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from postprocessdefn import *
from postprocesscontrol import PostProcessController, ThreadedWorker
from configdiffmodel import ConfigDiffModel

from Utilities import AppInfo


class ConfigDiffViewer(PostProcessController):
    '''
    ConfigDiffViewer Controller Class
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if not "ctl_file" in kwargs:
            kwargs["ctl_file"] = "configdiffviewer.ctl"

        PostProcessController.__init__(self, *args, **kwargs)

        # version and about info
        about = AppInfo()
        self.about_version = about.getAppVer()
        self.about_name = "Configuration Difference Viewer"  #about.getAppName()
        self.about_copyright = about.getCopyright()
        descr = "Find and display differences between two Picarro "
        descr += "configuration directories."
        self.about_description = descr  # about.getDescription()
        self.about_website = about.getWebSite()

        msg = "Searching for configuration differences."
        msg += "\nThis may take some time..."
        self._busy_msg = msg                

        self._show_complete_dialog = True

    def _do_control_configuration(self):
        '''
        set up all specific configurations for the class
        '''
        self._model = ConfigDiffModel()

        fmt_str = "%a, %b %d, %Y, %H:%M:%S"
        fmt2_str = "%Y%m%d%H%M%S"
        
        self._title = "ConfigDiffViewer - %s" % (self._dt.strftime(fmt_str))
        self._title_filename = "ConfigDiffViewer_%s" % (
                                                   self._dt.strftime(fmt2_str)
                                                       )

        self._layout_name = "configdiffviewer"
        ttl = "Picarro Post Processing - Configuration Difference Viewer"
        self._frame_title = ttl
        self._sz = ((900, 600))
        self._layout = "4ca4b7540000000000000002=0|4ca4b78e0000003900000003=+1\
        @layout2|name=dummy;caption=;state=67372030;dir=3;layer=0;row=0;pos=0;\
        prop=100000;bestw=180;besth=180;minw=180;minh=180;maxw=-1;maxh=-1;\
        floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|\
        name=4ca4b7540000000000000002;caption=;state=67372028;dir=5;layer=0;\
        row=0;pos=0;prop=100000;bestw=200;besth=200;minw=-1;minh=-1;maxw=-1;\
        maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;\
        transparent=255|name=4ca4b78e0000003900000003;caption=;state=67372028;\
        dir=3;layer=0;row=1;pos=0;prop=100000;bestw=442;besth=255;minw=-1;\
        minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;\
        notebookid=-1;transparent=255|dock_size(5,0,0)=202|dock_size(3,0,1)\
        =450|"
        
        self.parameter_names = [
                       SOURCE_PARM, 
                       SOURCE_PARM2, 
                       ]
        
        self.control_names = []

        self.hidden_names = []
        
        self.parm_cntl = {}
        self.name_fld_dict = {}

        self.parameter_defn_column_count = 2
        
        self.selection_defn_column_count = 1

        cntl_len = 350
        self.cntls_defn = { 
                           SOURCE_PARM: [
                                          1, #order of cntl (on frame)
                                          cntl_len, #cntl size (on frame)
                                          "path 1", #screen label
                                          "LAST SOURCE1", #cntl_file_entry
                                          TEXT_CNTL, #type of control
                                          PARAMETER, #location of control
                                          None, #default value
                                          None, #selection list
                                          ],
                           SOURCE_PARM2: [
                                          2, #order of cntl (on frame)
                                          cntl_len, #cntl size (on frame)
                                          "path 2", #screen label
                                          "LAST SOURCE2", #cntl_file_entry
                                          TEXT_CNTL, #type of control
                                          PARAMETER, #location of control
                                          None, #default value
                                          None, #selection list
                                          ],
                               }



        self.timers_defn_dict = {}
        
        self.button_size = 130
        self.buttons_defn_dict = {
                                  SOURCE: None,                                  
                                  "CUST1": (HTML, "Path 1", None, None),                                  
                                  "CUST2": (HTML, "Path 2", None, None),                                  
                                  "CUST3": (HTML, "Export Spreadsheet", None, None),
                                  #"CUST4": (HTML, "Export PDF", None, None),
                                  }
               
        self.custom1_routine_data = {DIROPEN: True, 
                                     OPEN_MSG: "Choose Config Path1",
                                     }

        self.custom2_routine_data = {DIROPEN: True, 
                                     OPEN_MSG: "Choose Config Path2",
                                     }

        self.custom3_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s.xls" % (self._title_filename),
                                     WILDCARD: "*.xls",
                                     GOOD_MSG: "Spreadsheet has been saved as",
                                     #OUTFILE2: "%s.txt" % (self._title_filename),
                                     #WILDCARD2: "*.txt",
                                     #GOOD_MSG2: "Image Data has been saved as",
                                     }

        self.panels_defn_dict = {HTML: 1,}       

        self._html = {0: "", 
                      }
        
        self._html_title = {0: "Viewer", 
                           } 
        
        self._plot = {0: None, 
                      1: None} 


        self._next_frame = HTML
        
        self._max_source_lines = 100
        
        self._outdir = ""

        self._brief_html = None


        #activate following when you need to save the layout to an external
        #file - for example, you need to change the default layout string
        #and you need to capture the layout
        #self._save_external_layout_file = "configdiffviewer.layout"



    def reset_selection_values(self, values_dict = None):
        '''
        reset selection values to default (or passed in values)
        '''
        if SOURCE_PARM in self.parameter_dict.keys():
            self.custom1_routine_data[START_PATH] = self.parameter_dict[
                                                                SOURCE_PARM
                                                                        ]
        if SOURCE_PARM2 in self.parameter_dict.keys():
            self.custom2_routine_data[START_PATH] = self.parameter_dict[
                                                                SOURCE_PARM2
                                                                        ]
        return 
    

    def do_post_ctl_processing(self, last_values_dict):
        #if self.parameter_dict:
        #    self.process_source_file(None)
        self.reset_selection_values(last_values_dict)
        self._build_process_dictionaries()
        
        #self.load_value_to_control(self.parameter_dict)



    def generate_chart(self, savefile=None, datavals=None):
        return
        return True

        
    def _export_data_file(self, 
                          exptfile, 
                          file_save_ttl, 
                          file_save_xx, 
                          file_save_xlabel, 
                          file_save_yy, 
                          file_save_ylabel,
                          ):

        #try:
        f = open(exptfile, "w")
        if f:
            str = "%s \n" %(file_save_ttl)
            str += " \n"

            str += "%s by %s \n" %(file_save_xlabel, file_save_ylabel)
            str += " \n"
            str += "%s, %s \n" %(file_save_xlabel, file_save_ylabel)
            for ii in range(0, len(file_save_yy)):
                str += "%s, %s \n" %(file_save_xx[ii], file_save_yy[ii])
            str += " \n"
                
            f.write(str)
        
        #except:
        #    pass
        
        return 

       
    def save_file(self, btn):
        routine_data = getattr(self, "custom%s_routine_data" % (btn))
        if RTN_OUTFILE in routine_data.keys():
            routine_data[INFO_MSG] = "%s: %s" % (
                                         routine_data[GOOD_MSG], 
                                         routine_data[RTN_OUTFILE]
                                                 )
            
            self._model.process_source(self._file_source, self._brief_html)
            self._model.export_to_spreadsheet(routine_data[RTN_OUTFILE])
            
            return True
        
        return None
    

    def custom1_btn_process(self, parm=None):
        if parm:
            if SOURCE_PARM in self.name_fld_dict.keys():
                fld_id, fld_type = self.name_fld_dict[SOURCE_PARM]

                self.parm_cntl["pctrl"][fld_id].SetValue(parm)
                self.parameter_dict[SOURCE_PARM] = parm
                self.custom1_routine_data[START_PATH] = parm
                
                #self.process_source_file(None)
                #self.reset_selection_values()
                
        self._next_frame = None
        return


    def custom2_btn_process(self, parm=None):
        if parm:
            if SOURCE_PARM2 in self.name_fld_dict.keys():
                fld_id, fld_type = self.name_fld_dict[SOURCE_PARM2]

                self.parm_cntl["pctrl"][fld_id].SetValue(parm)
                self.parameter_dict[SOURCE_PARM2] = parm
                self.custom2_routine_data[START_PATH] = parm
                
                #self.process_source_file(None)
                #self.reset_selection_values()
                
        self._next_frame = None
        return


    def custom3_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom4_btn_process(self, parm=None):
        self._next_frame = None
        return

    def next_frame(self):
        '''
        next frame stub:
        '''
        skip_layout = None
        if self._next_frame:

            self._model.process_source(self._file_source, self._brief_html)

            self.generate_chart()
        else:
            skip_layout = True
        
        self._next_frame = HTML
        return self._next_frame, skip_layout


    def export_to_spreadsheet(self, filename):
        self._model.process_source(self._file_source, self._brief_html)
        self._model.export_to_spreadsheet(filename)

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
                     "save_loc": None,
                     "save_name": None,
                    }

        _get_opts_and_args(parm_dict, opts)
        _setup_and_validate_parms(parm_dict, args)    
            
        ctl_file = None
        save_loc = None
        save_name = None
        
        if parm_dict["ctl_file"]:
            c = ConfigDiffViewer(ctl_file=parm_dict["ctl_file"]) 
        else:
            c = ConfigDiffViewer() 

        if parm_dict["skip_layout"]:
            c.skip_layout = True
    
        if parm_dict["save_loc"]:
            c.process_source_file()
            datavals = c.build_selection_dict()
            
            if not parm_dict["save_name"]:
                parm_dict["save_name"] = c._title_filename
                
            rtn_outfile = os.path.join(
                                   parm_dict["save_loc"], 
                                   "%s.%s" % (parm_dict["save_name"], 
                                              "xls")
                                       )
            
            c.export_to_spreadsheet(rtn_outfile)

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
        parm_dict["save_loc"] = args[1]
    if 3 <= len(args):
        parm_dict["save_name"] = args[2]
    
        
    if not all_ok:
        raise Usage(__doc__) 


if __name__ == '__main__':
    sys.exit(main())
