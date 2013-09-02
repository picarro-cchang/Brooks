"""
Copyright 2013 Picarro, Inc
"""

import glob
import os.path
from distutils import core

import py2exe


excludes = ["Tkconstants",
            "Tkinter",
            "tcl",
            '_gtkagg',
            '_tkagg',
            '_agg2',
            '_cairo',
            '_cocoaagg',
            '_fltkagg',
            '_gtk',
            '_gtkcairo', ]

includes = ["scipy.interpolate",
            "scipy.misc",
            "sip",
            "matplotlib.backends",
            "matplotlib.backends.backend_wxagg",
            "matplotlib.backends.backend_qt4agg",
            "matplotlib.figure",
            "pylab",
            "numpy"]

mplPath = r'c:\python25\lib\site-packages\matplotlib\mpl-data'
dataFiles = [
    ('mpl-data', glob.glob(os.path.join(mplPath, '*.*'))),
    ('mpl-data', [os.path.join(mplPath, 'matplotlibrc')]),
    (r'mpl-data\images', glob.glob(os.path.join(mplPath, 'images', '*.*'))),
    (r'mpl-data\fonts', glob.glob(os.path.join(mplPath, 'fonts', '*.*'))),
	('.', glob.glob('*.csv'))]

core.setup(console=['postProcessor.py'],
           data_files=dataFiles,
           options = {
               'py2exe' : {
                   'compressed' : 1,
                   'optimize' : 1,
                   'bundle_files' : 1,
                   'excludes' : excludes,
                   'includes' : includes}})
