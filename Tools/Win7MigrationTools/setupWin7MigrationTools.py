# setupWin7MigrationTools.py

from __future__ import with_statement

from distutils.core import setup
import os
import py2exe
import sys
import time
import subprocess
import os.path
#import numpy

version = sys.version_info
pyDirname = "Python%d%d" % (version[0], version[1])
pythonVer = "%d.%d" % (version[0], version[1])
pythonSubVer = "%d.%d.%d" % (version[0], version[1], version[2])

sys.path.append("Common")

#os.environ["PATH"] = os.environ["PATH"] + os.path.pathsep + \
#    os.path.split(zmq.__file__)[0]

def _getBuildVersion():
    try:
        import release_version as buildVersion
        verStr = buildVersion.versionNumString()
        print "Release version: %s" % verStr
    except Exception, e:
        # use default
        verStr = "1.0"
        print "Release version not found, using: %s" % verStr

    return verStr


versionStr = _getBuildVersion()

# simple check to save us from potential problems using paths in Picarro.pth
if "PYTHONPATH" not in os.environ:
    print "PYTHONPATH is not set in environment, potential exists for pulling local libs from wrong dir."
    print "Run 'python buildWin7MigrationTools.py' instead to build migration apps from the command line."
    sys.exit(1)


# And now to the main setup routine...
#
# The following lists and tuples are common to both Python 2.5 and 2.7 builds. If any
# require customization, they must be moved and maintained separately under the if statements below.
exclusionList = ["Tkconstants",
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

inclusionList = ["email",
                 "email.iterators",
                 "email.generator",
                 "email.mime.audio",
                 "email.mime.multipart",
                 "email.mime.image",
                 "email.mime.text",
                 "email.mime.base",
                 "scipy.interpolate",
                 "scipy.misc",
                 "sip",
                 "matplotlib.backends",
                 "matplotlib.backends.backend_wxagg",
                 "matplotlib.backends.backend_qt4agg",
                 "matplotlib.figure",
                 "pylab",
                 "numpy",
                 "configobj",
                 "encodings.*",
                 "tables.*"]

inclusionList = []

dllexclusionList = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', "mswsock.dll", "powrprof.dll" ]

dll_excludes = [ "IPHLPAPI.DLL", "NSI.dll",  "WINNSI.DLL",  "WTSAPI32.dll"]
dllexclusionList.extend(dll_excludes)

packageList = []
data_files = []

windowsList = []

consoleList = ["Win7Migrate_p1.py"]

if pythonVer == "2.5":
    packageList = ["simplejson", "werkzeug","flask","jinja2","email"]

    setup(version = versionStr,
          description = "Picarro Windows 7 Migration Software",
          name = "Picarro Win7Migration",
          options = dict(py2exe = dict(compressed = 1,
                                       optimize = 1,
                                       bundle_files = 1,
                                       excludes = exclusionList,
                                       includes = inclusionList,
                                       dll_excludes = dllexclusionList,
                                       packages = packageList)
                 ),
          # targets to build...
          console = consoleList,
          windows = windowsList,
          data_files = data_files
    )

elif pythonVer == "2.7":
    if pythonSubVer == "2.7.3":
        import zmq
        os.environ["PATH"] += os.path.pathsep + os.path.split(zmq.__file__)[0]

    packageList = ["werkzeug", "jinja2", "email"]
    packageList = []

    setup(version = versionStr,
          description = "Picarro Windows 7 Migration Software",
          name = "Picarro Win7Migration",
          options = dict(py2exe = dict(compressed=1,
                                       optimize=1,
                                       # bundle_files=1,
                                       excludes=exclusionList,
                                       includes=inclusionList,
                                       dll_excludes = dllexclusionList,
                                       packages=packageList)
                        ),
          # targets to build...
          console = consoleList,
          windows = windowsList,
          data_files = data_files,
          zipfile = "lib/share"
    )