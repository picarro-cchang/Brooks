'''
thresholdviewer.py -- The thresholdviewer module contains the ThresholdViewerModel class.
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


class ThresholdViewerModel(object):
    '''
    ThresholdViewer Model Class
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''

        # About Info
        self.about_name = "ThresholdViewer"
        self.about_version = "1.0.0"
        self.about_copyright = "(c) 2010 Picarro Inc."
        self.about_description = "Graphic plot of analyzer output."
        self.about_website = "http://www.picarro.com"

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

        self._title = "Threshold Viewer"
        self._max_source_lines = 100
        
        self._source = {
                        SOURCE_PARM: None,
                        SOURCE_PARM2: None,
                        SOURCE_PARM3: None,
                        SOURCE_PARM4: None,
                        SOURCE_PARM5: None,
                        }
        self._source_data = {
                        SOURCE_PARM: None,
                        SOURCE_PARM2: None,
                        SOURCE_PARM3: None,
                        SOURCE_PARM4: None,
                        SOURCE_PARM5: None,
                             }
        self._source_data_base = {
                        SOURCE_PARM: None,
                        SOURCE_PARM2: None,
                        SOURCE_PARM3: None,
                        SOURCE_PARM4: None,
                        SOURCE_PARM5: None,
                                  }
        self.list_of_columns = None
        
        self._init_process_parms()
        self._init_cntl_objs()

        self._line_source = None
        self.column_names_list = None

    
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
        (SOURCE_PARM, txt_len_long, "Source 1", TEXT_CNTL, None, "", True),
        ("color1", txt_len, "Color 1", CHOICE_CNTL, self.list_of_marker_colors, BLUE, True),

        ("cntl_spacer", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        (SOURCE_PARM2, txt_len_long, "Source 2", TEXT_CNTL, None, "", True),
        ("color2", txt_len, "Color 2", CHOICE_CNTL, self.list_of_marker_colors, GREEN, True),
        
        ("cntl_spacer2", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        (SOURCE_PARM3, txt_len_long, "Source 3", TEXT_CNTL, None, "", True),
        ("color3", txt_len, "Color 3", CHOICE_CNTL, self.list_of_marker_colors, RED, True),
        
        ("cntl_spacer3", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        (SOURCE_PARM4, txt_len_long, "Source 4", TEXT_CNTL, None, "", True),
        ("color4", txt_len, "Color 4", CHOICE_CNTL, self.list_of_marker_colors, CYAN, True),
        
        ("cntl_spacer4", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        (SOURCE_PARM5, txt_len_long, "Source 5", TEXT_CNTL, None, "", True),
        ("color5", txt_len, "Color 5", CHOICE_CNTL, self.list_of_marker_colors, BLACK, True),
        
        ("cntl_spacer5", tiny_len, "", SPACER_CNTL_SM, None, None, None),
        ("graphy1", txt_len_med, "Y1 Axis Column", CHOICE_CNTL, self.list_of_columns, CHOICE_NONE, True),
        ("marker1", txt_len, "Y1 Marker", CHOICE_CNTL, self.list_of_marker_points, "solid line", True),

        ("graphy2", txt_len_med, "Y2 Axis Column", CHOICE_CNTL, self.list_of_columns, CHOICE_NONE, True),
        ("marker2", txt_len, "Y2 Marker", CHOICE_CNTL, self.list_of_marker_points, "dashed line", True),

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
        
        
    def collist_from_source(self, values_dict):
        self.list_of_columns = []
        self.list_of_columns.append(CHOICE_NONE)
        
        for skey in (
                     SOURCE_PARM, 
                     SOURCE_PARM2, 
                     SOURCE_PARM3, 
                     SOURCE_PARM4, 
                     SOURCE_PARM5,
                     ):
            if skey in values_dict.keys():
                source = values_dict[skey]
                
                if source:
                    if not skey in self._source.keys():
                        self._source[skey] = source
                        
                    if not source == self._source[skey]:
                        self._setup_provider(skey, source)
                    
                    if self._source_data[skey]:
                        if self._source_data[skey].column_names_list:
                            self.column_names_list = self._source_data[skey].column_names_list
                            for name in self._source_data[skey].column_names_list:
                                self.list_of_columns.append(name)
        
                    if self._source[skey]:
                        sbase = os.path.basename(self._source[skey])
                        stuff, sep, type = sbase.rpartition(".")
                        
                        self._source_type = type

            else:
                self._source[skey] = None
                self._source_data[skey] = None
                
        return self.list_of_columns
    
    
    def _setup_provider(self, skey, source):
        
        try:
            self._source[skey] = source
            spath = self._source[skey]
            sbase = os.path.basename(spath)
            self._source_data_base[skey] = sbase
            self._source_data[skey] = PostDataProvider(
                                                      spath, 
                                                      type="threshold"
                                                        )
        
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
            self.process_parms["column_list"] = self.column_names_list
            self.process_parms["html_source"][0] = self._build_html(brief_html)
            self.process_parms[STATUS] = OK

    def _build_html(self, brief_html = None):
        '''
        build the html source file
        '''
        '''
        build the html source file
        '''
        if self._line_source:
            line_source = ""
            for skey in sorted(self._source.keys()):
                if not self._source[skey]:
                    continue
                
                spath = self._source[skey]
                line_source += spath

            if self._line_source == line_source:
                return self._line_data
        
        line = "<HTML><BODY bgcolor='%s'>" % (MAIN_BACKGROUNDCOLOR)
        line += "<H2 align='center'>%s</H2>" % (self._title)
        line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                    '98%', 
                                                    PNL_TBL_BACKGROUNDCOLOR
                                                                )

        # show source and instruction files
        for skey in sorted(self._source.keys()):
            if not self._source[skey]:
                continue
            
            spath = self._source[skey]
            line += "<tr><td>"
            line += "<table border = '0'>"
            line += "<tr><td>%s:</td><td><b>%s</b></td></tr>" % (skey, spath)
            line += "</table>"
            line += "</td></tr>"
    
            line += "<tr><td align='center'>"
            line += "<table width='%s' border='0' bgcolor='%s'>" % (
                                                            '98%', 
                                                            PNL_TBL_BORDERCOLOR
                                                                    )
    
            if self.column_names_list:
                for name in self.column_names_list:
                    line += "<th bgcolor='%s'><b>" %(PNL_TBL_HEADINGCOLOR)
                    line += name
                    line += "</b></th>"
            
            source_iter = self._source_data[skey].yield_rows()
            i = 0
            for row in source_iter:
                i += 1
                
                line += "<tr>"
                for name in self.column_names_list:
                    line += "<td bgcolor='%s'>" % (PNL_TBL_BACKGROUNDCOLOR)
                    if name in row.keys():
                        line += "%s" % (row[name]) 
                    line += "</td>"

                line += "</tr>"
                
                if i > self._max_source_lines:
                    break
                
            line += "</table>"
            line += "</td></tr>"
        line += "<tr><td><p></td><tr/>"
        line += "</table>"

        line += "<table><tr><td align='right'>&copy; 2010 Picarro Inc.</td></tr></table>"
        line += "</BODY></HTML>"
        
        self._line_source = ""
        for skey in sorted(self._source.keys()):
            spath = self._source[skey]
            if spath:
                self._line_source += spath
                
        self._line_data = line

        return line
        
        
    def generate_plot(self):
        '''
        generate an XY plot 
        '''
        plot_parameters = self._get_data_from_controls()
        
        graphx = "Threshold"
        
        graphy1 = None
        if not plot_parameters['y1'] == "-- None --":
            graphy1 = plot_parameters['y1']
            
        graphy2 = None
        if not plot_parameters['y2'] == "-- None --":
            graphy2 = plot_parameters['y2']

        color = {}
        for ci in range(1,6):
            skey = "source%s" % (ci)
            color[skey] = plot_parameters["color%s" % (ci)]
        
        marker1 = plot_parameters["marker1"]
        marker2 = plot_parameters["marker2"]
        combine_data_flag = plot_parameters["combine_data"]
        legend_loc = plot_parameters["legend_loc"]
        
        min_y = None
        max_y = None
        cnt_y = 0
        min_y2 = None
        max_y2 = None
        cnt_y2 = 0

        fig=Figure(frameon=True,facecolor=PLOT_FACECOLOR)
        ncol = 0
        self._plt = {}
        self._plt_twinx = {}
        self._plt_twiny = {}
        if combine_data_flag == "Yes":
            first_marker = True
            for skey in sorted(self._source_data.keys()):
                if not self._source[skey]:
                    continue
                
                if first_marker:
                    self._plt[1] = fig.add_subplot(111)
                    first_plt = self._plt[1]
                
                lbl = "%s" % (self._source_data_base[skey])
                xx=self._source_data[skey].get_column_array(graphx)
                yy=self._source_data[skey].get_column_array(graphy1)

                mkr = "%s%s" % (color[skey], marker1)
                self._plt[1].plot(xx, yy, mkr,label=lbl)
                for tl in self._plt[1].get_xticklabels():
                    tl.set_visible(False)
                
                if first_marker:
                    self._plt[1].set_xlabel(graphx)
                    self._plt[1].set_ylabel(graphy1)
                
                if graphy2:
                    if first_marker:
                        self._plt_twinx[1] = self._plt[1].twinx()
                        first_plt_twin = self._plt_twinx[1]
                    
                    lbl2 = "%s" % (self._source_data_base[skey])
                    y2=self._source_data[skey].get_column_array(graphy2)
                
                    mkr = "%s%s" % (color[skey], marker2)
                    self._plt_twinx[1].plot(xx, y2, mkr)
                    for tl in self._plt_twinx[1].get_xticklabels():
                        tl.set_visible(False)
                    
                    if first_marker:
                        self._plt_twinx[1].set_ylabel(graphy2)

                if first_marker:
                    first_marker = None
                        
                ncol += 1
                
            self._plt[1].legend(loc=legend_loc, ncol=ncol, prop=font_manager.FontProperties(size=10))
            self._plt[1].grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
            for tl in self._plt[1].get_xticklabels():
                tl.set_visible(True)
                tl.set_rotation(30)

            last_plot_idx = 1
        else:
            min_y2 = 0
            max_y2 = 0
            
            first_plt = None
            first_plt_twin = None
            plot_cycle = 0
            last_plot_idx = 0

            num_plots = 0
            for skey in self._source_data.keys():
                if self._source[skey]:
                    num_plots += 1
                
            for skey in sorted(self._source_data.keys()):
                if not self._source[skey]:
                    continue
                
                lbl = "%s" % (self._source_data_base[skey])
                last_plot_idx = plot_cycle
                subplt = "%s1%s" %(num_plots, plot_cycle + 1)

                if not first_plt:
                    self._plt[plot_cycle] = fig.add_subplot(subplt)
                    first_plt = self._plt[plot_cycle]
                else:
                    self._plt[plot_cycle] = fig.add_subplot(subplt, 
                                                            sharex=first_plt, 
                                                            sharey=first_plt
                                                            )

                xx=self._source_data[skey].get_column_array(graphx)
                yy=self._source_data[skey].get_column_array(graphy1)
                
                mkr = "%s%s" % (color[skey], marker1)
                self._plt[plot_cycle].plot(xx, yy, mkr,label=lbl)
                for tl in self._plt[plot_cycle].get_xticklabels():
                    tl.set_visible(False)

                self._plt[plot_cycle].set_ylabel(graphy1)

                self._plt[plot_cycle].legend(loc=legend_loc, ncol=1, prop=font_manager.FontProperties(size=10))
                self._plt[plot_cycle].grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)

                if graphy2:
                    mkr = "%s%s" % (color[skey], marker2)
                    lbl2 = "%s" % (self._source_data_base[skey])
                    y2=self._source_data[skey].get_column_array(graphy2)
                    
                    # get the min/max y2 values for the
                    # hack below to force all Y's to have same scale
                    for yval in y2:
                        if yval < min_y2:
                            min_y2 = yval
                        if yval > max_y2:
                            max_y2 = yval
                            
                    self._plt_twinx[plot_cycle] = self._plt[plot_cycle].twinx()

                    if not first_plt_twin:
                        first_plt_twin = self._plt_twinx[plot_cycle]

                    self._plt_twinx[plot_cycle].plot(xx, y2, mkr)
                    for tl in self._plt_twinx[plot_cycle].get_xticklabels():
                        tl.set_visible(False)

                    self._plt_twinx[plot_cycle].set_ylabel(graphy2)

                plot_cycle += 1

            # there is no "canned" method to lock the 2nd y plot,
            # so this hack will cause all the y's to have same range
            if graphy2:
                mx = xx[0]
                for pc in range(0, plot_cycle):
                    self._plt_twinx[pc].plot([mx, mx], [min_y2, max_y2], visible=False)

                    
            self._plt[plot_cycle-1].set_xlabel(graphx)
            for tl in self._plt[plot_cycle-1].get_xticklabels():
                tl.set_visible(True)
                tl.set_rotation(30)
            
            
        if first_plt:
            first_plt.set_autoscale_on(False)

            if graphy2:
                first_plt_twin.set_autoscale_on(False)

            self.process_parms["plot_fig"][0] = fig
            self.process_parms["plot_data"][0] = None
    

    def _get_data_from_controls(self):
        sel_vals = {}
        for name, control in self.cntls_obj.control_list.iteritems():
            sel_vals[name] = control.get_value()
            print name, sel_vals[name]
        
        exptfile = None

        graphy1 = sel_vals["graphy1"]
        graphy2 = sel_vals["graphy2"]
        marker1 = MARKER_POINTS_DICT[sel_vals["marker1"]]
        marker2 = MARKER_POINTS_DICT[sel_vals["marker2"]]

        color = {}
        for ci in range(1,6):
            ckey = "color%s" % (ci)
            if ckey in sel_vals.keys():
                color[ci] = MARKER_COLORS_DICT[sel_vals[ckey]]
            else:
                color[ci] = None

        combine_data = sel_vals["combine_data"]
        legend_loc = LEGEND_LOCATION_DICT[sel_vals["legend_loc"]]
 
        rtn_parms = {
                     "combine_data": combine_data,
                     "y1": graphy1, 
                     "y2": graphy2, 
                     "marker1": marker1,
                     "marker2": marker2,
                     "color1": color[1],
                     "color2": color[2],
                     "color3": color[3],
                     "color4": color[4],
                     "color5": color[5],
                     "legend_loc": legend_loc,
                    }

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
    raise RuntimeError, "%s %s" % ("thresholdviewermodel.py", STANDALONE_ERROR)
