'''
xyplot.py -- The xyplot module contains the XYPlotModel class.
This class will display an XY plot of data from the source CSV or H5 file (from 
coordinator).

'''
import os
import datetime

from postprocessdefn import *
from postdataprovider import PostDataProvider

from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.dates import date2num, YearLocator, MonthLocator, DateFormatter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

import matplotlib.font_manager as font_manager

import numpy

from Utilities import AppInfo


class XYPlotModel(object):
    '''
    XYPlot Model Class
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''

        # version and about info
        about = AppInfo()
        self.about_version = about.getAppVer()
        self.about_name = "XYPlot"  #about.getAppName()
        self.about_copyright = about.getCopyright()
        self.about_description = "Graphic plot of analyzer output."  # about.getDescription()
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

        self._title = "XY Plot"
        self._max_source_lines = 100
        
        self._source = None
        self._source_data = None
        self.list_of_columns = None
        
        self._init_process_parms()
        self._init_cntl_objs()

        self._line_source = None

    
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
        txt_len_med = 150
        txt_len_note = 1024
        cntl_len = 200
        tiny_len = 65

        parameter_cols = [
        (SOURCE_PARM, txt_len, "Source", TEXT_CNTL, None, "", True),
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
        ("expt_data", txt_len, "Export Data\nWith Graph?", CHOICE_CNTL, self.list_yes_no, "No", True),
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
        process the passed source file - for XY Plot we only need to open
        the source and get the column name list
        '''
#        if not source == self._source:
#            self._setup_provider(source)
        self._init_process_parms()
        
        if self._source:
            sbase = os.path.basename(self._source)
            stuff, sep, type = sbase.rpartition(".")
            
            self._source_type = type
            
            self.process_parms["column_list"] = self._source_data.column_names_list
            self.process_parms["html_source"][0] = self._build_html(brief_html)
            self.process_parms[STATUS] = OK

    def _build_html(self, brief_html = None):
        '''
        build the html source file
        '''
        show_truncation_msg = None
        
        if self._line_source:
            if self._line_source == self._source:
                return self._line_data
        
        if brief_html:
            self._max_source_lines = 50
        
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

        if "column_list" in self.process_parms.keys():
            for name in self.process_parms["column_list"]:
                line += "<th bgcolor='%s'><b>" %(PNL_TBL_HEADINGCOLOR)
                line += name
                line += "</b></th>"
            
            source_iter = self._source_data.yield_rows()
            i = 0
            for row in source_iter:
                i += 1
                line += "<tr>"
                for name in self.process_parms["column_list"]:
                    line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)
                    line += "%s" % (row[name]) 
                    line += "</td>"

                line += "</tr>"
                
                if i > self._max_source_lines:
                    show_truncation_msg = True
                    break
                
        line += "</table>"
        line += "</td></tr>"

        if show_truncation_msg:
            msg = "Source file truncated after this point."
            msg += " To see the rest of the source, please different viewer."
            line += "<tr><td><h3><p>%s</h3></td><tr/>" % (msg)
            
        line += "<tr><td><p></td><tr/>"
        line += "</table>"

        line += "<table><tr><td align='right'>"
        line += "&copy; 2010 Picarro Inc."
        line += "</td></tr></table>"
        line += "</BODY></HTML>"
        
        self._line_source = self._source
        self._line_data = line

        return line
        
    def generate_plot(self):
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
            
        self.fig=Figure(frameon=True,facecolor=PLOT_FACECOLOR)

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

                self._plot[1] = self._plt[1].plot(xarray, yarray, marker,label=lbl)
                
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
                                          DateFormatter('%H:%M:%S\n%Y/%m/%d', 
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

                
                self._plot[plot_cycle] = self._plt[plot_cycle].plot(xarray, yarray, marker,label=lbl)

                
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
            
        self._plot_was_generated = True
        
        self._status = ""

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

        if sel_vals["expt_data"]:
            export_data = True
        else:
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
    
                    
if __name__ == '__main__':
    raise RuntimeError, "%s %s" % ("xyplotmodel.py", STANDALONE_ERROR)
