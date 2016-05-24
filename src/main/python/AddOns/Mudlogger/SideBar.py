import wx
import wx.grid
import time
import numpy as np

class SideBar(wx.Panel):
    def __init__(self, parent, main_frame, flag):
        wx.Panel.__init__(self, parent)
        
        self.page = parent
        self.main_frame = main_frame
        
        flag_for_page_one = 1
        flag_for_page_two = 2

        self.SetBackgroundColour('white')

        self.notebook = wx.Notebook(self)
        self.page_one = Table(self.notebook,self)
        self.notebook.AddPage(self.page_one, 'Isotope Data, permil')
        self.page_two = Table(self.notebook,self)
        self.notebook.AddPage(self.page_two, 'Concentration Data, ppm')
        self.page_three = Table(self.notebook,self)
        self.notebook.AddPage(self.page_three, 'Retention Time, seconds')
        self.page_four = Table(self.notebook,self)
        self.notebook.AddPage(self.page_four, 'Integration Bounds')

        self.auto_size_columns()
        
        self.statistics = wx.TextCtrl(
                self, wx.ID_ANY, size=(-1,-1),
                style=wx.EXPAND)
        self.statistics.SetBackgroundColour((245,245,245))
        self.statistics.AppendText('Statistics:')
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        sizer.Add(self.statistics, 0, wx.EXPAND)

        if flag == flag_for_page_one:
            self.log_window = wx.TextCtrl(
                self, wx.ID_ANY, size=(100,200),
                style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
            sizer.Add(self.log_window, 0, wx.EXPAND)
            self.write_to_log(
                'Log...Session Started at...%s\n'%time.strftime(
                    '%Y_%b_%d__%H%M%S',time.localtime()))
        elif flag == flag_for_page_two:
            self.reprocess_area = ReprocessArea(self)
            sizer.Add(self.reprocess_area,0,wx.EXPAND)
        self.SetSizer(sizer)
        
        #hardcoded as defined by GC requirements
        self.sequence_dictionary = {1:'SEQ1',2:'SEQ2',3:'SEQ3',4:'SEQ4'}
    
    def write_to_log(self,text_str):
        self.log_window.WriteText(text_str)
        
    def write_alert_to_log(self, text_str):
        self.log_window.SetDefaultStyle(wx.TextAttr(wx.RED, wx.WHITE))
        self.log_window.AppendText(text_str)
        self.log_window.SetDefaultStyle(wx.TextAttr(wx.BLACK, wx.WHITE))

    def add_row_to_tables(self,run_cnt):
        number_of_rows_to_add = 1
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        if self.page_one.data_grid.GetNumberRows() < run_cnt:
            for page in page_lst:
                page.data_grid.AppendRows(number_of_rows_to_add)

        self.auto_size_columns()

    def add_rows_to_tables(self,number_of_runs):
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            number_of_rows_to_add = number_of_runs - page.data_grid.GetNumberRows()
            page.data_grid.AppendRows(number_of_rows_to_add)

    def add_cols_to_tables(self,number_of_cols_to_add):
        skip_static_col = 2
        shift = 1
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.InsertCols(skip_static_col,number_of_cols_to_add-skip_static_col+shift)

    def set_cols_labels(self,labels):
        skip_static_col = 2
        shift = 1
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for i,page in enumerate(page_lst):
            for j in range(skip_static_col,page.data_grid.GetNumberCols()):
                page.data_grid.SetColLabelValue(j,labels[j-skip_static_col+shift])
    
    def add_data_to_tables_page_two(self,data_dict,ordered_keys,number_of_peaks,
                               non_related_keys,related_keys_per_peak,
                               number_of_runs):
        time_key_index = 1
        sequence_key_index = 2
        time_column_index = 0
        sequence_column_index = 1 
        index_shift = 1
        
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for i,page in enumerate(page_lst):
            number_of_rows = len(data_dict[ordered_keys[time_key_index]])
            number_of_cols = page.data_grid.GetNumberCols()
            for j in range(number_of_rows):
                for k in range(number_of_cols):
                    if k == time_column_index:
                        key = ordered_keys[time_key_index]
                    elif k == sequence_column_index:
                        key = ordered_keys[sequence_key_index]
                    else:
                        index = non_related_keys+i*number_of_peaks+k-index_shift
                        key = ordered_keys[index]
                    value = data_dict[key][j]
                    page.data_grid.SetCellValue(j,k,value)
            page.data_grid.AutoSizeColumns()

    def clear_columns(self,number_of_cols):
        col_shift = 2
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.DeleteCols(col_shift, 
                                           number_of_cols-col_shift)

    def clear_rows(self,number_of_rows):
        row_shift = 1
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.DeleteRows(row_shift, 
                                           number_of_rows - row_shift)
        
    def clear_position(self,x,y):
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.SetCellValue(x,y,'')
        
    def clear_and_reset_tables(self):
        number_of_cols = self.page_one.data_grid.GetNumberCols()
        if number_of_cols > 2:
            self.clear_columns(number_of_cols)
        number_of_rows= self.page_one.data_grid.GetNumberRows()
        if number_of_rows > 1:
            self.clear_rows(number_of_rows)
        self.clear_position(0,0)
        self.clear_position(0,1)

    def auto_size_columns(self):
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.AutoSizeColumns()

    def force_refresh_for_tables(self):
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.ForceRefresh()

    def report_new_data(self,peak_assignment,run_cnt,peak_cnt,
                        isotope,conc,retention,integration_bounds,
                        tolerance):
        last_position = -1
        peak_match = self.check_against_previous_retention_times(retention,
                                                                 tolerance)
        if peak_match == None:
            position = self.figure_out_where_to_add_column(peak_cnt,
                                                           run_cnt,
                                                           retention)
            if position == last_position:
                index = self.index_of_last_position()
                
            else:
                index = position
            
            self.add_column_to_tables(index,peak_assignment,peak_cnt)
            self.check_peak_names_after_column_insert()
        else:
            index = peak_match
        
        self.add_data_to_tables(index,run_cnt,isotope,conc,
                                    retention,integration_bounds)
                                    

    def check_peak_names_after_column_insert(self):
        number_of_columns = self.page_one.data_grid.GetNumberCols()
        static_column = 2
        shift = 1
        
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for column in range(static_column, number_of_columns):
            column_name = self.page_one.data_grid.GetColLabelValue(column)
            if 'Peak' in column_name:
                if column_name != 'Peak'+str(column-shift):
                    name = 'Peak' + str(column-shift)
                    for page in page_lst:
                        page.data_grid.SetColLabelValue(column,name)
                        

    def add_data_to_tables(self,index,run_cnt,isotope,conc,
                           retention,integration_bounds):
        run_cnt_shift = 1
        run_cnt -= run_cnt_shift
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        data_lst = [isotope,conc,retention,integration_bounds]
        integration_index = 3
        for i,page in enumerate(page_lst):
            if i != integration_index:
                page.data_grid.SetCellValue(run_cnt,index,str(round(data_lst[i],2)))
            else:
                page.data_grid.SetCellValue(run_cnt,index,str(data_lst[i]))


    def label_column_with_auto_assignment(self,label,index,peak_cnt):
        if label == None:
            label = 'Peak'+str(peak_cnt)
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.SetColLabelValue(index,label)
            
    def get_species_lst(self):
        data = self.page_one.data_grid
        label_lst = []
        for i in range(data.GetNumberCols()):
            if i != 0:
                label_lst.append(data.GetColLabelValue(i))
        return label_lst
            
    def index_of_last_position(self):
        return self.page_one.data_grid.GetNumberCols()

    def add_column_to_tables(self,index,peak_assignment,peak_cnt):
        cols_to_add = 1
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.InsertCols(index,cols_to_add)
        self.label_column_with_auto_assignment(peak_assignment,
                                                       index,
                                                       peak_cnt)
        self.auto_size_columns()

    def figure_out_where_to_add_column(self,peak_cnt,run_cnt,retention):
        first_run = 1
        last_position = -1
        if run_cnt == first_run:
            return last_position
        else:
            return self.new_column_position(peak_cnt,run_cnt,retention)

    def new_column_position(self,peak_cnt,run_cnt,retention):
        number_of_columns = self.page_one.data_grid.GetNumberCols()
        just_the_static_columns = 2
        first_column = 2
        last_column = self.index_of_last_position()
        index_shift = 1
        adjustment_for_pairs = 1
        if number_of_columns > just_the_static_columns:
            if retention < self.retention_average(first_column):
                return first_column
            elif retention > self.retention_average(last_column-index_shift):
                return last_column
            else:
                for i in range(just_the_static_columns,number_of_columns
                               -adjustment_for_pairs):
                    left_retention = self.retention_average(i)
                    right_retention = self.retention_average(i+index_shift)
                    if left_retention < retention < right_retention:
                        return i+index_shift
        else:
            return first_column
                
    def check_against_previous_retention_times(self,retention,tolerance):
        number_of_columns = self.page_one.data_grid.GetNumberCols()
        just_the_static_columns = 2
        static_column_shift = 2
        found_match_flag = False
        if number_of_columns > just_the_static_columns:
            for i in range(static_column_shift,number_of_columns):
                index = i
                if abs(retention - self.retention_average(index)) < tolerance:
                    found_match_flag = True
                    return index
            if found_match_flag == False:
                return None
        else:
            return None

    def retention_average(self,index):
        starting_row = 0
        number_of_rows = self.page_one.data_grid.GetNumberRows()
        lst = []
        for i in range(starting_row,number_of_rows):
            try:
                cell_value = self.page_three.data_grid.GetCellValue(i,index)
                if cell_value != '':
                    lst.append(float(cell_value))
            except ValueError:
                pass
        return np.average(lst)

    def report_start_time(self,run_cnt,gmttime):
        time_column = 0
        run_cnt -= 1
        time_string = time.strftime('%H:%M:%S',gmttime)
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.SetCellValue(run_cnt,time_column,time_string)
            page.data_grid.AutoSizeColumns()

    def report_sequence_type(self,run_cnt,sequence_lst):
        ### sequence_lst is a list of hardcoded bytes that
        ### correspond the GC input requirement...
        run_cnt -= 1
        seq_len = len(sequence_lst)
        sequence = self.sequence_dictionary[sequence_lst[run_cnt%seq_len]]
        sequence_column = 1
        page_lst = [self.page_one,self.page_two,self.page_three,self.page_four]
        for page in page_lst:
            page.data_grid.SetCellValue(run_cnt,sequence_column,sequence)
            page.data_grid.AutoSizeColumns()
            
    def report_data_from_table(self,run_number,species_selection):
        skip_squence_column = 1
        
        i,j = run_number,species_selection+skip_squence_column
        pages = [self.page_one, self.page_two, self.page_three, self.page_four]
        current = []
        for page in pages:
            current.append(page.data_grid.GetCellValue(i,j))
        self.reprocess_area.set_original_string_items(current)
        
    def highlight_selection_in_table(self,run,species):
        shift_for_static_columns = 1
        tables = [self.page_one.data_grid,self.page_two.data_grid,
                    self.page_three.data_grid,self.page_four.data_grid]
        for table in tables:
            for i in range(table.GetNumberRows()):
                for j in range(table.GetNumberCols()):
                    if i == run and j-shift_for_static_columns == species:
                        table.SetCellBackgroundColour(i,j,'yellow')
                    else:
                        table.SetCellBackgroundColour(i,j,'white')
            table.ForceRefresh()
        
class Table(wx.Panel):
    def __init__(self,parent,sidebar):
        wx.Panel.__init__(self,parent)
        
        self.sidebar = sidebar

        self.data_grid = wx.grid.Grid(self)
        self.data_grid.CreateGrid(1,2)
        self.data_grid.EnableEditing(False)
        self.data_grid.SetDefaultCellAlignment(vert = wx.ALIGN_CENTER, horiz = wx.ALIGN_RIGHT)
        self.set_grid_label(0,'Time')
        self.set_grid_label(1,'Sequence')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.data_grid, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.selection_top = None
        self.selection_bottom = None
        self.selection_column = None
        self.selection_average = None
        self.selection_std = None
        
        self.data_grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, self.on_range_selection)
        
    def set_grid_label(self,idx,text_str):
        self.data_grid.SetColLabelValue(idx,text_str)
        
    def on_range_selection(self,event):
        if self.is_single_column():
            self.calculate_statistics()
        else:
            self.sidebar.statistics.Clear()
            self.sidebar.statistics.AppendText('Statistics:')
                
    def is_single_column(self):
        data_index = 0
        column_index = 1
        row_index = 0
        tl =  self.data_grid.GetSelectionBlockTopLeft()
        br =  self.data_grid.GetSelectionBlockBottomRight()
        if tl != [] and br != []:
            if tl[data_index][column_index] == br[data_index][column_index]:
                self.selection_top = tl[data_index][row_index]
                self.selection_bottom = br[data_index][row_index]
                self.selection_column = tl[data_index][column_index]
                return True
            else:
                return False
        else:
            return False
            
    def calculate_statistics(self):
        index_shift = 1
        values = []
        values_are_float = True
        for i in range(self.selection_top,self.selection_bottom+index_shift):
            try:
                values.append(float(self.data_grid.GetCellValue(i,self.selection_column)))
            except ValueError:
                values_are_float = False
                
        if values_are_float:
            self.selection_average = np.average(values)
            self.selection_std = np.std(values)
            self.sidebar.statistics.Clear()
            self.sidebar.statistics.AppendText('Average:\t%.3f\t\tStdDev:\t%.3f'
                            %(self.selection_average,self.selection_std))

        
        
class ReprocessArea(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        
        self.sidebar = parent
        self.size = (200,200)

        self.notebook = wx.Notebook(self)
        self.page_one = wx.Panel(self.notebook, -1, size = self.size)
        self.notebook.AddPage(self.page_one, 'Reprocess Individual Peaks')
        #self.page_two = wx.Panel(self.notebook, -1, size = self.size)
        #self.notebook.AddPage(self.page_two, 'Reprocess w/ Different Threshold')
        sizer_notebook = wx.BoxSizer(wx.VERTICAL)
        sizer_notebook.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer_notebook)

        sizer_page_one = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl_page_one = self.generate_list_ctrl_page_one()
        self.initialize_string_items()
        sizer_page_one.Add(self.list_ctrl_page_one,0,wx.ALIGN_TOP | wx.EXPAND)
        button = self.generate_buttons_page_one()
        sizer_page_one.Add(button,-1,wx.ALIGN_LEFT)
        self.page_one.SetSizer(sizer_page_one)

        #sizer_page_two = wx.BoxSizer(wx.VERTICAL)
        #self.list_ctrl_page_two = self.generate_list_ctrl_page_two()
        #sizer_page_two.Add(self.list_ctrl_page_two,0,wx.ALIGN_TOP | wx.EXPAND)
        #sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
        #button_one,button_two = self.generate_buttons_page_two()
        #sizer_buttons.Add(button_one,-1,wx.ALIGN_LEFT)
        #sizer_buttons.Add(button_two,-1,wx.ALIGN_LEFT)
        #sizer_page_two.Add(sizer_buttons,-1,wx.ALIGN_LEFT)
        #self.page_two.SetSizer(sizer_page_two)
        
        self.reprocessed_data = None
        self.reprocessed_data_flag = False
        self.species_selection = None
        self.run_number = None
        
    def generate_list_ctrl_page_one(self):
        list_ctrl_one = wx.ListCtrl(self.page_one, size=self.size,
                                       style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        str_list = ['Parameter','Original Values','Reprocessed Values']
        for i,str_value in enumerate(str_list):
            list_ctrl_one.InsertColumn(i, str_value,
                                          wx.LIST_FORMAT_RIGHT, width=125)
        
        str_list = ['Isotopic Ratio:','Max Concentration:',
                    'Retention Time:','Integration Bounds:']
        for i,str_value in enumerate(str_list):
            list_ctrl_one.InsertStringItem(i,str_value)
        return list_ctrl_one
    
    def generate_list_ctrl_page_two(self):
        list_ctrl_two = wx.ListCtrl(self.page_two, size=self.size,
                                       style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        return list_ctrl_two

    def initialize_string_items(self):
        self.current_data =['--','--','--','--']
        self.reprocessed_data = ['--','--','--','--']
        self.set_original_string_items(self.current_data)
        self.set_reprocessed_string_items(self.reprocessed_data,None,None)

    def set_original_string_items(self,current):
        number_of_data = 4
        original_column = 1
        current = self.to_string(current)
        for i in range(number_of_data):
                self.list_ctrl_page_one.SetStringItem(i,original_column,current[i])
    
    def to_string(self,lst):
        str_lst = []
        for value in lst:
            if isinstance(value,float):
                str_lst.append(str(round(value,2)))
            else:
                str_lst.append(str(value))
        return str_lst
            
        
    def clear_reprocessed_string_items(self,run_number,species_selection):
        self.reprocessed_data = ['--','--','--','--']
        self.species_selection = species_selection
        self.run_number = run_number
        self.set_reprocessed_string_items(self.reprocessed_data,
                                            self.run_number,
                                            self.species_selection)
        self.reprocessed_data_flag = False
            
    def set_reprocessed_string_items(self,reprocessed,run_number,species_selection):
        number_of_data = 4
        reprocessed_column = 2
        self.reprocessed_data_flag = True
        if run_number != None and species_selection != None:
            self.run_number = run_number
            self.species_selection = species_selection
            self.reprocessed_data = reprocessed
        reprocessed = self.to_string(reprocessed)
        for i in range(number_of_data):
            self.list_ctrl_page_one.SetStringItem(i,reprocessed_column,reprocessed[i])
        
    def convert_reprocessed_to_original(self):
        self.set_original_string_items(self.reprocessed_data)
        self.clear_reprocessed_string_items(self.run_number,self.species_selection)
        
    def generate_buttons_page_one(self):
        button = wx.Button(self.page_one, id=-1, label='Update Data')
        button.Bind(wx.EVT_BUTTON, self.on_update_data)
        return button

    def generate_buttons_page_two(self):
        button_threshold = wx.Button(self.page_two, id=-1, 
                                     label='Change Detection Threshold')
        button_threshold.Bind(wx.EVT_BUTTON, self.on_change_threshold)
        button_integration = wx.Button(self.page_two, id=-1,
                                       label='Change Integration Range')
        button_integration.Bind(wx.EVT_BUTTON, self.on_change_integration)
        return button_threshold,button_integration

    def on_update_data(self,event):
        if self.reprocessed_data_flag:
            self.update_data_table()
            self.update_data_plot()
            self.convert_reprocessed_to_original()
            
    def generate_table_list(self):
        return [self.sidebar.page_one.data_grid,
                    self.sidebar.page_two.data_grid,
                    self.sidebar.page_three.data_grid,
                    self.sidebar.page_four.data_grid]
                            
    def update_data_table(self):
        shift_for_time_column = 1
        row = self.run_number
        column = self.species_selection + shift_for_time_column
        tables = self.generate_table_list()
        for i,string_value in enumerate(self.reprocessed_data):
            try:
                string_value = str(round(string_value,2))
            except TypeError:
                string_value = str(string_value)
            tables[i].SetCellValue(row,column,string_value)
            tables[i].ForceRefresh()
                
    def update_data_plot(self):
        number_of_data = 4
        j = self.run_number
        k = self.species_selection
        for i in range(number_of_data):
            try:
                self.sidebar.main_frame.page_two.plot_area.peak_data[i][k][j] = float(self.reprocessed_data[i])
            except TypeError:
                self.sidebar.main_frame.page_two.plot_area.peak_data[i][k][j] = str(self.reprocessed_data[i])
        self.sidebar.main_frame.page_two.plot_area.update_plot_with_data()
        

    def on_change_threshold(self,event):
        pass

    def on_change_integration(self,event):
        pass
            
    