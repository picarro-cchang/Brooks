from distutils.core import setup
import py2exe

setup(console=['Hdf5ToMat.py'],options={"py2exe":
                                        {"bundle_files":1,
                                         "includes":["encodings.*", "tables.*", "numpy.*"],
                                         "excludes":["Tkconstants","Tkinter","tcl"]}})