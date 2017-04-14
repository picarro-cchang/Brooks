import glob
import os
import sys
from distutils.core import setup
from distutils.command.build_ext import build_ext
from Cython.Build import cythonize

class cythonize_picarro_code(build_ext):
    """
    Pyd files need to be generated alongside python source files. However, sometimes distutils generates 
    pyd files in new folders even though --inplace switch is specified. So here we subclass build_ext 
    and implement our own get_ext_fullpath().
    """
    user_options = build_ext.user_options + [("basepath=", None, "directory of Picarro source code")]
    
    def initialize_options (self):
        build_ext.initialize_options(self)
        self.basepath = None
        
    def get_ext_fullpath(self, ext_name):
        if self.basepath:
            modpath = ext_name.split('.')
            return os.path.join(self.basepath, *modpath) + ".so"
        else:
            return build_ext.get_ext_fullpath(self, ext_name)

def get_raw_source_list(base_path):
    pySourceFiles = []
    includeFolderList = [
            r"Host/AlarmSystem/*.py",
            r"Host/autogen/*.py",
            r"Host/Archiver/*.py",
            r"Host/Common/*.py",
            r"Host/CommandInterface/*.py",
            r"Host/DataLogger/*.py",
            r"Host/DataManager/*.py",
            r"Host/Driver/*.py",
            r"Host/DriverSimulator/*.py",
            r"Host/ElectricalInterface/*.py",
            r"Host/EventManager/*.py",
            r"Host/Fitter/*.py",
            r"Host/InstMgr/*.py",
            r"Host/MeasSystem/*.py",
            r"Host/PortListerner/*.py",
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
    return pySourceFiles

def get_source_list(base_path):
    pySourceFiles = get_raw_source_list(base_path)
    CanDelete = []
    DeleteFiles = [
            "__init__.py", "setup.py",
            "EventManagerGUI.py",
            "GuiTools.py", "GuiWidgets.py"
    ]
    for f in pySourceFiles:
        for df in DeleteFiles:
            if df in f:
                CanDelete.append(f)
                break
    for f in CanDelete:
        pySourceFiles.remove(f)
    return pySourceFiles
    
if __name__ == "__main__":   
    picarro_base_path = None
    for option in sys.argv:
        if '--basepath' in option:
            picarro_base_path = option.split("=")[1]
            
    setup(
      name = "PicarroHost",
      cmdclass={'build_ext': cythonize_picarro_code},
      ext_modules = cythonize(get_source_list(picarro_base_path))  
    )
