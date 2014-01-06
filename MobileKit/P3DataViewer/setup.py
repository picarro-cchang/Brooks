from distutils.core import setup
import py2exe
import sys

exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = []
packageList = ["simplejson", "werkzeug", "jinja2", "email"]
data_files = [(".", [])]
setup(console=['P3ViewFrame.py', 
               'dummyServer.py'],
     options = dict(py2exe = dict(compressed = 1,
                   optimize = 1,
                   # bundle_files = 1,
                   excludes = exclusionList,
                   includes = inclusionList,
                   packages = packageList)),
     data_files = data_files,
     zipfile = "lib/shared"              
    )


