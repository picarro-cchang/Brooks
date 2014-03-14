'''
postprocesscontrol.py -- the postprocesscontrol module contains the 
PostProcessController class. This class will interact with a data "model" class
and the control the PostProcessFrame "view" class.
'''

import os
import sys
import getopt
import datetime, time, random

import threading
import Queue

import wx

from postprocessdefn import *
from postprocessframe import PostProcessFrame

DSPVER = '1.2.0'

class PostProcessController(object):
    '''
    PostProcess Controller Class
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if "ctl_file" in kwargs:
            self._ctl_file = kwargs["ctl_file"]
            del kwargs["ctl_file"]

        self._gui_created = None
 
        # About Info
        self.about_name = "PostProcess Controller"
        
        if not 'dspver' in kwargs:
            self.about_version = DSPVER
        else:
            self.about_version = kwargs['dspver']
            del kwargs['dspver']
            
        self.about_copyright = "(c) 2011 Picarro Inc."
        self.about_description = "PostProcess Viewer Controller."
        self.about_website = "http://www.picarro.com"

        self._dt = datetime.datetime.now()
        self.cntls_obj = EntryControls()
        
        self.allow_fi = True

        self.show_progress_dialog = None
        self._show_complete_dialog = None
        self.skip_layout = None
        
        self.parm_cntl = {}
        self.name_fld_dict = {}
        self._save_external_layout_file = None
        self._plot_pnl = None
        self._plot_window_tidx = None
        self.fig_act = None
        self._notebook = None
        self._rlock = None
        self.refresh_the_plots = None  
        self.initial_frame_process = None
        
        self._plotcntl_first_is_done = {}
        
        self.buttons_ord_list = None
        self.pbuttons_ord_list = None
        
        self.custom1_routine_data = {}
        self.custom2_routine_data = {}
        self.custom3_routine_data = {}
        self.custom4_routine_data = {}
        self.custom5_routine_data = {}
        self.custom6_routine_data = {}
        self.custom7_routine_data = {}
        self.custom8_routine_data = {}
        self.custom9_routine_data = {}
        self.custom10_routine_data = {}
        self.custom11_routine_data = {}
        self.custom12_routine_data = {}
        self.custom13_routine_data = {}
        self.custom14_routine_data = {}
        self.custom15_routine_data = {}
        self.custom16_routine_data = {}
        self.custom17_routine_data = {}
        self.custom18_routine_data = {}
        self.custom19_routine_data = {}
        self.custom20_routine_data = {}
        self.custom21_routine_data = {}
        self.custom22_routine_data = {}
        self.custom23_routine_data = {}
        self.custom24_routine_data = {}
        self.custom25_routine_data = {}
        self.custom26_routine_data = {}
        self.custom27_routine_data = {}
        self.custom28_routine_data = {}
        self.custom29_routine_data = {}

        self.cntls_len = {} # length (num of items) for each control page
        self.cntls_cols = {} # num of columns for each control page
        
        self._do_control_configuration()

        if os.name == "nt":
            self._picarro_home = WIN_PICARRO_HOME
        else:
            self._picarro_home = UNIX_PICARRO_HOME
        
        self._busy_msg = "Processing request..."    
        
        self.entry_controls_are_defined = None
        
        # error log
        self._error_log = {}

        self._initialize_vars()
        
        self.selection_dict = {}
        
        self._entry_controls = None
        
        self._reload_from_ctl()

    
    def _do_control_configuration(self):
        '''
        set up all specific configurations for the class
        '''
        self._model = None

        fmt_str = "%a, %b %d, %Y, %H:%M:%S"
        fmt2_str = "%Y%m%d%H%M%S"
        
        self._title = "PostProcess - %s" % (self._dt.strftime(fmt_str))
        self._title_filename = "PostProcess_%s" % (self._dt.strftime(fmt2_str))

        
        self._layout_name = "postprocesscontrol"
        self._frame_title = "Picarro Post Processing"
        self._sz = None
        self._layout = None

        
        # i/o ui controls
        self.control_names = []
        
        # i/o hidden/private - usually from defaults or cntl file
        self.hidden_names = []
        
        self.parm_cntl = {}
        self.name_fld_dict = {}
        
        self.parameter_defn_column_count = 1
        self.selection_defn_column_count = 1

        self.cntls_defn = {
                    #cntl_name: (order, cntl_size, label, ctl_save_name),
        }
        
        self.timers_defn_dict = {
                    #cst_timer_name: (panel, parameter, timing, auto_bool),
        }
        
        self.button_size = 90
        self.buttons_defn_dict = {
            #std_btn_name: std_btn_parameter,
            #cst_btn_name: (panel_name, label, menu_location_name, menu_name),
        }
               
        self.pbutton_size = 90
        self.pbuttons_defn_dict = {
            #std_btn_name: std_btn_parameter,
            #cst_btn_name: (panel_name, label, menu_location_name, menu_name),
        }
               
        self.custom1_routine_data = {
        #either... FILEOPEN: True, 
        #          WILDCARD: wildcard, 
        #          OPEN_MSG: open_msg,

        #or....   FILESAVE: True, 
        #         OUTFILE: filename, 
        #         WILDCARD: wildcard, 
        #         GOOD_MSG: message_on_success,
        
        #or....   Any data to be passed to custom routine
        }
        self.custom2_routine_data = {}
        self.custom3_routine_data = {}
        self.custom4_routine_data = {}
        self.custom5_routine_data = {}
        self.custom6_routine_data = {}
        self.custom7_routine_data = {}
        self.custom8_routine_data = {}

        self.panels_defn_dict = {PLOT: 0, HTML: 0, COMBO: True}       

        self._html = {0: "",}
        
        self._html_title = {0: "Source",} 
        
        self._plot = {0: None, 
                      1: None} 

        self._next_frame = HTML
        
        self._max_source_lines = 100
        
        self._outdir = ""
        
        self._brief_html = None

    def _reload_from_ctl(self):
        '''
        reload selection and system data from the ctl_file
        '''
        f_data = None
        last_source = {}
        last_inst = None

        last_values_dict = {}
        #for ckey in self.cntls_defn.keys():
        for ckey in self.cntls_obj.control_list.keys():
            last_values_dict[ckey] = None

        try:
            ctl_f = open(self._ctl_file, "rw")
            if ctl_f:
                f_data = ctl_f.readline()
                while f_data:
                    
                    #for ckey in self.cntls_defn.keys():
                    for ckey, control in self.cntls_obj.control_list.iteritems():
                        #search_term = "%s: " % (self.cntls_defn[ckey][3])
                        search_term = "%s: " % (control.ctl_name)
                        if search_term in f_data:

                            slen = len(search_term)
                            val = f_data[slen:].strip()
                            
                            if ckey in self.cntls_obj.control_list.keys():
                                self.cntls_obj.control_list[ckey].default = val
                                #print ckey, val

                            last_values_dict[ckey] = val

                    f_data = ctl_f.readline()
            
        except:
            pass

        self.do_post_ctl_processing(last_values_dict)

    def do_post_ctl_processing(self, last_values_dict):
        return


    def restore_control_values(self, plt_id):
        '''
        restore control values for plot panels
        '''
        if not plt_id in self._plotcntl_first_is_done.keys():
            self._plotcntl_first_is_done[plt_id] = True
            for name, control in self.cntls_obj.control_list.iteritems():
                if control.location == plt_id:
                    control.set_value(control.default)
            
        return

    
    def reset_selection_values(self, values_dict = None):
        '''
        reset selection values to default (or passed in values)
        '''
        return 

    
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
                        save_term = "%s: %s\n" % (
                                            control.ctl_name,
                                            control.get_value()
                                                )

                        str += save_term
                        

                ctl_f.write(str)
        except:
            pass

        return


    def show_main_gui(self):
        '''
        show main gui process
        '''
        self._gui_created = True
        if self.skip_layout:
            layout, size, spos = (self._layout, self._sz, None)
        else:
            layout, size, spos = self._restore_layout()
        app = wx.PySimpleApp(0)
        self.frame = PostProcessFrame(
                         None, 
                         title=self._frame_title, 
                         process_class=self,
                         layout=layout,
                         size=size,
                         pos=spos,
                         allow_fi=self.allow_fi
                                 )
        
        self.post_frame_initialization()
        
        app.SetTopWindow(self.frame)
        self.frame.Show(True)
        app.MainLoop()
        app.Destroy()
        return


    def post_frame_initialization(self):
        '''
        stub for code to do any post frame init modificaions
        '''
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
        return None

    
    def _build_process_dictionaries(self):
        '''
        stub for code to build various required process dictionaries
        '''
        return True

    def generate_chart(self, savefile=None):
        self.fig_act = {}
        self._plot = {}
        self._plot_data = {}
        return True
        
    def _initialize_vars(self):
        '''
        initialize variables
        '''
        self._file_source = None
        self._plot = None
        
        self._first_tm = 0
        
        self._title = None
        self._title_spreadsheet = None
        self._outfile = None

        self._column_names_list = []
        self._source_column_count = 0 

        return True


    def next_frame(self):
        '''
        next frame stub:
        '''
        skip_layout = None
        return self._next_frame, skip_layout


    def resize_process(self):
        return 

    
    def close_plot_btn_process(self):
        self._next_frame = PARAMETER


    def refresh_routine_data(self, idx=None):
        return None


    def process_ok(self, dlg=None):
        '''
        stub process from ok (and reload) button
        '''
        return
        

    def custom1_btn_process(self, parm=None):
        return


    def custom2_btn_process(self, parm=None):
        return


    def custom3_btn_process(self, parm=None):
        return


    def custom4_btn_process(self, parm=None):
        return


    def custom5_btn_process(self, parm=None):
        return


    def custom6_btn_process(self, parm=None):
        return


    def custom7_btn_process(self, parm=None):
        return


    def custom8_btn_process(self, parm=None):
        return


    def custom9_btn_process(self, parm=None):
        return


    def custom10_btn_process(self, parm=None):
        return


    def custom11_btn_process(self, parm=None):
        return


    def custom12_btn_process(self, parm=None):
        return


    def custom13_btn_process(self, parm=None):
        return


    def custom14_btn_process(self, parm=None):
        return


    def custom15_btn_process(self, parm=None):
        return


    def custom16_btn_process(self, parm=None):
        return


    def custom17_btn_process(self, parm=None):
        return


    def custom18_btn_process(self, parm=None):
        return


    def custom19_btn_process(self, parm=None):
        return


    def custom20_btn_process(self, parm=None):
        return


    def custom21_btn_process(self, parm=None):
        return


    def custom22_btn_process(self, parm=None):
        return


    def custom23_btn_process(self, parm=None):
        return


    def custom24_btn_process(self, parm=None):
        return


    def custom25_btn_process(self, parm=None):
        return


    def custom26_btn_process(self, parm=None):
        return


    def custom27_btn_process(self, parm=None):
        return


    def custom28_btn_process(self, parm=None):
        return


    def custom29_btn_process(self, parm=None):
        return


    def pre_modal_process(self, routine_data=None):
        return
    
    def post_modal_process(self, rtn=None, routine_data=None):
        return
    
    def save_layout(self, layout, size, spos):
        '''
        save tab layout configuration
        '''
        if layout:
            wdt, hgth = size
            config = wx.Config(self._layout_name)
            config.Write("notebook_layout", layout)
            config.Write("notebook_size", "%s,%s" % (wdt, hgth) )
            config.Write("notebook_spos", "%s" % (spos) )
        
        if self._save_external_layout_file:
            try: 
                xl_f = open(self._save_external_layout_file, "w")
                if xl_f:
                    xl_f.write(layout)
            except:
                pass

            
    def _restore_layout(self):
        '''
        restore layout from last saved configuration
        '''
        #return None, None
        try:
            config = wx.Config(self._layout_name)
            layout = config.Read("notebook_layout")
            sizex = config.Read("notebook_size")
            wdt, sep, hgth = sizex.rpartition(",")
            size = (int(wdt), int(hgth))
            sposx = config.Read("notebook_spos")
            sposx = sposx.lstrip("(")
            sposx = sposx.rstrip(")")
            xpos, sep, ypos = sposx.rpartition(",")
            spos = (int(xpos), int(ypos))
            
            if layout:
                return layout, size, spos
        except:
            pass
        
        return self._layout, self._sz, None

            
    def save_file(self, btn):
        return None
    

    def retrieve_values_from_controls(self):
        rtn_val = {}
        for name, control in self.cntls_obj.control_list.iteritems():
            rtn_val[name] = control.get_value()
        
        return rtn_val

        
    def load_value_to_control(self, value_dict):
        if self.entry_controls_are_defined:
            for cname in value_dict.keys():
                self.cntls_obj.set_value(cname, value_dict[cname])
                
        return

    def _load_values_to_cntls_defn(self, value_dict):
        for cname in value_dict.keys():
            control = self.cntls_obj.get_control(cname)
            if control:
                control.default = value_dict[cname]

        return
    
    def _load_sellists_to_cntls_defn(self, value_dict):
        for cname in value_dict.keys():
            control = self.cntls_obj.get_control(cname)
            if control:
                control.set_choice_list(value_dict[cname])

#            if cname in self.cntls_defn.keys():
#                self.cntls_defn[cname][7] = value_dict[cname]
            
        return
    
   
class EntryControls(object):
    '''
    Entry Control Object holds all the entry columns
    '''   
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        self.control_list = {}
    
    def new_control(self, name, **kwargs):
        '''
        define a new control, and add it to the list
        '''
        if name in self.control_list.keys():
            return self.control_list[name]
        
        ctl = self.EntryControl(name, **kwargs)
        self._add_control(ctl)
        
        return ctl
        
        
    def _add_control(self, control):
        if not control.name in self.control_list.keys():
            self.control_list[control.name] = control 
    
    def get_control(self, name):
        if name in self.control_list.keys():
            return self.control_list[name]
        
        return None

    def yield_names_in_order(self):
        
        rtn_value = None
        ord_list = {}
        for name, obj in self.control_list.iteritems():
            ord_list[obj.name] = obj.order

        for k,v in \
            [(k, ord_list[k]) \
             for k in sorted(ord_list, key=ord_list.get) \
             ]:
                yield k
                rtn_value = True
        
        return 
        
                 
    def set_attribute(self, name, attribute, value):
        if name in self.control_list.keys():
            setattr(self.control_list[name], attribute, value)
            
            
    def get_attribute(self, name, attribute):
        if name in self.control_list.keys():
            return getattr(self.control_list[name], attribute)
        
        return None
        
        
    def get_value(self, name):
        if name in self.control_list.keys():
            return self.control_list[name].get_value()
        
        return None
            
            
    def set_value(self, name, value):
        if name in self.control_list.keys():
            return self.control_list[name].set_value(value)
        
        return None
    
    
    def set_choice_list(self, name, list):
        if name in self.control_list.keys():
            return self.control_list[name].set_choice_list(list)
        
        return None
            
            
    def set_label(self, name, value):
        if name in self.control_list.keys():
            return self.control_list[name].set_label(value)
        
        return None
            
    def set_disable(self, name):
        if name in self.control_list.keys():
            return self.control_list[name].set_disable()
        
        return None
            
    def set_enable(self, name):
        if name in self.control_list.keys():
            return self.control_list[name].set_enable()
        
        return None
            
    class EntryControl(object):
        '''
        Entry Control Object holds the wx control object and associated values
        '''   
        def __init__(self, name, *args, **kwargs):
            '''
            Constructor
            '''
            self.name = name
            
            if "label" in kwargs:
                self.label = kwargs["label"]
                del kwargs["label"]
            else:
                self.label = None
            
            if "order" in kwargs:
                self.order = kwargs["order"]
                del kwargs["order"]
            else:
                self.order = None
            
            if "default" in kwargs:
                self.default = kwargs["default"]
                del kwargs["default"]
            else:
                self.default = None
            
            if "type" in kwargs:
                self.type = kwargs["type"]
                del kwargs["type"]
            else:
                self.type = None
            
            if "location" in kwargs:
                self.location = kwargs["location"]
                del kwargs["location"]
            else:
                self.location = None
            
            if "control_size" in kwargs:
                self.control_size = kwargs["control_size"]
                del kwargs["control_size"]
            else:
                self.control_size = None
            
            if "values_list" in kwargs:
                self.values_list = kwargs["values_list"]
                del kwargs["values_list"]
            else:
                self.values_list = None
            
            if "ctl_name" in kwargs:
                self.ctl_name = kwargs["ctl_name"]
                del kwargs["ctl_name"]
            else:
                self.ctl_name = None
            
            if "cid" in kwargs:
                self.control = kwargs["cid"]
                del kwargs["cid"]
            else:
                self.cid = None
    
            if "control" in kwargs:
                self.control = kwargs["control"]
                del kwargs["control"]
            else:
                self.control = None
    
            if "label_control" in kwargs:
                self.label_control = kwargs["label_control"]
                del kwargs["label_control"]
            else:
                self.label_control = None
                
            if "font_attr" in kwargs:
                self.font_attr = kwargs["font_attr"]
                del kwargs["font_attr"]
            else:
                self.font_attr = None
            
            if "enable" in kwargs:
                self.enable = kwargs("enable")
            else:
                self.enable = None
                    
            self.initial_value = None
    
    
        def set_label(self, label=None):
            '''
            set the control display label
            '''
            if not label:
                label = self.label
                
            if self.label_control:
                self.label_control.SetLabel(label)
                self.label = label
                return True
            
            return None
        
        
        def set_choice_list(self, list):
            '''
            set (or reset) the choice list
            '''    
            #print self.name, list
            if self.control:
                if self.type in (CHOICE_CNTL, RADIO_CNTL):
                    self.control.Clear()
                    self.values_list = []
                    for elm in list:
                        self.control.Append(elm)
                        self.values_list.append(elm)
                    
                    return True
            else:
                self.values_list = []
                for elm in list:
                    self.values_list.append(elm)
                
                return True

            return None
        
        
        def set_disable(self):
            '''
            set the protect flag (and change style to wx.TE_READONLY and background to gray
            '''
            if self.control:
                self.enable = True
                self.control.Enable(False)

            else:
                self.enable = True
            
        def set_enable(self):
            '''
            unset the protect flag (and change style to wx.TE_PROCESS_ENTER and background to gray
            '''
            if self.control:
                self.enable = None
                self.control.Enable(True)
            else:
                self.enable = None
            
        def set_value(self, value):
            '''
            set the value into the control
            '''
            #print self.name, value
            if self.control:
                if self.type in (CHOICE_CNTL, RADIO_CNTL):
                    #self.control.SetValue(value)
                    posit = self.control.FindString(value)
                    if posit > -1:
                        self.control.SetSelection(posit)
                        return True
            
                else:
                    self.control.SetValue(value)
                    return True
     

            self.initial_value = value
            
            return None
                    
                
        def get_value(self):
            '''
            returns the current value of the control
            '''
            if self.control:
                if self.type in (CHOICE_CNTL, RADIO_CNTL):
                    return self.control.GetString(
                                            self.control.GetSelection()
                                                 )

                else:
                    return self.control.GetValue()
    
            else:
                if self.initial_value:
                    return self.initial_value
                    
            return None


class ThreadedWorker(threading.Thread):
    '''
    ThreadedWorker 
    '''
    def __init__(self, workload):
        self._workload = workload
        threading.Thread.__init__(self)

    def run(self):
        return            



if __name__ == '__main__':
    raise RuntimeError, "%s %s" % ("postprocesscontrol.py", STANDALONE_ERROR)
