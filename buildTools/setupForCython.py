import os
import sys
from distutils.core import setup
from distutils.command.build_ext import build_ext
from Cython.Build import cythonize

class cythonize_picarro_code(build_ext):
    """
    Pyd files need to be generated alongside python source files. However, sometimes distutils generates 
    pyd files in new folders even though --inplace switch is specified. So here we subclass build_ext 
    and implement our own get_ext_fullpath().
    """
    user_options = build_ext.user_options + [("filename=", None, "Target file for cythonization")]
    
    def initialize_options (self):
        build_ext.initialize_options(self)
        self.filename = None

    def get_ext_fullpath(self, ext_name):
        return  self.filename[:-3] + ".so"

    # def get_ext_fullpath(self, ext_name):
    #     if self.basepath:
    #         modpath = ext_name.split('.')
    #         return os.path.join(self.basepath, *modpath) + ".so"
    #     else:
    #         return build_ext.get_ext_fullpath(self, ext_name)

if __name__ == "__main__":   
    for option in sys.argv:
        if '--filename' in option:
            filename = option.split("=")[1]
            break
    else:
        raise Exception("Target file is not specified. Use '--filename=' to specify target file.")
            
    setup(
      name = "PicarroHost",
      cmdclass={'build_ext': cythonize_picarro_code},
      ext_modules = cythonize(filename)  
    )
