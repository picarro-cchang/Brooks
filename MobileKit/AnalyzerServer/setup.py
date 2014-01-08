from distutils.core import setup
import py2exe
import sys

sys.path.append("AnalyzerServer")
sys.path.append("MobileKitSetupNew")
sys.path.append("ViewServer")

exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = []
packageList = ["simplejson", "werkzeug", "jinja2", "email", 'sqlalchemy.databases.sqlite']
data_files = [(".", ["MobileKitSetupNew/LEDgreen2.ico", "MobileKitSetupNew/LEDred2.ico"])]
setup(console=['AnalyzerServer/RunPeakFinder.py', 
               'AnalyzerServer/RunPeakAnalyzer.py', 
               'AnalyzerServer/DatEchoP3.py', 
               'AnalyzerServer/analyzerServer.py',
               'ViewServer/ViewServer.py',],
     windows=['MobileKitSetupNew/MobileKitSetup.py',],
     options = dict(py2exe = dict(compressed = 1,
                   optimize = 1,
                   bundle_files = 1,
                   excludes = exclusionList,
                   includes = inclusionList,
                   packages = packageList)),
     data_files = data_files,
                   
    )


