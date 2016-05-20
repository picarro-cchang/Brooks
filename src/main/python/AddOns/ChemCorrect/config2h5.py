'''
Testing
'''
import os
import sys
import getopt
import shutil

from types import *

import tables

from datetime import datetime, timedelta
from time import mktime

from configobj import ConfigObj

class ConfigToH5(object):
    '''
    walk the given directory tree returning all config ini files
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if "start_dir" in kwargs:
            self._start_dir = kwargs["start_dir"]
            del kwargs["start_dir"]
        else:
            self._start_dir = "C:\Picarro\G2000\AppConfig"

        if "new_name" in kwargs:
            self._new_name = kwargs["new_name"]
            del kwargs["new_name"]
        else:
            now_dt = datetime.now()
            self._new_name = "h5config_%s.h5" % (now_dt.strftime("%Y%m%d%H%M%S"))

        self._h5file = None
        
    def get_config_files(self):
        rct = 0
        h5tbl = self._create_new_h5()
        h5row = h5tbl.row
        name_dup_check = {}
        source_iter = self._walker(self._start_dir)
        for root, name, ext, base in source_iter:
            if not base in name_dup_check.keys():
                name_dup_check[base] = (root, name)
            else:
                oroot, oname = name_dup_check[base]
            
            config_file = os.path.join(root, name)
            sect_iter = self._config_walker(config_file)
            for sect, keyword, val in sect_iter:
                if isinstance(val, str):
                    strng = val
                else:
                    sep = ""
                    strng = ""
                    for value in val:
                        strng += "%s%s" % (sep, value)
                        sep = ", "
                        
                dtype = "string"
                
                try:
                    int_val = int(strng)
                    dtype = "int"
                except:
                    try:
                        float_val = float(strng)
                        dtype = "float"
                    except:
                        pass
                    
                rct += 1
                #if sect == "Error" and keyword == "Error" and val == "Error":
                #    print "writing row with error sec/key/val"
                    
                location = root.replace(self._start_dir,"")
                h5row["location"] = location
                h5row["type"] = ext
                h5row["name"] = base
                h5row["section"] = sect
                h5row["keyword"] = keyword
                h5row["string_value"] = strng
                if dtype == "float":
                    h5row["float_value"] = float_val
                if dtype == "int":
                    h5row["int_value"] = int_val
                h5row.append()
                    
        h5tbl.flush()   
        h5tbl.close() 
        self._h5file.close()  
        #print "row count: ", rct 

    def _walker(self, search_dir):
        '''
        walk directory tree looking for picarro ini files.
        '''
        for root, dirs, files in os.walk(search_dir, topdown=True):
            for name in files:
                base, sep, ext = name.rpartition(".")
                
                if ext in  ("mode", "ini",):
                    yield root, name, ext, base
                    
        
        return

    def _config_walker(self, config_file):
        '''
        walk the entries in the config file
        '''
        #print "config_file", config_file
        good_file = True
        try:
            config = ConfigObj(config_file, 
                               list_values=True, 
                               raise_errors=True)
        except:
            good_file = False
            
        if good_file:
            for sect in config.keys():
                #print "sect:", sect, type(config[sect])
                if type(config[sect]) == type("this is a string"):
                    yield "None", sect, config[sect]
                else:
                    for keyword in config[sect]:
                        #print "keyword:", keyword
                        val = config[sect][keyword]
                        yield sect, keyword, val
        else:
            #print "found error"
            yield "Error", "Error", "Error"


    def _create_new_h5(self):
        '''
        create new picarro h5 archive using passed in name and description
        '''
        h5_name = self._new_name
        
        try:
            os.remove(h5_name)
            #print "h5 removed", h5_name
        except:
            pass
        
        self._h5file = tables.openFile(h5_name, mode = "w", title = "Picarro Config")
        new_table = self._h5file.createTable(
                                    "/", 
                                    "config_current", 
                                    PicarroConfig,
                                    "current configuration"
                                                )
        
        return new_table
    
class PicarroConfig(tables.IsDescription):
    '''
    Picarro Configuration Table
    '''
    location = tables.StringCol(64)
    name = tables.StringCol(32)
    type = tables.StringCol(32)
    section = tables.StringCol(32)
    keyword = tables.StringCol(32)
    string_value = tables.StringCol(4096)
    float_value = tables.FloatCol()
    int_value = tables.Int64Col()

class DiffTwoTables(object): 
    '''
    Show differences between two h5 config tables
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if "file1" in kwargs:
            self.file1 = kwargs["file1"]
            del kwargs["file1"]
        else:
            self.file1 = None

        if "file2" in kwargs:
            self.file2 = kwargs["file2"]
            del kwargs["file2"]
        else:
            self.file2 = None


    def compare(self):
        '''
        compare the two tables
        '''
        diff_array = {}
        self._h5table1, file1 = self._get_h5table(self.file1)
        self._h5table2, file2 = self._get_h5table(self.file2)
        
        tbl2rows = {}
        for ii in range(0,self._h5table2.nrows):
            tbl2rows[ii] = True
        
        #print "start compare: ", datetime.now()
        #print "len tbl2rows: ", len(tbl2rows)
        
        processed_locs = []
        new_rows = None
        current_loc = None
        ii = 0
        iii = 0
        
        #spin through all rows in table1 looking for matches
        for orig_row in self._h5table1:
            # when location changes, get a new set of location data from tbl2
            if not current_loc == orig_row["location"]:
                #spin through remaining data in new_rows for the location
                if new_rows:
                    for loc, locdict in new_rows.iteritems():
                        for fil, fildict in locdict.iteritems():
                            for typ, typdict in fildict.iteritems():
                                for sec, secdict in typdict.iteritems():
                                    for key, val in secdict.iteritems():

                                        iii += 1
                                        diff_array[iii] = {
                                                           "path1": None,
                                                           "path2": loc,
                                                           "file": fil,
                                                           "type": typ,
                                                           "section": sec,
                                                           "keyword": keyword,
                                                           "value1": None,
                                                           "value2": val,
                                                           }

                processed_locs.append(orig_row["location"])
                current_loc = orig_row["location"]
                new_rows = self._get_rows_by_location(current_loc)


            location = orig_row["location"]
            file = orig_row["name"]
            type = orig_row["type"]
            section = orig_row["section"]
            keyword = orig_row["keyword"]
            value = orig_row["string_value"]
            
            value2_exists = None
            try:
                value2 = new_rows[location][file][type][section][keyword]
                
                del new_rows[location][file][type][section][keyword]

                if len(new_rows[location][file][type][section]) <= 0:
                    del new_rows[location][file][type][section]
                if len(new_rows[location][file][type]) <= 0:
                    del new_rows[location][file][type]
                if len(new_rows[location][file]) <= 0:
                    del new_rows[location][file]
                if len(new_rows[location]) <= 0:
                    del new_rows[location]
                    
                value2_exists = True
                
            except:
                pass
            
            # check for location error, 
            # a location error is where the file failed ConfigObj parser
            # Note1: if side 1 fails, and there is also a matching side 2
            #   location, it means both sides failed. Write differ record
            #   for each failing side (even if both sides fail)
            # Note2: if the location error only exists in side 2 the error
            #    will be recorded as a normal course of the missing side 1
            #    logic.  No special test for the "Error" location is required. 
            if section == "Error" and keyword == "Error" and value == "Error":
                #print "found error for side1", file
                iii += 1
                diff_array[iii] = {
                                   "path1": location,
                                   "path2": None,
                                   "file": file,
                                   "type": type,
                                   "section": section,
                                   "keyword": keyword,
                                   "value1": value,
                                   "value2": None,
                                   }
                if value2_exists:
                    #print "found error for side2 along with side 1", file
                    iii += 1
                    diff_array[iii] = {
                                       "path1": None,
                                       "path2": location,
                                       "file": file,
                                       "type": type,
                                       "section": section,
                                       "keyword": keyword,
                                       "value1": None,
                                       "value2": value2,
                                       }
                    
            else:
                if value2_exists:
                    if value2 == value:
                        ii +=  1
                    else:
                        iii += 1
                        diff_array[iii] = {
                                           "path1": location,
                                           "path2": location,
                                           "file": file,
                                           "type": type,
                                           "section": section,
                                           "keyword": keyword,
                                           "value1": value,
                                           "value2": value2,
                                           }
                else:
                    iii += 1
                    diff_array[iii] = {
                                       "path1": location,
                                       "path2": None,
                                       "file": file,
                                       "type": type,
                                       "section": section,
                                       "keyword": keyword,
                                       "value1": value,
                                       "value2": None,
                                       }

        #spin through remaining data in new_rows for the location
        if new_rows:
            for loc, locdict in new_rows.iteritems():
                for fil, fildict in locdict.iteritems():
                    for typ, typdict in fildict.iteritems():
                        for sec, secdict in typdict.iteritems():
                            for key, val in secdict.iteritems():

                                loc1 = None
                                if loc in processed_locs:
                                    loc1 = loc
                                iii += 1
                                diff_array[iii] = {
                                                   "path1": None,
                                                   "path2": loc,
                                                   "file": fil,
                                                   "type": typ,
                                                   "section": sec,
                                                   "keyword": keyword,
                                                   "value1": None,
                                                   "value2": val,
                                                   }


        #spin through all rows of table2 looking for rows not processed 
        for new_row in self._h5table2:
            if not new_row["location"] in processed_locs:
                location = new_row["location"]
                file = new_row["name"]
                type = new_row["type"]
                section = new_row["section"]
                keyword = new_row["keyword"]
                value = new_row["string_value"]

                iii += 1
                diff_array[iii] = {
                                   "path1": None,
                                   "path2": location,
                                   "file": file,
                                   "type": type,
                                   "section": section,
                                   "keyword": keyword,
                                   "value1": None,
                                   "value2": value,
                                   }
                
        
        self._h5table1.close()
        self._h5table2.close()
        
        file1.close()
        file2.close()
        
        return diff_array
        
    def _get_rows_by_location(self, location):
        '''
        get rows by location
        '''
        found_match = False
        new_rows = {}
        for new_row in self._h5table2.where(
                                            "(location == loc)", 
                                            {"loc": location} 
                                            ):
            location = new_row["location"]
            file = new_row["name"]
            type = new_row["type"]
            section = new_row["section"]
            keyword = new_row["keyword"]
            value = new_row["string_value"]
            
            if not location in new_rows.keys():
                new_rows[location] = {}
            if not file in new_rows[location].keys():
                new_rows[location][file] = {}
            if not type in new_rows[location][file].keys():
                new_rows[location][file][type] = {}
            if not section in new_rows[location][file][type].keys():
                new_rows[location][file][type][section] = {}
            if not keyword in new_rows[location][file][type][section].keys():
                new_rows[location][file][type][section][keyword] = value
            
            found_match = True
            
        return new_rows
            
    def _get_h5table(self, file):
        '''
        get h5 table
        ''' 
        try:
            h5table = None
            h5file = tables.openFile(file, "a")
            for tbl in h5file.walkNodes("/", "Table"):
                if h5table == None:
                    h5table = tbl
                    break

        except:
            msg = "table: %s is not a valid h5 file" % (file)
            raise RuntimeError, "%s %s" % ("config2h5.compare", msg)
            
        return h5table, h5file
         
    
def main(argv=None):
    '''
    main routine for h5search module
    '''
    file1 = "Z:\VMShares\Workspaces\TurtlesFly\PicarroPost\PostProcess\AppConfig1"
    file2 = "Z:\VMShares\Workspaces\TurtlesFly\PicarroPost\PostProcess\AppConfig2"

    #file1 = "/Users/sirron/TurtlesFly/PicarroPost/PostProcess/AppConfig1"
    #file2 = "/Users/sirron/TurtlesFly/PicarroPost/PostProcess/AppConfig2"
    
    print "start", datetime.now()
    print 
    
    c=ConfigToH5(start_dir=file1,
                 new_name="config1.h5")
    c.get_config_files()
    
    #c2=ConfigToH5(start_dir="/Volumes/data/crd_G2000/CFxDS/650-CFADS2125/Config/20100925/AppConfig",
    #             new_name="config2.h5")
    c2=ConfigToH5(start_dir=file2,
                 new_name="config2.h5")
    c2.get_config_files()

    c3=DiffTwoTables(file1="config1.h5", file2="config2.h5")
    diff = c3.compare()
    
    for dkey in range(1,len(diff) + 1):
        print dkey
        print "path1:", diff[dkey]["path1"]
        print "path2:", diff[dkey]["path2"]
        print "   file:", diff[dkey]["file"]
        print "   section:", diff[dkey]["section"]
        print "   keyword:", diff[dkey]["keyword"]
        print "       value1:", diff[dkey]["value1"]
        print "       value2:", diff[dkey]["value2"]
        
        print


    print
    print "done: ", datetime.now()

if __name__ == '__main__':
    sys.exit(main())

    
    