'''
chemcorrect.py -- The chemcorrect module contains the ChemcorrectModel class.
This class will call the instproc.InstructionProcess class to process the
provided instruction set. And then generate HTML and Plot pages from the 
InstructionProcess result set.
'''
import os
import datetime

from instproc import InstructionProcess

import xlwt

from postprocessdefn import *
from postdataprovider import PostDataProvider

from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.dates import date2num, YearLocator, MonthLocator, DateFormatter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import matplotlib.font_manager as font_manager

from scipy import stats
from numpy import *

from Utilities import AppInfo


class ChemcorrectModel(object):
    '''
    Chemcorrect Model Class
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''

        # eat ccver if it is in kwargs
        if  'ccver' in kwargs:
            del kwargs['ccver']

        # version and about info
        about = AppInfo()

        self.about_version = about.getAppVer()
        self.about_name = about.getAppName()
        self.about_copyright = about.getCopyright()
        self.about_description = about.getDescription()
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

        self._ptitle = "ChemCorrect(tm)"
        self._max_source_lines = 1000
        
        self._spreadsheet_formats = None

        self._source = None
        self._source_data = None
        self.list_of_columns = None
        
        self._init_process_parms()
        self._init_cntl_objs()

        self._line_source = None
        self.html_summary = ""
        self.html_detail = ""
        self.html_instructions = ""
        self.cc_plots = None
        self.fig = None

        self.plot_name = {
                          0: "XY Plot",
                          1: "Plot 2",
                          2: "Plot 3",
                          3: "Plot 4",
                          }

    
    def _init_process_parms(self):
        '''
        initialize process_parms
        '''
        self.display_precision_five = [
                                       "SAMP_ORGANIC_MEOH_AMP_MEAN", 
                                       "SAMP_ORGANIC_CH4CONC_MEAN", 
                                       "ORGANIC_BASE_DIFF",
                                       "ORGANIC_MEOH_AMPL"
                                       ]
        self.display_precision_four = [
                                       ]
        self.display_precision_three = [
                                        "percentage_to_end_d18O",
                                        "percentage_to_end_dD",
                                        "memory_correction_ratio",
                                        "memory_correction_delta",
                                        "memory_correction_diff",
                                        ]
        self.display_precision_int = [
                                      "sample",
                                      ]
        
        self.process_parms = {
                              "column_list": None,
                              "html_source": {},
                              "plot_fig": {
                                           0: None,
                                           1: None,
                                           2: None,
                                           },
                              "plot_data": {},
                              }



    def _init_cntl_objs(self):
        '''
        Initialize the control objects (define the controls for the panels)
        '''
        self.list_of_columns = []
        self.list_of_columns.append(CHOICE_NONE)
        
        self.list_yes_no = []
        self.list_yes_no.append("No")
        self.list_yes_no.append("Yes")

        self.list_of_marker_colors = MARKER_COLORS_DICT.keys()
        self.list_of_marker_points = MARKER_POINTS_DICT.keys()
        self.list_of_legend_locs = LEGEND_LOCATION_DICT.keys()
        
        txt_len = 80
        txt_len_long = 200
        txt_len_xlong = 400
        txt_len_med = 150
        txt_len_note = 1024
        cntl_len = 200
        tiny_len = 65

        parameter_cols = [
        (SOURCE_PARM, txt_len_xlong, "Source", TEXT_CNTL, None, "", True),
        (INSTRUCTION_PARM, txt_len_xlong, "Instruction Set", TEXT_CNTL, None, "", True),
        (STANDARDS_PARM, txt_len_xlong, "Standards File", TEXT_CNTL, None, "", True),
        (IGNOREINST_PARM, tiny_len, "Injections to ignore", TEXT_CNTL, None, "", True),

        ("cntl_spacer", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("graphx", txt_len_med, "X Axis Column", CHOICE_CNTL, self.list_of_columns, CHOICE_NONE, True),

        ("cntl_spacer1", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("graphy1", txt_len_med, "Y Axis Column 1", CHOICE_CNTL, self.list_of_columns, CHOICE_NONE, True),
        ("marker_c1", txt_len, "Color 1", CHOICE_CNTL, self.list_of_marker_colors, BLUE, True),

        ("cntl_spacer2", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("graphy2", txt_len_med, "Y Axis Column 2", CHOICE_CNTL, self.list_of_columns, CHOICE_NONE, True),
        ("marker_c2", txt_len, "Color 2", CHOICE_CNTL, self.list_of_marker_colors, RED, True),

        ("cntl_spacer3", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("graphy3", txt_len_med, "Y Axis Column 3", CHOICE_CNTL, self.list_of_columns, CHOICE_NONE, True),
        ("marker_c3", txt_len, "Color 3", CHOICE_CNTL, self.list_of_marker_colors, GREEN, True),

        ("cntl_spacer4", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("graphy4", txt_len_med, "Y Axis Column 4", CHOICE_CNTL, self.list_of_columns, CHOICE_NONE, True),
        ("marker_c4", txt_len, "Color 4", CHOICE_CNTL, self.list_of_marker_colors, CYAN, True),

        ("cntl_spacer5", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("marker_m", txt_len, "Marker", CHOICE_CNTL, self.list_of_marker_points, "point marker", True),
        ("legend_loc", txt_len, "Legend Location", CHOICE_CNTL, self.list_of_legend_locs, "best", True),
        ("combine_data", txt_len, "Combine and\nCorrelate?", CHOICE_CNTL, self.list_yes_no, "No", True),
        ]
        
        ord = 0
        for ploc, clist in [  
                          (PARAMETER, parameter_cols),
                          ]:

            ord = self._load_cols(ploc, clist, ord)


    def _load_cols(self, ploc, clist, ord):
        for val in clist:
            ord += 10
    
            if val[3] in (CHOICE_CNTL, RADIO_CNTL):
                vlist = val[4]
                vdft = val[5]
            else:
                vlist = None
                vdft = None
            
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
        
        
    def collist_from_source(self, source):
        self.list_of_columns = []
        self.list_of_columns.append(CHOICE_NONE)

        if source:
            if not source == self._source:
                self._setup_provider(source)
            
            if self._source_data:
                if self._source_data.column_names_list:
                    for name in self._source_data.column_names_list:
                        self.list_of_columns.append(name)

            if self._source:
                sbase = os.path.basename(self._source)
                stuff, sep, type = sbase.rpartition(".")
                
                self._source_type = type


        return self.list_of_columns
    
    
    def _setup_provider(self, source):
        
        try:
            self._source = source
            self._source_data = PostDataProvider(self._source, type=type)
        except:
            raise RuntimeError, INVALID_SOURCE_ERROR

               
    def after_config_init(self):
        '''
        any follow up configuration after controller initialization
        '''
        for name, cntlobj in self.cntls_obj.control_list.iteritems():
            setattr(self, "%s_cntlobj" % (name), cntlobj)

        return
           
    def process_source(self, brief_html = None):
        '''
        process the passed source file - for ChemCorrect(tm) we only need to open
        the source and get the column name list
        '''
#        if not source == self._source:
#            self._setup_provider(source)
        if self._source:
            self._init_process_parms()
        
            sbase = os.path.basename(self._source)
            stuff, sep, type = sbase.rpartition(".")
            
            self._source_type = type
            
            self.process_parms["column_list"] = self._source_data.column_names_list
            #self.process_parms["html_source"][0] = self._build_html(brief_html)
            self.process_parms["html_source"][0] = self._build_source_html()
            self.process_parms["html_source"][1] = self.html_summary
            self.process_parms["html_source"][2] = self.html_detail
            self.process_parms["html_source"][3] = self.html_instructions
            
            if self.cc_plots:
                for ci in self.cc_plots.keys():
                    pi = ci + 1

                    self.process_parms["plot_fig"][pi] = self.cc_plots[ci]
                    self.process_parms["plot_data"][pi] = None
                    
            
            self.process_parms[STATUS] = OK


    def generate_plot(self, notebook=None, pltidx=None):
        '''
        generate an XY plot 
          plot_parameters 
              "x": x_column_name,
              "y": y_column_name,
              "y2": y2_column_name,
              "y3": y3_column_name,
              "y4": y4_column_name,
              "marker": matplotlib_color_and_marker_string,
              "marker2": matplotlib_color_and_marker_string,
              "marker3": matplotlib_color_and_marker_string,
              "marker4": matplotlib_color_and_marker_string,
              "combine_data": yes/no,
              "export_data": True_or_None, #optional
        '''
        plot_parameters = self._get_data_from_controls()
        
        combine_data_flag = plot_parameters["combine_data"]
        legend_loc = plot_parameters["legend_loc"]
        graphx = plot_parameters['x']
        
        attempt_date_plot = None
        dt_col_is = None
        
        if self._source_type == "h5" and graphx == "DATE_TIME":
            attempt_date_plot = True
            dt_col_is = "timestamp"
        elif self._source_type == "csv" and graphx == "Time Code":
            attempt_date_plot = True
            dt_col_is = "str_time_code"

        self._x = graphx
        self._y = {}
        y_array = []
        mkeys = [
                 ("y", "marker"), 
                 ("y2", "marker2"), 
                 ("y3", "marker3"), 
                 ("y4", "marker4")
                 ]
        
        for ykey, mkey in mkeys: 
            if not plot_parameters[ykey] == CHOICE_NONE:
                y_array.append((
                                plot_parameters[ykey], 
                                plot_parameters[mkey]
                                ))
                self._y[ykey] = plot_parameters[ykey]

        if self.fig:
            self.fig.clf()
            
        self.fig=Figure(frameon=True,facecolor=PLOT_FACECOLOR)

        if graphx == CHOICE_NONE:
            self.process_parms["plot_fig"][0] = self.fig
            self.process_parms["plot_data"][0] = None
            self._set_notebook_page(notebook, pltidx)
            return

        if len(y_array) < 1:
            self.process_parms["plot_fig"][0] = self.fig
            self.process_parms["plot_data"][0] = None
            self._set_notebook_page(notebook, pltidx)
            return
            
        ncol = 0
        self._plt = {}
        self._plot = {}
        if combine_data_flag == "Yes":
            first_marker = True

            for graphy, marker in y_array:
                if first_marker:
                    self._plt[1] = self.fig.add_subplot(111)
                    first_plt = self._plt[1]
                
                lbl = "%s" % (graphy)

                xx=self._source_data.get_column_array(graphx)

                if attempt_date_plot:
                    try:
                        if len(xx)>0:
                            if dt_col_is == "timestamp":
                                dt = datetime.datetime.fromtimestamp(
                                                                     xx[0],
                                                                     tz=None
                                                                     )
                            else:
                                dt = datetime.datetime.strptime(
                                                    xx[0],
                                                    "%Y/%m/%d %H:%M:%S"
                                                                )
                            t0 = date2num(dt)
                            tbase = t0 + (xx-xx[0])/(24.0*3600.0)
                        else:
                            tbase = []
                        
                        xx = tbase
                    except:
                        attempt_date_plot = None
                
                yy=self._source_data.get_column_array(graphy)

                xarray = []
                for x_val in xx:
                    try:
                        xarray.append(float(x_val))
                    except:
                        xarray.append(0.0)

                yarray = []
                for y_val in yy:
                    try:
                        yarray.append(float(y_val))
                    except:
                        yarray.append(0.0)

                self._plot[1] = self._plt[1].plot(
                                                  xarray, 
                                                  yarray, 
                                                  marker,
                                                  label=lbl
                                                  )
                
                for tl in self._plt[1].get_xticklabels():
                    tl.set_visible(False)
                
                if first_marker:
                    self._plt[1].set_xlabel(graphx)
                    self._plt[1].set_ylabel(graphy)

                if first_marker:
                    first_marker = None
                        
                ncol += 1
                
            self._plt[1].legend(
                                loc=legend_loc, 
                                ncol=ncol, 
                                shadow=True, 
                                prop=font_manager.FontProperties(size=10)
                                )
            self._plt[1].grid(
                              True, 
                              linestyle='-', 
                              which='major', 
                              color='lightgrey', 
                              alpha=0.5
                              )

            if attempt_date_plot:
                self._plt[1].xaxis.set_major_formatter(
                                          DateFormatter(
                                                        '%H:%M:%S\n%Y/%m/%d', 
                                                        tz=None)
                                                        )

            
            for tl in self._plt[1].get_xticklabels():
                tl.set_visible(True)
                tl.set_rotation(30)

            last_plot_idx = 1
        else:
            first_plt = None
            first_plt_twin = None
            plot_cycle = 0
            last_plot_idx = 0
            num_plots = len(y_array)
            
            for graphy, marker in y_array:
                lbl = "%s" % (graphy)
                last_plot_idx = plot_cycle
                subplt = "%s1%s" %(num_plots, plot_cycle + 1)

                if not first_plt:
                    self._plt[plot_cycle] = self.fig.add_subplot(subplt)
                    first_plt = self._plt[plot_cycle]
                else:
                    self._plt[plot_cycle] = self.fig.add_subplot(subplt, 
                                                            sharex=first_plt, 
                                                            )

                xx=self._source_data.get_column_array(graphx)

                if attempt_date_plot:
                    try:
                        if len(xx)>0:
                            dt = datetime.datetime.fromtimestamp(xx[0],tz=None)
                            t0 = date2num(dt)
                            tbase = t0 + (xx-xx[0])/(24.0*3600.0)
                        else:
                            tbase = []
                        
                        xx = tbase
                    except:
                        attempt_date_plot = None
                
                yy=self._source_data.get_column_array(graphy)

                xarray = []
                for x_val in xx:
                    try:
                        xarray.append(float(x_val))
                    except:
                        xarray.append(0.0)

                yarray = []
                for y_val in yy:
                    try:
                        yarray.append(float(y_val))
                    except:
                        yarray.append(0.0)

                
                self._plot[plot_cycle] = self._plt[plot_cycle].plot(
                                                                    xarray, 
                                                                    yarray, 
                                                                    marker,
                                                                    label=lbl
                                                                    )

                
                for tl in self._plt[plot_cycle].get_xticklabels():
                    tl.set_visible(False)

                self._plt[plot_cycle].set_ylabel(graphy)

                self._plt[plot_cycle].grid(
                                           True, 
                                           linestyle='-', 
                                           which='major', 
                                           color='lightgrey', 
                                           alpha=0.5
                                           )

                plot_cycle += 1

            self._plt[plot_cycle-1].set_xlabel(graphx)
            if attempt_date_plot:
                self._plt[plot_cycle-1].xaxis.set_major_formatter(
                                          DateFormatter('%H:%M:%S\n%Y/%m/%d', 
                                                        tz=None)
                                                                  )

            for tl in self._plt[plot_cycle-1].get_xticklabels():
                tl.set_visible(True)
                tl.set_rotation(30)



        if first_plt:
            first_plt.set_autoscale_on(True)

            self.process_parms["plot_fig"][0] = self.fig
            self.process_parms["plot_data"][0] = None

        self._set_notebook_page(notebook, pltidx)
            
        self._plot_was_generated = True
        
        self._status = ""


    def _set_notebook_page(self, notebook=None, pltidx=None):
        if notebook:
            if pltidx:
                for cidx in pltidx.keys():
                    notebook.SetPageText(
                                         pltidx[cidx], 
                                         self.plot_name[cidx]
                                        )
                    #print "notebook page", cidx, self.plot_name[cidx]

    
    def _get_data_from_controls(self):
        sel_vals = {}
        for name, control in self.cntls_obj.control_list.iteritems():
            sel_vals[name] = control.get_value()
        
        exptfile = None
        
        marker_c1 = MARKER_COLORS_DICT[sel_vals["marker_c1"]]
        marker_c2 = MARKER_COLORS_DICT[sel_vals["marker_c2"]]
        marker_c3 = MARKER_COLORS_DICT[sel_vals["marker_c3"]]
        marker_c4 = MARKER_COLORS_DICT[sel_vals["marker_c4"]]
        marker_m = MARKER_POINTS_DICT[sel_vals["marker_m"]]
        marker1 = "%s%s" % (marker_c1, marker_m)
        marker2 = "%s%s" % (marker_c2, marker_m)
        marker3 = "%s%s" % (marker_c3, marker_m)
        marker4 = "%s%s" % (marker_c4, marker_m)

        export_data = None
            
        rtn_parms = {"x": sel_vals["graphx"], 
                     "y": sel_vals["graphy1"], 
                     "y2": sel_vals["graphy2"], 
                     "y3": sel_vals["graphy3"], 
                     "y4": sel_vals["graphy4"], 
                     "marker": marker1,
                     "marker2": marker2,
                     "marker3": marker3,
                     "marker4": marker4,
                     "combine_data": sel_vals["combine_data"],
                     "legend_loc": sel_vals["legend_loc"],
                     "export_data": export_data}
        
        return rtn_parms
                                

    def save_fig(self, savefile):
        '''
        save the plot figure into savefile (a pdf or png file)
        '''
        self.fig.savefig(savefile)
    
    def save_fig_batch(self, savefile):
        '''
        save the plot figure into savefile (a pdf or png file)
        '''
        canvas=FigureCanvas(self.fig)
        canvas.print_figure(savefile)
        
        
    def save_data(self, savefile):
        '''
        save the plot figure data into savefile (a txt)
        '''
        graphx = self._x
        xx=self._source_data.get_column_array(graphx)
        xarray = []
        for x_val in xx:
            try:
                xarray.append(float(x_val))
            except:
                xarray.append(0.0)

        f = open(savefile, "w")
        if f:
            str = "%s \n" %(savefile)
            str += " \n"

            for ykey in self._y.keys():
                graphy  = self._y[ykey]

                str += "%s by %s \n" %(graphx, graphy)
                str += " \n"
                str += "%s, %s \n" %(graphx, graphy)
                
                yy=self._source_data.get_column_array(graphy)
                yarray = []
                ii = 0
                for y_val in yy:
                    try:
                        yval = float(y_val)
                    except:
                        yval = 0.0
            
                    str += "%s, %s \n" %(xarray[ii], yval)
                    ii += 1
                    
                str += " \n"
                
            f.write(str)

        return


    def save_workbook(self, filename):
        self._wb.save(filename)
        return



    def do_instruction_set(self, dlg=None, notebook=None, plot_page_tidx=None):
        '''
        process the instruction, then build a set of html pages based on the 
        result set.
        '''
        if not self._spreadsheet_formats:
            self._define_spreadsheet_formats()
        
        self._dt=datetime.datetime.now()
        tm = "&trade;"
        tma = "(tm)"
        self._title = "ChemCorrect%s - %s" % (
                                              tm, 
                                              self._dt.strftime(
                                                    "%a, %b %d, %Y, %H:%M:%S"
                                                                )
                                              )
        self._title_spreadsheet = "ChemCorrect%s - %s" % (
                                                          tma, 
                                                          self._dt.strftime(
                                                    "%a, %b %d, %Y, %H:%M:%S"
                                                                            )
                                                          )
        self._title_filename = "ChemCorrect_%s" % (
                                             self._dt.strftime("%Y%m%d%H%M%S")
                                                   )

        self._initialize_workbook()

        self._inst_parms = {}
        for name, control in self.cntls_obj.control_list.iteritems():
            self._inst_parms[name] = control.get_value()


        self.InstProc = InstructionProcess(ccver=self.about_version)
        
        try:
            self.InstProc._load_definition_instructions(self._inst_parms)
        except:
            return 'Error: Cannot load instruction definitions.'
            
        try:
            self.InstProc._load_standards(self._inst_parms)
        except:
            return 'Error: Cannot load standards file.'
            
        try:
            self.InstProc._load_source(self._inst_parms)
        except:
            return 'Error: Cannot load the source. \nThe instruction set file, and/or source file may be corrupt.'
            
        try:
            self.InstProc._load_instructions(self._inst_parms)
        except:
            return 'Error: Cannot load instruction set.'
            
        try:
            self.InstProc._evaluate_instruction_variables(self._inst_parms)
        except:
            return 'Error: Cannot load instruction set (evaluate variables).'
            

        self.html_summary = self._build_summary_html()
        self.html_detail = self._build_detail_html()
        self.html_instructions = self._build_instruction_brief_html()
        self._build_resolved_inst_sheets()
        
        self.generate_cc_plot(
                              notebook,
                              plot_page_tidx
                              )
        
        return 'OK'

    def _build_source_html(self, dlg=None):
        #print "building source HTML"

        if dlg:
            prg = 20
            inst_count = (
                          self.InstProc._source_column_count 
                          * len(self.InstProc._source_dict.keys())
                          )
        
        self._append_spreadsheet_title(
                                       self._title_spreadsheet, 
                                       self._sheet_source, 
                                       len(self.InstProc._display_order)
                                       )
        
        line = "<HTML><BODY bgcolor='%s'>" % (MAIN_BACKGROUNDCOLOR)
        line += "<H2 align='center'>%s</H2>" % (self._title)
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                    '98%', 
                                                    PNL_TBL_BACKGROUNDCOLOR
                                                                )

        # show source and instruction files
        line += "<tr><td>"
        line += "<table border = '0'>"
        line += "<tr><td>Source:</td><td><b>%s</b></td></tr>" % (self._source)
        line += "</table>"
        line += "</td></tr>"

        line += "<tr><td align='center'>"
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                        '98%', 
                                                        PNL_TBL_BORDERCOLOR
                                                                )
        
        step = 0
        for row in self.InstProc._source_dict.keys():
            if row == 1:
                for c in range(0,self.InstProc._source_column_count):
                    line += "<th bgcolor='%s'><b>" % (PNL_TBL_HEADINGCOLOR)
                    line += self.InstProc._source_dict[row][c][VALUE]
                    line += "</b></th>"
                    
                    self._append_col_to_spreadsheet(
                                    self.InstProc._source_dict[row][c][VALUE], 
                                    self._sheet_source, self._heading_xf
                                                    )
                
                    step += 1
                    if dlg:
                        if step >= (inst_count/30):
                            step = 0
                            if dlg:
                                prg = prg + 1
                                if prg >= 50:
                                    prg = 50
                                dlg.Update(prg)

                self._new_row_for_spreadsheet(self._sheet_source)
            else:
                line += "<tr>"
                for c in range(0,self.InstProc._source_column_count):
                    line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)
                    line += self.InstProc._source_dict[row][c][VALUE]
                    line += "</td>"

                    self._append_col_to_spreadsheet(
                                    self.InstProc._source_dict[row][c][VALUE], 
                                    self._sheet_source
                                                    )
                
                    step += 1
                    if dlg:
                        if step >= (inst_count/30):
                            step = 0
                            if dlg:
                                prg = prg + 1
                                if prg >= 50:
                                    prg = 50
                                dlg.Update(prg)

                line += "</tr>"
                self._new_row_for_spreadsheet(self._sheet_source)

        
        line += "</table>"
        line += "</td></tr>"
        line += "<tr><td><p></td><tr/>"
        line += "</table>"

        line += "<table><tr><td align='right'>%s</td></tr></table>" % (
                                                               HTML_COPYRIGHT
                                                                       )
        line += "</BODY></HTML>"
        
        return line
        #self._html_source = line

    def _build_summary_html(self):
        #print "building summary HTML"

        self._append_spreadsheet_title(
                                       self._title_spreadsheet, 
                                       self._sheet_summary, 
                                       len(self.InstProc._display_order)
                                       )
        
        line = "<HTML><BODY bgcolor='%s'><H2 align='center'>%s</H2>" % (
                                                        MAIN_BACKGROUNDCOLOR, 
                                                        self._title
                                                                        )
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                        '98%', 
                                                        PNL_TBL_BACKGROUNDCOLOR
                                                                )

        # show source and instruction files
        line += "<tr><td>"
        line += "<table border = '0'>"
        line += "<tr><td>Source:<br>Instructions<br>Standards</td>"
        line += "<td><b>%s<br>%s<br>%s</b></td></tr>" % (
                                           self._inst_parms[SOURCE_PARM], 
                                           self._inst_parms[INSTRUCTION_PARM],
                                           self._inst_parms[STANDARDS_PARM]
                                                   )
        line += "</table>"
        line += "</td></tr>"

        # show column headings
        line += "<tr><td align='center'>"
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                            '98%', 
                                                            PNL_TBL_BORDERCOLOR
                                                                )
        
        line += self._sample_header_html(self._sheet_summary)

        # show detail rows
        for smpl in self.InstProc._samples_name_dict.keys():
            line += self._sample_detail_html(smpl, self._sheet_summary)
            
        line += "</table>"
        line += "</td></tr>"
        line += "<tr><td><p></td><tr/>"

        # show the legend
        line += self._build_legend_html()
        
        line += "</table>"
        line += "<table><tr><td align='right'>%s</td></tr></table>" % (
                                                               HTML_COPYRIGHT
                                                                       )
        line += "</BODY></HTML>"

        return line

    def _build_detail_html(self):
        #print "building Detail HTML"

        self._append_spreadsheet_title(
                                       self._title_spreadsheet, 
                                       self._sheet_detail, 
                                       len(self.InstProc._display_order)
                                       )
        
        
        line = "<HTML><BODY bgcolor='%s'><H2 align='center'>%s</H2>" % (
                                                        MAIN_BACKGROUNDCOLOR, 
                                                        self._title
                                                                        )
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                        '98%', 
                                                        PNL_TBL_BACKGROUNDCOLOR
                                                                )


        # show source and instruction files
        line += "<tr><td>"
        line += "<table border = '0'>"
        line += "<tr><td>Source:<br>Instructions<br>Standards</td>"
        line += "<td><b>%s<br>%s<br>%s</b></td></tr>" % (
                                           self._inst_parms[SOURCE_PARM], 
                                           self._inst_parms[INSTRUCTION_PARM],
                                           self._inst_parms[STANDARDS_PARM]
                                                   )
        line += "</table>"
        line += "</td></tr>"

        # show column headings
        line += "<tr><td align='center'>"
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                            '98%', 
                                                            PNL_TBL_BORDERCOLOR
                                                                )
        line += self._detail_header_html(self._sheet_detail)
        

        # show detail rows
        self._row_in_sample = 0
        self._last_smpl = None
        for dtl in self.InstProc._details_name_dict.keys():
            line += self._detail_detail_html(dtl)
            
        # show last summary row
        line += self._detail_summary_html(self._last_smpl)

        line += "</table>"
        line += "</td></tr>"
        line += "<tr><td><p></td><tr/>"

        # show the legend
        line += self._build_legend_html()

        
        line += "</table>"
        line += "<table><tr><td align='right'>%s</td></tr></table>" % (
                                                               HTML_COPYRIGHT
                                                                       )
        line += "</BODY></HTML>"

        return line
    

    def _sample_header_html(self, sheet=None):
        if sheet:
            self._new_row_for_spreadsheet(sheet)
            
        line = ""
        data_hdr_done = None
        for ord in self.InstProc._display_order:
            #print "self._display_inst", self._display_inst
            tip_frag = ""
            #if self._display_inst[ord][7]:
            #    tip_frag = "title='%s'" %(self._display_inst[ord][7])
            line += "<th bgcolor='%s' %s><b>" % (
                                                 PNL_TBL_HEADINGCOLOR, 
                                                 tip_frag
                                                 )
            line += self.InstProc._display_inst[ord][2]
            line += "</b></th>"
            
            if sheet:
                if not data_hdr_done:
                    data_hdr_done = True
                    data_except_hdr = "Data\nError"
                else:
                    data_except_hdr = None
                    
                self._append_col_to_spreadsheet(
                                        self.InstProc._display_inst[ord][2], 
                                        sheet, 
                                        self._heading_xf,
                                        None,
                                        data_except_hdr
                                                )
                
        return line

    def _sample_detail_html(self, smpl, sheet=None):
        if sheet:
            self._new_row_for_spreadsheet(sheet)

        line = ""
        first_column = True
        line += "<tr>"
        for ord in self.InstProc._display_order:
            row_exception = None
            show_data, color_frag, color_name = self._determine_html_attributes(
                                    self.InstProc._display_inst[ord], 
                                    self.InstProc._instruction_proc_vars, 
                                    self.InstProc._instruction_samp_vars[smpl]
                                                                               )

            if color_name in (PNL_REDCOLOR, PNL_YELLOWCOLOR):
                self.InstProc._preserve_spectra(smpl)
            
            if first_column:
                color_frag = "bgcolor='%s'" %(PNL_TBL_HEADINGCOLOR)
            if show_data:
                if self.InstProc._display_inst[ord][0] == SAMPLE:
                    inst_var = SAMPLE
                    #val = str(smpl)
                    val = self.InstProc._sample_display_id(smpl)
                elif self.InstProc._display_inst[ord][0] == IDENTIFIER:
                    inst_var = IDENTIFIER
                    val = self.InstProc._instruction_samp_vars[smpl][IDENTIFIER]
                else:
                    inst_var = self.InstProc._display_inst[ord][0].strip()
                    val = self.InstProc._instruction_samp_vars[smpl][inst_var][VALUE]
                    if "except" in self.InstProc._instruction_samp_vars[smpl][inst_var].keys():
                        #print "there is an exception"
                        row_exception = "*"
                
                align_frag = ""

                try:
                    pval = float(val)
                    type = FLOAT
                except:
                    try:
                        pval = int(val)
                        type = INT
                    except:
                        pval = val
                        type = "text"
                
                line += self._html_td_col(
                                          first_column, 
                                          color_frag, 
                                          type, 
                                          inst_var, 
                                          pval, 
                                          row_exception
                                          )
                    
                if sheet:
                    fmt = self._resolve_spreadsheet_fmt(
                                                        first_column, 
                                                        color_name, 
                                                        type, 
                                                        inst_var
                                                        )
                    self._append_col_to_spreadsheet(
                                                    pval, 
                                                    sheet, 
                                                    fmt, 
                                                    None, 
                                                    row_exception
                                                    )

            else:
                #color_frag = "bgcolor='%s'" %(PNL_TBL_BACKGROUNDCOLOR)
                line += "<td %s></td>" %(color_frag)
            
                if sheet:
                    self._append_col_to_spreadsheet("", sheet)

            first_column = None

        line += "</tr>"
        return line


    def _detail_header_html(self, sheet=None):
        line = ""
        for ord in self.InstProc._detail_order:
            #print "self._detail_inst", self._detail_inst
            line += "<th bgcolor='%s'><b>" %(PNL_TBL_HEADINGCOLOR)
            line += self.InstProc._detail_inst[ord][2]
            line += "</b></th>"
            
            if sheet:
                self._append_col_to_spreadsheet(self.InstProc._detail_inst[ord][2], sheet, self._heading_xf)
                
        return line

    
    def _detail_spreadsheet_blank_row(self, sheet=None):
        for ord in self.InstProc._detail_order:
            if sheet:
                self._append_col_to_spreadsheet(self.InstProc._detail_inst[ord][2], sheet, self._heading_xf)
                
    
    def _detail_summary_html(self, smpl):
        line = ""
        line += "</table>"
        line += "</td></tr>"
        line += "<tr><td><p></td><tr/>"
        line += "<tr><td align='center'><b>Sample %s Summary</b></td></tr>" %(smpl)
        line += "<tr><td align='center'>"
        line += "<table width='%s' border='0' bgcolor='%s'>" %('98%', PNL_TBL_BORDERCOLOR)
        
        #self._new_row_for_spreadsheet(self._sheet_detail)
        self._append_merged_cols_to_spreadsheet("", self._sheet_detail, len(self.InstProc._display_order))
        self._new_row_for_spreadsheet(self._sheet_detail)
        self._append_merged_cols_to_spreadsheet("Sample %s Summary" %(smpl), self._sheet_detail, len(self.InstProc._display_order), self._heading_xf)
        
        line += self._sample_header_html(self._sheet_detail)
        line += self._sample_detail_html(smpl, self._sheet_detail)

        self._new_row_for_spreadsheet(self._sheet_detail)
        self._append_merged_cols_to_spreadsheet("", self._sheet_detail, len(self.InstProc._display_order))
        self._new_row_for_spreadsheet(self._sheet_detail)
        self._append_merged_cols_to_spreadsheet("", self._sheet_detail, len(self.InstProc._display_order))
        self._new_row_for_spreadsheet(self._sheet_detail)

        return line
    
    def _detail_detail_html(self, dtl, sheet=None):
        if not sheet:
            sheet = self._sheet_detail
            
        if sheet:
            self._new_row_for_spreadsheet(sheet)

        line = ""
        first_column = True
        line += "<tr>"
        for ord in self.InstProc._detail_order:
            row_exception = None
            row = int(dtl) + 1
            data = self.InstProc._source_dict[row]
            smpl = self.InstProc._sample_serial_id(
                               data[self.InstProc._sample_col][VALUE].strip(), 
                               data[self.InstProc._job_col][VALUE].strip()
                                                   )
            ident = self.InstProc._instruction_samp_vars[smpl][IDENTIFIER]
            
            # default to background color
            color_frag = "bgcolor='%s'" % (PNL_TBL_BACKGROUNDCOLOR)
            color_name = None

            if not self._last_smpl:
                self._last_smpl = smpl
            
            # if new sample, print the last sample summary, and new heading for new sample    
            if not smpl == self._last_smpl:
                self._new_row_for_spreadsheet(sheet)
                #self._detail_spreadsheet_blank_row(sheet)
                
                line += self._detail_summary_html(self._last_smpl)
                #self._new_row_for_spreadsheet(sheet)
                #self._new_row_for_spreadsheet(sheet)
                
                self._row_in_sample = 0
                self._last_smpl = smpl

                line += "</table>"
                line += "</td></tr>"
                line += "<tr><td><p></td><tr/>"
                line += "<tr><td align='center'>"
                line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                        '98%', 
                                                        PNL_TBL_BORDERCOLOR
                                                                        )            
                line += self._detail_header_html(sheet)   
                
                self._new_row_for_spreadsheet(sheet)

                line += "<tr>"


            if self.InstProc._detail_inst[ord][0] in (SAMPLE, IDENTIFIER):
                show_data = True
            elif "col(" in self.InstProc._detail_inst[ord][0]:
                show_data = True
            else:
                #print "detail_inst[ord]: ", self._detail_inst[ord]
                show_data, color_frag, color_name = self._determine_html_attributes(self.InstProc._detail_inst[ord], self.InstProc._instruction_proc_vars, self.InstProc._instruction_samp_vars[smpl], self.InstProc._instruction_dtl_vars[dtl])

            # override colors for first column
            if first_column:
                color_frag = "bgcolor='%s'" % (PNL_TBL_HEADINGCOLOR)
                color_name = None
            else:
                try:
                    igninst = int(self._inst_parms[IGNOREINST_PARM])
                except:
                    igninst = 0
                    self._inst_parms[IGNOREINST_PARM] = 0
                    
                if self._row_in_sample < igninst:
                    color_frag = "bgcolor='%s'" % (PLOT_SHADE_COLOR) #(PNL_SHADECOLOR)
                    color_name = IGNORE
            

            if show_data:
                if self.InstProc._detail_inst[ord][0] == SAMPLE:
                    inst_var = SAMPLE
                    #val = str(smpl)
                    val = self.InstProc._sample_display_id(smpl)
                elif self.InstProc._detail_inst[ord][0] == IDENTIFIER:
                    inst_var = IDENTIFIER
                    val = ident
                elif "col(" in self.InstProc._detail_inst[ord][0]:
                    inst, sep, pre_value = self.InstProc._detail_inst[ord][0].partition("(")
                    col_id, sep, right = pre_value.rpartition(")")
                    col_nbr = self.InstProc._label_column_dict[col_id]
                    inst_var = col_id
                    val = data[col_nbr][VALUE].strip()
                else:
                    inst_var = self.InstProc._detail_inst[ord][0].strip()
                    val = self.InstProc._instruction_dtl_vars[dtl][inst_var][VALUE]
                    if "except" in self.InstProc._instruction_dtl_vars[dtl][inst_var].keys():
                        #"should be showing an exception"
                        row_exception = "*"


                align_frag = ""

                try:
                    pval = float(val)
                    type = FLOAT
                except:
                    try:
                        pval = int(val)
                        type = INT
                    except:
                        is_a_string = True
                        pval = val
                        type = "text"
                
                line += self._html_td_col(first_column, color_frag, type, inst_var, pval, row_exception)
                    
                if sheet:
                    fmt = self._resolve_spreadsheet_fmt(first_column, color_name, type, inst_var)
                    self._append_col_to_spreadsheet(pval, sheet, fmt)
                        
            else:
                #color_frag = "bgcolor='%s'" %(PNL_TBL_BACKGROUNDCOLOR)
                line += "<td %s></td>" %(color_frag)
            
            first_column = None

        line += "</tr>"
        self._row_in_sample += 1
        return line
    
    def _build_instruction_brief_html(self, dlg=None):
        #print "building brief instructions HTML"

        if dlg:
            prg = 50
            inst_count = len(self.InstProc._inst_dict.keys()) / 10
        
        self._append_spreadsheet_title(self._title_spreadsheet, self._sheet_instructions, len(self.InstProc._display_order))
        
        line = "<HTML><BODY bgcolor='%s'><H2 align='center'>%s</H2>" %(MAIN_BACKGROUNDCOLOR, self._title)
        line += "<table width='%s' border='0' bgcolor='%s'>" %('98%', PNL_TBL_BACKGROUNDCOLOR)

        # show source and instruction files
        line += "<tr><td>"
        line += "<table border = '0'>"
        line += "<tr><td>Source:<br>Instructions<br>Standards</td>"
        line += "<td><b>%s<br>%s<br>%s</b></td></tr>" % (
                                           self._inst_parms[SOURCE_PARM], 
                                           self._inst_parms[INSTRUCTION_PARM],
                                           self._inst_parms[STANDARDS_PARM]
                                                   )
        line += "</table>"
        line += "</td></tr>"

        line += "<tr>"
        line += "<td align='center'>"
        line += "<table width='%s' border='0' bgcolor='%s'>" %('98%', PNL_TBL_BORDERCOLOR)
        
        for row in self.InstProc._inst_dict.keys():
            if len(self.InstProc._inst_dict[row]) < 1:
                continue
            
            if self.InstProc._inst_dict[row][0].strip() == COMMENTS_TYPE:
                break
            
            if self.InstProc._inst_dict[row][0].strip() in self.InstProc._valid_instruction_types:
                line += "<tr>"
                line += "<td bgcolor='%s' colspan='2'>" %(PNL_TBL_BORDERCOLOR)
                line += self.InstProc._inst_dict[row][0].strip()
                line += "</td>"
                line += "</tr>"

                if self.InstProc._inst_dict[row][0].strip() in (DISPLAY_SUMMARY_TYPE, DISPLAY_DETAIL_TYPE, PLOT_TYPE):
                    line += "<tr>"
                    for lbl in ("Variable", "Instruction", "Print?", "Label", "Red?", "Yellow?", "Green?", "Cyan?", "Comment"):
                        line += "<td bgcolor='%s'><b>" %(PNL_TBL_HEADINGCOLOR)
                        line += lbl
                        line += "</b></td>"
                        
                        self._append_col_to_spreadsheet(lbl, self._sheet_instructions, self._heading_xf)

                    line += "</tr>"
                    self._new_row_for_spreadsheet(self._sheet_instructions)
                else:
                    line += "<tr>"
                    for lbl in ("Variable", "Instruction", "Comment"):
                        spanfrag = ""
                        wdth = None
                        if lbl == "Variable":
                            wdth = 0x0d00 + 8000
                            spanfrag = ""
                        elif lbl == "Instruction":
                            wdth = 0x0d00 + 20000
                            spanfrag = ""
                        elif lbl == "Comment":
                            wdth = None
                            span = self.InstProc._inst_column_count - 2
                            spanfrag = "colspan='%s'" %(span)
                        line += "<td bgcolor='%s' %s><b>" %(PNL_TBL_HEADINGCOLOR, spanfrag)
                        line += lbl
                        line += "</b></td>"
                        
                        self._append_col_to_spreadsheet(lbl, self._sheet_instructions, self._heading_xf, wdth)

                    line += "</tr>"
                    self._new_row_for_spreadsheet(self._sheet_instructions)
                
            else:
                if self.InstProc._inst_dict[row][0]:
                    line += "<tr>"
                    for c in range(0,len(self.InstProc._inst_dict[row])):
                        line += "<td bgcolor='%s'>" %(PNL_TBL_BACKGROUNDCOLOR)
                        line += self.InstProc._inst_dict[row][c].strip()
                        line += "</td>"
                        self._append_col_to_spreadsheet(self.InstProc._inst_dict[row][c].strip(), self._sheet_instructions)
                    line += "</tr>"
                    self._new_row_for_spreadsheet(self._sheet_instructions)

            if dlg:
                prg = prg + (len(self.InstProc._inst_dict.keys())/10)
                if prg >= 60:
                    prg = 60
                dlg.Update(prg)
        
        
        line += "</table>"
        line += "</td>"
        line += "</tr>"
        
        #line += "<tr><td><p></td><tr/>"
        line += "</table>"

        line += "<table><tr><td align='right'>%s</td></tr></table>" % (
                                                               HTML_COPYRIGHT
                                                                       )
        line += "</BODY></HTML>"
        
        return line
        #self._html_inst = line

    def _build_resolved_inst_sheets(self, dlg=None):
        #print "building resolved instructions spreadsheet"
        
        if dlg:
            prg = 60
            inst_count = (len(self.InstProc._process_inst_var_order) + 
                         (len(self.InstProc._samples_name_dict.keys()) * len(self.InstProc._sample_inst_var_order)) +  
                         (len(self.InstProc._details_name_dict.keys()) * len(self.InstProc._detail_inst_var_order))
                         )
        
        curr_sheet = "Process Vars"
        self._sheet[curr_sheet] = self._wb.add_sheet(curr_sheet)     
        self._sheet_last_col[curr_sheet] = 0
        self._sheet_last_row[curr_sheet] = 0
        self._append_spreadsheet_title(self._title_spreadsheet, curr_sheet, len(self.InstProc._display_order))
        
        lbl = "Process Variables"
        self._append_col_to_spreadsheet(lbl, curr_sheet, self._heading_xf)
        self._new_row_for_spreadsheet(curr_sheet)
        
        self._append_col_to_spreadsheet("Variable", curr_sheet, self._heading_xf)
        self._append_col_to_spreadsheet("Value", curr_sheet, self._heading_xf)
        self._append_col_to_spreadsheet("Operations", curr_sheet, self._heading_xf)
        self._new_row_for_spreadsheet(curr_sheet)
        for inst_var in self.InstProc._process_inst_var_order:
            lbl1 = "%s" %(inst_var)
            lbl2 = "%s" %(self.InstProc._instruction_proc_vars[inst_var][VALUE])
            self._append_col_to_spreadsheet(lbl1, curr_sheet, self._text_fmt_left)
            self._append_col_to_spreadsheet(lbl2, curr_sheet, self._text_fmt_left)
            self._new_row_for_spreadsheet(curr_sheet)

            for k in self.InstProc._instruction_proc_vars[inst_var].keys():
                if not k == VALUE:
                    val = str(self.InstProc._instruction_proc_vars[inst_var][k])
                    lbl1 = ""
                    lbl2 = "%s: %s" %(k, val)
                    self._append_col_to_spreadsheet(lbl1, curr_sheet, self._text_fmt_left, 0x0d00 + 8000)
                    self._append_col_to_spreadsheet("", curr_sheet, self._text_fmt_left, 0x0d00 + 2000)
                    self._append_col_to_spreadsheet(lbl2, curr_sheet, self._text_fmt_left, 0x0d00 + 20000)
                    self._new_row_for_spreadsheet(curr_sheet)
            
        if dlg:
            prg = prg + (len(self.InstProc._process_inst_var_order)/inst_count/40)
            if prg >= 65:
                prg = 65
            dlg.Update(prg)
            
        self._new_row_for_spreadsheet(curr_sheet)

        for smpl in self.InstProc._samples_name_dict.keys():
            self._smpl_worksheet_cnt += 1
            curr_sheet = "%s - Sample %s Vars" %(self._smpl_worksheet_cnt, smpl)
            self._sheet[curr_sheet] = self._wb.add_sheet(curr_sheet)     
            self._sheet_last_col[curr_sheet] = 0
            self._sheet_last_row[curr_sheet] = 0
            self._append_spreadsheet_title(self._title_spreadsheet, curr_sheet, len(self.InstProc._display_order))

            lbl = "Sample Variables"
            self._append_col_to_spreadsheet(lbl, curr_sheet, self._heading_xf)
            self._new_row_for_spreadsheet(curr_sheet)
            
            lbl = "Sample %s" %(smpl)
            self._append_col_to_spreadsheet(lbl, curr_sheet, self._heading_xf)
            self._new_row_for_spreadsheet(curr_sheet)
            
            self._append_col_to_spreadsheet("Variable", curr_sheet, self._heading_xf)
            self._append_col_to_spreadsheet("Value", curr_sheet, self._heading_xf)
            self._append_col_to_spreadsheet("Operations", curr_sheet, self._heading_xf)
            self._new_row_for_spreadsheet(curr_sheet)

            for inst_var in self.InstProc._sample_inst_var_order:
                lbl1 = "%s" %(inst_var)
                lbl2 = "%s" %(self.InstProc._instruction_samp_vars[smpl][inst_var][VALUE])
                self._append_col_to_spreadsheet(lbl1, curr_sheet, self._text_fmt_left)
                self._append_col_to_spreadsheet(lbl2, curr_sheet, self._text_fmt_left)
                self._new_row_for_spreadsheet(curr_sheet)
                for k in self.InstProc._instruction_samp_vars[smpl][inst_var].keys():
                    if not k == VALUE:
                        val = str(self.InstProc._instruction_samp_vars[smpl][inst_var][k])
                        lbl1 = ""
                        lbl2 = "%s: %s" %(k, val)
                        self._append_col_to_spreadsheet(lbl1, curr_sheet, self._text_fmt_left, 0x0d00 + 8000)
                        self._append_col_to_spreadsheet("", curr_sheet, self._text_fmt_left, 0x0d00 + 2000)
                        self._append_col_to_spreadsheet(lbl2, curr_sheet, self._text_fmt_left, 0x0d00 + 20000)
                        self._new_row_for_spreadsheet(curr_sheet)

            if dlg:
                prg = prg + ( len(self.InstProc._sample_inst_var_order) /40  )
                if prg >= 75:
                    prg = 75
                dlg.Update(prg)
            


        self._new_row_for_spreadsheet(curr_sheet)

        last_smpl = None
        for dtl in self.InstProc._details_name_dict.keys():
            row = int(dtl) + 1
            data = self.InstProc._source_dict[row]
            smpl = self.InstProc._sample_serial_id(data[self.InstProc._sample_col][VALUE].strip(), data[self.InstProc._job_col][VALUE].strip())
            ident = data[self.InstProc._identifier_col][VALUE].strip()

            if not smpl == last_smpl:
                last_smpl = smpl
                self._dtl_worksheet_cnt += 1
                curr_sheet = "%s - Sample %s Detail Vars" %(self._dtl_worksheet_cnt, smpl)
                self._sheet[curr_sheet] = self._wb.add_sheet(curr_sheet)     
                self._sheet_last_col[curr_sheet] = 0
                self._sheet_last_row[curr_sheet] = 0
                self._append_spreadsheet_title(self._title_spreadsheet, curr_sheet, len(self.InstProc._display_order))
    
                lbl = "Detail Variables"
                self._append_col_to_spreadsheet(lbl, curr_sheet, self._heading_xf)
                self._new_row_for_spreadsheet(curr_sheet)

            
            dtl_name = self.InstProc._details_name_dict[dtl][NAME]
            lbl = "Detail %s" %(dtl_name)
            self._append_col_to_spreadsheet(lbl, curr_sheet, self._heading_xf)
            self._new_row_for_spreadsheet(curr_sheet)
            
            self._append_col_to_spreadsheet("Variable", curr_sheet, self._heading_xf)
            self._append_col_to_spreadsheet("Value", curr_sheet, self._heading_xf)
            self._append_col_to_spreadsheet("Operations", curr_sheet, self._heading_xf)
            self._new_row_for_spreadsheet(curr_sheet)
            
            for inst_var in self.InstProc._detail_inst_var_order:
                lbl1 = "%s" %(inst_var)
                lbl2 = "%s" %(self.InstProc._instruction_dtl_vars[dtl][inst_var][VALUE])
                self._append_col_to_spreadsheet(lbl1, curr_sheet, self._text_fmt_left)
                self._append_col_to_spreadsheet(lbl2, curr_sheet, self._text_fmt_left)
                self._new_row_for_spreadsheet(curr_sheet)
                for k in self.InstProc._instruction_dtl_vars[dtl][inst_var].keys():
                    if not k == VALUE:
                        val = str(self.InstProc._instruction_dtl_vars[dtl][inst_var][k])
                        lbl1 = ""
                        lbl2 = "%s: %s" %(k, val)
                        self._append_col_to_spreadsheet(lbl1, curr_sheet, self._text_fmt_left, 0x0d00 + 8000)
                        self._append_col_to_spreadsheet("", curr_sheet, self._text_fmt_left, 0x0d00 + 2000)
                        self._append_col_to_spreadsheet(lbl2, curr_sheet, self._text_fmt_left, 0x0d00 + 20000)
                        self._new_row_for_spreadsheet(curr_sheet)

                if dlg:
                    prg = prg + ( len(self.InstProc._details_name_dict.keys()) /40  )
                    if prg >= 99:
                        prg = 99
                    dlg.Update(prg)


        self._html_inst_full = ""

        
    def _build_legend_html(self):
        # show source and instruction files
        line = ""
        line += "<tr><td>"
        line += "<table border = '0'>"
        line += "<tr><td><b>Legend</b></td></tr>"
        line += "<tr><td><br><b>* (asterisk)</b> The detail information generating this value has exceptions.</td></tr>" 
        
        line += "<tr><td bgcolor='%s'><br><b>(grey)</b> Ignore this Injection Detail row.</td></tr>"  % (PLOT_SHADE_COLOR)
        line += "<tr><td bgcolor='%s'><br><b>(cyan)</b> The supplied isotopic standard.</td></tr>"  % (PNL_CYANCOLOR)
        line += "<tr><td bgcolor='%s'><br><b>(green)</b> Unknown sample, no contamination, GOOD.</td></tr>"  % (PNL_GREENCOLOR)
        line += "<tr><td bgcolor='%s'><br><b>(yellow)</b> Unknown sample, trace contamination, PROBABLY GOOD.</td></tr>"  % (PNL_YELLOWCOLOR)
        line += "<tr><td bgcolor='%s'><br><b>(red)</b> Unknown sample, heavy contamination, NOT RELIABLE.</td></tr>"  % (PNL_REDCOLOR)    
        
        line += "</table>"
        line += "</td></tr>"
        return line
    

    def _html_td_col(self, first_column, color_frag, type, inst_var, val, excpt=None):
        line = ""
        align_frag = ""
        excpt_frag = ""
        if excpt:
            #print "should be showing * after:", val
            excpt_frag = "<b>*</b>"
        if type == FLOAT:
            align_frag = "align='right'"
            if inst_var in self.display_precision_five:
                line += "<td %s %s>%3.5f %s</td>" %(color_frag, align_frag, val, excpt_frag)
            elif inst_var in self.display_precision_four:
                line += "<td %s %s>%3.4f %s</td>" %(color_frag, align_frag, val, excpt_frag)
            elif inst_var in self.display_precision_three:
                line += "<td %s %s>%3.3f %s</td>" %(color_frag, align_frag, val, excpt_frag)
            elif inst_var in self.display_precision_int:
                line += "<td %s %s>%3.0f %s</td>" %(color_frag, align_frag, val, excpt_frag)
            else:
                line += "<td %s %s>%3.2f %s</td>" %(color_frag, align_frag, val, excpt_frag)

        elif type == INT:
            align_frag = "align='right'"
            line += "<td %s %s>%s %s</td>" %(color_frag, align_frag, val, excpt_frag)
            
        else:
            line += "<td %s %s>%s %s</td>" %(color_frag, align_frag, val, excpt_frag)
        
        return line

    
    def _html_escape(self, text):
        """Produce entities within text."""
        return "".join(self._html_escape_table.get(c,c) for c in text)


    def _determine_html_attributes(self, 
                                   display_inst, 
                                   instruction_proc_vars, 
                                   instruction_samp_vars, 
                                   instruction_dtl_vars=None):
        #print display_inst
        show_data = None
        red_flag = None
        yellow_flag = None
        green_flag = None
        cyan_flag = None
        color_name = None
        
        if len(display_inst) >= 2 and display_inst[1]:
            show_data = self.InstProc._resolve_factor(
                                                      display_inst[1].strip(), 
                                                      instruction_proc_vars, 
                                                      instruction_samp_vars, 
                                                      instruction_dtl_vars
                                                      )
            
        if len(display_inst) >= 4 and display_inst[3]:
            red_flag = self.InstProc._resolve_factor(
                                                     display_inst[3].strip(), 
                                                     instruction_proc_vars, 
                                                     instruction_samp_vars, 
                                                     instruction_dtl_vars
                                                     )
            
        if len(display_inst) >= 5 and display_inst[4]:
            yellow_flag = self.InstProc._resolve_factor(
                                                        display_inst[4].strip(), 
                                                        instruction_proc_vars, 
                                                        instruction_samp_vars, 
                                                        instruction_dtl_vars
                                                        )
            
        if len(display_inst) >= 6 and display_inst[5]:
            green_flag = self.InstProc._resolve_factor(
                                                       display_inst[5].strip(), 
                                                       instruction_proc_vars, 
                                                       instruction_samp_vars, 
                                                       instruction_dtl_vars
                                                       )
            
        if len(display_inst) >= 7 and display_inst[6]:
            cyan_flag = self.InstProc._resolve_factor(
                                                      display_inst[6].strip(), 
                                                      instruction_proc_vars, 
                                                      instruction_samp_vars, 
                                                      instruction_dtl_vars
                                                      )
        
        color_frag = "bgcolor='%s'" % (PNL_TBL_BACKGROUNDCOLOR)
        if red_flag:
            color_frag = "bgcolor='%s'" % (PNL_REDCOLOR)
            color_name = RED
        elif yellow_flag:
            color_frag = "bgcolor='%s'" % (PNL_YELLOWCOLOR)
            color_name = YELLOW
        elif green_flag:
            color_frag = "bgcolor='%s'" % (PNL_GREENCOLOR)
            color_name = GREEN
        elif cyan_flag:
            color_frag = "bgcolor='%s'" % (PNL_CYANCOLOR)
            color_name = CYAN
            
        return show_data, color_frag, color_name
        
        

    def _append_col_to_spreadsheet(self, value, sheet, fmt=None, width=None, exception=None):
        col = self._sheet_last_col[sheet]
        row = self._sheet_last_row[sheet]
        if fmt:
            self._sheet[sheet].write(row, col, value, fmt)
        else:
            self._sheet[sheet].write(row, col, value)
        
        if sheet in ("Summary", "Detail"):
            if exception:
                try:
                    self._sheet[sheet].write(row, 1, exception, self._heading_xf)
                except:
                    pass
            
        if width:
            self._sheet[sheet].col(col).width = width
            
        self._sheet_last_col[sheet] += 1
        
        # skip column 1 for "summary" worksheet. this column is reserved
        if sheet in ("Summary", "Detail"):
            if self._sheet_last_col[sheet] == 1:
                self._sheet_last_col[sheet] += 1
        
        #print value, 


    def _new_row_for_spreadsheet(self, sheet):
        self._sheet_last_row[sheet] += 1
        self._sheet_last_col[sheet] = 0
        
        #print ""


    def _append_merged_cols_to_spreadsheet(self, value, sheet, cols=1, fmt=None):
        col = self._sheet_last_col[sheet]
        col2 = col + cols - 1
        row = self._sheet_last_row[sheet]
        if fmt:
            self._sheet[sheet].write_merge(row, row, col, col2, value, fmt)
        else:
            self._sheet[sheet].write_merge(row, row, col, col2, value)
        
        
        self._sheet_last_col[sheet] += cols
        
        #print value
        

    def _append_spreadsheet_title(self, title, sheet, cols):
        self._append_merged_cols_to_spreadsheet(title, sheet, cols, self._heading_xf)
        self._new_row_for_spreadsheet(sheet)
        self._append_merged_cols_to_spreadsheet("", sheet, cols)
        self._new_row_for_spreadsheet(sheet)
       
       
    
    def _initialize_workbook(self):
        self._smpl_worksheet_cnt = 0
        self._dtl_worksheet_cnt = 0
        self._wb = None
        self._wb = xlwt.Workbook()
        self._sheet = {}
        self._sheet[self._sheet_summary] = self._wb.add_sheet(self._sheet_summary)
        self._sheet[self._sheet_detail] = self._wb.add_sheet(self._sheet_detail)
        self._sheet[self._sheet_source] = self._wb.add_sheet(self._sheet_source)
        self._sheet[self._sheet_instructions] = self._wb.add_sheet(self._sheet_instructions)
        #self._sheet[self._sheet_resolved] = self._wb.add_sheet(self._sheet_resolved)

        self._sheet_last_col = {}
        self._sheet_last_row = {}
        for k in self._sheet.keys():
            self._sheet_last_col[k] = 0
            self._sheet_last_row[k] = 0

        return

    def _define_spreadsheet_formats(self):
        self._spreadsheet_formats = True
        
        self._sheet_summary = "Summary"
        self._sheet_detail = "Detail"
        self._sheet_source = "Source"
        self._sheet_instructions = "Instructions"
        self._sheet_resolved = "Resolved"

        self._ezxf = xlwt.easyxf
        self._heading_xf = self._ezxf('font: bold on; align: wrap on, vert centre, horiz center')
        self._heading_xf_right = self._ezxf('font: bold on; align: wrap on, vert centre, horiz right')

        self._float_fmt = self._ezxf(num_format_str='#0.00')
        self._float_fmt_no_color = self._ezxf(num_format_str='#0.00')
        self._float_fmt_ignore = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_SHADECOLOR,WS_SHADECOLOR), num_format_str='#0.00')
        self._float_fmt_green = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_GREENCOLOR,WS_GREENCOLOR), num_format_str='#0.00')
        self._float_fmt_yellow = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_YELLOWCOLOR,WS_YELLOWCOLOR), num_format_str='#0.00')
        self._float_fmt_red = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_REDCOLOR,WS_REDCOLOR), num_format_str='#0.00')
        self._float_fmt_cyan = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_CYANCOLOR,WS_CYANCOLOR), num_format_str='#0.00')

        self._float3_fmt = self._ezxf(num_format_str='#0.000')
        self._float3_fmt_no_color = self._ezxf(num_format_str='#0.000')
        self._float3_fmt_ignore = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_SHADECOLOR,WS_SHADECOLOR), num_format_str='#0.000')
        self._float3_fmt_green = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_GREENCOLOR,WS_GREENCOLOR), num_format_str='#0.000')
        self._float3_fmt_yellow = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_YELLOWCOLOR,WS_YELLOWCOLOR), num_format_str='#0.000')
        self._float3_fmt_red = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_REDCOLOR,WS_REDCOLOR), num_format_str='#0.000')
        self._float3_fmt_cyan = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_CYANCOLOR,WS_CYANCOLOR), num_format_str='#0.000')
        
        self._float4_fmt = self._ezxf(num_format_str='#0.0000')
        self._float4_fmt_no_color = self._ezxf(num_format_str='#0.0000')
        self._float4_fmt_ignore = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_SHADECOLOR,WS_SHADECOLOR), num_format_str='#0.0000')
        self._float4_fmt_green = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_GREENCOLOR,WS_GREENCOLOR), num_format_str='#0.0000')
        self._float4_fmt_yellow = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_YELLOWCOLOR,WS_YELLOWCOLOR), num_format_str='#0.0000')
        self._float4_fmt_red = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_REDCOLOR,WS_REDCOLOR), num_format_str='#0.0000')
        self._float4_fmt_cyan = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_CYANCOLOR,WS_CYANCOLOR), num_format_str='#0.0000')
        
        self._float5_fmt = self._ezxf(num_format_str='#0.00000')
        self._float5_fmt_no_color = self._ezxf(num_format_str='#0.00000')
        self._float5_fmt_ignore = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_SHADECOLOR,WS_SHADECOLOR), num_format_str='#0.00000')
        self._float5_fmt_green = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_GREENCOLOR,WS_GREENCOLOR), num_format_str='#0.00000')
        self._float5_fmt_yellow = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_YELLOWCOLOR,WS_YELLOWCOLOR), num_format_str='#0.00000')
        self._float5_fmt_red = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_REDCOLOR,WS_REDCOLOR), num_format_str='#0.00000')
        self._float5_fmt_cyan = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_CYANCOLOR,WS_CYANCOLOR), num_format_str='#0.00000')
        
        self._float_width = 0x0d00 + 1000

        self._int_fmt = self._ezxf(num_format_str='#,##0')
        self._int_fmt_no_color = self._ezxf(num_format_str='#,##0')
        self._int_fmt_ignore = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_SHADECOLOR,WS_SHADECOLOR), num_format_str='#,##0')
        self._int_fmt_green = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_GREENCOLOR,WS_GREENCOLOR), num_format_str='#,##0')
        self._int_fmt_yellow = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_YELLOWCOLOR,WS_YELLOWCOLOR), num_format_str='#,##0')
        self._int_fmt_red = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_REDCOLOR,WS_REDCOLOR), num_format_str='#,##0')
        self._int_fmt_cyan = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_CYANCOLOR,WS_CYANCOLOR), num_format_str='#,##0')

        self._datetime_fmt = self._ezxf(num_format_str='yyyy-mm-dd HH:MM:SS')
        self._datetime_fmt_no_color = self._ezxf(num_format_str='yyyy-mm-dd HH:MM:SS')
        self._datetime_fmt_ignore = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_SHADECOLOR,WS_SHADECOLOR), num_format_str='yyyy-mm-dd HH:MM:SS')
        self._datetime_fmt_green = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_GREENCOLOR,WS_GREENCOLOR), num_format_str='yyyy-mm-dd HH:MM:SS')
        self._datetime_fmt_yellow = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_YELLOWCOLOR,WS_YELLOWCOLOR), num_format_str='yyyy-mm-dd HH:MM:SS')
        self._datetime_fmt_red = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_REDCOLOR,WS_REDCOLOR), num_format_str='yyyy-mm-dd HH:MM:SS')
        self._datetime_fmt_cyan = self._ezxf('pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_CYANCOLOR,WS_CYANCOLOR), num_format_str='yyyy-mm-dd HH:MM:SS')
        self._datetime_width = 0x0d00 + 2000

        self._text_fmt = self._ezxf('align: wrap on, vert centre, horiz center')
        self._text_fmt_no_color = self._ezxf('align: wrap on, vert centre, horiz center')
        self._text_fmt_ignore = self._ezxf('align: wrap on, vert centre, horiz center; pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_SHADECOLOR,WS_SHADECOLOR))
        self._text_fmt_green = self._ezxf('align: wrap on, vert centre, horiz center; pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_GREENCOLOR,WS_GREENCOLOR))
        self._text_fmt_yellow = self._ezxf('align: wrap on, vert centre, horiz center; pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_YELLOWCOLOR,WS_YELLOWCOLOR))
        self._text_fmt_red = self._ezxf('align: wrap on, vert centre, horiz center; pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_REDCOLOR,WS_REDCOLOR))
        self._text_fmt_cyan = self._ezxf('align: wrap on, vert centre, horiz center; pattern: pattern fine_dots, back_color %s, fore_color %s' %(WS_CYANCOLOR,WS_CYANCOLOR))
        self._text_fmt_left = self._ezxf('align: wrap on, vert top, horiz left')

        self._html_escape_table = {"&": "&amp;",
                                   '"': "&quot;",
                                   "'": "&apos;",
                                   ">": "&gt;",
                                   "<": "&lt;",
                                   }

    def _resolve_spreadsheet_fmt(self, first_column, color_name, type, inst_var): 
        if type == FLOAT:
            #print "inst_var: ", inst_var
            if inst_var in self.display_precision_five:
                if first_column:
                    fmt = self._heading_xf
                elif color_name == IGNORE:
                    fmt = self._float5_fmt_ignore
                elif color_name == RED:
                    fmt = self._float5_fmt_red
                elif color_name == YELLOW:
                    fmt = self._float5_fmt_yellow
                elif color_name == GREEN:
                    fmt = self._float5_fmt_green
                elif color_name == CYAN:
                    fmt = self._float5_fmt_cyan
                else:
                    fmt =  self._float_fmt
            elif inst_var in self.display_precision_four:
                if first_column:
                    fmt = self._heading_xf
                elif color_name == IGNORE:
                    fmt = self._float4_fmt_ignore
                elif color_name == RED:
                    fmt = self._float4_fmt_red
                elif color_name == YELLOW:
                    fmt = self._float4_fmt_yellow
                elif color_name == GREEN:
                    fmt = self._float4_fmt_green
                elif color_name == CYAN:
                    fmt = self._float4_fmt_cyan
                else:
                    fmt =  self._float_fmt
            elif inst_var in self.display_precision_three:
                if first_column:
                    fmt = self._heading_xf
                elif color_name == IGNORE:
                    fmt = self._float3_fmt_ignore
                elif color_name == RED:
                    fmt = self._float3_fmt_red
                elif color_name == YELLOW:
                    fmt = self._float3_fmt_yellow
                elif color_name == GREEN:
                    fmt = self._float3_fmt_green
                elif color_name == CYAN:
                    fmt = self._float3_fmt_cyan
                else:
                    fmt =  self._float3_fmt
            else:
                if first_column:
                    fmt = self._heading_xf
                elif color_name == IGNORE:
                    fmt = self._float_fmt_ignore
                elif color_name == RED:
                    fmt = self._float_fmt_red
                elif color_name == YELLOW:
                    fmt = self._float_fmt_yellow
                elif color_name == GREEN:
                    fmt = self._float_fmt_green
                elif color_name == CYAN:
                    fmt = self._float_fmt_cyan
                else:
                    fmt =  self._float_fmt

        elif type == INT:
            if first_column:
                fmt = self._heading_xf
            elif color_name == IGNORE:
                fmt = self._int_fmt_ignore
            elif color_name == RED:
                fmt = self._int_fmt_red
            elif color_name == YELLOW:
                fmt = self._int_fmt_yellow
            elif color_name == GREEN:
                fmt = self._int_fmt_green
            elif color_name == CYAN:
                fmt = self._int_fmt_cyan
            else:
                fmt =  self._int_fmt
            
        else:
            if first_column:
                fmt = self._heading_xf
            elif color_name == IGNORE:
                fmt = self._text_fmt_ignore
            elif color_name == RED:
                fmt = self._text_fmt_red
            elif color_name == YELLOW:
                fmt = self._text_fmt_yellow
            elif color_name == GREEN:
                fmt = self._text_fmt_green
            elif color_name == CYAN:
                fmt = self._text_fmt_cyan
            else:
                fmt =  self._text_fmt
                
        return fmt
        
    def generate_cc_plot(self, notebook=None, pltidx=None):
        skip_standards = None
        fig = {}
        i = 0
        for c in self.InstProc._plot_order:
            #print self.InstProc._plot_inst[c]
            ii = 0
            for x in self.InstProc._plot_inst[c]:
                if ii == 0:
                    inst_var = x 
                if ii == 1:
                    show_cond = x 
                if ii == 2:
                    ttl = x 
                if ii == 3:
                    red_cond = x 
                if ii == 4:
                    yellow_cond = x 
                if ii == 5:
                    green_cond = x 
                if ii == 6:
                    cyan_cond = x 
                if ii > 6:
                    if x == "":
                        skip_standards = True
                
                ii += 1

            xyplot = None
            if "XY_X(" in inst_var:
                xyplot = True
                beg, sep, end = inst_var[5:].rpartition(" XY_Y(")
                xvar, sep, remain = beg.rpartition(")")
                xvar = xvar.strip()
                yvar, sep, trash = end.rpartition(")")
                yvar = yvar.strip()
                #print xvar, yvar
                inst_var = yvar
            
            xt = []
            
            si = {}
            ei = {}
            xsi = {}
            xei = {}

            gmwl_x = []
            gmwl_y = []
            bfx = []
            bfy = []

            xt.append("")
            for smpl in self.InstProc._samples_name_dict.keys():
                    si[smpl] = []
                    ei[smpl] = []
            
                    xsi[smpl] = []
                    xei[smpl] = []
                
            for smpl,v in self.InstProc._samples_name_dict.iteritems():
                cs = self.InstProc._instruction_samp_vars[smpl][inst_var][VARRAY]
                a = array(cs)
                meana = a.mean()
                stda = a.std(ddof=1)

                xt.append(v[NAME]+"      ")

                if xyplot:
                    cs = self.InstProc._instruction_samp_vars[smpl][xvar][VARRAY]
                    a = array(cs)
                    meanax = a.mean()
                    stdax = a.std(ddof=1)

                for dd in self.InstProc._samples_name_dict.keys():
                    if smpl == dd:
                        si[dd].append(meana)
                        ei[dd].append(stda)
                        
                        if xyplot:
                            xsi[dd].append(meanax)
                            xei[dd].append(stdax)

                            x = meanax
                            y = (8*x)+10
                            gmwl_x.append(x)
                            gmwl_y.append(y)
                
            fig[i] = Figure(frameon=True,facecolor=PLOT_FACECOLOR)
            plt = fig[i].add_subplot(111)

            for dd in self.InstProc._samples_name_dict.keys():
                if xyplot:
                    # Don't show "standards" in the xy plot
                    sname = xt[dd].strip()
                    if not sname in self.InstProc._stdsdata.keys():
                        plt.errorbar(xsi[dd], si[dd], xerr=xei[dd], yerr=ei[dd], fmt="o", elinewidth=1, mew=1, capsize=3, label="%s %s" % (dd, sname))   
                        bfx.append(xsi[dd][0])
                        bfy.append(si[dd][0])
                else:
                    red_flag = self.InstProc._resolve_factor(red_cond, self.InstProc._instruction_proc_vars, self.InstProc._instruction_samp_vars[dd])
                    yellow_flag = self.InstProc._resolve_factor(yellow_cond, self.InstProc._instruction_proc_vars, self.InstProc._instruction_samp_vars[dd])
                    green_flag = self.InstProc._resolve_factor(green_cond, self.InstProc._instruction_proc_vars, self.InstProc._instruction_samp_vars[dd])
                    cyan_flag = self.InstProc._resolve_factor(cyan_cond, self.InstProc._instruction_proc_vars, self.InstProc._instruction_samp_vars[dd])
    
                    if red_flag:
                        main_color = PNL_REDCOLOR
                    elif yellow_flag:
                        main_color = PNL_YELLOWCOLOR
                    elif green_flag:
                        main_color = PNL_GREENCOLOR
                    elif cyan_flag:
                        main_color = PNL_CYANCOLOR
                    else:
                        main_color = PLOT_DEFAULT_COLOR

                    plt.errorbar(dd, si[dd], yerr=ei[dd], fmt="o", elinewidth=1, mew=1, capsize=3, color=main_color)   
            
            if xyplot:
                plt.set_xlabel(xvar)
                plt.set_ylabel(yvar)
                
                show_gmwl = None
                show_best_fit = None

                #red_cond, yellow_cond, green_cond, cyan_cond hold the extra
                #plot types when doing an xyplot
                if "gmwl" in (red_cond, yellow_cond, green_cond, cyan_cond):
                    show_gmwl = True
                    
                #red_cond, yellow_cond, green_cond, cyan_cond hold the extra
                #plot types when doing an xyplot
                if "best_fit" in (red_cond, yellow_cond, green_cond, cyan_cond):
                    show_best_fit = True
                
                minx, maxx = plt.get_xlim()

                if show_gmwl:
                    gmwl_x = arange(minx, maxx+1, )
                    gmwl_y = 8*gmwl_x+10
    
                    plt.plot(gmwl_x, gmwl_y, label="gmwl")
                
                if show_best_fit:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(bfx,bfy)
                    bf_x = arange(minx, maxx+1, )
                    bf_y = slope*bf_x+intercept
    
                    leg = "\nBest Fit\nslp: %0.5f\nncpt: %0.5f\nrsq: %0.5f" % (slope, intercept, (r_value **2))
                    plt.plot(bf_x, bf_y, label=leg)

                plt.legend(shadow=True, prop=font_manager.FontProperties(size=10), loc="center left")

            else:
                plt.set_xticks(arange(len(xt)))
                plt.set_xticklabels(xt, visible=True, rotation=45)
                
            plt.set_title(ttl)
            plt.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
            
            pidx = i + 1
            self.plot_name[pidx] = ttl


            i += 1
        
        while i < 4:
            fig[i] = Figure(frameon=True,facecolor=PLOT_FACECOLOR)
            i += 1
             
        self.cc_plots = fig

      
if __name__ == '__main__':
    raise RuntimeError, "%s %s" % ("chemcorrectmodel.py", STANDALONE_ERROR)
