"""
Copyright 2013 Picarro Inc.

A disutils script that uses py2exe to build a Win32 executable for the
WlmCalUtils tool.

Usage: python WlmCalUtilitySetup.py py2exe
"""

from __future__ import with_statement

from distutils.core import setup
import py2exe
import sys
import glob

version = sys.version_info
pyDirname = "Python%d%d" % (version[0],version[1])

sys.path.append("Common")

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

WlmCalUtility = Target(description = "WlmCalUtility", # used for the versioninfo resource
                    script = "WlmCalUtility.py",      # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="WlmCalUtility")
                                        )],
                    ##    icon_resources = [(1, "icon.ico")],
                    dest_base = "WlmCalUtility"
                    )


################################################################

# And now to the main setup routine...
exclusionList = ["Tkconstants","Tkinter","tcl", '_gtkagg', '_tkagg', '_agg2', '_cairo', '_cocoaagg',
                '_fltkagg', '_gtk', '_gtkcairo', ]
                
inclusionList = ["scipy.interpolate",
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
                 
dllexclusionList = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', "mswsock.dll", "powrprof.dll" ]

data_files = [(".", ["WlmCalUtility.ini"]),
              (r'mpl-data', glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\*.*' % pyDirname)),
              # Because matplotlibrc does not have an extension, glob does not find it (at least I think that's why)
              # So add it manually here:
              (r'mpl-data', [r'C:\%s\Lib\site-packages\matplotlib\mpl-data\matplotlibrc' % pyDirname]),
              (r'mpl-data\images',glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\images\*.*' % pyDirname)),
              (r'mpl-data\fonts',glob.glob(r'C:\%s\Lib\site-packages\matplotlib\mpl-data\fonts\*.*' % pyDirname)),
             ]
            
setup(version = "1.0",
      description = "CRDS Wlm Calibration Utility Tool",
      name = "CRDS Wlm Calibration Utility",
      options = dict(py2exe = dict(compressed = 1,
                                   optimize = 1,
                                   bundle_files = 1,
                                   excludes = exclusionList,
                                   includes = inclusionList,
                                   dll_excludes = dllexclusionList)
                     ),
      windows = [WlmCalUtility],
      data_files = data_files
)