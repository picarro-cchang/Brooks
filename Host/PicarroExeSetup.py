"""
Copyright 2006-2014 Picarro Inc.

A disutils script that uses py2exe to build Win32 executables for the
Host platform.

Bails if PYTHONPATH is unset, to ensure Picarro.pth is being overridden
so Picarro libs are pulled from the proper dir (primitive check, could
be smarter)

Usage: python PicarroExeSetup py2exe

Notes: Use python buildHost.py from the command line, which sets up
       the environment for this script.
#
# File History:
# 2013-10-30 sze  Remove bundle=1, and write files to lib subdirectory
# 2014-01-14 tw   Support builds in both Python 2.5 and 2.7 so can bring
#                 this file into older release branches. Primitive check
#                 for PYTHONPATH to help ensure local libs pulled from
#                 current tree.
"""

from __future__ import with_statement

from distutils.core import setup
import py2exe
import sys
import glob
import time
import subprocess
import os.path
import platform

from Host.Common import OS
from Host.Common import version as hostVersion

version = sys.version_info
pyDirname = "Python%d%d" % (version[0],version[1])
sys.path.append("ActiveFileManager")
sys.path.append("Coordinator")
sys.path.append("ValveSequencer")
sys.path.append("AlarmSystem")
sys.path.append("RDFrequencyConverter")
sys.path.append("SpectrumCollector")
sys.path.append("CommandInterface")
sys.path.append("Common")
sys.path.append("autogen")
sys.path.append("Controller")
# sys.path.append("ControllerBuildStation")
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
sys.path.append("ReadExtSensor")
sys.path.append("IPV")
sys.path.append("ConfigMonitor")
sys.path.append("PeriphIntrf")
sys.path.append("Utilities")
sys.path.append("WebServer")
sys.path.append("rdReprocessor")
sys.path.append("Utilities/RemoteAccess")
sys.path.append("Utilities/DiagDataCollector")
sys.path.append("Utilities/SupervisorLauncher")
sys.path.append("Utilities/CoordinatorLauncher")
sys.path.append("Utilities/FluxSwitcher")
sys.path.append("Utilities/ValveDisplay")
sys.path.append("Utilities/InstrEEPROMAccess")
sys.path.append("Utilities/DataRecal")
sys.path.append("Utilities/IntegrationTool")
sys.path.append("Utilities/SetupTool")
sys.path.append("Utilities/PicarroKML")
sys.path.append("Utilities/ReadGPSWS")
sys.path.append("Utilities/IntegrationBackup")
sys.path.append("Utilities/FlowController")
sys.path.append("Utilities/ReadMemUsage")
sys.path.append("Utilities/PeriphModeSwitcher")
sys.path.append("Utilities/RecipeEditor")
sys.path.append("Utilities/BackpackServer")
sys.path.append("Utilities/ConfigManager")
sys.path.append("Utilities/AircraftValveSwitcher")
sys.path.append("Utilities/ProgramVariableGainRdd")
sys.path.append("Utilities/RestartSupervisor")
sys.path.append('Utilities/KillRestartSupervisor')
sys.path.append("../Firmware/Utilities")

sys.stderr = sys.stdout

def _getPythonVersion():
    """
    Returns a string such as "2.5" or 2.7"
    """
    pythonVer = sys.version_info
    return str(pythonVer[0]) + "." + str(pythonVer[1])


def _getPythonSubVersion():
    """
    Returns a string such as "2.7.3"
    """
    pythonVer = sys.version_info
    return str(pythonVer[0]) + "." + str(pythonVer[1]) + "." + str(pythonVer[2])


def _getOsType():
    osType = platform.uname()[2]

    if osType == '7':
        osType = 'win7'
    elif osType == 'XP':
        osType = 'winxp'
    else:
        osType = 'unknown'
        print "Unexpected OS type!"

    return osType


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
#

cDep = ""
if version[0] == 2 and version[1] > 5:
    cDep = """
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="X86"
            publicKeyToken="1fc8b3b9a1e18e3b"
            language="*"
        />
    </dependentAssembly>
</dependency>
    """
manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
  version="5.0.0.0"
  processorArchitecture="x86"
  name="%%(prog)s"
  type="win32"
/>
<description>%%(prog)s Program</description>
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
%s
</assembly>
''' % (cDep,)
RT_MANIFEST = 24
Controller = Target(description = "Controller", # used for the versioninfo resource
                    script = "Controller/Controller.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="Controller")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "Controller"
                    )

#ControllerBuildStation = Target(description = "ControllerBuildStation", # used for the versioninfo resource
#                    script = "ControllerBuildStation/ControllerBuildStation.py", # what to build
#                    other_resources = [(RT_MANIFEST,
#                                        1,
#                                        manifest_template % dict(prog="ControllerBuildStation")
#                                        )],
#                    ##    icon_resources = [(1, "icon.ico")],
#                    dest_base = "ControllerBuildStation"
#                    )

QuickGui = Target(description = "QuickGui", # used for the versioninfo resource
                    script = "QuickGui/QuickGui.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="QuickGui")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "QuickGui"
                    )

Fitter = Target(description = "Fitter", # used for the versioninfo resource
                    script = "Fitter/Fitter.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="Fitter")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "Fitter"
                    )

Coordinator = Target(description = "Coordinator", # used for the versioninfo resource
                    script = "Coordinator/Coordinator.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="Coordinator")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "Coordinator"
                    )

deltaCorrProcessor = Target(description = "DeltaCorrProcessor", # used for the versioninfo resource
                    script = "Coordinator/DeltaCorrProcessor.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="deltaCorrProcessor")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "DeltaCorrProcessor"
                    )

dilutionCorrProcessor = Target(description = "DilutionCorrProcessor", # used for the versioninfo resource
                    script = "Coordinator/DilutionCorrProcessor.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="dilutionCorrProcessor")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "DilutionCorrProcessor"
                    )

supervisorLauncher = Target(description = "SupervisorLauncher", # used for the versioninfo resource
                    script = "Utilities/SupervisorLauncher/SupervisorLauncher.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="supervisorLauncher")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "SupervisorLauncher"
                    )

# End of special controller setup stuff (except to use controller below)
################################################################

# simple check to save us from potential problems using paths in Picarro.pth
if "PYTHONPATH" not in os.environ:
    print "PYTHONPATH is not set in environment, potential exists for pulling local libs from wrong dir."
    print "Run 'python buildHost.py' instead to build Host apps from the command line."
    sys.exit(1)


pythonVer = _getPythonVersion()
pythonSubVer = _getPythonSubVersion()
osType = _getOsType()


# Build the various Host .pyd modules
#
# Fitter: build cluster_analyzer.pyd and fitutils.pyd
if pythonVer == "2.5":
    fitutilsBatFilename = "makeFitutils25.bat"
elif pythonVer == "2.7":
    fitutilsBatFilename = "makeFitutils27.bat"
else:
    print "Unsupported Python version %s!" % pythonVer
    sys.exit(1)

_runBatFile("fitutils.pyd, cluster_analyzer.pyd", fitutilsBatFilename, "Fitter")

# Common: swathP.pyd
if pythonVer == "2.5":
    swathPBatFilename = "makeSwathP25.bat"
elif pythonVer == "2.7":
    swathPBatFilename = "makeSwathP27.bat"
else:
    print "Unsupported Python version %s!" % pythonVer
    sys.exit(1)

_runBatFile("swathP.pyd", swathPBatFilename, "Common")

# Utilities\SuperBuildStation: fastLomb.pyd
_runBatFile("fastLomb.pyd", "setup.bat", os.path.join("Utilities", "SuperBuildStation"))

versionStr = _getBuildVersion()


# And now to the main setup routine...
#
# The following lists and tuples are common to both Python 2.5 and 2.7 builds. If any
# require customization, they must be moved and maintained separately under the if statements below.
exclusionList = ["Tkconstants", "Tkinter", "tcl", '_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                '_fltkagg', '_gtk', '_gtkcairo', ]

inclusionList = ["email",
                 "email.iterators",
                 "email.generator",
                 "email.mime.audio",
                 "email.mime.multipart",
                 "email.mime.image",
                 "email.mime.text",
                 "email.mime.base",
                 "scipy.interpolate",
                 "scipy.misc",
                 "sip",
                 "matplotlib.backends",
                 "matplotlib.backends.backend_wxagg",
                 "matplotlib.backends.backend_qt4agg",
                 "matplotlib.figure",
                 "pylab",
                 "numpy",
                 "configobj",
                 "encodings.*",
                 "tables.*"]

dllexclusionList = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', "mswsock.dll", "powrprof.dll" ]

hex_images = glob.glob("../Firmware/CypressUSB/Drivers/*.*")
hex_images = hex_images + [ "../Firmware/CypressUSB/analyzer/analyzerUsb.hex",
                            "../Firmware/DSP/src/Debug/dspMain.hex",
                            "../Firmware/MyHDL/Spartan3/top_io_map.bit"]

cypressDriverDirs = ["amd64", "ia64", "license/libusb0", "x86"]

data_files = [(".", ["EventManager/Warning_16x16_32.ico",
                   "EventManager/Info_16x16_32.ico",
                   "EventManager/Critical_16x16_32.ico",
                   "QuickGui/LEDgreen.ico",
                   "QuickGui/LEDgreen2.ico",
                   "QuickGui/LEDoff.ico",
                   "QuickGui/LEDoff2.ico",
                   "QuickGui/LEDred2.ico",
                   "QuickGui/logo.png",
                   "Fitter/fitutils.pyd",
                   "Fitter/cluster_analyzer.pyd",
                   "Utilities/SupervisorLauncher/Check.png",
                   "Utilities/SupervisorLauncher/alarm.png",
                   "Utilities/SupervisorLauncher/Cancel.ico",
                   "Utilities/SupervisorLauncher/Controller_icon.ico",
                   "Utilities/SupervisorLauncher/Diagnostics_icon.ico",
                   "Utilities/SupervisorLauncher/EnviroSense.ico",
                   "Utilities/SupervisorLauncher/Integration_icon.ico",
                   "Utilities/SupervisorLauncher/Picarro_icon.ico",
                   "Utilities/SupervisorLauncher/Utilities_icon.ico",
                   "PeriphIntrf/Serial2Socket.exe",
                   "../MobileKit/AnalyzerServer/configAnalyzerServer.ini",
                   "../repoBzrVer.py"]),
            (r'mpl-data', glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\*.*' % pyDirname)),
            # Because matplotlibrc does not have an extension, glob does not find it (at least I think that's why)
            # So add it manually here:
            (r'mpl-data', [r'C:\%s\Lib\site-packages\matplotlib\mpl-data\matplotlibrc' % pyDirname]),
            (r'mpl-data\images',glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\images\*.*' % pyDirname)),
            (r'mpl-data\fonts',glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\fonts\*.*' % pyDirname)),
            ("Images", hex_images),
            ("static", glob.glob(r'Utilities\BackpackServer\static\*.*')),
            ("templates", glob.glob(r'Utilities\BackpackServer\templates\*.*')),
            ("static", glob.glob(r'..\MobileKit\AnalyzerServer\static\*.*')),
            ("templates", glob.glob(r'..\MobileKit\AnalyzerServer\templates\*.*')),
            (r"static\images", glob.glob(r'..\MobileKit\AnalyzerServer\static\images\*.*')),
            (r"static\images\icons", glob.glob(r'..\MobileKit\AnalyzerServer\static\images\icons\*.*')),
            (r"static\css", glob.glob(r'..\MobileKit\AnalyzerServer\static\css\*.*')),
            (r"static\sound", glob.glob(r'..\MobileKit\AnalyzerServer\static\sound\*.*')),
            ]
for d in cypressDriverDirs:
    data_files.append(("Images/%s"%d, glob.glob("../Firmware/CypressUSB/Drivers/" + "%s/*.*" %d)))

if osType == "winxp":
    data_files.append("../Vendor/inpout/winxp/inpout32.dll")
elif osType == "win7":
    data_files.append("../Vendor/inpout/win7/Win32/inpout32.dll")
else:
    print "Failed to include inpout32.dll in build, OS is not supported! (osType='%s')" % osType
    sys.exit(1)


consoleList = [
    "ActiveFileManager/ActiveFileManager.py",
    "RDFrequencyConverter/RDFrequencyConverter.py",
    "SpectrumCollector/SpectrumCollector.py",
    "ValveSequencer/ValveSequencer.py",
    "AlarmSystem/AlarmSystem.py",
    "Archiver/Archiver.py",
    "CommandInterface/CommandInterface.py",
    "Common/SchemeProcessor.py",
    "DataLogger/DataLogger.py",
    "DataManager/DataManager.py",
    "Driver/Driver.py",
    "ElectricalInterface/ElectricalInterface.py",
    "EventManager/EventManager.py",
    "InstMgr/InstMgr.py",
    "FileEraser/FileEraser.py",
    "MeasSystem/MeasSystem.py",
    "SampleManager/SampleManager.py",
    "Supervisor/Supervisor.py",
    "ReadExtSensor/ReadExtSensor.py",
    "WebServer/server.py",
    "rdReprocessor/rdReprocessor.py",
    "Utilities/RemoteAccess/RemoteAccess.py",
    "Utilities/IntegrationTool/IntegrationTool.py",
    "Utilities/IntegrationBackup/IntegrationBackup.py",
    "Utilities/FlowController/FlowController.py",
    "Utilities/Restart/ResetAnalyzer.py",
    "Utilities/Restart/RestoreStartup.py",
    "Utilities/Restart/RtcAlarmOff.py",
    "Utilities/ReadMemUsage/ReadMemUsage.py",
    "Utilities/BackpackServer/backpackServer.py",
    "Utilities/RestartSupervisor/RestartSupervisor.py",
    "Utilities/ProgramVariableGainRdd/programRdd.py",
    'Utilities/KillRestartSupervisor/KillRestartSupervisor.py',
    "../Firmware/Utilities/CalibrateSystem.py",
    "../Firmware/Utilities/CalibrateFsr.py",
    "../Firmware/Utilities/AdjustWlmOffset.py",
    "../Firmware/Utilities/ExamineRawRD.py",
    "../Firmware/Utilities/ExamineRDCount.py",
    "../Firmware/Utilities/LaserLockPrbs.py",
    "../Firmware/Utilities/LaserPidPrbs.py",
    "../Firmware/Utilities/MakeWarmBoxCalFile.py",
    "../Firmware/Utilities/MakeWarmBoxCal_NoWlm.py",
    "../Firmware/Utilities/MakeWlmFile1.py",
    "../Firmware/Utilities/WriteLaserEeprom.py",
    "../Firmware/Utilities/MakeNoWlmFile.py",
    "../Firmware/Utilities/WriteWlmEeprom.py",
    "../Firmware/Utilities/DumpEeproms.py",
    "../Firmware/Utilities/MakeCalFromEeproms.py",
    "../Firmware/Utilities/FindWlmOffset.py",
    "../Firmware/Utilities/SaveData.py",
    "../Firmware/Utilities/SaveRaw.py",
    "../Firmware/Utilities/TestClient.py",
    "../Firmware/Utilities/ThresholdStats.py",
    "../Firmware/Utilities/CheckLaserCal.py",
    Fitter,
    "ConfigMonitor/ConfigMonitor.py",
    "PeriphIntrf/RunSerial2Socket.py",
    'LockWorkstation/LockWorkstation.py'
]

windowsList = [
    QuickGui, Coordinator,Controller,deltaCorrProcessor, dilutionCorrProcessor,
    "Common/StopSupervisor.py",
    "IPV/IPV.py",
    "IPV/IPVLicense.py",
    "Utilities/DiagDataCollector/DiagDataCollector.py",
    supervisorLauncher,
    "Utilities/SupervisorLauncher/HostStartup.py",
    "Utilities/CoordinatorLauncher/CoordinatorLauncher.py",
    "Utilities/FluxSwitcher/FluxScheduler.py",
    "Utilities/FluxSwitcher/FluxSwitcherGui.py",
    "Utilities/ValveDisplay/ValveDisplay.py",
    "Utilities/InstrEEPROMAccess/InstrEEPROMAccess.py",
    "Utilities/DataRecal/DataRecal.py",
    "Utilities/SetupTool/SetupTool.py",
    "Utilities/PicarroKML/PicarroKML.py",
    "Utilities/ReadGPSWS/ReadGPSWS.py",
    "Utilities/PeriphModeSwitcher/PeriphModeSwitcher.py",
    "Utilities/RecipeEditor/RecipeEditor.py",
    "Utilities/ConfigManager/ConfigManager.py",
    "Utilities/AircraftValveSwitcher/AircraftValveSwitcher.py",
]

# Autogenerate required files
with OS.chdir(os.path.join(os.path.dirname(__file__), '..', 'Firmware', 'xml')):
    subprocess.Popen(['python.exe', 'xmldom1.py']).wait()

# Generate repo version
with open(os.path.join(os.path.dirname(__file__), '..',
                       'repoBzrVer.py'), 'w') as fp:
    subprocess.Popen(['bzr.exe', 'version-info', '--python'], stdout=fp).wait()

# Generate internal build version
with open(os.path.join(os.path.dirname(__file__), 'Common',
                       'setup_version.py'), 'w') as fp:
    fp.writelines(
        ["# autogenerated by PicarroExeSetup.py, %s\n" % time.asctime(),
         "\n",
         "def versionString():\n",
         "    return '%s'\n" % hostVersion.versionString()])


if pythonVer == "2.5":
    # only packageList differs for Python 2.5 and 2.7
    packageList = ["simplejson", "werkzeug","flask","jinja2","email"]

    setup(version = versionStr,
      description = "Silverstone Host Core Software",
      name = "Silverstone CRDS",
      options = dict(py2exe = dict(compressed = 1,
                                   optimize = 1,
                                   bundle_files = 1,
                                   excludes = exclusionList,
                                   includes = inclusionList,
                                   dll_excludes = dllexclusionList,
                                   packages = packageList)
                     ),
      # targets to build...
      console = consoleList,
      windows = windowsList,
      data_files = data_files
)

elif pythonVer == "2.7":
    if pythonSubVer == "2.7.3":
        import zmq
        os.environ["PATH"] += os.path.pathsep + os.path.split(zmq.__file__)[0]

    packageList = ["werkzeug","jinja2","email"]

    # no bundle_files, specify zipfile
    setup(version = versionStr,
          description = "Silverstone Host Core Software",
          name = "Silverstone CRDS",
          options = dict(py2exe = dict(compressed = 1,
                                       optimize = 1,
                                       # bundle_files = 1,
                                       excludes = exclusionList,
                                       includes = inclusionList,
                                       dll_excludes = dllexclusionList,
                                       packages = packageList)
                         ),
          # targets to build...
          console = consoleList,
          windows = windowsList,
          data_files = data_files,
          zipfile = "lib/share"
    )

else:
    print "Unsupported Python version %s" % pythonVer
    sys.exit(1)
