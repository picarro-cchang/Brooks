from distutils.core import setup
import py2exe

exclusionList = ["Tkconstants", "Tkinter", "tcl", '_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                '_fltkagg', '_gtk', '_gtkcairo', ]
                
inclusionList = ["scipy.interpolate",
                 "scipy.misc",
                 "pylab",
                 "numpy",
                 "configobj",
                 "encodings.*",
                 "tables.*"]

consoleList = []
windowList = ['Priming.py']

setup(options = dict(py2exe = dict(compressed = 1,
                                       optimize = 1,
                                       #bundle_files = 1,
                                       excludes = exclusionList)
                         ),
      console = consoleList,
      windows = windowList,
      zipfile = "lib/share")