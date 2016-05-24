import numpy as np
import time
import os
import csv
from datetime import date
import wx
import sys
if 'C:\Picarro\G2000\Host\Common' not in sys.path: sys.path.append('C:\Picarro\G2000\Host\Common')
if 'C:\Picarro\G2000\Host\DataManager' not in sys.path: sys.path.append('C:\Picarro\G2000\Host\DataManager')
import CmdFIFO
from DataManagerListener_GCCRDS import DataManagerListener


''' The data created in the PlotAreaOne class is saved into two files.
The series file is a .dat file that is opened when the start button is 
pressed and remains open until the stop button is pressed.  Time series
data is written to this series file at the end of each run and when the
stop button is pressed.
'''

class DataCtrlOne(object):
    def __init__(self):
        self.dml = DataManagerListener()

    def initialize_series_data(self):
        return [],[],[]

    def initialize_data_peak_data(self):
        return [],[],[],[]

    def get_data_from_dml(self):
        try:
            self.data_queue = self.dml.queue.get()
            return self.data_queue
        except:
            return None
            
    def clear_queue(self):
        self.dml.clear(self.dml.queue)
            
    def create_files(self,start_time):
        file_base_name = time.strftime("%Y_%b_%d__%H%M%S", start_time)
        directory = self.create_directory_structure()
        if directory != None:
            peak_data_file = self.create_peak_data_file(directory,file_base_name)
            time_series_file = self.create_time_series_file(directory,
                                                                 file_base_name)
            return peak_data_file,time_series_file
        else:
            return None,None

    def create_directory_structure(self):
        index_shift = 1

        root_directory = 'C:/CSIA'
        year_month_directory = '_'.join([str(date.today().year),
                                         str(date.today().month)])
        day_directory = str(date.today().day)
        lst = [root_directory,year_month_directory,day_directory]
        try:
            for i in range(len(lst)):
                partial_path = '/'.join(lst[0:i+index_shift])
                if not os.path.isdir(partial_path):
                    os.mkdir(partial_path)
            return '/'.join(lst)
        except:
            return None

    def create_peak_data_file(self,directory,file_base_name):
        no_buffer = 0
        specific_name = 'peak_data.csv'
        file_name = '_'.join([file_base_name,specific_name])
        full_path = '/'.join([directory,file_name])
        self.peak_data_file_full_path = full_path
        return self.open_file(full_path,'w',no_buffer)

    def create_time_series_file(self,directory,file_base_name):
        no_buffer = 0
        specific_name = 'time_series.dat'
        file_name = '_'.join([file_base_name,specific_name])
        full_path = '/'.join([directory,file_name])
        self.series_data_file_full_path = full_path
        return self.open_file(full_path,'w',no_buffer)

    def open_file(self,full_path,mode,buffer):
        try:
            return open(full_path,mode=mode,buffering=buffer)
        except IOError:
            return None
   
    def close_file(self,file):
        if not file.closed:
            file.close()

    def save_series_data(self,run_cnt,file,data):
        precision = 4
        if not file.closed:
            index_shift = 1
            file.write(str(run_cnt)+'\n')
            for data_set in data:
                length_of_data_set = len(data_set)
                for i,data_point in enumerate(data_set):
                    if i != length_of_data_set-index_shift:
                        file.write(str(round(data_point,precision))+'\t')
                    else:
                        file.write(str(round(data_point,precision))+'\n')

    def save_peak_data(self,file,data_param_lst,grid_lst,m_to_file,b_to_file):
        ''' The peak data is saved to a csv file, which is over-written
        each time a run finished.  This allows structural changes that
        might have occurred to be saved in a user-usuable csv format.
        '''
        try:
            with open(file, 'w') as f:
                writer = csv.writer(f, delimiter =',',lineterminator='\n')
                #self.write_run_parameters(writer,data_param_lst)
                self.write_peak_data_from_table(writer,grid_lst)
                if m_to_file != None:
                    self.append_cal_data(writer,m_to_file,b_to_file)
        except:
            pass

    def write_run_parameters(self,writer,data_param_lst):
        ''' Used to report the run_parameters'''
        string_lst = ['Peak Detection Threshold:',
                      'Retention Time Autosorting Tolerance:',
                      'GCC CRDS Run Duration:',
                      'Maximum Number of Runs:']
        writer.writerows([['%s'%pair[0],pair[1]] for \
            pair in zip(string_lst,data_param_lst)])

    def write_peak_data_from_table(self,writer,grid_lst):
        start_time_col = 1
        index_shift = 1
        idx = 0 #use zeroth grid for logic
        number_of_cols = grid_lst[idx].GetNumberCols()
        number_of_rows = grid_lst[idx].GetNumberRows()

        peak_name_lst = [str(grid_lst[idx].GetColLabelValue(i)) \
            for i in range(start_time_col,number_of_cols)]

        variable_name_lst = ['Isotope',
                             'Concentration',
                             'Retention',
                             'Integration_Bounds']

        full_variable_lst = ['Run Count', 'Start Time']
        for variable in variable_name_lst:
            for peak in peak_name_lst:
                full_variable_lst.append('_'.join((peak,variable)))
        
        writer.writerow(full_variable_lst)

        data = []
        for row_index in range(number_of_rows):
            data.append([row_index+index_shift])
            for i,grid in enumerate(grid_lst):
                if i != 0:
                    for col_index in range(start_time_col,
                                           number_of_cols):
                        data[row_index].append(
                            str(grid.GetCellValue(row_index,col_index)))
                else:
                    for col_index in range(number_of_cols):
                        data[row_index].append(
                            str(grid.GetCellValue(row_index,col_index)))
        writer.writerows(data)
        
    def append_cal_data(self,writer,m_to_file,b_to_file):
        writer.writerow(['CalibrationParameters:',m_to_file,b_to_file])


        
       
