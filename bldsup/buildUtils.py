import os
import glob
import shutil

CYTHON_RESERVOIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../cython_reservoir")

def get_cython_source(base_path, after_cython=False):
    """
    if after_cython=False returns a list of files for cythonization
    if after_cython=True returns a list of files for copying to sandbox
    """
    pySourceFiles = []
    includeFolderList = [
            r"Host/AlarmSystem/*.py",
            r"Host/Archiver/*.py",
            r"Host/Common/*.py",
            r"Host/CommandInterface/*.py",
            r"Host/DataLogger/*.py",
            r"Host/DataManager/*.py",
            r"Host/Driver/*.py",
            r"Host/ElectricalInterface/*.py",
            r"Host/EventManager/*.py",
            r"Host/Fitter/*.py",
            r"Host/InstMgr/*.py",
            r"Host/MeasSystem/*.py",
            r"Host/RDFrequencyConverter/*.py",
            r"Host/rdReprocessor/*.py",
            r"Host/PeriphIntrf/*.py",
            r"Host/SampleManager/*.py",
            r"Host/SpectrumCollector/*.py",
            r"Host/Supervisor/*.py",
            r"Host/ValveSequencer/*.py"
    ]
    if base_path:
        for folder in includeFolderList:
            path = os.path.join(base_path, folder)
            pySourceFiles.extend(glob.glob(path))
    
    CanDelete = []
    SpecialFiles = [
            "__init__.py", "setup.py",
            "EventManagerGUI.py",
            "GuiTools.py", "GuiWidgets.py"
    ]
    if not after_cython:
        for f in pySourceFiles:
            for sf in SpecialFiles:
                if sf in f:
                    CanDelete.append(f)
                    break
        for f in CanDelete:
            pySourceFiles.remove(f)
    else:
        for idx in range(len(pySourceFiles)):
            filename = pySourceFiles[idx]
            for sf in SpecialFiles:
                if sf in filename:
                    break
            else:
                pySourceFiles[idx] = pySourceFiles[idx][:-3] + ".so"
    return pySourceFiles

def get_noncython_resource(base_path):
    """
    Return a list of python files and other resources that
    will be distributed. Note that this list does NOT include
    python files that are cythonized
    """
    sourceFiles = []
    includeFolderList = [
        "Assets/icons/*.ico",
        "Host/autogen/*.py",
        "Host/DriverSimulator/*.py",
        "Host/Controller/*.py",
        "Host/Coordinator/*.py",
        "Host/MfgUtilities/*.py",
        "Host/pydCaller/*.*",
        "Host/QuickGui/*.*",
        "Host/WebServer/*.*",
        "Host/Utilities/BuildHelper/*.py",
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
        "Host/__init__.py",
        "Host/Utilities/__init__.py",
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

def save_cython_file(cython_file, source_dir):
    """
    Copy cythonized file into reservoir for future use
    cython_file: full path of cythonized file
    source_dir: root folder of python source files
    """
    
    relative_path = os.path.relpath(cython_file, source_dir)
    dst = os.path.join(CYTHON_RESERVOIR, relative_path)
    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    shutil.copy(cython_file, dst)

def get_cython_file(python_file, source_dir):
    """
    Find cythonized file from reservoir and copy it to the folder of python source file
    python_file: full path of python source file
    source_dir: root folder of python source files
    """
    relative_path = os.path.relpath(python_file, source_dir)
    cython_file = os.path.join(CYTHON_RESERVOIR, relative_path)
    dst = python_file[:-2] + "so"
    if os.path.exists(cython_file):
        shutil.copy(cython_file, dst)