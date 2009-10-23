#!/usr/bin/python
#
# File Name: PicarroExeSetup.py
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
# 09-10-23 alex  Added RDFrequencyConverter and SpectrumCollector; removed CalManager, FrontPanel, and some Utilities modules; renamed ControllerGUI to Controller.

from distutils.core import setup
import py2exe
import sys
import glob

sys.path.append("Coordinator")
sys.path.append("ValveSequencer")
sys.path.append("AlarmSystem")
sys.path.append("RDFrequencyConverter")
sys.path.append("SpectrumCollector")
sys.path.append("CommandInterface")
sys.path.append("Common")
sys.path.append("autogen")
sys.path.append("Controller")
sys.path.append("DataLogger")
sys.path.append("DataManager")
sys.path.append("Driver")
sys.path.append("ElectricalInterface")
sys.path.append("EventManager")
sys.path.append("Fitter")
sys.path.append("InstMgr")
sys.path.append("Archiver")
sys.path.append("FileEraser")
sys.path.append("MeasSystem")
sys.path.append("QuickGui")
sys.path.append("SampleManager")
sys.path.append("Supervisor")
sys.path.append("Utilities")
sys.path.append("Utilities/DiagGui")
sys.path.append("Utilities/DasMaintenanceGui")
sys.path.append("Utilities/RemoteAccess")

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
controller = Target(description = "Controller", # used for the versioninfo resource
                    script = "Controller/Controller.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="controller")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "controller"
                    )

diaggui = Target(description = "DiagGUI", # used for the versioninfo resource
                    script = "Utilities/DiagGui/DiagGui.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="diaggui")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "DiagGui"
                    )

dasmaintenancegui = Target(description = "DasMaintenanceGUI", # used for the versioninfo resource
                    script = "Utilities/DasMaintenanceGui/DasMaintenanceGui.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="dasmaintenancegui")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "DasMaintenanceGui"
                    )

quickgui = Target(description = "QuickGUI", # used for the versioninfo resource
                    script = "QuickGui/QuickGui.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="quickgui")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "QuickGui"
                    )

fitter = Target(description = "Fitter", # used for the versioninfo resource
                    script = "Fitter/Fitter.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="fitter")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "Fitter"
                    )

# End of special controller setup stuff (except to use controller below)
################################################################

# And now to the main setup routine...
exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = ["email","email.iterators","email.generator","email.mime.audio",
                 "email.mime.multipart","email.mime.image","email.mime.text",
                 "email.mime.base","scipy.interpolate","scipy.misc"]
hex_images = glob.glob("Utilities/DasMaintenanceGui/Images/*.hex")
hex_images = hex_images + glob.glob("Utilities/DasMaintenanceGui/Images/*.xsvf")
hex_images = hex_images + glob.glob("Utilities/DasMaintenanceGui/Images/*.iic")


setup(version = "1.0",
      description = "Silverstone Host Core Software",
      name = "Silverstone CRDS",
      options = dict(py2exe = dict(compressed = 1,
                                   optimize = 1,
                                   bundle_files = 1,
                                   excludes = exclusionList,
                                   includes = inclusionList)
                     ),
      # targets to build...
      console = ["RDFrequencyConverter/RDFrequencyConverter.py",
                 "SpectrumCollector/SpectrumCollector.py",
                 "ValveSequencer/ValveSequencer.py",
                 "Coordinator/Coordinator.py",
                 "AlarmSystem/AlarmSystem.py",
                 "Archiver/Archiver.py",
                 "CommandInterface/CommandInterface.py",
                 "DataLogger/DataLogger.py",
                 "DataManager/DataManager.py",
                 "Driver/driver.py",
                 "ElectricalInterface/ElectricalInterface.py",
                 "EventManager/EventManager.py",
                 "InstMgr/InstMgr.py",
                 "FileEraser/FileEraser.py",
                 "MeasSystem/MeasSystem.py",
                 "SampleManager/SampleManager.py",
                 "Supervisor/supervisor.py",
                 "Utilities/RemoteAccess/RemoteAccess.py",
                 "Utilities/DasMaintenanceGui/usbProgramEEPROM.py",
                 fitter,
                 controller, 
                 diaggui, 
                 dasmaintenancegui, 
                 quickgui],

      data_files = [(".", ["EventManager/Warning_16x16_32.ico",
                           "EventManager/Info_16x16_32.ico",
                           "EventManager/Critical_16x16_32.ico",
                           "Utilities/DasMaintenanceGui/P_RGB_WHITEBCKGRND.bmp",
                           "QuickGui/LEDgreen.ico",
                           "QuickGui/LEDgreen2.ico",
                           "QuickGui/LEDoff.ico",
                           "QuickGui/LEDoff2.ico",
                           "QuickGui/LEDred2.ico",
                           "QuickGui/logo.png",
                           ]),
                    ("Images", hex_images),
                    ]
      )
