from distutils.core import setup
import py2exe
exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = []
packageList = ["simplejson", "werkzeug", "jinja2", "email"]
setup(console=['RunPeakFinder.py', 'RunPeakAnalyzer.py', 'DatEchoP3.py', 'analyzerServer.py'],
     options = dict(py2exe = dict(compressed = 1,
                   optimize = 1,
                   bundle_files = 1,
                   excludes = exclusionList,
                   includes = inclusionList,
                   packages = packageList)),
    )


