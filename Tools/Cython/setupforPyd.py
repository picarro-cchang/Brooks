from distutils.core import setup
from Cython.Build import cythonize
import glob

pySourceFiles = []
includeFolderList = [
        r"Host/AlarmSystem/*.py",
        r"Host/autogen/*.py",
        r"Host/Archiver/*.py",
        r"Host/CommandInterface/*.py",
        r"Host/DataLogger/*.py",
        r"Host/DataManager/*.py",
        r"Host/Driver/*.py",
        r"Host/ElectricalInterface/*.py",
        r"Host/Fitter/*.py",
        r"Host/InstMgr/*.py",
        r"Host/MeasSystem/*.py",
        r"Host/PortListerner/*.py",
        r"Host/RDFrequencyConverter/*.py",
        r"Host/rdReprocessor/*.py",
        r"Host/Utilities/RestartSupervisor/*.py",
        r"Host/PeriphIntrf/*.py",
        r"Host/SampleManager/*.py",
        r"Host/SpectrumCollector/*.py",
        r"Host/Supervisor/*.py",
        r"Host/ValveSequencer/*.py",
        r"Host/Common/*.py"
]
includeFileList = [
        r"Host/EventManager/EventManager.py"
]
for folder in includeFolderList:
    pySourceFiles.extend(glob.glob(folder))
for file in includeFileList:    
    pySourceFiles.append(file)

  
CanDelete = []
for f in pySourceFiles:
    if "__init__.py" in f or "setup.py" in f:
        CanDelete.append(f)
for f in CanDelete:
    pySourceFiles.remove(f)

setup(
  name = "G2000",
  ext_modules = cythonize(pySourceFiles)
)