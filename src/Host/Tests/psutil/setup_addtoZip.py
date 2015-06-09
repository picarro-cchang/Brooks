from distutils.core import setup
import os
from py2exe.build_exe import py2exe as build_exe

class MediaCollector(build_exe):
    def copy_extensions(self, extensions):
        build_exe.copy_extensions(self,extensions)
        media = 'psutil'
        full = os.path.join(self.collect_dir, media)
        if not os.path.exists(full):
            self.mkpath(full)
        for name in ['_psutil_mswindows.pyc']:
            self.copy_file(os.path.join('C:\GitHub\host\Host\Tests\psutil',name), os.path.join(full,name))
            self.compiled_files.append(os.path.join(media,name))

exclusionList = []
inclusionList = ['pkg_resources']
packageList = []
data_files = []
py2exe_options = dict(cmdclass={'py2exe': MediaCollector})

setup(console=['usePsutil.py'],
      options = {'py2exe': dict(compressed=1,
                   optimize=1,
                   bundle_files=1,
                   excludes=exclusionList,
                   includes=inclusionList,
                   packages=packageList)},
      data_files=data_files,**py2exe_options
      )