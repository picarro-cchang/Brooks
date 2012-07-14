from distutils.core import setup
import py2exe
import sys
import glob

sys.path.append("AnalyzerServer")

exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = []
packageList = []
data_files = [(".", ["AnalyzerServer/SendToP3.ini"])]
setup(console=['AnalyzerServer/SendToP3.py', 
               'AnalyzerServer/DatEchoP3.py',
               ],
     options = dict(py2exe = dict(compressed = 1,
                   optimize = 1,
                   bundle_files = 1,
                   excludes = exclusionList,
                   includes = inclusionList,
                   packages = packageList)),
     data_files = data_files,
    )


