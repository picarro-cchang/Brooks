import json
import os
import pprint
import subprocess
import sys
import textwrap

import time
from doit.tools import check_timestamp_unchanged

RELEASE_VERSION_FILE = ('src', 'main', 'python', 'Host', 'Common', 'release_version.py')
INTERNAL_VERSION_FILE = ('src', 'main', 'python', 'Host', 'build_version.py')

def _verAsNumString(ver):
    """
    Convert a version dict into a string of numbers in this format:
        <major>.<minor>.<revision>.<build>
    """
    number = "%(major)s.%(minor)s.%(revision)s.%(build)s" % ver
    return number
def _verAsString(product, ver, osType=None):
    """
    Convert a version dict into a human-readable string.
    """
    number = _verAsNumString(ver)
    if osType is not None:
        return "%s-%s-%s (%s)" % (product, osType, number, ver["git_hash"])
    else:
        return "%s-%s (%s)" % (product, number, ver["git_hash"])
def _remove_python_version_files():
    try:
        os.remove(os.path.join(*RELEASE_VERSION_FILE))
    except WindowsError:
        pass
    try:
        os.remove(os.path.join(*INTERNAL_VERSION_FILE))
    except WindowsError:
        pass
def run_command(command):
    """
    Run a command line command so we can capture its output.
    """
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout_value, stderr_value = p.communicate()
    return stdout_value, stderr_value
def task_make_sources_from_xml():
    python_scripts_dir = os.path.join(os.path.dirname(sys.executable))
    src_dir = os.path.join('src','main','python','Firmware','xml')
    python_dir = os.path.join('src','main','python','Host','autogen')
    usb_dir = os.path.join('src','main','python','Firmware','CypressUSB','autogen')
    dsp_dir = os.path.join('src','main','python','Firmware','DSP','autogen')
    return {
        'actions':[
            r'cd %s && python xmldom1.py' % (src_dir,),
        ],
        'targets':[os.path.join(python_dir,fname) for fname in ['interface.py', 'usbdefs.py']] + \
                  [os.path.join(usb_dir,fname) for fname in ['usbdefs.h', 'usbdefs.inc']] + \
                  [os.path.join(dsp_dir,fname) for fname in ['dspAutogen.c', 'dspAutogen.h', 'interface.h']],
        'file_dep':[os.path.join(src_dir,fname) for fname in ['interface.xml', 'Interface.dtd', 'ParameterPages.xml']],
        'clean': True
    }
def task_compile_fitutils():
    python_scripts_dir = os.path.join(os.path.dirname(sys.executable))
    src_dir = os.path.join('src','main','python','Host','Fitter')
    f2py = os.path.join(python_scripts_dir, 'f2py.py')
    return {
        'actions':[
            r'cd %s && if exist fitutils.pyd del fitutils.pyd' % src_dir,
            r'cd %s && python %s -c -m fitutils fitutils.f --compiler=mingw32' % (src_dir, f2py),
        ],
        'targets':[os.path.join(src_dir,'fitutils.pyd')],
        'file_dep':[os.path.join(src_dir,'fitutils.f')],
        'clean':True
    }
def task_compile_cluster_analyzer():
    python_scripts_dir = os.path.join(os.path.dirname(sys.executable))
    src_dir = os.path.join('src','main','python','Host','Fitter')
    return {
        'actions':[
            r'cd %s && if exist cluster_analyzer.pyd del cluster_analyzer.pyd' % (src_dir,),
            r'cd %s && python setup.py build_src build_ext --inplace -c mingw32' % (src_dir,),
            r'cd %s && del cluster_analyzermodule.c' % (src_dir,),
            r'cd %s && rd/s/q build' % (src_dir,)
        ],
        'targets':[os.path.join(src_dir,'cluster_analyzer.pyd')],
        'file_dep':[os.path.join(src_dir,fname) for fname in ['cluster_analyzer.c', 'cluster_analyzer.h']],
        'clean':True
    }
def task_compile_swathP():
    python_scripts_dir = os.path.join(os.path.dirname(sys.executable))
    src_dir = os.path.join('src','main','python','Host','Common')
    f2py = os.path.join(python_scripts_dir, 'f2py.py')
    return {
        'actions':[
            r'cd %s && if exist swathP.pyd del swathP.pyd' % src_dir,
            r'cd %s && python %s swathP.pyf swathP.c -c --compiler=mingw32' % (src_dir, f2py),
        ],
        'targets':[os.path.join(src_dir,'swathP.pyd')],
        'file_dep':[os.path.join(src_dir,fname) for fname in ['swathP.c', 'swathP.pyf']],
        'clean':True
    }
def task_compile_fastLomb():
    python_scripts_dir = os.path.join(os.path.dirname(sys.executable))
    src_dir = os.path.join('src','main','python','Host','Utilities','SuperBuildStation')
    return {
        'actions':[
            r'cd %s && if exist fastLomb.pyd del fastLomb.pyd' % (src_dir,),
            r'cd %s && setup.py build_src build_ext --inplace -c mingw32' % (src_dir,),
            r'cd %s && del fastLombmodule.c' % (src_dir,),
            r'cd %s && rd/s/q build' % (src_dir,)
        ],
        'targets':[os.path.join(src_dir,'fastLomb.pyd')],
        'file_dep':[os.path.join(src_dir,fname) for fname in ['fastLomb.c', 'fastLomb.pyf']],
        'clean':True
    }
def task_compile_sources():
    return {'actions': None,
            'task_dep': ['make_sources_from_xml', 'compile_fitutils', 'compile_cluster_analyzer', 'compile_swathP', 'compile_fastLomb']}
def task_build_hostexe():
    return {'actions': [r'cd %(build_dir)s && python buildHost.py'],
            'task_dep': ['compile_sources'],
            'params':[{'name':'build_dir', 'long':'build_dir', 'default':'.'}],
            'verbosity': 2
    }
def task_make_release():
    src_dir = os.path.join('versions')
    dest_dir = os.path.join('src', 'main', 'python', 'Host', 'Common')

    def python_make_release(product, targets, official):
        contents = textwrap.dedent("""\
        # autogenerated by PyBuilder / doit, %s
        
        def versionString():
            return '%s'
        
        def versionNumString():
            return '%s'
        
        def buildType():
            # Empty string indicates official release
            return '%s'
        """)
        src_file = os.path.join(src_dir, "%s_version.json" % product)
        git_hash, stdout_value = run_command("git.exe log -1 --pretty=format:%H")
        ver = {"git_hash":git_hash[:8]}

        target = os.path.join(*RELEASE_VERSION_FILE) if official else os.path.join(*INTERNAL_VERSION_FILE)
        with open(src_file,"r") as inp:
            ver.update(json.load(inp))
        with open(target,"w") as outp:
            outp.write(contents % (time.asctime(), _verAsString(product, ver), _verAsNumString(ver), '' if official else 'INTERNAL'))
    
    return {'actions':[(_remove_python_version_files,), (python_make_release,)],
            'params':[{'name':'product', 'long':'product', 'default':'g2000'},
                      {'name':'official', 'long':'official', 'type':bool, 'default':False}],
    }
def task_git_set_credentials():
    return {'actions': ['git config --global credential.helper wincred',
                        'git fetch']
    }
