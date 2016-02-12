### This script creates an executable file from the python modules

from distutils.core import setup
from distutils.filelist import findall
import py2exe
import os
import matplotlib
import scipy
from Host.Common import CmdFIFO


matplotlib_data_dir = matplotlib.get_data_path()
matplotlib_data = findall(matplotlib_data_dir)
matplotlib_data_files = []
for data in matplotlib_data:
    dirname = os.path.join('matplotlib_data', data[len(matplotlib_data_dir)+1])
    matplotlib_data_files.append((os.path.split(dirname)[0],[data]))

setup(
  console = ['main.py'],
  options = {
    'py2exe' : {
        'packages' : [
            'matplotlib',
            'Pyro',
            'scipy.sparse.csgraph._validation',
            'Host.Common'
            ],
        'dll_excludes' : [
            'libgdk-win32-2.0-0.dll',
            'libgdk_pixbuf-2.0-0.dll',
            'python25.dll'
            ],
        'excludes': [
            '_gtkagg',
            '_tkagg',
            '_agg2',
            '_cairo',
            '_cocoaagg',
            '_fltkagg',
            '_gtk',
            '_gtkcairo',
            'tcl'
            ]
    }
  },
  data_files = matplotlib.get_py2exe_datafiles()
)