"""
Copyright 2006-2014 Picarro Inc.

A disutils script that uses py2exe to build Win32 executables for the
MobileKit platform.

Bails if PYTHONPATH is unset, to ensure Picarro.pth is being overridden
so Picarro libs are pulled from the proper dir (primitive check, could
be smarter).

Usage: python PicarroExeSetup py2exe

Notes: Use python buildMobileKit.py from the command line, which sets up
       the environment for this script.
"""
from __future__ import with_statement

from distutils.core import setup
import os
import py2exe
import shutil
import sys
import glob
import subprocess
import zmq

from Host.Common import OS

os.environ["PATH"] = os.environ["PATH"] + os.path.pathsep + \
    os.path.split(zmq.__file__)[0]

sys.path.append("AnalyzerServer")
sys.path.append("MobileKitSetupNew")
sys.path.append("Utilities")
sys.path.append("ViewServer")
sys.path.append("ReportGen")

sys.stderr = sys.stdout


def _getPythonVersion():
    """
    Returns a string such as "2.5" or "2.7"
    """
    pythonVer = sys.version_info
    return str(pythonVer[0]) + "." + str(pythonVer[1])


def _getPythonSubVersion():
    """
    Returns a string such as "2.7.3"
    """
    pythonVer = sys.version_info
    return str(pythonVer[0]) + "." + str(pythonVer[1]) + "." + str(pythonVer[2])


def _runBatFile(batComponent, batFilename, batDir):
    """
    Runs a Windows .bat file to build a component. Arguments:
      batComponent   name of component being built (e.g., fitutils.pyd)
      batFilename    Windows .bat filename to execute
      batDir         folder containing the .bat file (can be relative to current dir)
    """
    print "building %s using %s" % (batComponent, batFilename)

    # this saves off current folder and restores it when done
    with OS.chdir(batDir):
        if not os.path.isfile(batFilename):
            print "Batch file '%s' does not exist in folder '%s'!" % (batFilename, batDir)
            sys.exit(1)

        retCode = subprocess.Popen([batFilename]).wait()

        if retCode != 0:
            print "Error building %s, retCode=%d, batFilename=%s" % (batComponent, retCode, batFilename)
            sys.exit(retCode)


def _getBuildVersion():
    try:
        from Host.Common import release_version as buildVersion
        verStr = buildVersion.versionNumString()
        print "Release version: %s" % verStr
    except Exception, e:
        # use default
        verStr = "1.0"
        print "Release version not found, using: %s" % verStr

    return verStr


################################################################
# Start of a pile of special setup with the sole purpose
# of making the wxPython apps look like Windows-native
#
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
# The manifest will be inserted as resource into test_wx.exe.  This
# gives the controls the Windows XP appearance (if run on XP ;-)
#
# Another option would be to store it in a file named
# test_wx.exe.manifest, and copy it with the data_files option into
# the dist-dir.

manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
  version="5.0.0.0"
  processorArchitecture="x86"
  name="%(prog)s"
  type="win32"
/>
<description>%(prog)s Program</description>
<dependency>
  <dependentAssembly>
    <assemblyIdentity
      type="win32"
      name="Microsoft.Windows.Common-Controls"
      version="6.0.0.0"
      processorArchitecture="X86"
      publicKeyToken="6595b64144ccf1df"
      language="*"
    />
  </dependentAssembly>
</dependency>
</assembly>
'''

RT_MANIFEST = 24
MobileKitSetup = Target(description = "MobileKitSetup", # used for the versioninfo resource
                    script = "MobileKitSetupNew/MobileKitSetup.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="MobileKitSetup")
                                        )],
                    dest_base = "MobileKitSetup"
                    )
RemoteMobileKitSetup = Target(description = "RemoteMobileKitSetup", # used for the versioninfo resource
                    script = "MobileKitSetupNew/RemoteMobileKitSetup.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="RemoteMobileKitSetup")
                                        )],
                    dest_base = "RemoteMobileKitSetup"
                    )

pythonVer = _getPythonVersion()
pythonSubVer = _getPythonSubVersion()

"""
# simple check to save us from potential problems using paths in Picarro.pth
if "PYTHONPATH" not in os.environ:
    print "PYTHONPATH is not set in environment, potential exists for pulling local libs from wrong dir."
    print "Run 'python buildMobileKit.py' instead to build MobileKit apps from the command line."
    sys.exit(1)
"""

# ../Host/Common: swathP.pyd
# AnalyzerServer: peakF.pyd
if pythonVer == "2.5":
    swathPBatFilename = "makeSwathP25.bat"
    peakFBatFilename = "makePeakF25.bat"
elif pythonVer == "2.7":
    swathPBatFilename = "makeSwathP27.bat"
    peakFBatFilename = "makePeakF27.bat"
else:
    print "Unsupported Python version %s!" % pythonVer
    sys.exit(1)

_runBatFile("swathP.pyd", swathPBatFilename, os.path.join("..", "Host", "Common"))
_runBatFile("peakF.pyd", peakFBatFilename, "AnalyzerServer")

versionStr = _getBuildVersion()

if pythonVer == "2.5":
    # Python 2.5
    exclusionList = ["Tkconstants", "Tkinter", "tcl"]
    inclusionList = []
    packageList = ["simplejson", "werkzeug", "jinja2", "email", 'sqlalchemy.dialects.sqlite']
    data_files = [(".", ["MobileKitSetupNew/LEDgreen2.ico",
                         "MobileKitSetupNew/LEDred2.ico",
                         "MobileKitSetupNew/MobileKitSetup.ini",
                         "MobileKitSetupNew/MobileKit_inactive.ini",
                         "ViewServer/view.kml",
                         "ReportGen/platBoundaries.json",
                         "msvcp71.dll",
                         "AnalyzerServer/openssl.cnf"]),
                  (r'static\css', glob.glob(r'ReportGen\static\css\*.*')),
                  (r'static\images', glob.glob(r'ReportGen\static\images\*.*')),
                  (r'static\img', glob.glob(r'ReportGen\static\img\*.*')),
                  (r'static\scripts', glob.glob(r'ReportGen\static\scripts\*.*')),
                  (r'templates', glob.glob(r'ReportGen\templates\*.*')),
                 ]

    setup(version=versionStr,
          console=['AnalyzerServer/RunPeakFinder.py',
                   'AnalyzerServer/RunPeakAnalyzer.py',
                   'AnalyzerServer/DatEchoP3.py',
                   'AnalyzerServer/analyzerServer.py',
                   'ViewServer/ViewServer.py',
                   'ReportGen/batchReport.py',
                   'ReportGen/reportServer.py',
                   'Utilities/createReportBooklet.py'
                   ],
          windows=[MobileKitSetup, RemoteMobileKitSetup],
          options = dict(py2exe = dict(compressed = 1,
                         optimize = 1,
                         bundle_files = 1,
                         excludes = exclusionList,
                         includes = inclusionList,
                         packages = packageList)),
          data_files = data_files
        )
    shutil.copyfile('dist/DatEchoP3.exe','dist/GPSEchoP3.exe')
    shutil.copyfile('dist/DatEchoP3.exe','dist/WSEchoP3.exe')

elif pythonVer == "2.7":
    # Python 2.7
    print "**** setup for Python 2.7 ****"

    exclusionList = ["Tkconstants", "Tkinter", "tcl"]
    inclusionList = ["zmq.core.*", "zmq.utils", "zmq.utils.jsonapi", "zmq.utils.strtypes"]
    packageList = ["simplejson", "werkzeug", "jinja2", "email", 'sqlalchemy.dialects.sqlite']

    data_files = [(".", ["MobileKitSetupNew/LEDgreen2.ico",
                         "MobileKitSetupNew/LEDred2.ico",
                         "MobileKitSetupNew/MobileKitSetup.ini",
                         "MobileKitSetupNew/MobileKit_inactive.ini",
                         "ViewServer/view.kml",
                         "ReportGen/platBoundaries.json",
                         "msvcp71.dll",
                         "AnalyzerServer/openssl.cnf"]),
                  (r'static\css', glob.glob(r'ReportGen\static\css\*.*')),
                  (r'static\images', glob.glob(r'ReportGen\static\images\*.*')),
                  (r'static\img', glob.glob(r'ReportGen\static\img\*.*')),
                  (r'static\scripts', glob.glob(r'ReportGen\static\scripts\*.*')),
                  (r'templates', glob.glob(r'ReportGen\templates\*.*')),
                 ]

    #  Remove bundle=1, and write files to lib subdirectory
    setup(version=versionStr,
          console=['AnalyzerServer/RunPeakFinder.py', 
                   'AnalyzerServer/RunPeakAnalyzer.py', 
                   'AnalyzerServer/DatEchoP3.py', 
                   'AnalyzerServer/analyzerServer.py',
                   'ViewServer/ViewServer.py',
                   'ReportGen/batchReport.py',
                   'ReportGen/reportServer.py',
                   'Utilities/createReportBooklet.py'],
          windows=[MobileKitSetup, RemoteMobileKitSetup],
          options = dict(py2exe = dict(compressed = 1,
                         optimize = 1,
                         # bundle_files = 1,
                         excludes = exclusionList,
                         includes = inclusionList,
                         packages = packageList)),
          data_files = data_files,
          zipfile = "lib/shared"
          )

    shutil.copyfile('dist/DatEchoP3.exe','dist/GPSEchoP3.exe')
    shutil.copyfile('dist/DatEchoP3.exe','dist/WSEchoP3.exe')

else:
    print "Unsupported Python version %s" % pythonVer
    sys.exit(1)
