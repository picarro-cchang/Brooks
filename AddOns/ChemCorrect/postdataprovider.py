'''
postdataprovider.py -- The postdataprovider module contains the 
PostDataProvider class.
This class will provide data from a csv or h5 file to PostProcess modules.

'''

import sys
import csv
import tables

from postprocessdefn import *

class PostDataProvider(object):
    '''
    Csv data provider for Picarro PostProcess 
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor requires file_source as first argument
        '''
        if "type" in kwargs:
            self._rtype = kwargs["type"]
            del kwargs["type"]
        else:
            self._rtype = None

        self.column_names_list = []
        self.column_count = 0

        self._last_row_returned = None
        self._data_reader = None
        self._csv_column_names_dict = {}
        
        if 1 <= len(args):
            self._file_source = args[0]
        else:
            raise RuntimeError, SOURCE_REQ_ERROR
        
        self._setup()

    def _setup(self):
        '''
        initial setup
        '''
        self._type = self._set_type()

        if self._type == "csv":
            self._open_csv()
        elif self._type == "h5":
            self._open_h5()
        elif self._type == "threshold":
            self._open_threshold()
        else:
            raise RuntimeError, INVALID_SOURCE_ERROR

        
    def _set_type(self):
        '''
        determine and set the data type
        either the passed in type, or default based on source file extension
        '''
        if self._rtype in ("csv", "h5", "threshold"):
            return self._rtype
        
        req_type = "csv"
        
        name, sep, ext = self._file_source.rpartition(".")
        if ext == "h5":
            req_type = "h5"
            
        return req_type
        

    def _open_csv(self):
        '''
        open the picarro csv file and return the first (column def) row
        '''
        try:
            self._csv_data_file = open(self._file_source,"rb")
            self._data_reader = csv.reader(self._csv_data_file, )
        except:
            raise RuntimeError, CSV_REQ_ERROR
        
        col_desc_row = self._data_reader.next()

        self.column_count = len(col_desc_row)

        for i in range(0, self.column_count):
            col_name = col_desc_row[i].strip()
            self.column_names_list.append(col_name)
            self._csv_column_names_dict[i] = col_name
        
    
    def _open_h5(self):
        '''
        open picarro h5 file and return the column definitions from the 
        selected (or first by default) table
        '''

        try:
            self._h5table = None
            self.h5file = tables.openFile(self._file_source, "a")
            for tbl in self.h5file.walkNodes("/", "Table"):
                if self._h5table == None:
                    self._h5table = tbl
                    break
            
        except:
            raise RuntimeError, H5_REQ_ERROR
        
        for name in self._h5table.colnames:
            self.column_names_list.append(name)
    
    
    def _open_threshold(self):
        '''
        open picarro threshold stats file
        this is a .txt file in format:
        Colname: nnnnn Colname: nnnn Shot Colname: nnnn .....
        '''
        self._text_parser_mthd = self._colon_space_line_parse
        self._text_validator_mthd = self._validate_threshold_row
        self._open_textfile()
        
    def _open_textfile(self):
        '''
        open picarro text file and use passed in parser to evaluate the data
        '''
        try:
            text_data_file = open(self._file_source,"rb")
        except:
            raise RuntimeError, TEXT_REQ_ERROR
        
        self._threshold_data = {}
        self._threshold_data = text_data_file.readlines()
        for line in self._threshold_data:
            if len(line) > 2:
                row, row_msg = self._text_parser_mthd(line)
                if not row_msg:
                    for ckey in row.keys():
                        self.column_names_list.append(ckey)
                    
                    break
                    
        
    def _colon_space_line_parse(self, line):
        '''
        parse text line in format of column: value column2: value2 ...
        return dictionary {column: value, column2: value.....}
        '''
        rtn = {}
        rtn_error = None
        
        more = True
        rest_of_data = line
        while more:
            more = None
            new_col, sep, rest_of_data = rest_of_data.partition(":")
            #print
            #print "new_col: ", new_col
            rest_of_data = rest_of_data.strip()
            if new_col:
                new_value, sep, rest_of_data = rest_of_data.partition(" ")
                
                if new_value:
                    try:
                        new_float = float(new_value)
                    except:
                        new_float = 0.0
                        
                    #print "new_float: ", new_float
                    rtn[new_col] = new_float
                    more = True
        
        if rtn:
            rtn_error = self._text_validator_mthd(rtn)   
             
        return rtn, rtn_error

    def _validate_threshold_row(self, row):
        '''
        validate that threshold row contains valid columns
        '''
        col_exists = {"Threshold": None, 
                      "Ringdown rate": None, 
                      "Shot-to-shot": None, 
                      "Mean loss": None, 
                      "Mean wavenumber": None,
                       }
        
        for rtn_col in row.keys():
            if not rtn_col in col_exists.keys():
                return "Invalid Column"
            else:
                col_exists[rtn_col] = True
        
        for ckey, cval in col_exists.iteritems():
            if not cval:
                return "Missing Column"
            
        return None
                
    def yield_rows(self):
        '''
        yields one row at-a-time from start to end (beginning to end if 
        start/end not provided)
        
        Each row returned is a dict in form {column_name: value, ...}
        '''
        
        if self._type == "csv":
            source_iter = self._csv_yield()
        elif self._type == "h5":
            source_iter = self._h5_yield()
        elif self._type == "threshold":
            source_iter = self._text_yield()
        else:
            raise RuntimeError, INVALID_SOURCE_ERROR

        for row in source_iter:
            yield(row)
            
        return
    
    def get_column_array(self, name):
        '''
        return column array
        '''
        if self._type == "h5":
            return self._h5table.col(name)

        elif self._type == "csv":
            col_array = []
            source_iter = self._csv_yield()
            for row in source_iter:
                col_array.append(row[name])
            
            return col_array
        
        elif self._type == "threshold":
            col_array = []
            source_iter = self._text_yield()
            for row in source_iter:
                if name in row.keys():
                    col_array.append(row[name])
                else:
                    col_array.append(None)
            
            return col_array
        
        return []
        
    def _csv_yield(self):
        '''
        yields csv rows one row at-a-time from start to end
        Each row returned is a dict in form {column_name: value, ...}
        '''
        # reset to begining (in case we did a partial read previously
        self._csv_data_file.seek(0)
        skip_row = self._data_reader.next()
        
        row = self._data_reader.next()
        while row:
            # first row contains col definitions - so subtract it out
            self._last_row_returned = self._data_reader.line_num - 1

            # build yield row as dictionary
            y_row = {}
            for col_key in self._csv_column_names_dict.keys():
                y_row[self._csv_column_names_dict[col_key]] = row[col_key]

            yield(y_row)
            row = self._data_reader.next()
        
        return

    def _h5_yield(self):
        '''
        yields h5 rows one row at-a-time from start to end
        Each row returned is a dict in form {column_name: value, ...}
        '''
        for row in self._h5table.iterrows():
            yield(row)
            
        return
    
    def _text_yield(self):
        '''
        yields text rows one row at-a-time from start to end
        Each row returned is a dict in form {column_name: value,....}
        '''
        for line in self._threshold_data:
            if len(line) > 2:
                row, row_error = self._text_parser_mthd(line)
                if not row_error:
                    yield(row)
        
        return


if __name__ == '__main__':
    raise RuntimeError, "%s %s" % ("postdataprovider.py", STANDALONE_ERROR)
