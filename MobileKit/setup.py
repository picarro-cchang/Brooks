from distutils.core import setup
import os
import py2exe
import shutil
import sys
import glob

sys.path.append("AnalyzerServer")
sys.path.append("MobileKitSetupNew")
sys.path.append("Utilities")
sys.path.append("ViewServer")
sys.path.append("ReportGen")

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

manifest_template = '''
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
<assemblyIdentity
  version="5.0.0.0"
  processorArchitecture="x86"
  name="%(prog)s"
  type="win32"
/>
<description>%(prog)s Program</description>
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
</assembly>
'''

RT_MANIFEST = 24
MobileKitSetup = Target(description = "MobileKitSetup", # used for the versioninfo resource
                    script = "MobileKitSetupNew/MobileKitSetup.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="MobileKitSetup")
                                        )],
                    dest_base = "MobileKitSetup"
                    )
RemoteMobileKitSetup = Target(description = "RemoteMobileKitSetup", # used for the versioninfo resource
                    script = "MobileKitSetupNew/RemoteMobileKitSetup.py", # what to build
                    other_resources = [(RT_MANIFEST,
                                        1,
                                        manifest_template % dict(prog="RemoteMobileKitSetup")
                                        )],
                    dest_base = "RemoteMobileKitSetup"
                    )

exclusionList = ["Tkconstants","Tkinter","tcl"]
inclusionList = []
packageList = ["simplejson", "werkzeug", "jinja2", "email", 'sqlalchemy.dialects.sqlite']
data_files = [(".", ["MobileKitSetupNew/LEDgreen2.ico",
                     "MobileKitSetupNew/LEDred2.ico",
                     "MobileKitSetupNew/MobileKitSetup.ini",
                     "MobileKitSetupNew/MobileKit_inactive.ini",
                     "ViewServer/view.kml",
                     "ReportGen/platBoundaries.json",
                     "msvcp71.dll",
                     "openssl.cnf"]),
              (r'static\css', glob.glob(r'ReportGen\static\css\*.*')),
              (r'static\images', glob.glob(r'ReportGen\static\images\*.*')),
              (r'static\img', glob.glob(r'ReportGen\static\img\*.*')),
              (r'static\scripts', glob.glob(r'ReportGen\static\scripts\*.*')),
              (r'templates', glob.glob(r'ReportGen\templates\*.*')),
             ]
setup(console=['AnalyzerServer/RunPeakFinder.py',
               'AnalyzerServer/RunPeakAnalyzer.py',
               'AnalyzerServer/DatEchoP3.py',
               'AnalyzerServer/analyzerServer.py',
               'ViewServer/ViewServer.py',
               'ReportGen/batchReport.py',
               'ReportGen/reportServer.py',
               'Utilities/createReportBooklet.py'
               ],
     windows=[MobileKitSetup, RemoteMobileKitSetup],
     options = dict(py2exe = dict(compressed = 1,
                   optimize = 1,
                   bundle_files = 1,
                   excludes = exclusionList,
                   includes = inclusionList,
                   packages = packageList)),
     data_files = data_files,

    )
shutil.copyfile('dist/DatEchoP3.exe','dist/GPSEchoP3.exe')
shutil.copyfile('dist/DatEchoP3.exe','dist/WSEchoP3.exe')
