from distutils.core import setup
import os
import py2exe
import shutil
import sys
import glob

sys.path.append("AnalyzerServer")
sys.path.append("MobileKitSetupNew")
sys.path.append("ViewServer")
sys.path.append("WeatherStation")

exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = []
packageList = ["simplejson", "werkzeug", "jinja2", "email"]
data_files = [(".", ["MobileKitSetupNew/LEDgreen2.ico", "MobileKitSetupNew/LEDred2.ico", "MobileKitSetupNew/MobileKitSetup.ini",
                    "MobileKitSetupNew/MobileKit_inactive.ini", "ViewServer/view.kml", "WeatherStation/platBoundaries.json"]),
              (r'static\css', glob.glob(r'WeatherStation\static\css\*.*')),
              (r'static\images', glob.glob(r'WeatherStation\static\images\*.*')),
              (r'static\img', glob.glob(r'WeatherStation\static\img\*.*')),
              (r'static\scripts', glob.glob(r'WeatherStation\static\scripts\*.*')),
              (r'templates', glob.glob(r'WeatherStation\templates\*.*')),
             ]
setup(console=['AnalyzerServer/RunPeakFinder.py', 
               'AnalyzerServer/RunPeakAnalyzer.py', 
               'AnalyzerServer/DatEchoP3.py', 
               'AnalyzerServer/analyzerServer.py',
               'ViewServer/ViewServer.py',
               'WeatherStation/reportServer.py',
               ],
     windows=['MobileKitSetupNew/MobileKitSetup.py',
              'MobileKitSetupNew/RemoteMobileKitSetup.py',],
     options = dict(py2exe = dict(compressed = 1,
                   optimize = 1,
                   bundle_files = 1,
                   excludes = exclusionList,
                   includes = inclusionList,
                   packages = packageList)),
     data_files = data_files,
                   
    )
shutil.copyfile('dist/DatEchoP3.exe','dist/GPSEchoP3.exe')
shutil.copyfile('dist/DatEchoP3.exe','dist/WSEchoP3.exe')

