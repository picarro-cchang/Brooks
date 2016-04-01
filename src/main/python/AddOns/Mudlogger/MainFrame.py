import wx
import os
import csv
import time
from Page import Page
from SetupParameters import SetupParameters
from Calibration import Calibration
from IsotopeScalingFrame import IsotopeScaling
from Host.Common.CustomConfigObj import CustomConfigObj

class IsotopeScalingFrame(IsotopeScaling):
    def __init__(self, *args, **kwds):
        parameters = kwds.pop("parameters")
        IsotopeScaling.__init__(self, *args, **kwds)
        self.userOK = False
        if parameters is not None:
            self.radio_scaling.SetValue(True)
            self.scalingControl(True)
            self.txtScale.SetValue(str(parameters[0]))
            self.txtOffset.SetValue(str(parameters[1]))
    
    def scalingControl(self, flag):
        self.txtScale.Enable(flag)
        self.txtOffset.Enable(flag)
        self.btnLoadFile.Enable(flag)
    
    def onLoadParameters(self, event):
        fd = wx.FileDialog(None, "Choose a Reprocessed Series where calibration parameters will be loaded from",
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                       wildcard="csv files (*.csv)|*.csv")
        if fd.ShowModal() == wx.ID_OK:
            file_name = fd.GetPath()
            with open(file_name, 'r') as f:
                while True:
                    line = f.readline()
                    if len(line) == 0:
                        break
                    if "CalibrationParameters" in line:
                        items = line.strip().split(",")
                        self.txtScale.SetValue(items[1])
                        self.txtOffset.SetValue(items[2])
                        break
                        
    def onNoScaling(self, event):
        self.scalingControl(False)
        
    def onScaling(self, event):
        self.scalingControl(True)
                        
    def onOK(self, event):
        self.userOK = True
        self.Close()
        
    def onCancel(self, event):
        self.Close()
    
class MainFrame(wx.Frame):
    def __init__(self, parent, configFile, generate_fake_data=False, read_data_file=None, test_peak_detection=False):
        wx.Frame.__init__(self, parent)
        flag_for_page_one = 1
        flag_for_page_two = 2
        
        self.setup_parameters_flag = False
        self.generate_fake_data = generate_fake_data
        self.read_data_file = read_data_file
        self.test_peak_detection = test_peak_detection
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            print "Configuration file not found: %s" % configFile
            import sys
            sys.exit()
        
        self.notebook = wx.Notebook(self)
        self.page_one = Page(self.notebook,self,flag_for_page_one)
        self.page_two = Page(self.notebook,self,flag_for_page_two)

        self.notebook.AddPage(self.page_one, 'Real Time')
        self.notebook.AddPage(self.page_two, 'Logged Data')

        self.create_status_bar()
        self.write_frame_title('Picarro: GC Combustion Pulse Processing Software')
        self.create_menu_bar()
        
        self.setup_defaults()
        self.data_loaded_flag = False
        self.Show(True)

    def create_status_bar(self):
        self.status_bar_number_of_areas = 4
        status_bar_relative_widths_of_areas = [-2,-6,-2,-2]
        status_bar_size = (1400,800)

        self.CreateStatusBar(self.status_bar_number_of_areas)
        self.SetStatusWidths(status_bar_relative_widths_of_areas)
        self.SetSize(status_bar_size)

        for i in range(self.status_bar_number_of_areas):
            self.status_bar_write(i,'')
        self.status_bar_write(1,'Welcome to the Picarro GC Combustion Pulse Processing Software')
        
    def status_bar_write(self,bar_index,text_string):
        self.SetStatusText(text_string, bar_index)
        
    def status_bar_clear(self,index_list):
        for index in index_list:
            self.status_bar_write(index,'')

    def clear_status_bars(self):
        shift_for_indexing = 1
        for idx in range(0,self.status_bar_number_of_areas-shift_for_indexing):
            self.status_bar_write(idx,'')

    def write_frame_title(self,text_string):
        self.SetTitle(text_string)

    def create_menu_bar(self):
        
        menu_bar = wx.MenuBar()

        menu_file = wx.Menu()
        menu_file_exit = menu_file.Append(wx.ID_EXIT, '&Exit', 'Exit')
        self.Bind(wx.EVT_MENU, self.on_exit, menu_file_exit)

        menu_setup = wx.Menu()
        menu_setup_data_collection_options = menu_setup.Append(wx.ID_SETUP, 'Setup &Chromatograph Runs', 'Parameter setup for chromatography runs')
        self.Bind(wx.EVT_MENU, self.on_setup_runs, menu_setup_data_collection_options)
        menu_setup_peak_IDs = menu_setup.Append(wx.ID_ANY, 'Setup &Peak Identifications', 'Peak IDs for auto assignments')
        self.Bind(wx.EVT_MENU, self.on_setup_IDs, menu_setup_peak_IDs)
        menu_scale_isotope_data = menu_setup.Append(wx.ID_ANY, '&Isotope Data scaling', 'Scale isocope data based on selected calibration parameters')
        self.Bind(wx.EVT_MENU, self.on_scale_isotope, menu_scale_isotope_data)

        menu_process = wx.Menu()
        menu_process_open_file = menu_process.Append(wx.ID_OPEN, '&Load Chromatograph Series','Load chromatograph series')
        self.Bind(wx.EVT_MENU, self.on_load_file, menu_process_open_file)
        menu_process_clear = menu_process.Append(wx.ID_CLOSE, '&Clear Chromatograph Series','Clear chromatograph series')
        self.Bind(wx.EVT_MENU, self.on_clear, menu_process_clear)
        menu_process_cal = menu_process.Append(wx.ID_ANY, '&Calibrate Isotope Data', 'Calibrate Isotope Data')
        self.Bind(wx.EVT_MENU, self.on_calibrate, menu_process_cal)
        menu_process_save_file = menu_process.Append(wx.ID_SAVEAS, '&Save As Reprocessed Series','Save modified changes in CSV formate')
        self.Bind(wx.EVT_MENU, self.on_save_as, menu_process_save_file)

        menu_bar.Append(menu_file, '&Exit Program')
        menu_bar.Append(menu_setup, '&Setup Runs')
        menu_bar.Append(menu_process, '&Process Data')

        self.SetMenuBar(menu_bar)

    #def on_new_file(self, event):
    #    pass
        
    def on_calibrate(self,event):
        if self.data_loaded_flag:
            dlg = Calibration(self)
            dlg.Show(True)

    def on_exit(self, event):
        if not self.page_one.plot_area.update_timer.IsRunning():
            self.Destroy()
        else:
            wx.MessageBox('Stop Run to Exit Program', 'Error', wx.OK | wx.ICON_ERROR)

    def on_setup_runs(self, event):
        dlg = SetupParameters(self)
        dlg.Show(True)

    def setup_defaults(self):
        self.retention_library={'Methane':'40'}
        self.standards_library={'Standard_1':['-25.0','3,4,5'],
                                'Standard_2':['-69.0','8,9,10'], 
                                'Standard_3':['','']}
        # if a peak is within this threshold in seconds to a
        # previously recorded peak, then it will be assigned
        # to that previous peak...
        self.auto_assignment_threshold = 10
        self.b,self.m = None, None ###Values used for calibration 
        self.b_current, self.m_current = None, None
    
    def on_setup_IDs(self, event):
        self.auto_assignment_threshold = 10 #seconds
        self.retention_library={}
        dlg = self.setup_IDs(self)
        dlg.Show()
        
    def on_scale_isotope(self, event):
        if self.m_current is not None and self.b_current is not None:
            parameters = [self.m_current, self.b_current]
        else:
            parameters = None
        sf = IsotopeScalingFrame(None, wx.ID_ANY, "", parameters=parameters)
        sf.ShowModal()
        if sf.userOK:
            try:
                if sf.radio_scaling.GetValue():
                    self.m_current = float(sf.txtScale.GetValue())
                    self.b_current = float(sf.txtOffset.GetValue())
                else:
                    self.m_current = None
                    self.b_current = None
            except:
                pass
        sf.Destroy()

    def on_load_file(self, event):
        integration_bounds_index = 3
        if not self.data_loaded_flag:
            dlg = wx.FileDialog(self,'Choose a Chromatograph Series', 
                                '', '','*.csv',wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                file_name = dlg.GetFilename()
                directory_name = dlg.GetDirectory()
                self.parameter_file_path = '\\'.join((directory_name,file_name))
                try:
                    self.open_and_read_parameter_file()
                    self.open_and_read_series_file()

                    self.data_loaded_flag = True
                    self.page_two.plot_area.add_parameter_data_to_table()
                    self.status_bar_write(1,'File Opened: %s'%file_name)
                    if self.page_two.plot_area.page_selection != \
                        integration_bounds_index:
                        self.page_two.plot_area.update_plot_with_data()
                except:
                    wx.MessageBox('Problem Opening Series File. File is either corrupt or emtpy.',
                              'Error', wx.OK | wx.ICON_ERROR)
                dlg.Destroy()

    def open_and_read_parameter_file(self):
        first_row_flag = True
        self.parameter_file_dict = {}
        self.keys = []
        with open(self.parameter_file_path,'r') as parameter_file:
            reader = csv.reader(parameter_file,delimiter=',')
            for line in reader:
                if first_row_flag:
                    for key in line:
                        self.keys.append(key)
                        self.parameter_file_dict[key]=[]
                    first_row_flag = False
                else:
                    if line[0] != 'CalibrationParameters:':
                        for i,data in enumerate(line):
                            self.parameter_file_dict[self.keys[i]].append(data)
                    else:
                        self.m, self.b = float(line[1]), float(line[2])
                        self.m_current, self.b_current = self.m, self.b
        self.page_two.plot_area.copy_p_data_over(self.parameter_file_dict,
                                                 self.keys)

    def open_and_read_series_file(self):
        time_index = 0
        concentration_index = 1
        isotope_index = 2
        self.page_two.plot_area.series_data = \
            self.page_two.plot_area.data_ctrl_two.initialize_data_trace()
        data_lines_per_series = 4
        self.series_file_dict = {}
        
        p_file = self.parameter_file_path
        self.series_file_path = \
            p_file.replace('peak_data.csv','time_series.dat')
            
        if not os.path.isfile(self.series_file_path):
            self.series_file_path = \
                p_file[:p_file.find('_reprocessed_')]+ 'time_series.dat'
        with open(self.series_file_path,'r') as series_file:
            reader = csv.reader(series_file,delimiter='\t')
            for i,line in enumerate(reader):
                line = [float(x) for x in line]
                if self.data_line_is_run_time(i,data_lines_per_series):
                    self.page_two.plot_area.series_data[time_index].append(line)
                elif self.data_line_is_run_conc(i,data_lines_per_series):
                    self.page_two.plot_area.series_data[concentration_index].append(line)
                elif self.data_line_is_run_iso(i,data_lines_per_series):
                    self.page_two.plot_area.series_data[isotope_index].append(line)

    def data_line_is_run_time(self,line,check):
        return line%check == 1
    def data_line_is_run_conc(self,line,check):
        return line%check == 2
    def data_line_is_run_iso(self,line,check):
        return line%check == 3

    def on_clear(self, event):
        if self.data_loaded_flag:
            self.data_loaded_flag = False
            self.page_two.plot_area.data_in_table_flag = False
            self.clear_data_and_parameters()
            self.status_bar_write(1,'Data Cleared')

            self.page_two.plot_area.figure =\
                    self.page_two.plot_area.plt_ctrl_two.clear_plot_data()
            self.page_two.plot_area.clear_selection()
            self.page_two.plot_area.canvas.draw()
            self.page_two.sidebar.reprocess_area.initialize_string_items()
            self.page_two.sidebar.reprocess_area.reprocessed_data_flag = False

    def clear_data_and_parameters(self):
        self.page_two.plot_area.clear_data_and_reset_flags()
        self.page_two.sidebar.clear_and_reset_tables()
        self.b, self.m = None, None
        self.b_current, self.m_current = None, None

    def on_save_as(self, event):
        ### save peak data in new file
        m_to_file = None
        b_to_file = None
        file_name = self.parameter_file_path
        current_date = time.strftime("%Y_%b_%d__%H%M%S", time.localtime())
        extension = 'peak_data.csv'
        file_addendum = '_reprocessed_' + current_date + '_' + extension
        file_name = file_name.replace(extension,file_addendum)
        
        grid_lst = [self.page_two.sidebar.page_one.data_grid,
                    self.page_two.sidebar.page_two.data_grid,
                    self.page_two.sidebar.page_three.data_grid,
                    self.page_two.sidebar.page_four.data_grid]
        
        if self.m_current != None:
            m_to_file = self.m_current
            b_to_file = self.b_current
        self.page_one.plot_area.data_ctrl_one.save_peak_data(file_name,'XXXX',grid_lst,m_to_file,b_to_file)
                
    class setup_IDs(wx.Frame):
        def __init__(self,main_frame):
            self.main_frame = main_frame
            size = (300,445)
            id_size = (75,-1)
            number_of_peaks = 10+1
            number_of_columns = 3

            title = 'Setup Peak IDs'
            wx.Frame.__init__(self,self.main_frame,title=title,size=size)
            self.setup_IDs_panel = wx.Panel(self,-1)
            grid_sizer = wx.GridSizer(number_of_peaks,
                                      number_of_columns,
                                      vgap = 5, hgap = 5)
                                      
            empty_text   = wx.StaticText(self.setup_IDs_panel,
                                     -1,
                                     '',
                                     size =(-1,-1))
                                     
            label_one = wx.StaticText(self.setup_IDs_panel,
                                     -1,
                                     'Peak IDs',
                                     size =(-1,-1))
                                    
            label_two = wx.StaticText(self.setup_IDs_panel,
                                     -1,
                                     'Retention Time\n    (seconds)',
                                     size =(-1,-1))
          
            self.cb_0 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_1 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_2 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_3 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_4 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_5 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_6 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_7 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_8 = wx.CheckBox(self.setup_IDs_panel,-1)
            self.cb_9 = wx.CheckBox(self.setup_IDs_panel,-1)
            
            self.id_0 = wx.TextCtrl(self.setup_IDs_panel, -1, value = 'Methane', size = id_size)
            self.id_1 = wx.TextCtrl(self.setup_IDs_panel, -1, value = 'Ethane', size = id_size)
            self.id_2 = wx.TextCtrl(self.setup_IDs_panel, -1, value = 'Propane', size = id_size)
            self.id_3 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.id_4 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.id_5 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.id_6 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.id_7 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.id_8 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.id_9 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)

            self.rt_0 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '20.0', size = id_size)
            self.rt_1 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '40.0', size = id_size)
            self.rt_2 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '60.0', size = id_size)
            self.rt_3 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.rt_4 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.rt_5 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.rt_6 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.rt_7 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.rt_8 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)
            self.rt_9 = wx.TextCtrl(self.setup_IDs_panel, -1, value = '', size = id_size)

            self.cb_lst = [empty_text,self.cb_0,self.cb_1,self.cb_2,self.cb_3,self.cb_4,
                      self.cb_5,self.cb_6,self.cb_7,self.cb_8,self.cb_9]
            self.id_lst = [label_one,self.id_0,self.id_1,self.id_2,self.id_3,self.id_4,
                      self.id_5,self.id_6,self.id_7,self.id_8,self.id_9]
            self.rt_lst = [label_two,self.rt_0,self.rt_1,self.rt_2,self.rt_3,self.rt_4,
                      self.rt_5,self.rt_6,self.rt_7,self.rt_8,self.rt_9]

            for i,cb in enumerate(self.cb_lst):
                grid_sizer.Add(self.cb_lst[i],0,wx.ALIGN_CENTER)
                grid_sizer.Add(self.id_lst[i],0,wx.ALIGN_CENTER)
                grid_sizer.Add(self.rt_lst[i],0,wx.ALIGN_CENTER)
            
            sizer_top = wx.BoxSizer(wx.VERTICAL)
            sizer_top.Add(grid_sizer, 0, wx.EXPAND | wx.ALIGN_LEFT)
            
            button_cancel = wx.Button(self.setup_IDs_panel, -1, label='Cancel')
            button_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
            button_ok = wx.Button(self.setup_IDs_panel, -1, label='OK')
            button_ok.Bind(wx.EVT_BUTTON, self.on_ok)

            sizer_bottom = wx.BoxSizer(wx.HORIZONTAL)
            sizer_bottom.Add(button_ok, -1, wx.ALIGN_RIGHT)
            sizer_bottom.Add(button_cancel, -1, wx.ALIGN_RIGHT)

            sizer = wx.BoxSizer(wx.VERTICAL)
            
            text_string = 'Check Boxs to Include the Peak IDs\n'
            text_one = wx.StaticText(self.setup_IDs_panel,
                                     -1,
                                     text_string,
                                     size =(-1,-1))
 
            text_space =  wx.StaticText(self.setup_IDs_panel,
                                     -1,
                                     '',
                                     size =(-1,10))
                                     
            sizer.Add(text_one, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
            sizer.Add(sizer_top, 0, wx.ALIGN_TOP | wx.EXPAND)
            sizer.Add(text_space, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
            sizer.Add(sizer_bottom, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)

            self.setup_IDs_panel.SetSizer(sizer, wx.EXPAND)

        def on_cancel(self,event):
            self.Destroy()

        def on_ok(self,event):
            static_text = 0
            error_flag = False
            self.clear_library()
            for i,check_box in enumerate(self.cb_lst):
                if i != static_text and check_box.IsChecked():
                    key = self.id_lst[i].GetValue()
                    retention = self.rt_lst[i].GetValue()
                    if key != '' and retention != '':
                        try:
                            retention = float(retention)
                            self.main_frame.retention_library[key] = retention
                        except ValueError:
                            wx.MessageBox('Retention Time must be Numeric',
                                              'Error', wx.OK | wx.ICON_ERROR)
                            error_flag = True
            if not error_flag:
                self.Destroy()
            

        def clear_library(self):
            self.main_frame.retention_library = {}

