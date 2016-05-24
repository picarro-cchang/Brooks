# 2015.06.02 11:02:41 Pacific Daylight Time
import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from PltCtrlOne import PltCtrlOne
from DataCtrlOne import DataCtrlOne
from RunCtrlParams import RunCtrlParams
from PeakDection import PeakDection
from BaselineControl import BaselineControl
import time
import numpy as np

class PlotAreaOne(wx.Panel):

    def __init__(self, parent, main_frame, sidebar):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.main_frame = main_frame
        self.sidebar = sidebar
        self.data_ctrl_one = DataCtrlOne()
        self.clear_series_variables()
        self.clear_peak_variable()
        self.peak_file, self.series_file = None, None
        self.grid_lst = [self.sidebar.page_one.data_grid,
            self.sidebar.page_two.data_grid,
            self.sidebar.page_three.data_grid,
            self.sidebar.page_four.data_grid]
        self.plt_ctrl_one = PltCtrlOne()
        self.figure = self.plt_ctrl_one.initialize_plots(self.series_variables)
        self.canvas = FigCanvas(self, -1, self.figure)
        self.canvas.draw()
        self.methane_threshold = main_frame.config.getfloat("Alarm", "Methane_Threshold")
        self.methane_concentration = 0
        self.methane_concentration_previous = 0
        self.water_threshold = main_frame.config.getfloat("Alarm", "Water_Threshold")
        self.water_concentration = 0
        self.intialize_layout()
        self.run_ctrl_params = RunCtrlParams()
        self.peak_detector = PeakDection()
        self.update_timer = self.setup_wx_timer()
        self.baseline_control = BaselineControl(sidebar)
        self.serial_connection = self.baseline_control.get_device_port()
        
        if self.main_frame.generate_fake_data:
            self.baseline_control.furnace_delay = 0
            self.run_ctrl_params.run_duration = 10
            self.main_frame.setup_parameters_flag = True
            self.faux_run_amplitude_1 = np.random.random()
            self.faux_run_amplitude_2 = np.random.random()
            self.faux_run_amplitude_3 = np.random.random()
        elif self.main_frame.read_data_file is not None:
            self.baseline_control.furnace_delay = 0
            self.run_ctrl_params.run_duration = 10
            self.main_frame.setup_parameters_flag = True
            self.input_dataset = {}
            self.run_ctrl_params.max_runs = -1
            with open(self.main_frame.read_data_file, "r") as fin:
                content = fin.read().split('\n')
                line_index = 0
                while True:
                    try:
                        run_number = int(content[line_index])
                        self.run_ctrl_params.max_runs = max(run_number-1, self.run_ctrl_params.max_runs)
                        self.input_dataset[run_number] = {
                                'time': content[line_index + 1].split('\t'),
                                'concentration': content[line_index + 2].split('\t'),
                                'delta': content[line_index + 3].split('\t')}
                        line_index += 4
                    except:
                        break
        
        if self.serial_connection != None:
            self.baseline_control.set_monitor_flag()
            self.sidebar.write_to_log('... GC Monitor found on %s\n' % self.serial_connection)
        else:
            self.sidebar.write_alert_to_log('... GC Monitor not found\n')
        


    def intialize_layout(self):
        self.SetBackgroundColour('white')
        start_button = wx.Button(self, id=-1, label='Start Runs')
        start_button.Bind(wx.EVT_BUTTON, self.on_start)
        clear_button = wx.Button(self, id=-1, label='Clear All')
        clear_button.Bind(wx.EVT_BUTTON, self.on_clear)
        stop_button = wx.Button(self, id=-1, label='Stop Runs')
        stop_button.Bind(wx.EVT_BUTTON, self.on_stop)
        sizer_for_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_for_buttons.Add(clear_button, 0, wx.ALIGN_TOP, 10)
        sizer_for_buttons.Add(start_button, 0, wx.ALIGN_TOP, 10)
        sizer_for_buttons.Add(stop_button, 0, wx.ALIGN_TOP, 10)
        sizer_for_buttons.Add((20, 20), 1, 0, 0)
        logoBmp = wx.Bitmap('logo.png', wx.BITMAP_TYPE_PNG)
        sizer_for_buttons.Add(wx.StaticBitmap(self, -1, logoBmp), proportion=0, flag=wx.ALIGN_TOP,border = 10)
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_main.Add(sizer_for_buttons, 0, wx.EXPAND)
        sizer_main.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizerAndFit(sizer_main)



    def on_start(self, event):
        if not self.update_timer.IsRunning() and self.main_frame.setup_parameters_flag:
            self.clear_tables()
            self.report_setup_parameters()
            
            warnings = self.baseline_control.has_warnings()
            if warnings is True:
                self.stop_run_baseline_problems()
            elif warnings == None:
                # Don't show error message for current version. - Yuan Ren
                #self.sidebar.write_to_log('...Serial Communication Error with Baseline Monitor...\n')
                self.stop_run()
            
            self.start_new_run()
            self.setup_data_files(self.run_ctrl_params.start_local_time)
            self.data_ctrl_one.clear_queue()



    def on_clear(self, event):
        if not self.update_timer.IsRunning():
            self.run_ctrl_params.clear_all()
            self.clear_plots()
            self.clear_tables()
            self.main_frame.clear_status_bars()
            self.peak_detector.clear_current_peak_variables()
            self.sidebar.log_window.Clear()
            self.baseline_control.set_warning_flag(False)



    def on_stop(self, event):
        self.stop_run()



    def stop_run(self):
        if self.update_timer.IsRunning():
            self.stop_timer()
            self.main_frame.status_bar_write(1, 'Series Stopped...')
            self.main_frame.status_bar_clear([0, 2, 3])
            self.data_ctrl_one.save_series_data(self.run_ctrl_params.run_cnt, self.series_file, self.series_variables)
            self.data_ctrl_one.close_file(self.series_file)
            self.run_ctrl_params.clear_all()
            self.baseline_control.stop_all()



    def save_peak_data(self, data_param_lst):
        """ This function closes the file first, if open, and then overwrites
        the file with up-to-data peak structure
        """
        if not self.peak_file.closed:
            self.data_ctrl_one.close_file(self.peak_file)
        file = self.data_ctrl_one.peak_data_file_full_path
        self.data_ctrl_one.save_peak_data(file, data_param_lst, self.grid_lst, self.main_frame.m_current, self.main_frame.b_current)



    def report_setup_parameters(self):
        self.sidebar.write_to_log('...Detection Threshold:  %7.2f\n' % self.peak_detector.concentration_threshold)
        self.sidebar.write_to_log('...GC Run Duration:  %7.2f\n' % self.run_ctrl_params.run_duration)
        if self.run_ctrl_params.max_runs == -1:
            self.sidebar.write_to_log('...Number of GC Runs:  infinite\n')
        else:
            self.sidebar.write_to_log('...Number of GC Runs:  %5.0f\n' % self.run_ctrl_params.max_runs)



    def log_start_time_and_start_timer(self):
        self.mark_new_start_time()
        self.start_timer()
        self.sidebar.report_start_time(self.run_ctrl_params.run_cnt,self.run_ctrl_params.start_local_time)
        self.sidebar.report_sequence_type(self.run_ctrl_params.run_cnt,self.run_ctrl_params.seq_lst)


    def start_timer(self):
        delay = 0.1 #  0.1 seconds for normal operation
        self.update_timer.Start(delay)



    def stop_timer(self):
        self.update_timer.Stop()



    def setup_data_files(self, start_time):
        (self.peak_file, self.series_file,) = self.data_ctrl_one.create_files(start_time)
        if self.peak_file == None or self.series_file == None:
            self.main_frame.status_bar_write(0, 'Unable to Setup Files!')
            self.stop_run()



    def clear_plots(self):
        self.figure = self.plt_ctrl_one.clear_plots()
        self.canvas.draw()



    def clear_tables(self):
        self.sidebar.clear_and_reset_tables()



    def setup_wx_timer(self):
        update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_timer, update_timer)
        return update_timer



    def is_at_max_run(self):
        index_shift = 1
        if self.run_ctrl_params.max_runs != -1:
            return self.run_ctrl_params.run_cnt == self.run_ctrl_params.max_runs + index_shift
        else:
            return False



    def is_ready_to_collect_data(self):
        return time.time() - self.run_ctrl_params.start_time > self.baseline_control.furnace_delay



    def collect_new_data_and_report_to_menubar(self):
        if self.is_ready_to_collect_data():
            self.data_ctrl_one.clear_queue()
            if self.main_frame.generate_fake_data:
                self.collect_new_faux_data()
            elif self.main_frame.read_data_file is not None:
                self.collect_new_record_data()
            else:
                self.collect_new_data()
            self.report_data_to_menubar()



    def save_peak_data_and_start_new_run(self):
        data_param_lst = [self.peak_detector.concentration_threshold,
             self.peak_detector.retention_time_tolerance,
             self.run_ctrl_params.run_duration,
             self.run_ctrl_params.max_runs]
        self.save_peak_data(data_param_lst)
        if self.main_frame.generate_fake_data:
            self.faux_run_amplitude_1 = np.random.random()
            self.faux_run_amplitude_2 = np.random.random()
            self.faux_run_amplitude_3 = np.random.random()        ## only for faux data generation
        self.start_new_run()



    def is_done_with_current_run(self):
        if self.main_frame.read_data_file is not None:
            return len(self.time) >= len(self.input_dataset[self.run_ctrl_params.run_cnt]['time'])
        else:
            time_elapsed = time.time() - self.run_ctrl_params.start_time
            return time_elapsed > self.run_ctrl_params.run_duration + self.baseline_control.furnace_delay



    def ready_to_update_plots(self):
        time_elapsed = time.time() - self.run_ctrl_params.plot_timer
        return time_elapsed > self.run_ctrl_params.delay_for_plot_update



    def clear_and_update_plots(self):
        self.run_ctrl_params.plot_timer = time.time()
        self.figure = self.plt_ctrl_one.clear_plots()
        self.figure = self.plt_ctrl_one.update_plots(self.series_variables)
        self.canvas.draw()



    def on_update_timer(self, event):
        if not self.is_at_max_run():
            if not self.is_done_with_current_run():
                self.collect_new_data_and_report_to_menubar()
            else:
                self.save_peak_data_and_start_new_run()
                # Jeff's intention was to reset dynamic threshold after a peak is found rather than end of the run
                # May need to move the line below to if self.peak_detector.current_peak_data_ready:
                self.peak_detector.reset_dynamic_threshold() 
            
            if self.ready_to_update_plots():
                self.clear_and_update_plots() 
            
            try:
                self.peak_detector.detection_algo(self.series_variables)
            except:
                self.peak_detector.clear_current_peak_variables()
                self.run_ctrl_params.run_duration += 15.0
                self.sidebar.write_to_log('...Increased GC Run Duration:  %7.2f\n' % self.run_ctrl_params.run_duration)
            
            if self.peak_detector.current_peak_data_ready:
                self.peak_detector.current_peak_data_ready = False
                self.peak_detector.calculate_isotope_value(self.series_variables)
                # overrides integrated isotope value with calibrated one...
                if self.main_frame.m_current is not None and self.main_frame.b_current is not None:
                    self.peak_detector.current_peak_isotope_value =\
                            self.main_frame.m_current * self.peak_detector.current_peak_isotope_value + self.main_frame.b_current
                self.check_against_retention_library()
                self.sidebar.report_new_data(self.peak_detector.peak_assignment,
                                                self.run_ctrl_params.run_cnt,
                                                self.peak_detector.peak_cnt,
                                                self.peak_detector.current_peak_isotope_value,
                                                self.peak_detector.current_peak_max_concentration,
                                                self.peak_detector.current_peak_retention_time,
                                                self.peak_detector.current_peak_integration_bounds,
                                                self.peak_detector.retention_time_tolerance)
                                                
                self.peak_detector.clear_current_peak_variables()
        else:
            self.stop_run()


    def check_against_retention_library(self):
        for key in self.main_frame.retention_library:
            if abs(self.peak_detector.current_peak_retention_time - float(self.main_frame.retention_library[key])) < self.main_frame.auto_assignment_threshold:
                self.peak_detector.peak_assignment = key



    def collect_new_faux_data(self):
        self.time.append(len(self.time) + 1)
        self.concentration.append(50.0 + self.gaussian_faux(500*self.faux_run_amplitude_1, 20, self.time[-1])
                                + self.gaussian_faux(200*self.faux_run_amplitude_2, 40, self.time[-1])
                                + self.gaussian_faux(150*self.faux_run_amplitude_3, 60, self.time[-1]) + np.random.random())
        self.delta.append((np.random.random()-0.5)*100.0/(np.random.random()+self.concentration[-1]-50.0)**2)



    def gaussian_faux(self, amplitude, center, time):
        return amplitude * np.exp(-(center - time) ** 2 / 15.0)

    def collect_new_record_data(self):
        index = len(self.time)
        self.time.append(float(self.input_dataset[self.run_ctrl_params.run_cnt]['time'][index]))
        self.concentration.append(float(self.input_dataset[self.run_ctrl_params.run_cnt]['concentration'][index]))
        try:
            self.delta.append(float(self.input_dataset[self.run_ctrl_params.run_cnt]['delta'][index]))
        except:
            self.delta.append(np.NaN)

    def collect_new_data(self):
        last_point = -1
        check = 0.002 # fractional
        offset = 0.1 # seconds
        concentration_minimum = 25 # ppm
        delta_threhsold = 10 # permil
        data = self.data_ctrl_one.get_data_from_dml()
        if data != None:
            ### fisrt data point
            if len(self.time) == 0:
                self.run_ctrl_params.plot_start_time = data['time'] - offset
                self.assign_nan_to_lsts(data)
            ### only report delta if concentration is greater than concentration_minimum in ppm
            elif self.concentration[last_point] < concentration_minimum:
                self.assign_nan_to_lsts(data)
            ### normal opeation, but fileter out first data point after methane scan if bad...
            elif self.concentration[last_point] > 4*concentration_minimum and \
                                self.methane_concentration_previous != data['CH4'] and \
                                abs(data['Delta13C']-self.delta[-1]) > delta_threhsold:
                pass
            ### normal operation, but filter out repeat data
            elif abs(self.concentration[last_point] - data['CO2_dry']) > check*data['CO2_dry']:
                self.assign_data_to_lsts(data)
                
            self.methane_concentration_previous = self.methane_concentration    
            self.methane_concentration = data['CH4']
            self.water_concentration = data['H2O']

    def assign_nan_to_lsts(self,data):
        self.time.append(data['time'] - self.run_ctrl_params.plot_start_time)
        self.concentration.append(data['CO2_dry'])
        self.delta.append(np.NaN)
            
    def assign_data_to_lsts(self, data):
        self.time.append(data['time'] - self.run_ctrl_params.plot_start_time)
        self.concentration.append(data['CO2_dry'])
        self.delta.append(data['Delta13C'])



    def report_data_to_menubar(self):
        if self.concentration[-1] > self.peak_detector.concentration_threshold:
            self.main_frame.SetStatusText('CO2 Peak Detected', 0)
        else:
            self.main_frame.SetStatusText('', 0)
        if self.methane_concentration > self.methane_threshold:
            self.sidebar.write_alert_to_log("High methane concentration!!!\n")
            self.main_frame.SetStatusText('Warning...high methane', 0)
        if self.water_concentration > self.water_threshold:
            self.sidebar.write_alert_to_log("High water concentration!!!\n")
            self.main_frame.SetStatusText('Warning...high water', 0)
        self.main_frame.SetStatusText('[CO2]:  %13.2f' % round(self.concentration[-1], 2), 2)
        self.main_frame.SetStatusText('Delta 13C:  %4.2f' % round(self.delta[-1], 2), 3)



    def start_new_run(self):
        first_run = 0
        run_cnt_increment = 1
        reset_to_zero = 0
        infinite_runs = -1
        if not self.is_at_max_run():
            self.peak_detector.peak_cnt = reset_to_zero
            if self.run_ctrl_params.run_cnt > first_run:
                self.data_ctrl_one.save_series_data(self.run_ctrl_params.run_cnt, self.series_file, self.series_variables)
            if self.run_ctrl_params.run_cnt < self.run_ctrl_params.max_runs or self.run_ctrl_params.max_runs == infinite_runs:
                self.run_ctrl_params.run_cnt += run_cnt_increment
                self.clear_plots()
                self.log_signal_sent()
                self.sidebar.add_row_to_tables(self.run_ctrl_params.run_cnt)
                self.log_start_time_and_start_timer()
                self.baseline_control.trigger_gc_sequence(self.run_ctrl_params.next_sequence())
            else:
                self.stop_run()
            self.clear_series_variables()



    def log_signal_sent(self):
        self.sidebar.write_to_log('GC Run %i Started...\n' % self.run_ctrl_params.run_cnt)
        self.main_frame.SetStatusText('Signal sent to start GC run %i...' % self.run_ctrl_params.run_cnt, 1)



    def mark_new_start_time(self):
        self.run_ctrl_params.start_time = time.time()
        self.run_ctrl_params.start_asctime = time.asctime()
        self.run_ctrl_params.start_local_time = time.localtime()
        self.run_ctrl_params.plot_timer = self.run_ctrl_params.start_time



    def clear_series_variables(self):
        (self.time, self.concentration, self.delta,) = self.data_ctrl_one.initialize_series_data()
        self.series_variables = [self.time, self.concentration, self.delta]



    def clear_peak_variable(self):
        (self.peak_isotope, self.peak_concentration, self.peak_retention, self.bounds,) = self.data_ctrl_one.initialize_data_peak_data()



    def stop_run_baseline_problems(self):
        self.sidebar.write_to_log('...Baseline Warning Detected... Data Collected Stopped...\nCheck Baseline Status...\n')
        self.stop_run()




#+++ okay decompyling PlotAreaOne.pyc 
# decompiled 1 files: 1 okay, 0 failed, 0 verify failed
# 2015.06.02 11:02:41 Pacific Daylight Time
