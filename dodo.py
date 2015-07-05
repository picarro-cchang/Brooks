import json
import os
import pprint
import shutil
import subprocess
import sys
import textwrap

import time
from doit.tools import check_timestamp_unchanged
from doit import get_var

def run_command(command):
    """
    Run a command line command so we can capture its output.
    """
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout_value, stderr_value = p.communicate()
    return stdout_value.replace('\r\n','\n').replace('\r','\n'), stderr_value.replace('\r\n','\n').replace('\r','\n')

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
    dist_dir = get_var('dist_dir', '.')

    def python_buildhost(dist_dir):
        build_dir = os.path.join(dist_dir, "Host")
        old_dir = os.getcwd()
        os.chdir(build_dir)
        try:
            # Get the current dir. Expect that we are in the Host folder.
            cur_dir_path = os.getcwd()
            cur_dir = os.path.split(cur_dir_path)[1]
            # Windows dirs are not case-sensitive.
            # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
            if cur_dir.lower() != "host":
                raise ValueError("Not running in expected folder 'Host'.")
            # Set the PYTHONPATH environment variable so the current folder tree is used to
            # pull local libraries from.
            parent_dir = os.path.normpath(os.path.join(cur_dir_path, ".."))
            firmware_dir = os.path.normpath(os.path.join(cur_dir_path, "..", "Firmware"))

            # for a sanity check -- not needed in PYTHONPATH as the parent dir will already be there
            common_dir = os.path.join(parent_dir, "Host", "Common")

            # folders must exist
            folders = [parent_dir, common_dir, firmware_dir]
            for folder in folders:
                if not os.path.isdir(folder):
                    raise ValueError("Expected folder '%s' does not exist." % folder)

            build_env = dict(os.environ)
            build_env.update({'PYTHONPATH' : "%s;%s" %(parent_dir, firmware_dir)})
            ret_code = subprocess.call(['python.exe', 'PicarroExeSetup.py', 'py2exe'], env=build_env)
            if ret_code != 0:
                raise ValueError("PicarroExeSetup.py failed")
            dist_target = os.path.join(dist_dir, "HostExe")
            if os.path.exists(dist_target):
                shutil.rmtree(dist_target)
            shutil.move(os.path.join(build_dir, "dist"), dist_target)
        finally:
            os.chdir(old_dir)

    yield {'actions': [(python_buildhost, (dist_dir,))],
           'name':dist_dir,
           'targets' : [os.path.join(dist_dir, "HostExe")],
           'file_dep': [os.path.join(dist_dir, "last_updated.txt")],
           'verbosity': 2
    }

def task_build_vap_clean_exe():
    dist_dir = get_var('dist_dir', '.')

    def python_build_vap_clean_exe(dist_dir):
        build_dir = os.path.join(dist_dir, "AddOns", "VaporizerCleaner")
        old_dir = os.getcwd()
        os.chdir(build_dir)
        try:
            # Get the current dir. Expect that we are in the Host folder.
            cur_dir_path = os.getcwd()
            cur_dir = os.path.split(cur_dir_path)[1]
            # Windows dirs are not case-sensitive.
            # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
            if cur_dir.lower() != "vaporizercleaner":
                raise ValueError("Not running in expected folder 'VaporizerCleaner'.")
            # Set the PYTHONPATH environment variable so the current folder tree is used to
            # pull local libraries from.
            parent_dir = os.path.normpath(os.path.join(cur_dir_path, "..", ".."))
            firmware_dir = os.path.normpath(os.path.join(cur_dir_path, "..", "..", "Firmware"))

            # for a sanity check -- not needed in PYTHONPATH as the parent dir will already be there
            common_dir = os.path.join(parent_dir, "Host", "Common")

            # folders must exist
            folders = [parent_dir, common_dir, firmware_dir]
            for folder in folders:
                if not os.path.isdir(folder):
                    raise ValueError("Expected folder '%s' does not exist." % folder)

            build_env = dict(os.environ)
            build_env.update({'PYTHONPATH' : "%s;%s" %(parent_dir, firmware_dir)})
            ret_code = subprocess.call(['python.exe', 'vaporizerCleanerSetup.py', 'py2exe'], env=build_env)
            if ret_code != 0:
                raise ValueError("vaporizerCleanerSetup.py failed")
            dist_target = os.path.join(dist_dir, "VaporizerCleanerExe")
            if os.path.exists(dist_target):
                shutil.rmtree(dist_target)
            shutil.move(os.path.join(build_dir, "dist"), dist_target)

        finally:
            os.chdir(old_dir)

    yield {'actions': [(python_build_vap_clean_exe,(dist_dir,))],
           'name':dist_dir,
           'targets' : [os.path.join(dist_dir, "VaporizerCleanerExe")],
           'file_dep': [os.path.join(dist_dir, "last_updated.txt")],
            'verbosity': 2
    }


def task_git_set_credentials():
    return {'actions': ['git config --global credential.helper wincred',
                        'git fetch']
    }
