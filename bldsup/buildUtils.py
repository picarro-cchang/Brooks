import os
import glob

def get_package_resource(base_path):
    """
    Return a list of python files and other resources that
    will be distributed. Note that this list does NOT include
    python files that are cythonized (list of cythonized modules
    can be obtained from get_raw_source_list in setupforPyd.py)
    """
    sourceFiles = []
    includeFolderList = [
        "Assets/icons/*.ico",
        "Host/__init__.py",
        "Host/DriverSimulator/*.py",
        "Host/Controller/*.py",
        "Host/Coordinator/*.py",
        "Host/MfgUtilities/*.py",
        "Host/pydCaller/*.*",
        "Host/QuickGui/*.*",
        "Host/WebServer/*.*",
        "Host/Utilities/__init__.py",
        "Host/Utilities/ConfigManager/*.py",
        "Host/Utilities/CoordinatorLauncher/*.py",
        "Host/Utilities/DataRecal/*.py",
        "Host/Utilities/FlowController/*.py",
        "Host/Utilities/InstrEEPROMAccess/*.py",
        "Host/Utilities/IntegrationTool/*.py",
        "Host/Utilities/ModbusServer/*.py",
        "Host/Utilities/RestartSupervisor/*.py",
        "Host/Utilities/SetupTool/*.py",
        "Host/Utilities/SupervisorLauncher/*.py",
        "Host/Utilities/Four220/*.*",
        "AddOns/DatViewer/*.py",
        "AddOns/DatViewer/Scripts/*.py",
        "AddOns/DatViewer/tzlocal/*.py",
        "AddOns/DatViewer/Manual/*.*",
        "AddOns/DatViewer/Manual/_images/*.*",
        "AddOns/DatViewer/Manual/_sources/*.*",
        "AddOns/DatViewer/Manual/_static/*.*"
    ]

    includeFileList = [
        "Firmware/CypressUSB/analyzer/analyzerUsb.hex",
        "Firmware/DSP/src/Debug/dspMain.hex",
        "Firmware/MyHDL/Spartan3/top_io_map.bit",
        "Host/Fitter/fitutils.so",
        "Host/Fitter/cluster_analyzer.so",
    ]
    if base_path:
        for folder in includeFolderList:
            path = os.path.join(base_path, folder)
            sourceFiles.extend(glob.glob(path))
        for f in includeFileList:
            path = os.path.join(base_path, f)
            sourceFiles.append(path)
    return sourceFiles