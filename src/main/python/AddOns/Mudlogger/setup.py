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

import zmq
os.environ["PATH"] += os.path.pathsep + os.path.split(zmq.__file__)[0]

data_files = matplotlib.get_py2exe_datafiles()
for fileName in os.listdir("."):
    if fileName.endswith(".pyd"):
        data_files.append(fileName)

setup(
  windows = [{"script" : "Mudlogger.py",
              "icon_resources" : [(1, "Mudlogger.ico")]}],
  options = {
    'py2exe' : {
        'compressed' : 1,
        'optimize' : 1,
        'packages' : [
            'matplotlib',
            'Pyro',
            'scipy.sparse.csgraph._validation',
            'scipy.optimize',
            r'scipy.special._ufuncs_cxx',
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
  data_files = data_files,
  zipfile = "lib/share"
)