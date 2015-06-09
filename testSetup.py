from distutils.core import setup
from Common import version as hostVersion
import glob
import py2exe
import os
import platform
import sys
import time

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


def _getPythonVersion():
    """
    Returns a string such as "2.5" or 2.7"
    """
    pythonVer = sys.version_info
    return str(pythonVer[0]) + "." + str(pythonVer[1])


def _getBuildVersion():
    try:
        # First look for release_version which is generated by
        # release.py
        from Host.Common import release_version as buildVersion
        verStr = buildVersion.versionNumString()
        print "Release version: %s" % verStr
    except Exception, e:
        # Next try build_version which is generated by
        # buildHost.py (command line script for internal builds)
        try:
            import build_version as buildVersion
            verStr = buildVersion.versionNumString()
            print "Setup version: %s" % verStr
        except Exception, e:
            # use default
            verStr = "1.0.0.0"
            print "Release or setup version not found, using: %s" % verStr

    return verStr


def _getBuildType():
    try:
        # First look for release_version which is generated by
        # release.py
        import release_version as buildVersion
        buildTypeStr = buildVersion.buildType()
        print "Release build type: %s" % buildTypeStr
    except Exception, e:
        try:
            # Not found, try setup_version (generated by buildHost.py
            # during internal builds)
            #import build_version as buildVersion
            #buildTypeStr = buildVersion.buildType()
            #print "Setup build type: %s" % buildTypeStr

            # Internal build, includes last git check-in SHA1
            # returns "Internal (<SHA1>)"
            buildTypeStr = hostVersion.versionString()
            print "Setup build type: %s" % buildTypeStr

        except Exception, e:
            # Should never get here...
            buildTypeStr = "DEVELOPMENT"
            print "Release or setup version build type not found, using: %s" % buildTypeStr

    return buildTypeStr


class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)

if __name__ == "__main__":
    # Get the current dir. Expect that we are in the Host folder.
    curDirPath = os.getcwd()
    curDir = os.path.split(curDirPath)[1]

    # Windows dirs are not case-sensitive. 
    # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
    if curDir.lower() != "host":
        print "Not running in expected folder 'Host'!"
        sys.exit(1)
    
    # Set the PYTHONPATH environment variable so the current folder tree is used to
    # pull local libraries from.
    parentDir = os.path.normpath(os.path.join(curDirPath, ".."))
    firmwareDir = os.path.normpath(os.path.join(curDirPath, "..", "Firmware"))
    
    # for a sanity check -- not needed in PYTHONPATH as the parent dir will already be there
    commonDir = os.path.join(parentDir, "Host", "Common")
    
    # folders must exist
    folders = [parentDir, commonDir, firmwareDir]
    for folder in folders:
        print "folder=", folder
        if not os.path.isdir(folder):
            print "Expected folder '%s' does not exist!", folder
            sys.exit(1)
            
    osType = _getOsType()
    pythonVer = _getPythonVersion()
    version = sys.version_info
    pyDirname = "Python%d%d" % (version[0],version[1])
    versionStr = _getBuildVersion()
    buildTypeStr = _getBuildType()
    
    sys.path.insert(1,firmwareDir)
    sys.path.insert(1,parentDir)
    
    cDep = ""

    if pythonVer == "2.7":
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
        
    manifest_template = """
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
    """ % (cDep,)
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
                       "PeriphIntrf/Serial2Socket.exe"]),
                (r'mpl-data', glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\*.*' % pyDirname)),
                # Because matplotlibrc does not have an extension, glob does not find it (at least I think that's why)
                # So add it manually here:
                (r'mpl-data', [r'C:\%s\Lib\site-packages\matplotlib\mpl-data\matplotlibrc' % pyDirname]),
                (r'mpl-data\images',glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\images\*.*' % pyDirname)),
                (r'mpl-data\fonts',glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\fonts\*.*' % pyDirname)),
                ("Images", hex_images),
                ("static", glob.glob(r'Utilities\BackpackServer\static\*.*')),
                ("templates", glob.glob(r'Utilities\BackpackServer\templates\*.*'))
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
        "EventLogWatcher/EventLogWatcher.py",
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
        "ConfigMonitor/ConfigMonitor.py",
        "PeriphIntrf/RunSerial2Socket.py",
        'LockWorkstation/LockWorkstation.py'
    ]
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
                        
    windowsList = [
        Controller,
        Coordinator,
        deltaCorrProcessor, 
        dilutionCorrProcessor,
        Fitter, 
        QuickGui, 
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

    # Generate internal build version
    with open(os.path.join(os.path.dirname(__file__), 'Common',
                           'setup_version.py'), 'w') as fp:
        fp.writelines(
            ["# autogenerated by PicarroExeSetup.py, %s\n" % time.asctime(),
             "\n",
             "def versionString():\n",
             "    return '%s'\n" % hostVersion.versionString()])


    description = "Picarro Host Core Analyzer Software"

    productName = "Picarro CRDS"
    if buildTypeStr != "":
        productName = "Picarro CRDS (%s)" % buildTypeStr
    if pythonVer == "2.5":
        # only packageList differs for Python 2.5 and 2.7
        packageList = ["simplejson", "werkzeug","flask","jinja2","email"]

        setup(version = versionStr,
          description = description,
          name = productName,
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
        import zmq
        os.environ["PATH"] += os.path.pathsep + os.path.split(zmq.__file__)[0]

        packageList = ["werkzeug","jinja2","email"]

        # no bundle_files, specify zipfile
        setup(version = versionStr,
              description = description,
              name = productName,
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
