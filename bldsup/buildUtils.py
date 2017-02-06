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
        "Host/Controller/*.py",
        "Host/Coordinator/*.py",
        "Host/MfgUtilities/*.py",
        "Host/pydCaller/*.*",
        "Host/QuickGUI/*.*",
        "Host/Utilities/ConfigManager/*.py",
        "Host/Utilities/CoordinatorLauncher/*.py",
        "Host/Utilities/DataRecal/*.py",
        "Host/Utilities/FlowController/*.py",
        "Host/Utilities/InstrEEPROMAccess/*.py",
        "Host/Utilities/IntegrationTool/*.py",
        "Host/Utilities/SetupTool/*.py",
        "Host/Utilities/SupervisorLauncher/*.py"
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

def write_xubuntu_desktop_file(filePath, fileType, name, command, iconPath, category="", terminal=False):
    context = "[Desktop Entry]\n" + \
        "Type=%s\n" % fileType + \
        "Name=%s\n" % name + \
        "Icon=%s\n" % iconPath + \
        "Exec=%s\n" % command + \
        "Categories=X-XFCE;X-Xfce-Toplevel;%s\n" % category + \
        "Terminal=%s" % ("true" if terminal else "false")
    with open(filePath, "w") as f:
        f.write(context)

def make_xubuntu_launchers(base_path):
    icon_folder = os.path.join(base_path, "usr", "share", "applications")
    if not os.path.exists(icon_folder):
        os.makedirs(icon_folder)

    directory_folder = os.path.join(base_path, "usr", "share", "desktop-directories")
    if not os.path.exists(directory_folder):
        os.makedirs(directory_folder)
    
    # directories
    write_xubuntu_desktop_file("%s/picarro.directory" % directory_folder, 
                            "Directory", "Picarro", "",
                            "/home/picarro/SI2000/Assets/icons/Picarro_icon.ico")

    write_xubuntu_desktop_file("%s/picarro-diagnostics.directory" % directory_folder, 
                            "Directory", "Picarro-Diagnostics", "",
                            "/home/picarro/SI2000/Assets/icons/Diagnostics_icon.ico")

    write_xubuntu_desktop_file("%s/picarro-utilities.directory" % directory_folder, 
                            "Directory", "Picarro-Utilities", "",
                            "/home/picarro/SI2000/Assets/icons/Utilities_icon.ico")                        

    # icons    
    write_xubuntu_desktop_file("%s/modeSwitcher.desktop" % icon_folder, 
                            "Application", "Picarro Mode Switcher", 
                            "bash -c 'cd /home/picarro/SI2000/Host/Utilities/SupervisorLauncher;python -O SupervisorLauncher.py -v -k -c ../../../AppConfig/Config/Utilities/SupervisorLauncher.ini'",
                            "/home/picarro/SI2000/Assets/icons/Picarro_icon.ico", "picarro")
    write_xubuntu_desktop_file("%s/startInstrument.desktop" % icon_folder,
                            "Application", "Start Instrument", 
                            "bash -c 'cd /home/picarro/SI2000/Host/Utilities/SupervisorLauncher;python -O SupervisorLauncher.py -a -c ../../../AppConfig/Config/Utilities/SupervisorLauncher.ini'",
                            "/home/picarro/SI2000/Assets/icons/Picarro_icon.ico", "picarro")
    write_xubuntu_desktop_file("%s/stopInstrument.desktop" % icon_folder, 
                            "Application", "Stop Instrument", 
                            "bash -c 'python /home/picarro/SI2000/Host/Common/StopSupervisor.py'",
                            "/home/picarro/SI2000/Assets/icons/Cancel.ico", "picarro-diagnostics")
    write_xubuntu_desktop_file("%s/integrationTool.desktop" % icon_folder, 
                            "Application", "Integration Tool", 
                            "bash -c 'cd /home/picarro/SI2000/Host/Utilities/IntegrationTool;python -O IntegrationTool.py -c ../../../CommonConfig/Config/Utilities/IntegrationTool.ini'",
                            "/home/picarro/SI2000/Assets/icons/Integration_icon.ico", "picarro-diagnostics", True)
    write_xubuntu_desktop_file("%s/controller.desktop" % icon_folder,
                            "Application", "Controller", 
                            "bash -c 'python -O /home/picarro/SI2000/Host/Controller/Controller.py'",
                            "/home/picarro/SI2000/Assets/icons/Controller_icon.ico", "picarro")
