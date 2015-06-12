import os
import sys

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
