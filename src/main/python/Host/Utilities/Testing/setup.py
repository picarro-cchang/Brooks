from distutils.core import setup
import py2exe
exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = []
setup(console=['WriteDataManagerOutput.py'],
     options = dict(py2exe = dict(compressed = 1,
                   optimize = 1,
                   bundle_files = 1,
                   excludes = exclusionList,
                   includes = inclusionList)),
    )
