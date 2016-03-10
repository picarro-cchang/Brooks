"""Calibraion module is used to calibrate the integrated isotope data.  The
module is called when the user clicks the calibrate pull down menu option."""
import wx
import numpy as np
import pylab as pylab
import matplotlib as mpl
import matplotlib.pyplot as plt

class Calibration(wx.Frame):
    def __init__(self, main_frame):
        self.main_frame = main_frame
        size = (325, 275)
        id_size = (75, -1)
        title_size = (100, -1)
        number_of_standards = 4
        number_of_columns = 3
        isotope_index = 0
        range_index = 1
        self.calibration_species = None
        self.calibration_lst = None
        self.calibration_dict = None
        title = 'Calibration of Isotope Data'
        wx.Frame.__init__(self, self.main_frame, title=title, size=size)
        self.setup_ids_panel = wx.Panel(self, -1)
        grid_sizer = wx.GridSizer(number_of_standards,
                                  number_of_columns,
                                  vgap=5, hgap=5)
        self.st_title = wx.StaticText(self.setup_ids_panel, -1, '', size=id_size)
        self.st_0 = wx.StaticText(self.setup_ids_panel, -1, 'Standard 1:', size=id_size)
        self.st_1 = wx.StaticText(self.setup_ids_panel, -1, 'Standard 2:', size=id_size)
        self.st_2 = wx.StaticText(self.setup_ids_panel, -1, 'Standard 3:', size=id_size)
        self.id_title = wx.StaticText(self.setup_ids_panel, -1,
                                      u'Std \u03B4\u00B9\u00B3C Value', size=title_size)
        self.id_0 = wx.TextCtrl(self.setup_ids_panel, -1,
                                value=self.main_frame.standards_library['Standard_1'][isotope_index],
                                size=id_size)
        self.id_1 = wx.TextCtrl(self.setup_ids_panel, -1,
                                value=self.main_frame.standards_library['Standard_2'][isotope_index],
                                size=id_size)
        self.id_2 = wx.TextCtrl(self.setup_ids_panel, -1,
                                value=self.main_frame.standards_library['Standard_3'][isotope_index],
                                size=id_size)
        self.rg_title = wx.StaticText(self.setup_ids_panel, -1,
                                      'Std Run #', size=title_size)
        self.rg_0 = wx.TextCtrl(self.setup_ids_panel, -1,
                                value=self.main_frame.standards_library['Standard_1'][range_index],
                                size=id_size)
        self.rg_1 = wx.TextCtrl(self.setup_ids_panel, -1,
                                value=self.main_frame.standards_library['Standard_2'][range_index],
                                size=id_size)
        self.rg_2 = wx.TextCtrl(self.setup_ids_panel, -1,
                                value=self.main_frame.standards_library['Standard_3'][range_index],
                                size=id_size)

        self.st_lst = [self.st_title, self.st_0, self.st_1, self.st_2]
        self.id_lst = [self.id_title, self.id_0, self.id_1, self.id_2]
        self.rg_lst = [self.rg_title, self.rg_0, self.rg_1, self.rg_2]
        for i in range(len(self.st_lst)):
            grid_sizer.Add(self.st_lst[i], 0, wx.ALIGN_CENTER)
            grid_sizer.Add(self.id_lst[i], 0, wx.ALIGN_CENTER)
            grid_sizer.Add(self.rg_lst[i], 0, wx.ALIGN_CENTER)
        sizer_top = wx.BoxSizer(wx.VERTICAL)
        sizer_top.Add(grid_sizer, 0, wx.EXPAND)
        button_cancel = wx.Button(self.setup_ids_panel, -1, label='Cancel')
        button_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        button_ok = wx.Button(self.setup_ids_panel, -1, label='OK')
        button_ok.Bind(wx.EVT_BUTTON, self.on_ok)

        number_of_columns =\
            self.main_frame.page_two.sidebar.page_one.data_grid.GetNumberCols()
        label_lst = []
        first_two_columns = 1
        for i in range(number_of_columns):
            ### skips the time and sequence column as input to calibration options
            if i > first_two_columns:
                label_lst.append(str(self.main_frame.page_two.sidebar.page_one.data_grid.GetColLabelValue(i)))

        self.label_choice = wx.Choice(self.setup_ids_panel, -1, choices=label_lst)
        self.Bind(wx.EVT_CHOICE, self.event_choice, self.label_choice)

        text_selection = wx.StaticText(self.setup_ids_panel, -1,
                                       'Select Species for Calibration:',
                                       size=(150, -1))

        sizer_column_selection = wx.BoxSizer(wx.HORIZONTAL)
        sizer_column_selection.Add(wx.StaticText(self.setup_ids_panel,
                                                 -1, '', size=(10, -1)))
        sizer_column_selection.Add(text_selection, 0, wx.ALIGN_LEFT)
        sizer_column_selection.Add(self.label_choice, 0, wx.ALIGN_LEFT | wx.EXPAND)

        sizer_buttom = wx.BoxSizer(wx.HORIZONTAL)
        sizer_buttom.Add(button_ok, -1, wx.ALIGN_RIGHT)
        sizer_buttom.Add(button_cancel, -1, wx.ALIGN_RIGHT)

        sizer = wx.BoxSizer(wx.VERTICAL)

        text_string = 'Input Isotope Values and Run Ranges for Standards\n'

        text_buffer = wx.StaticText(self.setup_ids_panel, -1, '', size=(-1, -1))
        text_one = wx.StaticText(self.setup_ids_panel, -1, text_string, size=(-1, -1))
        text_two = wx.StaticText(self.setup_ids_panel, -1, '', size=(-1, 10))
        text_three = wx.StaticText(self.setup_ids_panel, -1, '', size=(-1, 10))

        sizer.Add(text_buffer, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        sizer.Add(text_one, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        sizer.Add(sizer_top, 0, wx.ALIGN_TOP | wx.EXPAND)
        sizer.Add(text_two, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        sizer.Add(sizer_column_selection, 0, wx.ALIGN_BOTTOM | wx.ALIGN_LEFT)
        sizer.Add(text_three, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)
        sizer.Add(sizer_buttom, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTER)

        self.setup_ids_panel.SetSizer(sizer, wx.EXPAND)

    def event_choice(self, event):
        self.calibration_species = event.GetSelection()

    def on_cancel(self, event):
        self.Destroy()

    def on_ok(self, event):
        self.read_and_save_calibration_parameters()


    def calculate_calibration(self):
        '''calculate the linear regression using the user chosen calibration data'''
        shift_index = 1
        isotope_index = 0
        if self.main_frame.data_loaded_flag:
            empty_list = ''
            skip_first_row = 0
            self.calibration_dict = {}
            for sample in self.calibration_lst:
                self.calibration_dict[sample] = []
                # print 'sample: ', sample

            ### looping over calibration samples
            for i in range(len(self.st_lst)):
                ### skipping the first point, since it is just a padded value of ''
                if i != skip_first_row:
                    try:
                        ### get user-input isotope value of the calibration gas
                        isotope_value = float(self.id_lst[i].GetValue())
                        # print 'isotope_value: ', isotope_value
                        ### how many injections are of this calibration gas type
                        standard_range = self.rg_lst[i].GetValue()
                        if standard_range != empty_list:
                            ### split input into a list that will be looped over
                            range_split = standard_range.split(',')
                            for value in range_split:
                                measured =\
                                    self.main_frame.page_two.plot_area.peak_data[isotope_index][self.calibration_species+1][int(value)-shift_index]
                                # print 'measured: ', measured
                                if not np.isnan(float(measured)):
                                    self.calibration_dict[str(value.strip())] =\
                                        [measured, isotope_value]
                    except:
                        pass

            self.plot_calibration()
            self.calibrate_all_data()
            self.update_plot_and_reprocessing_area()

    def calibrate_all_data(self):
        '''calibrates all data using the optimal linear regression
        from the calculate_calibration method'''
        isotope_index = 0
        index_shift = 1
        skip_first_two_columns = 2
        number_of_columns =\
            self.main_frame.page_two.sidebar.page_one.data_grid.GetNumberCols()
        number_of_rows =\
            self.main_frame.page_two.sidebar.page_one.data_grid.GetNumberRows()
        ### copies over the data from the calibration in the event
        ### that no previous calibration was performed previously,
        ### i.e. the intercept and slope are not recorded in the peak data file.
        if self.main_frame.b_current == None and self.main_frame.m_current == None:
            self.main_frame.b_current = self.main_frame.b
            self.main_frame.m_current = self.main_frame.m
        else:
            ### logic necessary for recursive calibrations...
            ### since the series data remains raw only the peak
            ### integrated data is ever re-calibrated... this is
            ### necessary to include nested linear fits in the
            ### manor... these parameters are used in the plot_area_two
            ### in the reprocess_data_with_new_bounds...
            self.main_frame.b_current =\
                self.main_frame.b_current*self.main_frame.m + self.main_frame.b
            self.main_frame.m_current = self.main_frame.m_current*self.main_frame.m
        for i in range(skip_first_two_columns, number_of_columns):
            for j in range(number_of_rows):
                try:
                    old_value =\
                        self.main_frame.page_two.plot_area.peak_data[isotope_index][i-index_shift][j]
                    if not np.isnan(float(old_value)):
                        calibrated_value =\
                            self.main_frame.m*float(old_value)+self.main_frame.b
                        self.main_frame.page_two.sidebar.page_one.data_grid.SetCellValue(j, i, str(round(calibrated_value, 2)))
                        self.main_frame.page_two.plot_area.peak_data[isotope_index][i-index_shift][j] =\
                            calibrated_value
                except ValueError:
                    pass
        
    def update_plot_and_reprocessing_area(self):
        self.main_frame.page_two.plot_area.update_plot_with_data()
        self.main_frame.page_two.sidebar.reprocess_area.initialize_string_items()

        
    def plot_calibration(self):
        dpi = 150
        size = 6
        mpl.rcParams['toolbar'] = 'None'
        fig = plt.figure(dpi=dpi, facecolor='white', frameon=True, figsize=(4, 4))
        ax_one = fig.add_subplot(111)
        ax_one.set_axis_bgcolor('white')
        ax_one.set_ylabel('Standard $\delta^{13}$C', size=size)
        ax_one.set_xlabel('Measured $\delta^{13}$C', size=size)
        pylab.setp(ax_one.get_xticklabels(), fontsize=size)
        pylab.setp(ax_one.get_yticklabels(), fontsize=size)
        x = []
        y = []
        for key in self.calibration_dict:
            try:
                x.append(self.calibration_dict[key][0])
                y.append(self.calibration_dict[key][1])
            except IndexError:
                pass
        plt.plot(x, y, 'o')
        ###get current slope and intercept for calibration
        try:
            self.main_frame.m, self.main_frame.b = np.polyfit(x, y, 1)
            plt.plot(x, np.asarray(x)*self.main_frame.m+self.main_frame.b, 'k')
            SS_residual =\
                sum([(y[i]-(self.main_frame.m*x[i]+self.main_frame.b))**2 for i in range(len(x))])
            y_average = np.average(y)
            SS_total = sum([(y[i]-y_average)**2 for i in range(len(x))])
            r2 = 1.0-SS_residual/SS_total
            plt.text(0.5, 0.95,
                     'Calibration: %.3f$\delta^{13}$C + %.3f\t\tR$^2$=%.3f' %(self.main_frame.m,self.main_frame.b,r2),
                     horizontalalignment='center',
                     verticalalignment='center',
                     transform = ax_one.transAxes,
                     fontsize = 6)
            fig.show()
        except:
            wx.MessageBox('Calibration problem: Please check data.',
                          'Error', wx.OK | wx.ICON_ERROR)
        
    def read_and_save_calibration_parameters(self):
        skip_first_row = 0
        index_shift = 1
        error_flag = False
        unique_flag = True
        isotope_index = 0
        empty_list = ''
        all_values_in_row_range = 0
        one_data_point = 1
        key_lst = ['Standard_1', 'Standard_2', 'Standard_3']
        number_of_cal_points = 0
        for i in range(len(self.st_lst)):
            if i != skip_first_row:
                isotope_value = self.id_lst[i].GetValue()
                standard_range = self.rg_lst[i].GetValue()
                ### if calibration runs are not empty,
                ### the isotope calibration value is recorded.
                if standard_range != empty_list:
                    try:
                        isotope_value = float(isotope_value)
                        self.main_frame.standards_library[key_lst[i-index_shift]][isotope_index] = str(isotope_value)
                    except ValueError:
                        wx.MessageBox('Isotope Values must be Numeric',
                                      'Error', wx.OK | wx.ICON_ERROR)
                        error_flag = True
                    try:
                        range_split = standard_range.split(',')
                        number_of_cal_points += len(range_split)
                    except ValueError:
                        wx.MessageBox('Input Syntax Error',
                                      'Error', wx.OK | wx.ICON_ERROR)
                        error_flag = True
                else:
                    self.main_frame.standards_library[key_lst[i-index_shift]][isotope_index] = ''
        if not error_flag:
            ### Checks to see if calibration samples are in the data set range
            number_of_rows = self.main_frame.page_two.sidebar.page_one.data_grid.GetNumberRows()
            if sum([int(value) > number_of_rows or int(value) < 1 for value in range_split]) != all_values_in_row_range:
                wx.MessageBox('Calibration Selection is not Available',
                           'Error', wx.OK | wx.ICON_ERROR)
                error_flag = True
        if number_of_cal_points == one_data_point:
            wx.MessageBox('Calibration Selection should be Expanded',
                          'Error', wx.OK | wx.ICON_ERROR)
            error_flag = True

        if not error_flag:
            unique_flag = self.check_for_unique_indices()

        if not unique_flag:
            wx.MessageBox('Standard Runs must be Unique',
                          'Error', wx.OK | wx.ICON_ERROR)

        if not error_flag and unique_flag and self.calibration_species != None:
            self.calculate_calibration()
            self.Destroy()


    def check_for_unique_indices(self):
        range_index = 1
        temp_copy_of_data = []
        for key in self.main_frame.standards_library:
            temp = self.main_frame.standards_library[key][range_index]
            if temp != '':
                temp_copy_of_data.append(self.main_frame.standards_library[key][range_index])
        temp_copy_of_data = [x.split(',') for x in temp_copy_of_data]
        self.calibration_lst = []
        for i in temp_copy_of_data:
            for j in i:
                self.calibration_lst.append(j.strip())
        return len(set(self.calibration_lst)) == len(self.calibration_lst)