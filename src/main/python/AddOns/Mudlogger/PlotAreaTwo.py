import wx
import numpy as np
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from PltCtrlTwo import PltCtrlTwo
from DataCtrlTwo import DataCtrlTwo

class PlotAreaTwo(wx.Panel):
    def __init__(self, parent, main_frame, sidebar):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.main_frame = main_frame
        self.sidebar = sidebar
        
        self.run_number = None
        self.data_in_table_flag = False
        self.left_bound_flag = False
        self.right_bound_flag = False
        self.left_bound, self.right_bound = None,None
        self.species_selection = None
        self.page_selection = 0
        ### Setup Data
        self.initialize_data()
        ### Setup Plotter
        self.initialize_plotter()
        ### Setup GUI
        self.intialize_sizer()
        ### Setup mpl_connect
        self.connection_ID = \
            self.canvas.mpl_connect('button_press_event',self.on_click)
        ### Setup Event Binding to Notebook selection changes
        self.setup_notebook_binding()

    def setup_notebook_binding(self):
        self.sidebar.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED,
                  self.on_page_changed)

    def on_page_changed(self,event):
        self.page_selection = event.GetSelection()
        self.sidebar.notebook.ChangeSelection(self.page_selection)
        if self.main_frame.data_loaded_flag and \
                        self.page_selection != self.p_integ_bounds_index:
            self.update_plot_with_data()
        
    def initialize_data(self):
        self.s_run_time_index = 0
        self.s_concentration_index = 1
        self.s_isotope_index= 2
        self.p_isotope_index = 0
        self.p_concentration_index = 1
        self.p_retention_index = 2
        self.p_integ_bounds_index = 3
        self.p_sample_index = 4
        self.data_ctrl_two = DataCtrlTwo()
        self.series_data = self.data_ctrl_two.initialize_data_trace()
        self.peak_data = self.data_ctrl_two.initialize_data_integrated()

        #self.series_data = self.data_ctrl_two.initialize_faux_data_trace()
        #self.peak_data = self.data_ctrl_two.initialize_faux_data_integrated()
        
        self.CO2_data = [self.series_data,self.peak_data]

    def copy_p_data_over(self,dict,ordered_keys_lst):
        non_related_keys = 2
        related_keys_per_peak = 4
        run_cnt_key_index = 0
        number_of_peaks = (len(dict)-non_related_keys)/ \
            related_keys_per_peak

        for i in range(len(self.peak_data)):
            if i == self.p_sample_index:
                self.peak_data[i] = dict[ordered_keys_lst[run_cnt_key_index]]
            elif i != self.p_integ_bounds_index:
                self.peak_data[i] = []
                for j in range(number_of_peaks):
                    key_index = non_related_keys + \
                        i*number_of_peaks + j
                    subset = []
                    for value in dict[ordered_keys_lst[key_index]]:
                        try:
                           subset.append(float(value))
                        except ValueError:
                           subset.append(np.NaN)
                    self.peak_data[i].append(subset)
            else:
                self.peak_data[i] = []
                for j in range(number_of_peaks):
                    key_index = non_related_keys + \
                        i*number_of_peaks + j
                    subset = dict[ordered_keys_lst[key_index]]
                    self.peak_data[i].append(subset)

    def clear_data_and_reset_flags(self):
        self.clear_data()
        self.reset_flags()

    def reset_flags(self):
        self.left_bound_flag = False
        self.right_bound_flag = False


    def clear_data(self):
        self.series_data = self.data_ctrl_two.initialize_data_trace()
        self.peak_data = self.data_ctrl_two.initialize_data_integrated()
        self.CO2_data = [self.series_data,self.peak_data]


    def initialize_plotter(self):
        initial_index = 0 #used to determine what data to plot
        self.plt_ctrl_two = PltCtrlTwo()
        self.figure = self.plt_ctrl_two.initialize_plots()
        self.plot_data()
    
    def intialize_sizer(self):
        self.SetBackgroundColour('white')

        left_button = wx.Button(self, id=-1, label='Previous 25')
        left_button.Bind(wx.EVT_BUTTON, self.on_shift_left)
        right_button = wx.Button(self, id=-1, label='Next 25')
        right_button.Bind(wx.EVT_BUTTON, self.on_shift_right)

        sizer_for_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_for_buttons.Add(left_button, 0, wx.ALIGN_TOP, 10)
        sizer_for_buttons.Add(right_button, 0, wx.ALIGN_TOP, 10)

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(sizer_for_buttons, 0, wx.EXPAND)
        sizer_main.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer_main)


    def plot_data(self):
        self.figure = self.plt_ctrl_two.clear_plots()
        self.figure = \
            self.plt_ctrl_two.plot_data(self.peak_data[self.p_sample_index],
                                        self.peak_data[self.page_selection],
                                        self.series_data[self.s_run_time_index],
                                        self.series_data[self.s_concentration_index],
                                        self.page_selection,
                                        self.sidebar.get_species_lst())
        self.canvas = FigCanvas(self, -1, self.figure)
    
    def update_plot_with_data(self):
        self.plt_ctrl_two.clear_plots()
        self.figure = \
            self.plt_ctrl_two.plot_data(self.peak_data[self.p_sample_index],
                                        self.peak_data[self.page_selection],
                                        self.series_data[self.s_run_time_index],
                                        self.series_data[self.s_concentration_index],
                                        self.page_selection,
                                        self.sidebar.get_species_lst())
        self.highlight_selection(self.run_number,self.species_selection)
        self.canvas.draw()
           
    def on_shift_left(self, event):
        if self.page_selection != self.p_integ_bounds_index:
            min_value = 0
            decrement_by_one = 1
            '''Calculates whether or not to allow the plot x_limits to decrease'''
            if self.plt_ctrl_two.shift_cnt > min_value and self.main_frame.data_loaded_flag:
                self.plt_ctrl_two.shift_cnt -= decrement_by_one
                self.plt_ctrl_two.reset_plot_range(self.plt_ctrl_two.max_range,
                                               self.plt_ctrl_two.shift_cnt,
                                               self.peak_data[self.page_selection])
                self.canvas.draw()

    def on_shift_right(self, event):
        if self.page_selection != self.p_integ_bounds_index:
            increment_by_one = 1
            '''Calculates whether or not to allow the plot x_limits to increase'''
            if self.main_frame.data_loaded_flag:
                if (self.plt_ctrl_two.shift_cnt+1)*self.plt_ctrl_two.max_range <\
                    len(self.peak_data[self.p_sample_index]):
                    self.plt_ctrl_two.shift_cnt += increment_by_one
                    self.plt_ctrl_two.reset_plot_range(self.plt_ctrl_two.max_range,
                                                   self.plt_ctrl_two.shift_cnt,
                                                   self.peak_data[self.page_selection])
                    self.canvas.draw()

    def on_click(self,event):
        scalar_two = 2
        vertical_index = 1
        ### Testing if a data set was loaded and which mouse button clicked
        if self.main_frame.data_loaded_flag and event.button == 1:
            ### Testing if the click was in a valid area
            if event.xdata != None and event.ydata != None:
                x_data, y_data = event.xdata, event.ydata
                ### Testing which of the two plots were clicked
                if event.y > self.canvas.GetSize()[vertical_index]/scalar_two:
                    self.run_number = self.determine_selection_run(x_data)
                    if self.run_number > -1:
                        self.species_selection = \
                            self.determine_selection_species(self.run_number,
                                                             y_data)
                        if self.species_selection != None:
                            self.highlight_selection(self.run_number,
                                                        self.species_selection)
                            self.report_table_data_to_sidebar(self.run_number,
                                                                self.species_selection)
                            self.clear_reprocessed_data()
                            self.reset_flags()
                            
                else:
                    if self.species_selection != None:
                        self.calculate_and_show_users_bounds(x_data)
                    if self.left_bound_flag and self.right_bound_flag:
                        if self.left_bound != self.right_bound:
                            self.reprocess_data_with_new_bounds()
                            self.main_frame.status_bar_write(2,'')
                        else:
                            self.main_frame.status_bar_write(2,'Integration Bounds Not Unique...')
                    else:
                        self.clear_reprocessed_data()
                    

    def report_table_data_to_sidebar(self,run_number,species_selection):
        self.sidebar.report_data_from_table(run_number,
                                                species_selection)
                                                
    def reprocess_data_with_new_bounds(self):
        time = self.series_data[self.s_run_time_index][self.run_number][self.left_bound:self.right_bound]
        conc = self.series_data[self.s_concentration_index][self.run_number][self.left_bound:self.right_bound]
        conc_baseline = np.average(self.series_data[self.s_concentration_index][self.run_number][self.left_bound:self.left_bound + 3])
        conc = [conc_i-conc_baseline for conc_i in conc]
        
        delta = self.series_data[self.s_isotope_index][self.run_number][self.left_bound:self.right_bound]

        reprocessed_data = []
        
        ### same code as for peak detection calculations...
        
        limit_of_reliable_delta = 15000 #ppm
        start_integration = 5000 #ppm
        
        ### Normal peak integration method...
        if max(conc) < limit_of_reliable_delta:
            i = 0
            integrated_delta = 0
            integrated_conc = 0
            while i < len(time)-2:
                try:
                    time_factor = (time[i+2]-time[i])/6.0
                    integrated_conc += time_factor*(conc[i]+4*conc[i+1]+conc[i+2])
                    d_delta = time_factor*(conc[i]*np.average(delta[i:i+3])+4*conc[i+1]*np.average(delta[i+1:i+4])+conc[i+2]*np.average(delta[i+2:i+5]))
                    if not np.isnan(d_delta):
                        integrated_delta += d_delta
                except: pass
                i += 3
            reprocessed_data = [integrated_delta / integrated_conc]
        
        ### Using tail of peak for integration...
        else:
            i = 0
            integrated_delta = 0
            integrated_conc = 0
            while i < len(time)-2:
                ### only integration over the right (or tail) side of the peak
                if time[i] > self.current_peak_retention_time and conc[i] < start_integration:
                    try:
                        time_factor = (time[i+2]-time[i])/6.0
                        integrated_conc += time_factor*(conc[i]+4*conc[i+1]+conc[i+2])
                        d_delta = time_factor*(conc[i]*np.average(delta[i:i+3])+4*conc[i+1]*np.average(delta[i+1:i+4])+conc[i+2]*np.average(delta[i+2:i+5]))
                        if not np.isnan(d_delta):
                            integrated_delta += d_delta
                    except: pass
                i += 3
            reprocessed_data = [integrated_delta / integrated_conc]

        ### use previous calibration parameters to calibrate data
        if self.main_frame.b_current != None and self.main_frame.m_current != None:
            reprocessed_data = [self.main_frame.m_current*reprocessed_data[0]+self.main_frame.b_current]
        reprocessed_data.append(max(conc))
        reprocessed_data.append(time[conc.index(max(conc))])
        reprocessed_data.append([self.left_bound,self.right_bound])

        self.sidebar.reprocess_area.set_reprocessed_string_items(reprocessed_data,
                                                                    self.run_number,
                                                                    self.species_selection)

    def clear_reprocessed_data(self):
        self.sidebar.reprocess_area.clear_reprocessed_string_items(
                                                        self.run_number,
                                                        self.species_selection)
                    
    def calculate_and_show_users_bounds(self,x_data):
        shift_for_time_column = 1
        number_of_peaks = self.sidebar.page_one.data_grid.GetNumberCols() -\
            shift_for_time_column
        self.calculate_point(self.run_number,x_data)
        self.plt_ctrl_two.display_new_integration_bounds(
            number_of_peaks,
            self.series_data[self.s_concentration_index][self.run_number],
            self.series_data[self.s_run_time_index][self.run_number],
            self.left_bound_flag,self.right_bound_flag,
            self.left_bound, self.right_bound,
            self.integration_bounds_for_run(self.run_number),
            self.species_selection)
        self.canvas.draw()

    def calculate_point(self,run, x_selected):
        min_value_dist = 1e6
        min_value_index = None
        min_value_y_val = None
        x_selected = float(x_selected)
        for i,x_value in enumerate(self.series_data[self.s_run_time_index][run]):
            distance = abs(x_selected - x_value)
            if distance < min_value_dist:
                min_value_dist = distance
                min_value_index = i
                min_value_y_val = self.series_data[self.s_concentration_index][run]
        if not self.left_bound_flag:
            self.left_bound_flag = True
            self.left_bound = min_value_index
        elif self.left_bound_flag and not self.right_bound_flag:
            self.right_bound_flag = True
            self.right_bound = min_value_index
            ### Reorders boundaries if necessary
            if not self.left_bound < self.right_bound:
                self.left_bound, self.right_bound = self.right_bound, self.left_bound
        elif self.left_bound_flag and self.right_bound_flag:
            self.right_bound_flag = False
            self.right_bound = None
            self.left_bound = min_value_index


    def determine_selection_run(self,x_data):
        shift_to_get_index_value = 1
        '''returns the run number of the data point selected'''
        run_number = self.round_this(x_data-shift_to_get_index_value)
        return run_number

    def determine_selection_species(self,run,y_data):
        min_distance_species = None
        if self.page_selection != self.p_integ_bounds_index:
            min_distance = 1e6
            for i in np.arange(len(self.peak_data[self.page_selection])):
                distance = self.distance(self.peak_data[self.page_selection][i][run],y_data)
                if distance < min_distance:
                    min_distance = distance
                    min_distance_species = i
        return min_distance_species
    
    
    def clear_selection(self):
        self.species_selection = None
        self.run_number = None
    
    def highlight_selection(self,run,species):
        self.highlight_selection_in_plot(run,species)
        self.highlight_selection_in_table(run,species)
        
    def highlight_selection_in_table(self,run,species):
        if species != None:
            self.sidebar.highlight_selection_in_table(run,species)
    
    def highlight_selection_in_plot(self,run,species):
        if species != None:
            self.plt_ctrl_two.highlight_selection(
                self.peak_data[self.p_sample_index][run],
                self.peak_data[self.page_selection][species][run])
            self.plt_ctrl_two.display_selected_GC_run(
                self.series_data[self.s_run_time_index][run],
                self.series_data[self.s_concentration_index][run])
            bounds = self.integration_bounds_for_run(run)
            self.plt_ctrl_two.display_integration_bounds(
                bounds,
                self.series_data[self.s_run_time_index][run],
                self.series_data[self.s_concentration_index][run],
                species)

        self.canvas.draw()

    def integration_bounds_for_run(self,run):
        skip_sequence_column = 1
        return [bounds[run] for bounds in self.peak_data[self.p_integ_bounds_index][skip_sequence_column:]]

    def distance(self,x,y):
        return abs(x-y)

    def round_this(self,point):
        if isinstance(point,float):
            return int(np.around(point))
        elif isinstance(point, int):
            return np.rint(point)
        else:
            return None

    def add_parameter_data_to_table(self):
        non_related_keys = 2
        related_keys_per_peak = 4
        run_cnt_key_index = 0

        ordered_keys = self.main_frame.keys
        run_cnt_key = ordered_keys[run_cnt_key_index]
        data_dict = self.main_frame.parameter_file_dict
        number_of_peaks = (len(data_dict)-non_related_keys)/ \
            related_keys_per_peak
        number_of_runs = len(data_dict[run_cnt_key])

        peak_name_labels = self.get_ordered_peak_names(ordered_keys,
                                               non_related_keys,
                                               number_of_peaks)
        self.create_and_label_columns(number_of_peaks,peak_name_labels)
        self.add_rows_to_table(number_of_runs)
        self.sidebar.add_data_to_tables_page_two(data_dict,
                                                 ordered_keys,
                                                 number_of_peaks,
                                                 non_related_keys,
                                                 related_keys_per_peak,
                                                 number_of_runs)
        self.data_in_table_flag = True

        

    def create_and_label_columns(self,peak_cnt,labels):
        self.sidebar.add_cols_to_tables(peak_cnt)
        self.sidebar.set_cols_labels(labels)


    def add_rows_to_table(self,number_of_runs):
        self.sidebar.add_rows_to_tables(number_of_runs)

    def get_ordered_peak_names(self,keys,non_related_keys,
                               number_of_peaks):
        sub_str_to_replace = '_Isotope'
        i = non_related_keys
        f = i+number_of_peaks
        return [keys[i].replace(sub_str_to_replace,'') for i in range(i,f)]

    def clear_and_reset_plots(self):
        self.figure = self.plt_ctrl_two.clear_plots()
        self.canvas.draw()