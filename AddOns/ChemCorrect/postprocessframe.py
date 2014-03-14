"""
postprocessframe.py -- the postprocessframe module contains the 
PostProcessFrame class
This class defines the generic UI for the Picarro PostProcess functionality.

This module is a wx.Frame definition, and cannot run stand-alone.
"""
import gc
#gc.set_debug(gc.DEBUG_SAVEALL)
gc.enable()
import os
import sys
import time
import datetime
import threading
import Queue

import wx
import wx.html
import wx.lib.agw.aui as aui

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from postprocessdefn import *
from Utilities.FigureInteraction import FigureInteraction

import wx.lib.inspection
#from matplotlib.widgets import Button

DSPVER = '1.2.0'

class PostProcessFrame(wx.Frame):
    """ 
    a Frame containing a parameters window, optional display HTML window(s) 
    and optional plot window
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        self.counter = 0
        if "process_class" in kwargs:
            self._pclass = kwargs["process_class"]
            del kwargs["process_class"]
        else:
            raise RuntimeError, "Cannot create GUI, Process Class not passed."
        
        if "layout" in kwargs:
            rlayout = kwargs["layout"]
            del kwargs["layout"]
        else:
            rlayout = None

        if "size" in kwargs:
            rsize = kwargs["size"]
            del kwargs["size"]
        else:
            rsize = None

        if "allow_fi" in kwargs:
            self.allow_fi = kwargs["allow_fi"]
            del kwargs["allow_fi"]
        else:
            self.allow_fi = None
            
        # About Info
        self.about_name = "Picarro Post Processing"
        if not 'dspver' in kwargs:
            self.about_version = DSPVER
        else:
            self.about_version = kwargs['dspver']
            del kwargs['dspver']
        self.about_copyright = "(c) 2011 Picarro Inc."
        self.about_description = "PostProcess Frame"
        self.about_website = "http://www.picarro.com"
        
        wx.Frame.__init__(self, *args, **kwargs)

        self.rlock = threading.RLock()
                
        self._notebook = None
        self.first_layout_done = None
        self._elapsed_time_dlg_active = None
        self.initial_process_done = None

        
        self._default_layout = self._pclass._layout
        self._default_size = self._pclass._sz
        
        self.mainBackgroundColor = MAIN_BACKGROUNDCOLOR
        self.controlBackgroundColor = CONTROL_BACKGROUNDCOLOR
        self.plotBackgroundColor = PLOT_FACECOLOR

        color = self._pclass.frame_color_init()
        
        if color:
            if "mainBackgroundColor" in color.keys():
                self.mainBackgroundColor = color["mainBackgroundColor"]
            if "controlBackgroundColor" in color.keys():
                self.controlBackgroundColor = color["controlBackgroundColor"]
            if "plotBackgroundColor" in color.keys():
                self.plotBackgroundColor = color["plotBackgroundColor"]

        print "plotBackgroundColor", self.plotBackgroundColor
        
        self._pentry_controls = self._pclass.cntls_obj
        self._entry_controls_are_defined = None
        self._html_list = []
        self._plot_list = []
        
        self._btnmax = 29

        self._plot_page = None
        self._plot_win = None
        self._plot_page_tidx = {}
        self._pclass._plot_page_tidx = self._plot_page_tidx
        self._pclass._rlock = self.rlock

        self.fig_act = {}        
        self._pclass.fig_act = self.fig_act

        self._auto_time_first_time_done = None
        
        self._determine_panels_and_buttons()
        
        self._build_parameter_panel()

        self._current_plot_idx = 0
        
        self._type = "paramater_pnl" 
        
        self._cust_btn = {}
        self._cust_btn_id = {}
        self._cust_mnu = {}

        self._pcust_btn = {}
        self._pcust_btn_id = {}
        
        self._cust_mnu_id = {}
        self._cust_timer = {}
        self._cust_timer_param = {}
        self._cust_timer_id = {}
        self._cust_timer_state = {}
        
        self._btn_size = self._pclass.button_size
        self._pbtn_size = self._pclass.pbutton_size


        buttons_pnl = self._html_buttons_pnl
        self._type = "html_pnl" 

        self._define_custom_buttons_for_panel(PARAMETER, buttons_pnl)
        
        # OK/Cancel always available    
        self._ok_btn = wx.Button(
                                 buttons_pnl, 
                                 wx.ID_OK, 
                                 "", 
                                 style=wx.BU_EXACTFIT
                                 )
        self._ok_btn.SetMinSize((self._btn_size, 20))
        
        if not self._notebook:
            self._notebook = aui.AuiNotebook(self, 
                                             -1, 
                                             agwStyle = aui.AUI_NB_TAB_FLOAT | aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS | aui.AUI_NB_DRAW_DND_TAB | aui.AUI_NB_CLOSE_ON_ALL_TABS
                                             )
            self._notebook.SetBackgroundColour(self.mainBackgroundColor)
            self._pclass._notebook = self._notebook

        self._notebook.AddPage(self._parm_page, "parameters")
        self._parm_page_tidx = self._notebook.GetPageIndex(self._parm_page)
        self._notebook.SetCloseButton(self._parm_page_tidx, False)

        # plot panel
        if self._plot_active:
            self._plot_figure = {}
            for i in range(0, self._plot_active):
                self._plot_figure[i] = Figure()
                
            if not self._plot_page:
                self._plot_win = {}
                self._plot_page = {}
                self._plot_pnl = {}
                for i in range(0, self._plot_active):
                    self._plot_page[i] = wx.Window(self, -1)
                    self._plot_win[i] = wx.Window(self, -1)
                    self._plot_pnl[i] = FigureCanvas(
                                                     self._plot_win[i], 
                                                     -1, 
                                                     self._plot_figure[i]
                                                     )

            buttons_pnl = self._html_buttons_pnl
            
            # plot panel
            if self._plot_next_btn_active:
                self._next_plot_btn = wx.Button(buttons_pnl, -1, "Next", style=wx.BU_EXACTFIT)
                self._next_plot_btn.SetMinSize((self._btn_size, 20))

            self._define_custom_timers_for_figure(HTML, self._plot_figure)
            
            for i in range(0, self._plot_active):
                self._notebook.AddPage(self._plot_page[i], "Plot %s" %(i+1))
                self._plot_page_tidx[i] = self._notebook.GetPageIndex(self._plot_page[i])
                self._notebook.SetCloseButton(self._plot_page_tidx[i], False)

                


        # html panel
        if self._html_active:
            self._html_page = {}
            self._html_page_tidx = {}
            for i in range(0, self._html_active):
                init_html = ""
                html_title = "default %s" %(i)

                try:
                    if i in self._pclass._html.keys():
                        init_html = self._pclass._html[i]
                except:
                    pass

                
                try:
                    if i in self._pclass._html_title.keys():
                        html_title = self._pclass._html_title[i]
                except:
                    pass
                
                self._html_page[i] = wx.html.HtmlWindow(self._notebook, -1)
                self._html_page[i].SetPage(init_html)
                self._html_page[i].SetBackgroundColour(self.mainBackgroundColor)
                
                self._notebook.AddPage(self._html_page[i], html_title)
                self._html_page_tidx[i] = self._notebook.GetPageIndex(self._html_page[i])
                self._notebook.SetCloseButton(self._html_page_tidx[i], False)

            self._define_custom_buttons_for_panel(HTML, self._html_buttons_pnl)

            self._cancel_btn = wx.Button(self._html_buttons_pnl, -1, "Exit", style=wx.BU_EXACTFIT)
            self._cancel_btn.SetMinSize((self._btn_size, 20))

        # Menu bar
        self._frame_menubar = wx.MenuBar()
        menu_item = {}
        file_menu = "&File"
        help_menu = "&Help"
        view_menu = "&View"
        
        #Load Source menu inside &File menu
        menu_item[file_menu] = wx.Menu()
        menu_item[view_menu] = wx.Menu()


        #Exit inside &File menu
        self._id_exit = wx.NewId()
        self._i_exit = wx.MenuItem(menu_item[file_menu], self._id_exit, "E&xit\tCtrl+x", "", wx.ITEM_NORMAL)
        menu_item[file_menu].AppendItem(self._i_exit)

        #Restore Tab Layout inside &View menu
        self._id_restore = wx.NewId()
        self._i_layout = wx.MenuItem(menu_item[view_menu], self._id_restore, "&Restore Layout\tCtrl+r", "", wx.ITEM_NORMAL)
        menu_item[view_menu].AppendItem(self._i_layout)

        #About menu inside &Help menu
        menu_item[help_menu] = wx.Menu()
        self._id_about = wx.NewId()
        self._i_about = wx.MenuItem(menu_item[help_menu], wx.ID_ABOUT, "&About %s" %(self.about_name), "", wx.ITEM_NORMAL)        
        menu_item[help_menu].AppendItem(self._i_about)

        #find any custom menus and instantiate them inside the proper menu
        for i in range(1,self._btnmax):
            if self._cust["mact"][i]:
                if not self._cust["mloc"][i] in menu_item.keys():
                    menu_item[self._cust["mloc"][i]] = wx.Menu()
                self._cust_mnu_id[i] = wx.NewId()
                self._cust_mnu[i] = wx.MenuItem(menu_item[self._cust["mloc"][i]], self._cust_mnu_id[i], self._cust["mact"][i], "", wx.ITEM_NORMAL)        
                menu_item[self._cust["mloc"][i]].AppendItem(self._cust_mnu[i])

        #file menu first, then other menus and help menu last
        self._frame_menubar.Append(menu_item[file_menu], file_menu)
        
        for k in menu_item.keys():
            if not k == file_menu:
                if not k == help_menu:
                    self._frame_menubar.Append(menu_item[k], k)
        
        self._frame_menubar.Append(menu_item[help_menu], help_menu)
        

        self.SetMenuBar(self._frame_menubar)
        
        self.SetSize((900,600))
        self._initClientSize = self.GetClientSize()
        
        self.__do_layout(rlayout, rsize)
        self._bind_events()
        

            
        
    def _determine_panels_and_buttons(self):
        '''
        set up panels, buttons, timers based on process class dictionary
        '''
        self._html_active = None
        self._plot_active = None
        self._plot_next_btn_active = None
        self._mod_active = None

        self._cust = {
                      "bact": {}, #button active
                      "bloc": {}, #button location
                      "mact": {}, #menu active
                      "mloc": {}, #menu location
                      "tparm": {}, #timer passed parameter
                      "tloc": {}, #timer location
                      "ttime": {}, #timer time period
                      "tauto": {}, #timer autostart
                     }

        self._pcust = {
                      "bact": {}, #button active
                      "bloc": {}, #button location
                      "mact": {}, #menu active
                      "mloc": {}, #menu location
                      "tparm": {}, #timer passed parameter
                      "tloc": {}, #timer location
                      "ttime": {}, #timer time period
                      "tauto": {}, #timer autostart
                     }
        
        for ii in range(1,self._btnmax):
            for kk in self._cust.keys():
                self._cust[kk][ii] = None
                
                
        self._values_column_count = self._pclass.selection_defn_column_count
        self._parameter_column_count = self._pclass.parameter_defn_column_count
        
        try:
            if PLOT_NEXT in self._pclass.buttons_defn_dict.keys():
                self._plot_next_btn_active = self._pclass.buttons_defn_dict[PLOT_NEXT]
                
            for i in range(1,self._btnmax):
                k = "CUST%s" %(i)
                #print "k:", k
                if k in self._pclass.buttons_defn_dict.keys():
                    bloc, bact, mloc, mact = self._pclass.buttons_defn_dict[k]
                    self._cust["bloc"][i] = bloc
                    self._cust["bact"][i] = bact
                    self._cust["mloc"][i] = mloc
                    self._cust["mact"][i] = mact
                    
                if k in self._pclass.pbuttons_defn_dict.keys():
                    bloc, bact, mloc, mact = self._pclass.pbuttons_defn_dict[k]
                    self._pcust["bloc"][i] = bloc
                    self._pcust["bact"][i] = bact
                    self._pcust["mloc"][i] = mloc
                    self._pcust["mact"][i] = mact
                
                if k in self._pclass.timers_defn_dict.keys():
                    tloc, tparm, ttime, tauto = self._pclass.timers_defn_dict[k]
                    if not ttime:
                        ttime = 50
                    self._cust["tloc"][i] = tloc
                    self._cust["tparm"][i] = tparm
                    self._cust["ttime"][i] = ttime
                    self._cust["tauto"][i] = tauto
                    
                
        except:
            pass

        try:
            if HTML in self._pclass.panels_defn_dict.keys():
                self._html_active = self._pclass.panels_defn_dict[HTML]
                #print "self._html_active", self._html_active
            if PLOT in self._pclass.panels_defn_dict.keys():
                self._plot_active = self._pclass.panels_defn_dict[PLOT]
            if MOD in self._pclass.panels_defn_dict.keys():
                self._mod_active = self._pclass.panels_defn_dict[MOD]

        except:
            pass
        

    def _build_parameter_panel(self):
        '''
        build parameter controls in parameter panel
        build general selection controls in parameter panel
        '''
        #self._pnl_request_queue = deque()
        #self._pnl_response_queue = {}
        
        self._name_fld_dict = {}
        
        self._parm_page = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.WANTS_CHARS|wx.NO_BORDER)
        self._parm_page.SetName("parameters")
        self._parm_page.SetBackgroundColour(self.mainBackgroundColor)
        #wx.EVT_SCROLLWIN( self, self.OnScroll) 
 
        self._instantiate_buttons_pnls()
        
        self._add_controls_to_panel(PARAMETER, self._parm_page)
        
        self._pclass.name_fld_dict = self._name_fld_dict
        self._pclass.entry_controls_are_defined = self._entry_controls_are_defined
        
                
    def _add_controls_to_panel(self, loc_identity, screen_loc):
        
        sysfont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        fpoint = sysfont.GetPointSize()
        bigpoint = fpoint + 2
        ffamily = sysfont.GetFamily()
        fstyle = sysfont.GetStyle()
        fweight = sysfont.GetWeight()
        bigfont = wx.Font(bigpoint, ffamily, fstyle, fweight)
        boldfont = wx.Font(fpoint, ffamily, fstyle, wx.BOLD)
        bigboldfont = wx.Font(bigpoint, ffamily, fstyle, wx.BOLD)

        
        for name, control in self._pentry_controls.control_list.iteritems():
            #print "control", name, control
            if not control.location == loc_identity:
                continue
            
            control.cid = wx.NewId()
            control.label_control = wx.StaticText(
                                                  screen_loc, 
                                                  label=control.label
                                                  )

            if control.type in (TEXT_CNTL, NOTE_CNTL, PASSWD_CNTL):
                if not control.default:
                    control.default = ""

                if control.initial_value:
                    value = control.initial_value
                else:
                    value = control.default
                
                if control.type == NOTE_CNTL:    
                    style = wx.TE_PROCESS_ENTER|wx.TE_LEFT|wx.TE_MULTILINE
                    size = control.control_size
                elif control.type == PASSWD_CNTL:    
                    style = wx.TE_PROCESS_ENTER|wx.TE_PASSWORD
                    size = (control.control_size, -1)
                else:    
                    style = wx.TE_PROCESS_ENTER|wx.TE_CENTRE
                    size = (control.control_size, -1)
                    
                control.control = wx.TextCtrl(
                                      screen_loc, 
                                      control.cid, 
                                      value, 
                                      size = size, 
                                      style = style
                                      )
                

            elif control.type == TEXT_CNTL_DSP:
                if not control.default:
                    control.default = ""
                
                if control.initial_value:
                    value = control.initial_value
                else:
                    value = control.default
                    
                control.control = wx.TextCtrl(
                                      screen_loc, 
                                      control.cid, 
                                      value, 
                                      size = (control.control_size, -1), 
                                      style = wx.TE_READONLY|wx.TE_LEFT
                                      )

                control.control.SetBackgroundColour("#C0C0C0")
            
            elif control.type == CHOICE_CNTL:
                if not control.values_list:
                    control.values_list = []
                
                style = wx.TE_PROCESS_ENTER|wx.TE_LEFT
                      
                control.control = wx.Choice(
                                    screen_loc, 
                                    control.cid, 
                                    choices = control.values_list, 
                                    size = (control.control_size,-1), 
                                    style = style
                                        ) 

                # setting the choice control to the appropriate value
                if control.default == "None":
                    control.default = CHOICE_NONE

                if control.initial_value:
                    posit = control.control.FindString(control.initial_value)
                    if posit > -1:
                        control.control.SetSelection(posit)
                elif control.default:
                    posit = control.control.FindString(control.default)
                    if posit > -1:
                        control.control.SetSelection(posit)
    
            elif control.type == RADIO_CNTL:
                if not control.values_list:
                    control.values_list = []
                    
                style = wx.TE_PROCESS_ENTER|wx.TE_LEFT
                    
                control.control = wx.RadioBox(
                                    screen_loc, 
                                    control.cid,
                                    label="",
                                    choices = control.values_list, 
                                    size = (control.control_size,-1), 
                                    majorDimension=1,
                                    style = style
                                        ) 

                # setting the choice control to the appropriate value
                if control.default == "None":
                    control.default = CHOICE_NONE
    
                if control.initial_value:
                    posit = control.control.FindString(control.initial_value)
                    if posit > -1:
                        control.control.SetSelection(posit)
                elif control.default:
                    posit = control.control.FindString(control.default)
                    if posit > -1:
                        control.control.SetSelection(posit)

            if control.type in (
                                TEXT_CNTL, 
                                TEXT_CNTL_DSP, 
                                RADIO_CNTL, 
                                CHOICE_CNTL,
                                NOTE_CNTL,
                                ):
                if control.enable:
                    control.control.Enable(False)
                else:
                    control.control.Enable(True)

            
            if control.type in (
                                TEXT_CNTL, 
                                TEXT_CNTL_DSP, 
                                RADIO_CNTL, 
                                CHOICE_CNTL
                                ):
                
                if control.font_attr == "big":
                    control.control.SetFont(bigfont)
                    control.label_control.SetFont(bigfont)
                elif control.font_attr == "bold":
                    control.control.SetFont(boldfont)
                    control.label_control.SetFont(boldfont)
                elif control.font_attr == "bigbold":
                    control.control.SetFont(bigboldfont)
                    control.label_control.SetFont(bigboldfont)
            

    def _instantiate_buttons_pnls(self):
        # controls panels
        if self._html_active:
            self._html_buttons_pnl = wx.Panel(self, -1, style=wx.NO_BORDER)
            self._html_buttons_pnl.SetBackgroundColour(self.controlBackgroundColor)
            
            tid = wx.NewId()
            self._html_timer = wx.Timer(self, tid)
            #self.Bind(wx.EVT_TIMER, self._on_request_queue_timer, self._html_timer)
            self._html_timer.Start(100)

            #self._plot_buttons_pnl.SetBackgroundColour(RED)


    def __do_layout(self, restore_layout=None, restore_size=None):
        #pause timers during layout
        self._timer_init("pause")
        #self.fig_act = {}        

        entry_size = self.GetSize()
        client_size = self.GetClientSize()
        init_min_w, init_min_h = self._initClientSize

        # minimum width/height set from the initial client width/height when setting up controls
        w,h = client_size
        min_w = w
        if min_w < init_min_w:
            min_w = init_min_w
        min_h = h - 22
        if min_h < init_min_h:
            min_h = init_min_h
        
        main_layout_sizer = None
        main_layout_sizer = wx.BoxSizer(wx.VERTICAL)
        main_layout_sizer.SetMinSize((min_w,min_h))

        buttons_pnl_sizer = None
        buttons_pnl_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_pnl_sizer.Add((20, 0), 1, 0, 0) # push controls to right

        if self._type == "html_pnl":
            main_layout_sizer.Add(self._notebook, 1,wx.ALL|wx.EXPAND, 4)

            buttons_pnl_sizer.Add(self._ok_btn, 0, wx.ALL|wx.EXPAND, 4)
            self._add_custom_buttons_to_sizer(HTML, buttons_pnl_sizer)
                    
            buttons_pnl_sizer.Add(self._cancel_btn, 0, wx.ALL|wx.EXPAND, 4)
        
            buttons_pnl_sizerMargin = wx.BoxSizer(wx.VERTICAL)
            buttons_pnl_sizerMargin.Add(buttons_pnl_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

            parameter_pnl_sizer = self._controls_sizer(PARAMETER)
            self._parm_page.SetSizer(parameter_pnl_sizer)
            
            self._do_plot_configuration()
            self._pclass._plot_pnl = self._plot_pnl
            #print "should have a canvas"
            
            self._do_mod_configuration()

            self._html_buttons_pnl.Show()
            self._notebook.Show()

            self.SetMenuBar(self._frame_menubar)
        
            self._enable_custom_menus_for_panel(HTML)
            
            self._html_buttons_pnl.SetSizer(buttons_pnl_sizer)
            main_layout_sizer.Add(self._html_buttons_pnl, 0, wx.EXPAND, 0)
            
        elif self._type == "plot_pnl":
            #destroy the old plot
            try:
                self._plot_pnl.Destroy()
            except:
                True

            self._plot_figure = self._pclass._plot_figure[self._current_plot_idx]
            self._plot_pnl = FigureCanvas(self, -1, self._plot_figure)
            self._pclass._plot_pnl = self._plot_pnl
            #print "should have a canvas2"

            wx.EVT_PAINT(self, self._on_paint)

            plot_sizer = wx.BoxSizer(wx.VERTICAL)
            plot_sizer.Add(self._plot_pnl, 1, wx.LEFT|wx.TOP|wx.GROW)
            
            main_layout_sizer.Add(plot_sizer, 1, wx.ALL|wx.EXPAND, 4)
            
            self._add_custom_buttons_to_sizer(PLOT, buttons_pnl_sizer)
                    
            if self._plot_next_btn_active:
                buttons_pnl_sizer.Add(self._next_plot_btn, 0, wx.ALL|wx.EXPAND, 4)
                
            buttons_pnl_sizer.Add(self._close_plot_btn, 0, wx.ALL|wx.EXPAND, 4)
            buttons_pnl_sizer.Add(self._cancel_plot_btn, 0, wx.ALL|wx.EXPAND, 4)
 
            buttons_pnl_sizerMargin = wx.BoxSizer(wx.VERTICAL)
            buttons_pnl_sizerMargin.Add(buttons_pnl_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

            self._parameter_buttons_pnl.Hide()
            self._parm_page.Hide()

            if self._html_active:
                self._html_buttons_pnl.Hide()
                self._notebook.Hide()
                
            #self._plot_buttons_pnl.Show()
            self._plot_pnl.Show()

            self._frame_menubar.Show(False)
            self.SetMenuBar(None)
            
            self._enable_custom_menus_for_panel(PLOT)
 
        else: ## self._type == "paramater_pnl"
            parameter_pnl_sizer = self._controls_sizer(PARAMETER)
            
            main_layout_sizer.Add(self._parm_page, 1,wx.ALL|wx.EXPAND, 4)
            self._parm_page.SetSizer(parameter_pnl_sizer)

            buttons_pnl_sizer.Add(self._ok_btn, 0, wx.ALL|wx.EXPAND, 4)
            buttons_pnl_sizer.Add(self._cancel_parm_btn, 0, wx.ALL|wx.EXPAND, 4)

            buttons_pnl_sizerMargin = wx.BoxSizer(wx.VERTICAL)
            buttons_pnl_sizerMargin.Add(buttons_pnl_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

            # Showing/Hiding the appropriate panels -
            # on some machines, they show even though not put in the layout
            self._parameter_buttons_pnl.Show()
            self._parm_page.Show()

            if self._plot_active:
                for i in range(0, self._plot_active):
                    self._plot_pnl[i].Hide()

            if self._html_active:
                self._html_buttons_pnl.Hide()
                self._notebook.Hide()

            self._frame_menubar.Show(True)
            self.SetMenuBar(self._frame_menubar)
        
            self._enable_custom_menus_for_panel(PARAMETER)

            self._parameter_buttons_pnl.SetSizer(buttons_pnl_sizer)
            main_layout_sizer.Add(self._parameter_buttons_pnl, 0, wx.EXPAND, 0)
        
        self.SetSizer(main_layout_sizer)
        main_layout_sizer.Fit(self)
        
        #don't let size go below minimum (but can be bigger)
        w,h = entry_size
        if w < 900:
            w = 900
        if h < 600:
            h = 600
        self.SetSize((w,h))
        #print "do layout"
        self._layout_main(restore_layout, restore_size)
        #wx.lib.inspection.InspectionTool().Show()
        
        self._timer_init("start")

        if not self._auto_time_first_time_done:
            self._auto_time_first_time_done = True
            self._start_auto_timers()


    def _do_plot_configuration(self):
        '''
        configure the plot panels
        '''
        #destroy the old plot
        try:
            if self._plot_active:
                for i in range(0, self._plot_active):
                    self._plot_pnl[i].Destroy()
        except:
            True

        plot_sizer = {}
        self._plot_buttons_pnl = {}
        self._plot_controls_pnl = {}

        pltwin_sizer = {}
        pltcontrols_pnl_sizer = {}
        pltbuttons_pnl_sizer = {}
        pltbuttons_pnl_sizerMargin = {}
        
        if self._pclass._plot_figure:
            if self._plot_active:
                self._pclass._plot_pnl = None
                for i in range(0, self._plot_active):
                    plt_id = "plot%s" % (i)
                    
                    if i not in self._plot_buttons_pnl.keys():
                        self._plot_buttons_pnl[i] = wx.Panel(self._plot_page[i], -1, style=wx.NO_BORDER)
                        self._plot_buttons_pnl[i].SetBackgroundColour(self.controlBackgroundColor)
                        self._define_custom_buttons_for_plot(plt_id, self._plot_buttons_pnl[i])

                        for ii in range(1,self._btnmax):
                            if ii in self._pcust_btn.keys():
                                if self._pcust["bact"][ii]:
                                    #print "binding"
                                    self.Bind(
                                              wx.EVT_BUTTON, 
                                              self._on_custom_btn, 
                                              self._pcust_btn[ii]
                                              )
                                    
                        self._plot_controls_pnl[i] = wx.Panel(self._plot_page[i], -1, style=wx.NO_BORDER)
                        self._plot_controls_pnl[i].SetBackgroundColour(self.plotBackgroundColor)
                        self._add_controls_to_panel(plt_id, self._plot_controls_pnl[i])
                        pltcontrols_pnl_sizer[i] = self._controls_sizer(plt_id)
                        self._plot_controls_pnl[i].SetSizer(pltcontrols_pnl_sizer[i])

                        self._pclass.restore_control_values(plt_id)

                    pltbuttons_pnl_sizer[i] = None
                    pltbuttons_pnl_sizer[i] = wx.BoxSizer(wx.HORIZONTAL)
                    pltbuttons_pnl_sizer[i].Add((20, 0), 1, 0, 0) # push pltbuttons to right

                    if self._plot_next_btn_active:
                        pltbuttons_pnl_sizer[i].Add(self._next_plot_btn, 0, wx.ALL|wx.EXPAND, 4)
        
                    self._add_custom_pbuttons_to_sizer(plt_id, pltbuttons_pnl_sizer[i])
                            
                    pltbuttons_pnl_sizerMargin[i] = wx.BoxSizer(wx.VERTICAL)
                    pltbuttons_pnl_sizerMargin[i].Add(pltbuttons_pnl_sizer[i], 0, wx.EXPAND|wx.BOTTOM, 10)
                   
#                    print
#                    print "self._pclass._plot_figure",i, self._pclass._plot_figure[i]
#                    print
                    
                    if self._pclass._plot_figure[i]:
                        self._plot_figure[i] = self._pclass._plot_figure[i]
                        self._plot_pnl[i] = FigureCanvas(self._plot_page[i], -1, self._plot_figure[i])
    
                        plot_sizer[i] = wx.BoxSizer(wx.VERTICAL)
    
                        if plt_id in self._pclass.cntls_len.keys():
                            cntl_cols, size_factor = self._pclass.cntls_cols[plt_id]
                            pltwin_sizer[i] = None
                            pltwin_sizer[i] = wx.BoxSizer(wx.HORIZONTAL)
                            pltwin_sizer[i].Add(
                                                self._plot_pnl[i], 
                                                (100-size_factor), 
                                                wx.ALL|wx.EXPAND
                                                )
                            pltwin_sizer[i].Add(
                                                self._plot_controls_pnl[i], 
                                                size_factor, 
                                                wx.ALL|wx.EXPAND
                                                )
                            plot_sizer[i].Add(pltwin_sizer[i], 1, wx.ALL|wx.EXPAND)
                        else:
                            plot_sizer[i].Add(self._plot_pnl[i], 1, wx.ALL|wx.EXPAND)

                        self._plot_buttons_pnl[i].SetSizer(pltbuttons_pnl_sizer[i])
                        plot_sizer[i].Add(self._plot_buttons_pnl[i], 0, wx.EXPAND, 0)
                        
                        if plt_id in self._pclass.cntls_len.keys():
                            self._plot_controls_pnl[i].Show()
                            
                        self._plot_buttons_pnl[i].Show()
                        self._plot_page[i].SetSizer(plot_sizer[i])
                    

                # give access to pnl inside of control class
                self._pclass._plot_pnl = self._plot_pnl
                wx.EVT_PAINT(self, self._on_paint)


    def _do_mod_configuration(self):
        '''
        configure the modal panels
        '''
        self._mod_controls_pnl = {}

        mdlcontrols_pnl_sizer = {}
        
        if self._mod_active:
            self._pclass._mod_pnl = None
            for i in range(0, self._mod_active):
                mdl_id = "mod%s" % (i)
                
                if i not in self._mod_controls_pnl.keys():
                    self._mod_controls_pnl[i] = wx.Dialog(
                                                          None, 
                                                          -1, 
                                                          mdl_id, 
                                                          style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
                                                          )
                    self._mod_controls_pnl[i].SetBackgroundColour(self.mainBackgroundColor)
                    self._add_controls_to_panel(mdl_id, self._mod_controls_pnl[i])
                    mdlcontrols_pnl_sizer[i] = self._controls_sizer(mdl_id)

                    mdlsizer = wx.BoxSizer(wx.VERTICAL)
                    mdlsizer.Add(mdlcontrols_pnl_sizer[i])

                    btnsizer = self._mod_controls_pnl[i].CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
                    mdlsizer.Add(btnsizer)
                    
                    self._mod_controls_pnl[i].SetSizer(mdlsizer)

                    self._pclass.restore_control_values(mdl_id)



    def _timer_init(self, action):
        if action == "pause":
            for i in self._cust_timer.keys():
                if i in self._cust_timer_state.keys():
                    if self._cust_timer_state[i] == "start":
                        self._cust_timer_state[i] = "pause"
                        self._cust_timer[i].Stop()

        elif action == "start":
            for i in self._cust_timer.keys():
                if i in self._cust_timer_state.keys():
                    if self._cust_timer_state[i] == "pause":
                        self._cust_timer_state[i] = "start"
                        tme = self._cust["ttime"][i]
                        self._cust_timer[i].Start(tme)
        

    def _layout_main(self, restore_layout=None, restore_size=None):
        self._timer_init("pause")
        self.counter += 1
        
        self._pclass.refresh_the_plots = True            

        if not self.first_layout_done:
            self.first_layout_done = True
            if self._plot_active:
                for i in range(0, self._plot_active):
                    if self.allow_fi:
                        if self._pclass._plot_figure:
                            if self._pclass._plot_figure[i]:
                                if not i in self.fig_act.keys():
                                    self.fig_act[i] =  FigureInteraction(self._plot_figure[i], self.rlock)
                                    #print "created", self.fig_act[i]
                                else:
                                    if not self.fig_act[i].fig == self._plot_figure[i]:
                                        del(self.fig_act[i])
                                        self.fig_act[i] =  FigureInteraction(self._plot_figure[i], self.rlock)
                                        #print "recreated", self.fig_act[i]
                                
                    self._plot_page[i].Layout()

            #self._parm_page.Layout() 

            if restore_layout:
                layout = restore_layout
                size = restore_size
                self._notebook.LoadPerspective(layout)
                self.SetSize(size)
                self.Layout()
            else:
                self.Layout()
        else:
            if self._plot_active:
                for i in range(0, self._plot_active):
                    if self.allow_fi:
                        if self._pclass._plot_figure:
                            if self._pclass._plot_figure[i]:
                                if not i in self.fig_act.keys():
                                    self.fig_act[i] =  FigureInteraction(self._plot_figure[i], self.rlock)
                    self._plot_page[i].Layout()

        self._timer_init("start")
        
        if not self.initial_process_done:
            self.initial_process_done = True
            self._initial_frame_process()
    
    def _initial_frame_process(self):
        if not self._pclass.initial_frame_process:
            return
        
        for proc in self._pclass.initial_frame_process:
            if BUTTON in proc.keys():
                bname = proc[BUTTON]
                i_str = bname[4:]
                idx = int(i_str)
                self._custom_btn_preprocess(idx)
            elif PROCESS in proc.keys():
                if proc[PROCESS]:
                    self._process_parameters()
                
        
                 
    def _restore_default_tabs(self):
        '''
        restore default tab layout 
        '''
        if self._plot_active:
            for i in range(0, self._plot_active):
                if self.allow_fi:
                    if self._pclass._plot_figure:
                        if not i in self.fig_act.keys():
                            self.fig_act[i] =  FigureInteraction(self._plot_figure[i], self.rlock)

                self._plot_page[i].Layout()

        #self._parm_page.Layout() 
        if self._default_layout:
            self._notebook.LoadPerspective(self._default_layout)
            self.SetSize(self._default_size)
            self.Layout()
        

    def _controls_sizer(self, cntl_location):
        
        if not cntl_location in self._pclass.cntls_len.keys():
            return None
        
        cntl_len = self._pclass.cntls_len[cntl_location]
        cntl_cols, size_factor = self._pclass.cntls_cols[cntl_location]
        
        parms_sizer = wx.GridBagSizer(hgap=10, vgap=5)
        parms_sizer.SetEmptyCellSize((0, 0))
        
        prev_cntl = None
        last_cntl = None
        first_cntl = None
        name_ord_list = self._pentry_controls.yield_names_in_order()
        row = 0
        lcol = 0
        ccol = 1
        for name in name_ord_list:
            control = self._pentry_controls.control_list[name]
            row_moved = None
            if control.location == cntl_location:
                if control.type in (SPACER_CNTL, SPACER_CNTL_SM):
                    if cntl_cols > 1:
                        row_moved = True
                        if lcol > 0:
                            row += 1
                            lcol = 0
                            ccol = 1
                    
                if control.type == SPACER_CNTL:
                    parms_sizer.Add((20,20), (row, lcol))
                    parms_sizer.Add((20,20), (row, ccol))
                elif control.type == SPACER_CNTL_SM:
                    parms_sizer.Add((5,5), (row, lcol))
                    parms_sizer.Add((5,5), (row, ccol))
                elif control.type == SPACER_CNTL_SKIP:
                    lcol += 1
                    ccol += 1
                else:
                    if not first_cntl:
                        first_cntl = control.control
                        
                    last_cntl = control.control
                    if control.type in (NOTE_CNTL, ):
                        if cntl_cols > 1:
                            row_moved = True
                            if lcol > 0:
                                row += 1
                                lcol = 0
                                ccol = 1
                            
                        control.label_control.Hide()
                        parent = control.control.GetParent()
                        box = wx.StaticBox(parent, -1, control.label)
                        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
                        box_sizer.Add(control.control)
                        parms_sizer.Add(box_sizer, (row, lcol), span=(2,4))
                        row += 2
                    
                    elif control.type in (RADIO_CNTL,):
                        control.label_control.Hide()
                        parent = control.control.GetParent()
                        box = wx.StaticBox(parent, -1, control.label)
                        box_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
                        box_sizer.Add(control.control)
                        parms_sizer.Add(box_sizer, (row, lcol), span=(1,2))
                        #row += 1
                        
                    else:
                        parms_sizer.Add(control.label_control, (row, lcol))
                        parms_sizer.Add(control.control, (row, ccol))
        
                    if prev_cntl:
                        control.control.MoveAfterInTabOrder(prev_cntl)
                
                if row_moved:
                    lcol = 3
                    ccol = 4
                
                #parms_outer_sizer.Add(parms_sizer)
                if not control.type in (
                                        SPACER_CNTL, 
                                        SPACER_CNTL_SM, 
                                        TEXT_CNTL_DSP
                                        ):
                    prev_cntl = control.control
                
                if cntl_cols > 1:
                    if lcol == 0:
                        lcol = 2
                        ccol = 3
                    else:
                        row += 1
                        lcol = 0
                        ccol = 1
                else:
                    row += 1
                    
        if prev_cntl:
            if last_cntl:
                last_cntl.MoveAfterInTabOrder(prev_cntl)
                
                if first_cntl:
                    first_cntl.MoveAfterInTabOrder(last_cntl)

        parameter_pnl_sizer = wx.BoxSizer(wx.VERTICAL)
        parameter_pnl_sizer.Add(parms_sizer, 0, wx.ALL|wx.EXPAND, 4)
        parameter_pnl_sizer.Add((20, 0), 1, 0, 0)
        
        return parameter_pnl_sizer
    
    def _save_nb_layout(self):
        size = self.GetSize()
        spos = self.GetScreenPosition()
        perspective = self._notebook.SavePerspective()
        return perspective, size, spos
    
    def _define_custom_buttons_for_panel(self, pnl, buttons_pnl):
        for i in range(1,self._btnmax):
            if self._cust["bloc"][i] == pnl:
                self._cust_btn_id[i] = wx.NewId()
                self._cust_btn[i] = wx.Button(
                                              buttons_pnl, 
                                              self._cust_btn_id[i], 
                                              self._cust["bact"][i], 
                                              style=wx.BU_EXACTFIT
                                              )
                self._cust_btn[i].SetMinSize((self._btn_size, 20))

        return
    
    def _define_custom_buttons_for_plot(self, pnl, buttons_pnl):
        for i in range(1,self._btnmax):
            if i in self._pcust["bloc"].keys():
                if self._pcust["bloc"][i] == pnl:
                    if not i in self._pcust_btn_id.keys():
                        #print "we have a button"
                        self._pcust_btn_id[i] = wx.NewId()
                        self._pcust_btn[i] = wx.Button(
                                                       buttons_pnl, 
                                                       self._pcust_btn_id[i], 
                                                       self._pcust["bact"][i], 
                                                       style=wx.BU_EXACTFIT
                                                       )
                        self._pcust_btn[i].SetMinSize((self._pbtn_size, 20))

        return
        
    def _define_custom_timers_for_figure(self, pnl, fig):
        for i in range(1,self._btnmax):
            if self._cust["tloc"][i] == pnl:
                self._cust_timer_id[i] = wx.NewId()

        return
    
    def _enable_custom_menus_for_panel(self, pnl):
        for i in range(1,self._btnmax):
            if self._cust["mact"][i]:
                self._cust_mnu[i].Enable(False)
                if self._cust["bloc"][i] == pnl:
                    self._cust_mnu[i].Enable(True)

        return
    
    def _add_custom_buttons_to_sizer(self, pnl, sizer_control):
        if self._pclass.buttons_ord_list:
            for bname in self._pclass.buttons_ord_list:
                i_str = bname[4:]
                i = int(i_str)

                if self._cust["bloc"][i] == pnl:
                    sizer_control.Add(self._cust_btn[i], 0, wx.ALL|wx.EXPAND, 4)
        else:
            for i in range(1,self._btnmax):
                if self._cust["bloc"][i] == pnl:
                    sizer_control.Add(self._cust_btn[i], 0, wx.ALL|wx.EXPAND, 4)

        return
    
    def _add_custom_pbuttons_to_sizer(self, pnl, sizer_control):
        if self._pclass.pbuttons_ord_list:
            for bname in self._pclass.pbuttons_ord_list:
                i_str = bname[4:]
                i = int(i_str)
                
                if i in self._pcust["bloc"].keys():
                    if self._pcust["bloc"][i] == pnl:
                        sizer_control.Add(self._pcust_btn[i], 0, wx.ALL|wx.EXPAND, 4)

        else:
            for i in range(1,self._btnmax):
                if i in self._pcust["bloc"].keys():
                    if self._pcust["bloc"][i] == pnl:
                        sizer_control.Add(self._pcust_btn[i], 0, wx.ALL|wx.EXPAND, 4)

        return


    def _bind_events(self):  
        self.Bind(wx.EVT_SIZE, self._on_resize_pnl)
        
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_MENU, self._on_about, id=wx.ID_ABOUT)
        
        self.Bind(wx.EVT_BUTTON, self._on_ok_btn, self._ok_btn)     

        self.Bind(wx.EVT_MENU, self._on_close, self._i_exit)
        self.Bind(wx.EVT_MENU, self._on_restore_layout, self._i_layout)
        
        if self._plot_active:
            if self._plot_next_btn_active:
                self.Bind(wx.EVT_BUTTON, self._on_next_plot_btn, self._next_plot_btn)           
         

        if self._html_active:
            self.Bind(wx.EVT_BUTTON, self._on_cancel_btn, self._cancel_btn)           

        for i in range(1,self._btnmax):
            if self._cust["bact"][i]:
                self.Bind(wx.EVT_BUTTON, self._on_custom_btn, self._cust_btn[i])
            if self._cust["mact"][i]: 
                exec "self.Bind(wx.EVT_MENU, self._on_custom_mnu_%s, self._cust_mnu[i])" % (i)
                #self.Bind(wx.EVT_MENU, self._on_custom_mnu, self._cust_mnu[i])
        
        self.Bind(aui.EVT_AUINOTEBOOK_DRAG_DONE, self._on_notebook_drag_done) 
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self._on_notebook_drag_done) 
        self.Bind(aui.EVT_AUINOTEBOOK_END_DRAG, self._on_notebook_drag_done)
        if self._plot_active:
            for i in range(0, self._plot_active):
                self._plot_page[i].Bind(wx.EVT_SIZE, self._on_nb_render)


    def _on_paint(self, event):
        if self._plot_active:
            for i in range(0, self._plot_active):
                if self._plot_pnl[i]:
                    try:
                        self._plot_pnl[i].draw()
                    except:
                        continue

        event.Skip()
        

    def OnScroll( self, event ): 
        p = event.GetPosition() 
        d = event.GetOrientation() 
        if event.GetEventType() == wxEVT_SCROLLWIN_THUMBTRACK: 
            self.SetScrollPos( d,p ) 
        px = self.GetScrollPos( wxHORIZONTAL ) 
        py = self.GetScrollPos( wxVERTICAL ) 
        self._parm_page.Move( wxPoint(-px, -py) ) 


    def OnSize( self, event ): 
        cs = self.GetClientSize() 
        px = self.GetScrollPos( wxHORIZONTAL ) 
        py = self.GetScrollPos( wxVERTICAL ) 
        self.SetScrollbar( wxHORIZONTAL, px, cs.x, self._parm_page.min_size[0] ) 
        self.SetScrollbar( wxVERTICAL  , py, cs.y, self._parm_page.min_size[1] ) 


    def _on_about(self, event):
        #wx.MessageBox("Picarro PostProcess version: %s\nCopyright 2010 Picarro, Inc." % ("beta_v01"))
        info = wx.AboutDialogInfo()
        info.Name = "%s (%s)" %(self.about_name, self._pclass.about_name)
        info.Version = "%s (%s)" %(self.about_version, self._pclass.about_version)
        info.Copyright = self._pclass.about_copyright
        info.Description = self._pclass.about_description
        info.WebSite = self._pclass.about_website
        
        wx.AboutBox(info)
        return
    
    def _on_reload_btn(self, event):
        self._process_parameters()


    def _on_ok_btn(self, event):
        self._process_parameters()

            
    def _on_cancel_btn(self, event):
        self._close()


    def _on_close(self, event):
        self._close()

    
    def _on_restore_layout(self, event):
        self._restore_default_tabs()

    
    def _on_cancel_parm_btn(self, event):
        self._close()

    
    def _on_next_plot_btn(self, event):
        self._current_plot_idx += 1
        if not self._current_plot_idx in self._pclass._plot_figure.keys():
            self._current_plot_idx = 0
        
        self._type = "html_pnl"
        #print "next_plot_btn"
        self.__do_layout()
    
    def _on_close_plot_btn(self, event):
        self._pclass.close_plot_btn_process()
        nxt, skip_layout = self._pclass.next_frame()
        if nxt == HTML:
            self._type = "html_pnl"
        elif nxt == PLOT:
            self._type = "plot_pnl"
        else:
            self._type = "parameter_pnl"
        #print "close_plot_btn"    
        self.__do_layout()
        
    def _on_cancel_plot_btn(self, event):
        self._close()

    def _on_resize_pnl(self, event):
        #print "resize_pnl"
        self.first_layout_done = None
        self._layout_main()
        self._pclass.resize_process()
    
    def _on_notebook_drag_done(self, event):
        self._layout_main()
     
    def _on_nb_render(self, event):
        self._layout_main()
                
    def _on_custom_btn(self, event):
        ctl_obj_id = event.GetEventObject().GetId()
        #print ctl_obj_id
        skip_layout = None
        idx = 0
        for i in range(1,self._btnmax):
            if i in self._cust_btn_id.keys():
                if self._cust_btn_id[i] == ctl_obj_id:
                    idx = i
                    break 
                
            if i in self._pcust_btn_id.keys():
                if self._pcust_btn_id[i] == ctl_obj_id:
                    idx = i
                    #print "cust button ping"
                    skip_layout = True
                    break 
                
        if idx > 0:
            self._custom_btn_preprocess(idx)
            
    def _on_custom_mnu_1(self, event):
        skip_layout = None
        self._custom_btn_preprocess(1)
            
    def _on_custom_mnu_2(self, event):
        skip_layout = None
        self._custom_btn_preprocess(2)
            
    def _on_custom_mnu_3(self, event):
        skip_layout = None
        self._custom_btn_preprocess(3)
            
    def _on_custom_mnu_4(self, event):
        skip_layout = None
        self._custom_btn_preprocess(4)
            
    def _on_custom_mnu_5(self, event):
        skip_layout = None
        self._custom_btn_preprocess(5)
            
    def _on_custom_mnu_6(self, event):
        skip_layout = None
        self._custom_btn_preprocess(6)
            
    def _on_custom_mnu_7(self, event):
        skip_layout = None
        self._custom_btn_preprocess(7)
            
    def _on_custom_mnu_8(self, event):
        skip_layout = None
        self._custom_btn_preprocess(8)
            
    def _on_custom_mnu_9(self, event):
        skip_layout = None
        self._custom_btn_preprocess(9)
            
    def _on_custom_mnu_10(self, event):
        skip_layout = None
        self._custom_btn_preprocess(10)

    def _on_custom_mnu_11(self, event):
        skip_layout = None
        self._custom_btn_preprocess(11)
            
    def _on_custom_mnu_12(self, event):
        skip_layout = None
        self._custom_btn_preprocess(12)
            
    def _on_custom_mnu_13(self, event):
        skip_layout = None
        self._custom_btn_preprocess(13)
            
    def _on_custom_mnu_14(self, event):
        skip_layout = None
        self._custom_btn_preprocess(14)
            
    def _on_custom_mnu_15(self, event):
        skip_layout = None
        self._custom_btn_preprocess(15)
            
    def _on_custom_mnu_16(self, event):
        skip_layout = None
        self._custom_btn_preprocess(16)
            
    def _on_custom_mnu_17(self, event):
        skip_layout = None
        self._custom_btn_preprocess(17)
            
    def _on_custom_mnu_18(self, event):
        skip_layout = None
        self._custom_btn_preprocess(18)
            
    def _on_custom_mnu_19(self, event):
        skip_layout = None
        self._custom_btn_preprocess(19)
            
    def _on_custom_mnu_20(self, event):
        skip_layout = None
        self._custom_btn_preprocess(20)

            
    def _on_custom_timer(self, event):
        self._timer_init("pause")

        ctl_obj_id = event.GetEventObject().GetId()
        
        idx = -1
        for i in self._cust_timer_id.keys():
            if self._cust_timer_id[i] == ctl_obj_id:
                idx = i
                break 

        if idx >= 0:
            rtn_value = None
            exec "rtn_value = self._pclass.custom%s_timer_process(None, %s)" % (idx, self._cust["tparm"][i])
            if rtn_value:
                self._do_return_operation(rtn_value)

        self._timer_init("start")

                
    def _do_return_operation(self, req_operation):
        for kk, vv in req_operation.iteritems():
            if vv == "refresh":
                pnl, sep, idx = kk.rpartition(".")
                idx = int(idx)
                if pnl == "html":
                    if idx in self._pclass._html.keys():
                        init_html = self._pclass._html[idx]
                        self._html_page[idx].SetPage(init_html)
            elif vv == "layout":
                self._layout_main()
                    
    
    def _close(self):
        self._pclass.save_ctl()
        layout, size, spos = self._save_nb_layout()
        self._pclass.save_layout(layout, size, spos)
        
        print gc.garbage
        print gc.collect(), "unreachable objects"
        print gc.collect(), "unreachable objects"
        
        #self.Destroy()
        sys.exit()
    
    def _custom_btn_preprocess(self, idx):
        self._pclass.refresh_routine_data(idx)
        routine_data = getattr(self._pclass, "custom%s_routine_data" % (idx))
        rtn_val = self._custom_btn_process(idx, routine_data)

        exec "self._pclass.custom%s_btn_process(rtn_val)" % (idx)
        
        next_type, skip_layout = self._pclass.next_frame()

        if next_type == HTML:
            self._type = "html_pnl"
        elif next_type == PLOT:
            self._type = "plot_pnl"
        elif next_type == PARAMETER:
            self._type = "parameter_pnl"
    
        if not skip_layout:
            self.__do_layout()

        
    def _custom_btn_process(self, btn, routine_data):
        rtn_data = None
        
        if FILEOPEN in routine_data.keys():
            rtn_data = self._fileopen_dialog(routine_data)
            
        if DIROPEN in routine_data.keys():
            rtn_data = self._diropen_dialog(routine_data)
            
        if FILESAVE in routine_data.keys():
            if routine_data[FILESAVE] == True:
                self._custom_filesave(btn, routine_data)
        
        if START_TIMER in routine_data.keys():
            i = routine_data[START_TIMER]
            if i in self._cust_timer_id.keys():
                if not i in self._cust_timer.keys():
                    self._cust_timer[i] = wx.Timer(self, self._cust_timer_id[i])
                    self.Bind(wx.EVT_TIMER, self._on_custom_timer, self._cust_timer[i])
                tme = self._cust["ttime"][i]
                self._cust_timer[i].Start(tme)
                self._cust_timer_state[i] = "start"
        
        if STOP_TIMER in routine_data.keys():
            i = routine_data[STOP_TIMER]
            if i in self._cust_timer_id.keys():
                if i in self._cust_timer.keys():
                    self._cust_timer[i].Stop()
                    self._cust_timer_state[i] = ""
        
        
        if MODAL_WIN in routine_data.keys():
            rtn_data = self._modal_dialog(routine_data)


        if POST_BTN_MSG in routine_data.keys():
            self._infomsg_dialog(routine_data[POST_BTN_MSG])
            
        if POST_BTN_ERROR_MSG in routine_data.keys():
            self._errormsg_dialog(routine_data[POST_BTN_ERROR_MSG])

        if POST_BTN_MSG in routine_data.keys():
            del routine_data[POST_BTN_MSG]
        if POST_BTN_ERROR_MSG in routine_data.keys():
            del routine_data[POST_BTN_ERROR_MSG]
            
        return rtn_data
    
    def _start_auto_timers(self):
        for i in self._cust["tauto"].keys():
            if self._cust["tauto"][i]:
                if not i in self._cust_timer_id.keys():
                    self._cust_timer_id[i] = wx.NewId()
                    
                if not i in self._cust_timer.keys():
                    self._cust_timer[i] = wx.Timer(self, self._cust_timer_id[i])
                    self.Bind(wx.EVT_TIMER, self._on_custom_timer, self._cust_timer[i])
                    
                tme = self._cust["ttime"][i]
                self._cust_timer[i].Start(tme)
                self._cust_timer_state[i] = "start"


    def _custom_filesave(self, btn, class_routine_data):
        outfile = class_routine_data[OUTFILE]
        wildcard = class_routine_data[WILDCARD]
        
        rtn_outfile = self._filesave_dialog(outfile, wildcard)
        class_routine_data[RTN_OUTFILE] = rtn_outfile

        if rtn_outfile:
            class_routine_data[STEP] = 1
            if self._pclass.save_file(btn):
                self._infomsg_dialog(class_routine_data[INFO_MSG])

        if SKIPOUT_2 in class_routine_data.keys():
            if class_routine_data[SKIPOUT_2] == True:
                return
                
        if OUTFILE2 in class_routine_data.keys():
            outfile2 = class_routine_data[OUTFILE2]
            wildcard2 = class_routine_data[WILDCARD2]
            rtn_outfile2 = self._filesave_dialog(outfile2, wildcard2)
            class_routine_data[RTN_OUTFILE2] = rtn_outfile2
            
            if rtn_outfile2:
                class_routine_data[STEP] = 2
                if self._pclass.save_file(btn):
                    self._infomsg_dialog(class_routine_data[INFO_MSG])

    def _filesave_dialog(self, outfile, wildcard):
        rtn_outfile = None
        dlg = wx.FileDialog(self, "", "", outfile, wildcard = wildcard, style=wx.FD_SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dirname=dlg.GetDirectory()
            rtn_outfile = os.path.join(dirname, filename)
            
        #dlg.Destroy()
        
        return rtn_outfile


    def _fileopen_dialog(self, rtn_data):
        rtn_sourcefile = None

        if WILDCARD in rtn_data.keys():
            wildcard = rtn_data[WILDCARD]
        else:
            wildcard = "*.*"
            
        if OPEN_MSG in rtn_data.keys():
            dlg_message = rtn_data[OPEN_MSG]
        else:
            dlg_message = "Choose file"
            
        dlg = wx.FileDialog(self, dlg_message, wildcard = wildcard, style=wx.OPEN)
        if dlg.ShowModal():
            path = dlg.GetPath()
            if path:
                rtn_sourcefile = path

        dlg.Destroy()
        
        return rtn_sourcefile

    
    def _diropen_dialog(self, rtn_data):
        rtn_sourcefile = None

        if OPEN_MSG in rtn_data.keys():
            dlg_message = rtn_data[OPEN_MSG]
        else:
            dlg_message = "Choose Folder"
            
        dlg = wx.DirDialog(self, dlg_message, style=wx.OPEN)
        if START_PATH in rtn_data.keys():
            dlg.SetPath(rtn_data[START_PATH])
        if dlg.ShowModal():
            path = dlg.GetPath()
            if path:
                rtn_sourcefile = path

        dlg.Destroy()
        
        return rtn_sourcefile

    
    def _infomsg_dialog(self, msg):
        wx.MessageBox(msg, "Info", style = wx.ICON_INFORMATION)
        return
    
    def _errormsg_dialog(self, msg):
        wx.MessageBox(msg, "Error", style = wx.ICON_ERROR)
        return
    
    
    def _modal_dialog(self, routine_data):
        #print "modal 1"
        timer_paused = None
        if "pause_timer" in routine_data.keys():
            if routine_data["pause_timer"]:
                self._timer_init("pause")
                timer_paused = True
                
        #print "modal 2"
        self._pclass.pre_modal_process(routine_data)
        
        #print "modal 3"
        if "release_timer" in routine_data.keys():
            if routine_data["release_timer"]:
                if timer_paused:
                    self._timer_init("start")
                    timer_paused = None
                
        #print "modal 4", routine_data.keys()
        if "idx" in routine_data.keys():
            idx = routine_data["idx"]
            #print "modal 5"
            if idx in self._mod_controls_pnl.keys():
                dlg = self._mod_controls_pnl[idx]
                if "title" in routine_data.keys():
                    dlg.Title = routine_data["title"]
                else:
                    dlg.Title = ""
                dlg.Fit()
                dlg.CenterOnScreen()
                #print "modal 6"
                #print "dlg: ", dlg
                rtn = dlg.ShowModal()
                #print "modal 7"
                if rtn == wx.ID_OK:
                    print datetime.datetime.now(), "OK return from modal:", rtn
                else:
                    print datetime.datetime.now(), "else return from modal:", rtn

                self._pclass.post_modal_process(rtn, routine_data)

        if timer_paused:
            self._timer_init("start")
            
        return 
        
    def _process_parameters(self):
        self._type == "paramater_pnl"
        
        if self._pclass.show_progress_dialog:
            max = 100
            dlg = wx.ProgressDialog("%s" %(self._pclass.about_name), 
                                    "Processing the instructions...", 
                                    maximum=max, 
                                    parent=self,
                                    style= wx.PD_APP_MODAL|wx.PD_AUTO_HIDE
                                    )
        else:
            dlg = None

        #run the process_class main process
        self._pclass.process_ok(dlg)

        #get values from entry_controls, and pass to selection_dict
        #for name in self._pclass.control_names:
        nxt, skip_layout = self._pclass.next_frame()
        if nxt == HTML:
            self._html_page_tidx = {}
            for i in range(0, self._html_active):
                init_html = ""
                html_title = "default %s" %(i)

                try:
                    if i in self._pclass._html.keys():
                        init_html = self._pclass._html[i]
                except:
                    pass
                
                try:
                    if i in self._pclass._html_title.keys():
                        html_title = self._pclass._html_title[i]
                except:
                    pass
                
                if not self._html_page[i]:
                    self._html_page[i] = wx.html.HtmlWindow(self._notebook, -1)
                    self._notebook.AddPage(self._html_page[i], html_title)
                    self._html_page_tidx[i] = self._notebook.GetPageIndex(self._html_page[i])
                    self._notebook.SetCloseButton(self._html_page_tidx[i], False)
            
                self._html_page[i].SetPage(init_html)
                self._html_page[i].SetBackgroundColour(self.mainBackgroundColor)
            
            self._type = "html_pnl"

        elif nxt == PLOT:
            self._type = "plot_pnl"
            
        else:
            self._type == "paramater_pnl"
            
        if dlg:
            dlg.Destroy()
        
        if self.first_layout_done:
            self.first_layout_done = None

        self.__do_layout()
        
        return
    

if __name__ == '__main__':
    raise RuntimeError, "postprocessframe.py defines a class which cannot be run as a stand-alone process."
 