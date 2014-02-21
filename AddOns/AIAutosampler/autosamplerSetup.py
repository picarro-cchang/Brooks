# autosamplerSetup.py

"""
Copyright 2014 Picarro Inc.

A disutils script that uses py2exe to build Win32 executables for the
AI Autosampler.

Bails if PYTHONPATH is unset, to ensure Picarro.pth is being overridden
so Picarro libs are pulled from the proper dir (primitive check, could
be smarter)

Usage: python autosamplerSetup.py py2exe

Notes: Use python buildAutosampler.py from the command line, which sets up
       the environment for this script.
#
# File History:

"""


from __future__ import with_statement

from distutils.core import setup
import py2exe
import sys
import glob
import time
import subprocess
import os.path
import platform

#from Host.Common import OS

# version needs to come from the local dir
#from Host.Common import version as hostVersion
# prolly something like this
# import version as appVersion

version = sys.version_info
pyDirname = "Python%d%d" % (version[0],version[1])

sys.path.append("Common")

sys.stderr = sys.stdout

def _getPythonVersion():
    """
    Returns a string such as "2.5" or 2.7"
    """
    pythonVer = sys.version_info
    return str(pythonVer[0]) + "." + str(pythonVer[1])


def _getPythonSubVersion():
    """
    Returns a string such as "2.7.3"
    """
    pythonVer = sys.version_info
    return str(pythonVer[0]) + "." + str(pythonVer[1]) + "." + str(pythonVer[2])


def _getOsType():
    osType = platform.uname()[2]

    if osType == '7':
        osType = 'win7'
    elif osType == 'XP':
        osType = 'winxp'
    else:
        osType = 'unknown'
        print "Unexpected OS type!"

    return osType

def _getBuildVersion():
    try:
        # TODO: we need our own version separate from Host code
        from Host.Common import release_version as buildVersion
        verStr = buildVersion.versionNumString()
        print "Release version: %s" % verStr
    except Exception, e:
        # use default
        verStr = "1.0"
        print "Release version not found, using: %s" % verStr

    return verStr

    
################################################################
# Start of a pile of special setup with the sole purpose
# of making the wxPython apps look like Windows-native
#
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
# The manifest will be inserted as resource into test_wx.exe.  This
# gives the controls the Windows XP appearance (if run on XP ;-)
#
# Another option would be to store it in a file named
# test_wx.exe.manifest, and copy it with the data_files option into
# the dist-dir.
#

cDep = ""
if version[0] == 2 and version[1] > 5:
    cDep = """
<dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="X86"
            publicKeyToken="1fc8b3b9a1e18e3b"
            language="*"
        />
    </dependentAssembly>
</dependency>
    """
manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
  version="5.0.0.0"
  processorArchitecture="x86"
  name="%%(prog)s"
  type="win32"
/>
<description>%%(prog)s Program</description>
<dependency>
  <dependentAssembly>
    <assemblyIdentity
      type="win32"
      name="Microsoft.Windows.Common-Controls"
      version="6.0.0.0"
      processorArchitecture="X86"
      publicKeyToken="6595b64144ccf1df"
      language="*"
    />
  </dependentAssembly>
</dependency>
%s
</assembly>
''' % (cDep,)
RT_MANIFEST = 24

Autosampler = Target(description = "Autosampler", # used for the versioninfo resource
                     script = "Autosampler.py", # what to build
                     other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="Autosampler")
                                        )],
                    ##    icon_resources = [(1, "cogwheel.ico")],
                    dest_base = "Autosampler"
                    )

# End of special autosampler setup stuff (except to use autosampler below)
################################################################

# simple check to save us from potential problems using paths in Picarro.pth
if "PYTHONPATH" not in os.environ:
    print "PYTHONPATH is not set in environment, potential exists for pulling local libs from wrong dir."
    print "Run 'python buildAutosampler.py' instead to build Autosampler from the command line."
    sys.exit(1)


pythonVer = _getPythonVersion()
pythonSubVer = _getPythonSubVersion()
osType = _getOsType()

versionStr = _getBuildVersion()

# And now to the main setup routine...
#
# The following lists and tuples are common to both Python 2.5 and 2.7 builds. If any
# require customization, they must be moved and maintained separately under the if statements below.
exclusionList = ["Tkconstants", "Tkinter", "tcl", '_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                '_fltkagg', '_gtk', '_gtkcairo', ]

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

# redefine this, I don't think everything above is needed
inclusionList = ["configobj"]

dllexclusionList = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', "mswsock.dll", "powrprof.dll" ]


# Both WinXP and Win7 use the same 32 bit ALSG_API.dll
data_files = [(".", ["cogwheel.ico",
                     "Autosampler.ini",
                     "AutosamplerState.ini",
                     "Default.td",
                     "Method.td",
                     "Parameter.td",
                     "Sequence.td",
                     "../../Vendor/Applied Instruments/ALS-G/x86/ALSG_API.dll"])]

# Python2.5 (WinXP) needs to include MSVCR71.dll
if pythonVer == "2.5":
    data_files.append("../../Vendor/Microsoft/Python25/MSVCR71.dll")

windowsList = [
    Autosampler
]


# TODO: This should be done elsewhere (release.py and buildAutosampler.py), not here.
# Generate internal build version
with open(os.path.join(os.path.dirname(__file__),
                       'setup_version.py'), 'w') as fp:
    fp.writelines(
        ["# autogenerated by autosamplerSetup.py, %s\n" % time.asctime(),
         "\n",
         "def versionString():\n",
         # TODO: handle this!!
         #"    return '%s'\n" % appVersion.versionString()])
         "    return '%s'\n" % "1.0.0.0"])

if pythonVer == "2.5":
    # only packageList differs for Python 2.5 and 2.7
    packageList = ["simplejson", "werkzeug","flask","jinja2","email"]

    setup(version = versionStr,
      description = "Picarro Autosampler Software",
      name = "Picarro",
      options = dict(py2exe = dict(compressed = 1,
                                   optimize = 1,
                                   bundle_files = 1,
                                   excludes = exclusionList,
                                   includes = inclusionList,
                                   dll_excludes = dllexclusionList,
                                   packages = packageList)
                     ),
      # targets to build...
      #console = consoleList,
      windows = windowsList,
      data_files = data_files
)

elif pythonVer == "2.7":
    if pythonSubVer == "2.7.3":
        import zmq
        os.environ["PATH"] += os.path.pathsep + os.path.split(zmq.__file__)[0]

    packageList = ["werkzeug","jinja2","email"]

    # no bundle_files, specify zipfile
    setup(version = versionStr,
          description = "Picarro Autosampler Software",
          name = "Picarro",
          options = dict(py2exe = dict(compressed = 1,
                                       optimize = 1,
                                       # bundle_files = 1,
                                       excludes = exclusionList,
                                       includes = inclusionList,
                                       dll_excludes = dllexclusionList,
                                       packages = packageList)
                         ),
          # targets to build...
          #console = consoleList,
          windows = windowsList,
          data_files = data_files,
          zipfile = "lib/share"
    )

else:
    print "Unsupported Python version %s" % pythonVer
    sys.exit(1)
