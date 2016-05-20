from distutils.core import setup
from Cython.Build import cythonize
import os

sourceFiles = []

excludeList = ["main.py", "setupforPyd.py", "__init__.py", "Calibration_boken.py", "setup.py"]

for f in os.listdir('.'):
    if f.endswith(".py") and f not in excludeList:
        sourceFiles.append(f)

setup(
  name = "Mudlogger",
  ext_modules = cythonize(sourceFiles)
)