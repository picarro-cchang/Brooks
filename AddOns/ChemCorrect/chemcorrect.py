'''
chemcorrect.py -- The chemcorrect module contains the ChemcorrectController class.
This class will display an XY plot of data from the source CSV file (from 
coordinator).

The interactive UI allows for selection of the X and Y columns of data from the 
source CSV or H5 file.

The interactive UI allows user selection for graph markers and marker colors.

The interactive UI displays the selected graph

This module can run interactively or in batch. In batch mode it 
will export (save) a graph as its normal output:

Interactive mode USAGE: 
chemcorrect.py [ -h ] [ -s ] [ --help ] [ --skip-layout ] [ ctl_file_name ]

Batch mode USAGE:
chemcorrect.py ctl_file_name type dest_dir name

OPTIONS
  -h, --help                Show usage information
      
  -s, --skip-layout         Skip using last layout (start off with the default 
                            tab layout)

ARGUMENTS 
  ctl_file_name             Name of the ctl_file to use to restore the last 
                            saved parameters.

                            ini file format:
                            LAST SOURCE1: source_file_name
                            LAST GRAPHX: column_name 
                            LAST GRAPHY1: column_name 
                            LAST GRAPHY2: column_name 
                            LAST GRAPHY3: column_name 
                            LAST GRAPHY4: column_name 
                            LAST COLOR1: c
                            LAST COLOR2: c
                            LAST COLOR3: c
                            LAST COLOR4: c
                            LAST MARKER: m
                            LAST COMBINE DATA: yn
                            LAST LEGEND LOC: loc
                            LAST EXPORT DATA: yn
                            
                            source_file_name is the path and name for the 
                            source csv file.
                            
                            column_name is the name of the column 
                            (from the source csv file) to plot.
                            
                            c is marker color
                                'blue'
                                'green'
                                'red'
                                'cyan'
                                'magenta'
                                'yellow'
                                'black'
                                'white'
                            
                            m is marker type
                                'solid line'
                                'dashed line'
                                'dash-dot'
                                'dotted line'
                                'point marker'
                                'pixel marker'
                                'circle marker'
                            
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
    chemcorrect.py --skip-layout
        This would run the xy plot but skip restoring the last tab layout. 
        
    chemcorrect.py some_new_ctl_file.ini
        This would run the xy plot and use data in some_new_ctl_file.ini to 
        fill the parameters

    chemcorrect.py some_new_ctl_file.ini png ./ chemcorrectexpt
        This would run the xy plot in batch, using data in some_new_ctl_file.ini
        to fill the parameters, and place the created plot in a file named
        chemcorrectexpt.png


'''
import os
import sys
import getopt
import datetime, time, random

import wx

from postprocessdefn import *
from postprocesscontrol import PostProcessController, ThreadedWorker
from chemcorrectmodel import ChemcorrectModel

CCVER = '1.2.0'

class ChemcorrectController(PostProcessController):
    '''
    Chemcorrect Controller Class
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if not "ctl_file" in kwargs:
            kwargs["ctl_file"] = "chemcorrect.ctl"

        if not 'ccver' in kwargs:
            self.about_version = CCVER
        else:
            self.about_version = kwargs['ccver']
            del kwargs['ccver']

        PostProcessController.__init__(self, *args, **kwargs)

        # About Info
        self.about_name = "ChemCorrect(tm) Viewer"
        self.about_copyright = "(c) 2011 Picarro Inc."
        self.about_description = "Graphic display of ChemCorrect(tm) output."
        self.about_website = "http://www.picarro.com"

        
        msg = "Processing the parameters."
        msg += "\nThis may take some time..."
        self._busy_msg = msg 
        self.dlg = None               

    def _do_control_configuration(self):
        '''
        set up all specific configurations for the class
        '''
        self._model = ChemcorrectModel(
                                cntls_obj = self.cntls_obj,
                                fig_act = self.fig_act,
                                ccver = self.about_version
                                  )

        fmt_str = "%a, %b %d, %Y, %H:%M:%S"
        fmt2_str = "%Y%m%d%H%M%S"
        
        self._title = "Chemcorrect - %s" % (self._dt.strftime(fmt_str))
        self._title_pre = "Chemcorrect"
        self._title_filename = "%s_%s" % (
                                          self._title_pre,
                                          self._dt.strftime(fmt2_str)
                                          )

        self._layout_name = "chemcorrect"
        self._frame_title = "Picarro Post Processing - ChemCorrect(tm)"
        self._sz = ((900, 600))
        self._layout = None
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
        
        self.button_size = 120
        self.buttons_defn_dict = {
                                  SOURCE: None, #SOURCE is obsolete, and no longer used                             
                                  "CUST1": (HTML, "Source", "&File", "Choose &Source File\tCtrl+S"),                                  
                                  "CUST2": (HTML, "Instruction Set", "&File", "Choose &Instruction Set File\tCtrl+I"),                                  
                                  "CUST3": (HTML, "Standards", "&File", "Choose S&tandards File\tCtrl+T"),                                  
                                  "CUST4": (HTML, "Export Spreadsheet", "&File", "&Export Spreadsheet\tCtrl+E"),                                  
                                  }

        self.pbutton_size = 90
        self.pbuttons_defn_dict = {
            #std_btn_name: std_btn_parameter,
            #cst_btn_name: (panel_name, label, menu_location_name, menu_name),
                                  "CUST5": (PLOT0, "Export PNG", None, None),
                                  "CUST6": (PLOT0, "Export PDF", None, None),
                                  "CUST7": (PLOT1, "Export PNG", None, None),
                                  "CUST8": (PLOT1, "Export PDF", None, None),
                                  "CUST9": (PLOT2, "Export PNG", None, None),
                                  "CUST10": (PLOT2, "Export PDF", None, None),
                                  "CUST11": (PLOT3, "Export PNG", None, None),
                                  "CUST12": (PLOT3, "Export PDF", None, None),
        }
        
        self.source_wc_csv = "Csv files|*.csv"
        self.custom1_routine_data = {FILEOPEN: True, 
                                     WILDCARD: self.source_wc_csv,
                                     OPEN_MSG: "Choose Source File",
                                     }

        self.source_wc_csv = "Csv files|*.csv"
        self.custom2_routine_data = {FILEOPEN: True, 
                                     WILDCARD: self.source_wc_csv,
                                     OPEN_MSG: "Choose Instruction Set File",
                                     }

        self.source_wc_csv = "Csv files|*.csv"
        self.custom3_routine_data = {FILEOPEN: True, 
                                     WILDCARD: self.source_wc_csv,
                                     OPEN_MSG: "Choose Standards File",
                                     }

        self.custom4_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s.xls" % (self._title_filename),
                                     WILDCARD: "*.xls",
                                     GOOD_MSG: "Spreadsheet has been saved as",
                                     }

        self.custom5_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s.png" % (self._title_filename),
                                     WILDCARD: "*.png",
                                     GOOD_MSG: "Image has been saved as",
                                     }

        self.custom6_routine_data = {FILESAVE: True, 
                                     OUTFILE: "%s.pdf" % (self._title_filename),
                                     WILDCARD: "*.pdf",
                                     GOOD_MSG: "Image has been saved as",
                                     }

        self.custom7_routine_data = self.custom5_routine_data
        self.custom8_routine_data = self.custom6_routine_data

        self.custom9_routine_data = self.custom5_routine_data
        self.custom10_routine_data = self.custom6_routine_data

        self.custom11_routine_data = self.custom5_routine_data
        self.custom12_routine_data = self.custom6_routine_data

        self.panels_defn_dict = {PLOT: 4, HTML: 4, MOD: 0}       

        self._html = {
                      0: "", 
                      1: "",
                      2: "",
                      3: "",
                      }
        
        self._html_title = {
                            0: "Source", 
                            1: "Summary", 
                            2: "Detail", 
                            3: "Instructions"
                            } 
        
        self._plot_figure = {
                             0: None, 
                             1: None,
                             2: None,
                             3: None,
                             } 
        
        self._plot_figure = None


        self._next_frame = HTML
        
        self._max_source_lines = 100
        
        self._outdir = ""

        self._brief_html = None


        #activate following when you need to save the layout to an external
        #file - for example, you need to change the default layout string
        #and you need to capture the layout
        #self._save_external_layout_file = "chemcorrect.layout"
        
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
            
        initial_src = last_values_dict[SOURCE_PARM]
        self._setup_source(initial_src)
        self.reset_selection_values(last_values_dict)
        

    def _setup_source(self, source):
        
        list_of_columns = self._model.collist_from_source(source)

        for cname in (
                      "graphx", 
                      "graphy1",
                      "graphy2",
                      "graphy3",
                      "graphy4",
                      ):
            
            self.cntls_obj.control_list[cname].set_choice_list(list_of_columns)
            if not self.cntls_obj.control_list[cname].get_value():
                self.cntls_obj.control_list[cname].default = CHOICE_NONE
                self.cntls_obj.control_list[cname].set_value(CHOICE_NONE)

        return

    def generate_chart(self):
        
        self._model.generate_plot(
                                  self._notebook,
                                  self._plot_page_tidx
                                  )

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
            if routine_data[STEP] == 1:
                if RTN_OUTFILE in routine_data.keys():
                    routine_data[INFO_MSG] = "%s: %s" % (
                                                 routine_data[GOOD_MSG], 
                                                 routine_data[RTN_OUTFILE]
                                                         )

                    if btn in (4,):
                        self._save_plot_workbook(routine_data[RTN_OUTFILE])
                    elif btn in (5, 6):
                        self._save_plot_fig(routine_data[RTN_OUTFILE])
                    
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

    def _save_plot_workbook(self, savefile):
        '''
        save the plot to requested location, and also save the data.
        '''
        self._model.save_workbook(savefile)
        #self._plot_figure[plotidx].savefig(savefile)

    def _save_plot_data(self, savefile):
        '''
        save the plot to requested location, and also save the data.
        '''
        self._model.save_data(savefile)


    def refresh_routine_data(self, idx=None):
        if idx in (5, 6, 7, 8, 9, 10):
            if idx in (5, 7, 9):
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
        msg = "Processing the instruction set."
        msg += "\nThis may take some time."
        msg += "Please wait..."
        
        if not self.dlg:
            self.dlg = wx.BusyInfo(msg)
    
        rtnval = self._model.do_instruction_set()
        if rtnval == 'OK':
            self._next_frame = HTML
        else:
            if self.dlg:
                del self.dlg
                self.dlg = None
                
            errdlg = wx.MessageDialog(None, rtnval, 'Error', wx.OK | wx.ICON_ERROR)
            errdlg.ShowModal()
            del errdlg
            self._next_frame = None
            
        skip_layout = None
        return self._next_frame, skip_layout
        

    def custom1_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[SOURCE_PARM].set_value(parm)
            self._setup_source(parm)
            
                
        self._next_frame = None
        return


    def custom2_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[INSTRUCTION_PARM].set_value(parm)
                
        self._next_frame = None
        return

    def custom3_btn_process(self, parm=None):
        if parm:
            self.cntls_obj.control_list[STANDARDS_PARM].set_value(parm)
            self._setup_source(parm)
            


    def custom4_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom5_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom6_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom7_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom8_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom9_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom10_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom11_btn_process(self, parm=None):
        self._next_frame = None
        return

    def custom12_btn_process(self, parm=None):
        self._next_frame = None
        return

                
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
        
        if self.dlg:
            del self.dlg
            self.dlg = None
            
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
            c = ChemcorrectController(ctl_file=parm_dict["ctl_file"]) 
        else:
            c = ChemcorrectController() 

        if parm_dict["skip_layout"]:
            c.skip_layout = True
    
        if parm_dict["batch_type"]:
            export_data_flag = c.cntls_obj.control_list[
                                                       "expt_data"
                                                        ].get_value()
            
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
                
                if export_data_flag == "Yes":
                    c._save_plot_data(text_file_name)
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
