#!/usr/bin/env python

"""
setup.py file for SWIG example
"""

from distutils.core import setup, Extension

peakDetectModule = Extension('_peakDetect',
                             sources=['peakDetect_wrap.c', 'peakDetect.c'],
                             )

setup(name='peakDetect',
      version='0.1',
      author="SWIG Docs",
      description="""Simple swig peak_detect from docs""",
      ext_modules=[peakDetectModule],
      py_modules=["peakDetect"],
      )
