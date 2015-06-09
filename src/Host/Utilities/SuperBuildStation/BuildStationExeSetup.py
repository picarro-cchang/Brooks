#!/usr/bin/python
#
# File Name: BuildStationExeSetup.py
# Purpose:
#   This is the setup script to create executables for Silverstone.
#
# Notes:
#   Run the build process by entering:
#            'python PicarroExeSetup.py py2exe'
#   in a console prompt.
#
#   If everything works well, you should find a subdirectory named 'dist'
#   with the executables and other data.
#
#   We should add script for customer builds at some point.
#
# File History:
# 06-02-23 sze  First version of basic setup script
# 06-03-28 russ Changed for new project layout; Added data_files; Excluded
#               TCL & Tkinter from build (drops 4MB off of 11MB!)
# 06-04-20 sze  Added Utilities to path and RescaleCalibration to the list of
#                executables.
# 06-05-12 sze  Added build of Yih-Shyang's diagnostic and DAS maintenance GUIs
# 06-05-29 russ Added Librarian; Minor cleanup
# 06-06-07 sze  Added DasRingdownStats, LockerCalibrator and TunerCalibrator for runtime diagnostics
# 06-07-27 sze  Added *.xsvf files in Images directory for FPGA
# 06-08-31 sze  Added remote access utility
# 06-09-14 russ Added MeasSystem
# 08-01-16 sze  Added .iic files in Images directory for FX2 USB
# 08-02-13 sze  Added ValveSequencer to list of executables
# 09-03-12 alex Added Coordinator and ValveSequencer
# 09-10-23 alex Added RDFrequencyConverter and SpectrumCollector; removed CalManager, FrontPanel, and some Utilities modules; renamed ControllerGUI to Controller.
# 10-03-31 alex Added DiagDataCollector

from distutils.core import setup
import py2exe
import sys
import glob
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
#
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
BuildStation = Target(description = "BuildStation", # used for the versioninfo resource
                    script = "BuildStation.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="BuildStation")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "BuildStation"
                    )
DetectorViewer = Target(description = "DetectorViewer", # used for the versioninfo resource
                    script = "DetectorViewer.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="DetectorViewer")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "DetectorViewer"
                    )

################################################################

# And now to the main setup routine...
exclusionList = ["Tkconstants","Tkinter","tcl", '_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                '_fltkagg', '_gtk', '_gtkcairo', ]
inclusionList = ["encodings.*", "tables.*" ]
dllexclusionList = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll']

setup(version = "1.0",
      description = "Build Station Software",
      name = "CRDS Build Station Software",
      options = dict(py2exe = dict(compressed = 1,
                                   optimize = 1,
                                   bundle_files = 1,
                                   excludes = exclusionList,
                                   includes = inclusionList,
                                   dll_excludes = dllexclusionList)
                     ),
      windows = [BuildStation, DetectorViewer])