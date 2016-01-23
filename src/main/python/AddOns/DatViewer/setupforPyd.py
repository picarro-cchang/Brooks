from distutils.core import setup
from Cython.Build import cythonize

sourceFiles = ['DatViewer.py', 'DateRangeSelectorFrame.py', 'Analysis.py', 'FileOperations.py', 'timestamp.py', 'CustomConfigObj.py']

setup(
  name = "DatViewer",
  ext_modules = cythonize(sourceFiles)
)