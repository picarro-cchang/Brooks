'''
NAME
h5search.py - The h5search module contains the H5Search class.
This class will search the contents of Picarro H5 data containers for data 
matching specific criteria. This criteria includes columns with specified date 
ranges.

This module can be instantiated as an interactive class or run in batch.  In 
batch mode it will display (output to the standard output device) a list of h5 
containers that match the criteria. It can also copy the matching h5 containers
to a specified location in the file system.

Batch mode USAGE:
"d" search type
h5search.py [ -h ] [ -z ] [ -n ] [ --help ] [ --include-zip ] [ --zip-only ]
            [ -c <dirname> ] [ --concat-dir=<dirname> ] d file_type search_dir 
            search_colname start_ts end_ts optional_copy_dir

"l" search type
h5search.py [ -h ] [ -z ] [ -n ] [ --help ] [ --include-zip ] [ --zip-only ] 
            [ -c <dirname> ] [ --concat-dir=<dirname> ] l file_type search_dir 
            optional_copy_dir

"u" search type
h5search.py [ -h ] [ -z ] [ -n ] [ --help ] u zip_path copy_dir 


OPTIONS
  -c <dirname>, --concat-dir=<dirname> Concatenate the results into a single
                                       h5 file, and locate that file in the 
                                       directory specified by dirname
                                         
                                       The filename will be 
                                       h5concat_YYYYMMDDHHMMSS.h5 where 
                                       YYYYMMDDHHMMSS is the year, month, 
                                       day, hour, min, sec that the search 
                                       was run.
      
                                       The attributes (columns) in the new h5 
                                       container will be based on the 
                                       attributes within the first h5 
                                       container that matches.
      
  -h, --help                           Show usage information
      
  -z, --include-zip                    include zip file archives within search. 
                                       This can cause a considerable slow-down 
                                       as each archive must be uncompressed 
                                       and then searched for an h5 file, and 
                                       then that file searched for matching 
                                       criteria

  -n, --zip-only                       Only search zip file archives. 
                                       This can cause a considerable slow-down 
                                       as each archive must be uncompressed 
                                       and then searched for an h5 file, and 
                                       then that file searched for matching 
                                       criteria


ARGUMENTS 
  search_type                          "d" for DateTime search
                                       "l" search for and list h5 containers
                                       "u" unzip all h5 containers in the zip
                                       archive

  file_type                            "private", "user", "all"

  search_dir                           The directory to start the search.

  search_colname                       The name of the column containing the 
                                       timestamp data.

  start_ts                             Starting search time criteria. 
                                       This is an actual date in format 
                                       "YYYY-MM-DD HH:MM:SS" for actual time
                                       or offset (hours) from current 
                                       date-time in format "1.0" or 
                                       "-1.0" or "0" for Now.
                                         
  end_ts                               Ending search time criteria. 
                                       This is an actual date in format 
                                       "YYYY-MM-DD HH:MM:SS" for actual time
                                       or offset (hours) from current 
                                       date-time in format "1.0" or 
                                       "-1.0" or "0" for Now.
                                         
  optional_copy_dir                    (optional) If given, copy files 
                                       matching the criteria into this 
                                       directory. The directory must exist.

  copy_dir                             copy h5 files into this directory. 
                                       The directory must exist.
      
      
EXAMPLES
    h5search.py --include-zip d private ./ DATE_TIME -5.0 -1.5 ./FoundRecords
        This would perform a date search on "private" h5 files starting in the 
        current directory. The search criteria is the DATE_TIME column and 
        looking for records that are between 5 hours earlier until 90 minutes 
        earlier. H5 Containers that have matching records are copied to the 
        directory "FoundRecords" in the local path
        
    h5search.py --include-zip d private ./ DATE_TIME "2010-08-01 12:00:00" \
    "2010-08-16 20:10:00" ./FoundRecords
        This would perform a date search on "private" h5 files starting in the 
        current directory. The search criteria is the DATE_TIME column and 
        looking for records that are between Aug 1 2010 at noon, and Aug 16 
        2010 at 8:10pm. The path for H5 Containers that have matching records 
        are displayed to the local output device.
    
        
    h5search.py --include-zip d private ./ DATE_TIME "2010-08-01 12:00:00" \
    "2010-08-16 20:10:00" ./FoundRecords
        This would perform a date search on "private" h5 files starting in the 
        current directory. The search criteria is the DATE_TIME column and 
        looking for records that are between Aug 1 2010 at noon, and Aug 16 
        2010 at 8:10pm. The path for H5 Containers that have matching records 
        are displayed to the local output device.
    
'''

import os
import sys
import getopt
import shutil

import tables
from datetime import datetime, timedelta
from time import mktime

import zipfile

class H5Search(object):
    '''
    Search Picarro h5 containers for data matching specified criteria
    '''
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        self.search_parms = {
                            "concat_dir": None,
                            "include_zip": None,
                            }

        self.remove_tmpdir = True
        self.extract_tmpdir = None

        self._concat_dict = {
                            "tbl_name": None,
                            "file": None,
                            "table_h5": None,
                            }

        self._first_description = None
        self.use_zip_path = None

    
    def search_by_datetime(self, search_args):
        '''
        Search for data by date/time. Walk the given search directory looking 
        inside h5 data containers for rows containing search_args["col"] with 
        a date between the search_args["start_ts"] and search_args["end_ts"]. 
           search_args["file_type"] - "all", "private", "user"
           search_args["dir"] - directory for search 
           search_args["col"] - column name of the date-time columns
           search_args["start_ts"] - start timestamp
           search_args["end_ts"] - end timestamp
        Return list of paths (of h5 containers with matching data)
        '''
         
        first_ti = self._evaluate_time(search_args["start_ts"])
        second_ti = self._evaluate_time(search_args["end_ts"])
        
        # Since we are doing a date "between" search, correct the start/end 
        # values appropriately
        if first_ti <= second_ti:
            start_ti = first_ti
            end_ti = second_ti
        else:
            start_ti = second_ti
            end_ti = first_ti
            
        search_criteria = "(%s >= %s) & (%s <= %s)" % (
                                                       search_args["col"], 
                                                       start_ti, 
                                                       search_args["col"], 
                                                       end_ti
                                                       )
        
        return self._do_search(search_args, search_criteria)

    def list_h5_containers(self, search_args):
        '''
        Search for h5 containers within zip archives. Walk the given search 
        directory looking inside for h5 containers. Extract those identified 
        h5 containers into given copy directory.
           search_args["file_type"] - "all", "private", "user"
           search_args["dir"] - directory for search
           search_args["copy_to_dir"] - optional destination directory
        '''
        res_list = []

        source_iter = self._walker(
                                   search_args["file_type"], 
                                   search_args["dir"],
                                   search_args["include_zip"],
                                   )
        for root, dirs, files, name, tbl, zpth in source_iter:
            last_root, last_name = (None, None)

            if self.use_zip_path:
                if zpth:
                    root = zpth
            if not (root, name) == (last_root, last_name):
                res_list.append(os.path.join(root, name))
                last_root, last_name = (root, name)

        self._close()
        
        if res_list:
            if "copy_to_dir" in search_args.keys():
                self.copy_results_to_dir(res_list, search_args["copy_to_dir"])

        return res_list
   
    def unzip_single_zip_archive(self, zip_path, dest):
        '''
        unzip all h5 files within a single zip archive
        '''
        zip_archive = zipfile.ZipFile(zip_path, "r")

        for zmember in zip_archive.namelist():
            base, sep, ext = zmember.rpartition(".")
            if ext == "h5":
                head, zmbr = os.path.split(zmember)
                outfile = open(os.path.join(
                                    dest, 
                                    zmbr
                                            ), 
                                'wb')
                outfile.write(zip_archive.read(zmember))
                outfile.flush()
                outfile.close()    
        
        
    def copy_results_to_dir(self, res_list, out_dir):
        '''
        copy result files into given directory
        '''
        for res_name in res_list:
            shutil.copy(res_name, out_dir)
        
        
    def _evaluate_time(self, start_ts):
        '''
        convert enterd time (format string YYYY-MM-DD HH:MM:MM or float)
        into time
        '''
        try:
            start_dt = datetime.strptime(
                                         start_ts, 
                                         "%Y-%m-%d %H:%M:%S"
                                         )
        except ValueError:
            val = float(start_ts)
            delta = timedelta(hours=val)
            start_dt = datetime.now() + delta

        return mktime(start_dt.timetuple())+1e-6*start_dt.microsecond
    
    
    def _do_search(self, search_args, search_criteria):
        '''
        search for data meeting search_criteria, and return results
        '''
        res_list = []

        source_iter = self._walker(
                                   search_args["file_type"], 
                                   search_args["dir"],
                                   search_args["include_zip"],
                                   )
        for root, dirs, files, name, tbl, zpth in source_iter:
            try:
                if tbl.col(search_args["col"]).any():
                    last_root, last_name = (None, None)
                    for row in tbl.readWhere(search_criteria):
                        if self.use_zip_path:
                            if zpth:
                                root = zpth
                                
                        if not (root, name) == (last_root, last_name):
                            res_list.append(os.path.join(root, name))
                            last_root, last_name = (root, name)
                        
                        if self.search_parms["concat_dir"]:
                            if not self._first_description:
                                self._first_description = tbl.description
                                self._create_new_h5(
                                            self._concat_dict["tbl_name"], 
                                            self._first_description
                                                    )
                            
                            self._append_to_h5(row, tbl)    
                        else:
                            break 
                
                if self._first_description:
                    self._concat_dict["file"].flush()
                        
            except KeyError:
                pass

        self._close()
        return res_list
    
    def _walker(self, file_type, search_dir, include_zip, top_only = None):
        '''
        walk directory tree looking for specific type (user/private/all) of
        picarro h5 archives.
        '''
        for root, dirs, files in os.walk(search_dir, topdown=True):
            for name in files:
                base, sep, ext = name.rpartition(".")
                
                if ext == "h5":
                    if include_zip == True or include_zip == None:
                        otbl = self._open_h5_and_walk(
                                                    {"file_type": file_type, 
                                                     "root": root, 
                                                     "dirs": dirs, 
                                                     "files": files, 
                                                     "name": name, 
                                                     "base": base}
                                                                )
                        
                        for iroot, idir, ifile, iname, itbl in otbl:
                            yield(iroot, 
                                  idir, 
                                  ifile, 
                                  iname, 
                                  itbl,
                                  None)
                        
                        
                        
                elif ext == "zip":
                    if include_zip == True or include_zip == "Only":
                        zip_archive_path = os.path.join(root, name)
                        zip_archive = zipfile.ZipFile(zip_archive_path, "r")

                        for zmember in zip_archive.namelist():
                            base, sep, ext = zmember.rpartition(".")
                            if ext == "h5":
                                base2, sep2, ext2 = base.rpartition("_")
                                
                                if (file_type == "all"
                                or (file_type == "private" 
                                     and ext2 == "Private")
                                or (file_type == "user" 
                                     and ext2 == "User")):
    
                                    head, zmbr = os.path.split(zmember)
                                    if not self.extract_tmpdir:
                                        self._create_tmp_extractdir()
                                    
                                    outfile = open(os.path.join(
                                                        self.extract_tmpdir, 
                                                        zmbr
                                                                ), 
                                                    'wb')
                                    outfile.write(zip_archive.read(zmember))
                                    outfile.flush()
                                    outfile.close()    
    
                                    otbl = self._open_h5_and_walk(
                                                {"file_type": file_type, 
                                                 "root": self.extract_tmpdir, 
                                                 "dirs": dirs, 
                                                 "files": files, 
                                                 "name": zmbr, 
                                                 "base": base}
                                                                       )
                                    for iroot, idir, ifile, iname, itbl in otbl:
                                        yield(iroot, 
                                              idir, 
                                              ifile, 
                                              iname, 
                                              itbl,
                                              zip_archive_path)
                                    
                        zip_archive.close()
                    
        
        return

        
    def _create_new_h5(self, h5_name, h5_description):
        '''
        create new picarro h5 archive using passed in name and description
        '''
        now_dt = datetime.now()
        h5_name = "h5concat_%s.h5" % (now_dt.strftime("%Y%m%d%H%M%S"))
        
        self._concat_dict["file"] = tables.openFile(os.path.join(
                                            self.search_parms["concat_dir"], 
                                            h5_name
                                                                 ), 
                                                'w')
        self._concat_dict["table_h5"] = self._concat_dict["file"].createTable(
                                                            "/", 
                                                            "concat_result", 
                                                            h5_description
                                                                             )
        
        return
    
    def _append_to_h5(self, source_row, source_tbl):
        '''
        append row to h5 archive table
        '''
        row = self._concat_dict["table_h5"].row
        for col in source_tbl.colnames:
            if col in self._concat_dict["table_h5"].colnames:
                row[col] = source_row[col]
                    
        row.append()
                
    
    def _open_h5_and_walk(self, func_args):
        '''
        open given h5 archive, and walk the nodes
        yeild each node (name and table)
        '''
        base2, sep2, ext2 = func_args["base"].rpartition("_")
        
        if (func_args["file_type"] == "all"
            or (func_args["file_type"] == "private" and ext2 == "Private")
            or (func_args["file_type"] == "user" and ext2 == "User")):
            
            try:
                table = None
                h5file = tables.openFile(os.path.join(
                                                  func_args["root"], 
                                                  func_args["name"]), 
                                                  "r"
                                                      )

                for tbl in h5file.walkNodes("/", "Table"):
                    yield(func_args["root"], 
                          func_args["dirs"], 
                          func_args["files"], 
                          func_args["name"], 
                          tbl)
                    
                h5file.close()
            except AttributeError:
                pass

    
    def _create_tmp_extractdir(self):
        '''
        create temp extract directory
        '''
        now_dt = datetime.now()
        dirname = "h5tmp_%s" % (now_dt.strftime("%Y%m%d%H%M%S"))
        self.extract_tmpdir = os.path.join(os.curdir, dirname)
        os.mkdir(self.extract_tmpdir)


    def _close(self):
        '''
        closing processing:
          remove temp directory if one was created
        '''
        if self.remove_tmpdir:
            self.remove_extract_tmpdir()
    
    def remove_extract_tmpdir(self):
        '''
        remove temp directory
        '''
        if self.extract_tmpdir:
            shutil.rmtree(self.extract_tmpdir)
            
class Usage(Exception):
    '''
    Usage class for h5search module
    '''
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    '''
    main routine for h5search module
    '''
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], 
                                       "hznc:", 
                                       ["help", 
                                        "include-zip", 
                                        "zip-only", 
                                        "concat-dir=",]
                                       )
        except getopt.error, msg:
            raise Usage(msg)

        parm_dict = {
                    "include_zip": None,
                    "search_type": None,
                    "file_type": None,
                    "search_dir": None,
                    "search_colname": None,
                    "search_start_ts": None,
                    "search_end_ts": None,
                    "copy_to_dir": None,
                    "concat_dir": None,
                    "do_the_copy": None,
                    "zip_path": None,
                    }

        _get_opts_and_args(parm_dict, opts)
        _setup_and_validate_parms(parm_dict, args)    

        search_class = H5Search()
        if parm_dict["copy_to_dir"]:
            search_class.remove_tmpdir = None
        if parm_dict["concat_dir"]:
            search_class.search_parms["concat_dir"] = parm_dict["concat_dir"]

        if parm_dict["search_type"] == "d":
            res_dir = _do_datetime_search(search_class, 
                                          parm_dict)

            _do_copy_or_display_result(search_class, 
                                       parm_dict, 
                                       res_dir)

        elif parm_dict["search_type"] == "l":
            res_dir = _do_list(search_class, 
                               parm_dict)

            _do_copy_or_display_result(search_class, 
                                       parm_dict, 
                                       res_dir)
        elif parm_dict["search_type"] == "u":
            _do_unzip(search_class, 
                      parm_dict)
            
            return 0
        
        else:
            raise Usage(__doc__)
        
                
        # more code, unchanged
    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "for help use --help"
        return 2


def _get_opts_and_args(parm_dict, opts):
    '''
    get passed in options and arguments
    '''
    for user_opt, user_arg in opts:
        if user_opt in ("-h", "--help"):
            raise Usage(__doc__) 
        if user_opt in ("-z", "--include-zip"):
            parm_dict["include_zip"] = True
        if user_opt in ("-n", "--zip-only"):
            parm_dict["include_zip"] = "Only"
        if user_opt in ("-c", "--concat-dir"):
            parm_dict["concat_dir"] = user_arg
        
    
def _setup_and_validate_parms(parm_dict, args):
    '''
    setup parms from passed in arguments
    '''
    all_ok = True

    if len(args) < 3:
        all_ok = None
    else:
        parm_dict["search_type"] = args[0]
        
        if parm_dict["search_type"] in ("d", "l", "u"):
            if parm_dict["search_type"] == "d":
                parm_dict["file_type"] = args[1]
                parm_dict["search_dir"] = args[2]
                
                if len(args) < 6:
                    all_ok = None
                else:
                    parm_dict["search_colname"] = args[3]
                    parm_dict["search_start_ts"] = args[4]
                    parm_dict["search_end_ts"] = args[5]
            
                    if 7 <= len(args):
                        parm_dict["copy_to_dir"] = args[6]
            elif parm_dict["search_type"] == "l":
                parm_dict["file_type"] = args[1]
                parm_dict["search_dir"] = args[2]
                if 4 <= len(args):
                    parm_dict["copy_to_dir"] = args[3]
                
            elif parm_dict["search_type"] == "u":
                parm_dict["zip_path"] = args[1]
                parm_dict["copy_to_dir"] = args[2]
                
                
            if parm_dict["copy_to_dir"]:
                if os.path.isdir(parm_dict["copy_to_dir"]):
                    parm_dict["do_the_copy"] = True
                else:
                    all_ok = None
        
            if parm_dict["concat_dir"]:
                if not os.path.isdir(parm_dict["concat_dir"]):
                    all_ok = None 
        else:
            all_ok = None

    if not all_ok:
        raise Usage(__doc__) 
        
    
def _do_datetime_search(search_class, parm_dict):
    '''
    do datetime search of Picarro h5 container
    '''
    res_dir = search_class.search_by_datetime({
                                      "file_type": parm_dict["file_type"], 
                                      "dir": parm_dict["search_dir"], 
                                      "col": parm_dict["search_colname"], 
                                      "start_ts": parm_dict["search_start_ts"], 
                                      "end_ts": parm_dict["search_end_ts"],
                                      "include_zip": parm_dict["include_zip"],
                                             })
    return res_dir

def _do_list(search_class, parm_dict):
    '''
    do search of zip archives for Picarro h5 container
    '''
    res_dir = search_class.list_h5_containers({
                                      "file_type": parm_dict["file_type"], 
                                      "dir": parm_dict["search_dir"], 
                                      "include_zip": parm_dict["include_zip"],
                                             })
    return res_dir
    

def _do_unzip(search_class, parm_dict):
    '''
    unzip the path
    '''
    search_class.unzip_single_zip_archive(parm_dict["zip_path"], 
                                          parm_dict["copy_to_dir"])
    
        
def _do_copy_or_display_result(search_class, 
                               parm_dict, 
                               res_dir):
    '''
    copy result to the copy directory or display results
    '''
    if parm_dict["copy_to_dir"]:
        if parm_dict["do_the_copy"]:
            search_class.copy_results_to_dir(res_dir, parm_dict["copy_to_dir"])

        search_class.remove_extract_tmpdir()
    else:
        for res_name in res_dir:
            print res_name

                    
        
if __name__ == '__main__':
    sys.exit(main())
