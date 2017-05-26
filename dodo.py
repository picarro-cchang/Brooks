import jinja2
import json
import os
import shutil
import subprocess32 as subprocess
import sys
from doit import get_var

bldsup_path = os.path.join(os.getcwd(), "bldsup")
if bldsup_path not in sys.path:
    sys.path.append(bldsup_path)
import buildUtils

def run_command(command):
    """
    Run a command line command so we can capture its output.
    """
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    stdout_value, stderr_value = p.communicate()
    if stdout_value and stderr_value:
        return stdout_value.replace('\r\n','\n').replace('\r','\n'), stderr_value.replace('\r\n','\n').replace('\r','\n')
    else:
        return '', ''

def task_make_sources_from_xml():
    python_scripts_dir = os.path.join(os.path.dirname(sys.executable),"Scripts")
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
        'file_dep':[os.path.join(src_dir,fname) for fname in ['Interface.xml', 'Interface.dtd', 'ParameterPages.xml']],
        'clean': True
    }

def task_compile_fitutils():
    src_dir = os.path.join('src','main','python','Host','Fitter')
    return {
        'actions':[
            r'cd %s && if [-f fitutils.so ]; then rm fitutils.so; fi' % src_dir,
            r'cd %s && f2py -c -m fitutils fitutils.f' % (src_dir),
        ],
        'targets':[os.path.join(src_dir,'fitutils.so')],
        'file_dep':[os.path.join(src_dir,'fitutils.f')],
        'clean':True
    }

def task_compile_cluster_analyzer():
    src_dir = os.path.join('src','main','python','Host','Fitter')
    return {
        'actions':[
            r'cd %s && if [-f cluster_analyzer.so ]; then rm cluster_analyzer.so; fi' % (src_dir,),
            r'cd %s && python setup.py build_src build_ext --inplace' % (src_dir,),
            r'cd %s && rm cluster_analyzermodule.c' % (src_dir,),
            r'cd %s && rm -rf build' % (src_dir,)
        ],
        'targets':[os.path.join(src_dir,'cluster_analyzer.so')],
        'file_dep':[os.path.join(src_dir,fname) for fname in ['cluster_analyzer.c', 'cluster_analyzer.h']],
        'clean':True
    }

def task_compile_swathP():
    src_dir = os.path.join('src','main','python','Host','Common')
    return {
        'actions':[
            r'cd %s && if [ -f swathP.so ]; then rm swathP.so; fi' % src_dir,
            r'cd %s && f2py swathP.pyf swathP.c -c' % (src_dir),
        ],
        'targets':[os.path.join(src_dir,'swathP.so')],
        'file_dep':[os.path.join(src_dir,fname) for fname in ['swathP.c', 'swathP.pyf']],
        'clean':True
    }

def task_compile_fastLomb():
    src_dir = os.path.join('src','main','python','Host','Utilities','SuperBuildStation')
    return {
        'actions':[
            r'cd %s && if [ -f fastLomb.so ]; then rm fastLomb.so; fi' % (src_dir,),
            r'cd %s && python setup.py build_src build_ext --inplace' % (src_dir,),
            r'cd %s && rm fastLombmodule.c' % (src_dir,),
            r'cd %s && rm -rf build' % (src_dir,)
        ],
        'targets':[os.path.join(src_dir,'fastLomb.so')],
        'file_dep':[os.path.join(src_dir,fname) for fname in ['fastLomb.c', 'fastLomb.pyf']],
        'clean':True
    }

def task_compile_DatViewer():
    def compile_datviewer_source():
        import py_compile
        py_compile.compile(os.path.join(datviewer_dir, 'DatViewer.py'))
        py_compile.compile(os.path.join(datviewer_dir, 'DateRangeSelectorFrame.py'))
        py_compile.compile(os.path.join(datviewer_dir, 'Analysis.py'))
        py_compile.compile(os.path.join(datviewer_dir, 'FileOperations.py'))
        py_compile.compile(os.path.join(datviewer_dir, 'timestamp.py'))
        py_compile.compile(os.path.join(datviewer_dir, 'CustomConfigObj.py'))
        
    datviewer_dir = os.path.join('src','main','python','AddOns','DatViewer')
    return {
        'actions':[
            compile_datviewer_source
        ],
        'targets': [os.path.join(datviewer_dir, 'DatViewer.pyc'),
                    os.path.join(datviewer_dir, 'DateRangeSelectorFrame.pyc'),
                    os.path.join(datviewer_dir, 'Analysis.pyc'),
                    os.path.join(datviewer_dir, 'FileOperations.pyc'),
                    os.path.join(datviewer_dir, 'timestamp.pyc'),
                    os.path.join(datviewer_dir, 'CustomConfigObj.pyc')
        ],
        'file_dep':[os.path.join(datviewer_dir, 'DatViewer.py'),
                    os.path.join(datviewer_dir, 'DateRangeSelectorFrame.py'),
                    os.path.join(datviewer_dir, 'Analysis.py'),
                    os.path.join(datviewer_dir, 'FileOperations.py'),
                    os.path.join(datviewer_dir, 'timestamp.py'),
                    os.path.join(datviewer_dir, 'CustomConfigObj.py')
        ]
    }

def task_compile_sources():
    return {'actions': None,
            'task_dep': ['make_sources_from_xml', 'compile_fitutils', 'compile_cluster_analyzer', 'compile_swathP', 'compile_fastLomb', 'compile_DatViewer']}

def task_build_datviewer_exe():
    dist_dir = get_var('dist_dir', '.')

    def python_build_datviewer_exe(dist_dir):
        build_dir = os.path.join(dist_dir, "AddOns", "DatViewer")
        old_dir = os.getcwd()
        os.chdir(build_dir)
        try:
            # Get the current dir. Expect that we are in the DatViewer folder.
            cur_dir_path = os.getcwd()
            cur_dir = os.path.split(cur_dir_path)[1]
            # Windows dirs are not case-sensitive.
            # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
            if cur_dir.lower() != "datviewer":
                raise ValueError("Not running in expected folder 'DatViewer'.")
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
            ret_code = subprocess.call(['python.exe', 'datviewerSetup.py', 'py2exe'], env=build_env)
            if ret_code != 0:
                raise ValueError("datviewerSetup.py failed")
            dist_target = os.path.join(dist_dir, "DatViewerExe")
            if os.path.exists(dist_target):
                shutil.rmtree(dist_target)
            shutil.move(os.path.join(build_dir, "dist"), dist_target)

        finally:
            os.chdir(old_dir)

    yield {'actions': [(python_build_datviewer_exe,(dist_dir,))],
           'name':dist_dir,
           'targets' : [os.path.join(dist_dir, "DatViewerExe")],
           'file_dep': [os.path.join(dist_dir, "last_updated.txt")],
            'verbosity': 2
    }            
            
def task_build_ai_autosampler_exe():
    dist_dir = get_var('dist_dir', '.')

    def python_build_ai_autosampler_exe(dist_dir):
        build_dir = os.path.join(dist_dir, "AddOns", "AIAutosampler")
        old_dir = os.getcwd()
        os.chdir(build_dir)
        try:
            # Get the current dir. Expect that we are in the AIAutosampler folder.
            cur_dir_path = os.getcwd()
            cur_dir = os.path.split(cur_dir_path)[1]
            # Windows dirs are not case-sensitive.
            # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
            if cur_dir.lower() != "aiautosampler":
                raise ValueError("Not running in expected folder 'AIAutosampler'.")
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
            ret_code = subprocess.call(['python.exe', 'autosamplerSetup.py', 'py2exe'], env=build_env)
            if ret_code != 0:
                raise ValueError("autosamplerSetup.py failed")
            dist_target = os.path.join(dist_dir, "AIAutosamplerExe")
            if os.path.exists(dist_target):
                shutil.rmtree(dist_target)
            shutil.move(os.path.join(build_dir, "dist"), dist_target)

        finally:
            os.chdir(old_dir)

    yield {'actions': [(python_build_ai_autosampler_exe,(dist_dir,))],
           'name':dist_dir,
           'targets' : [os.path.join(dist_dir, "AIAutosamplerExe")],
           'file_dep': [os.path.join(dist_dir, "last_updated.txt")],
            'verbosity': 2
    }

def task_before_cythonization():
    """
    This task just creates an empty so file if it doesn't exist
    This is to meet the file_dep requirement in task_cythonization
    """
    def check_file(cython_file):
        if not os.path.exists(cython_file):
            with open(cython_file, "w") as f:
                pass

    dir_source = get_var('dir_source', '')
    if len(dir_source) > 0:
        for filename in buildUtils.get_cython_source(dir_source):
            cython_file = filename[:-2] + "so"
            yield {
                'name': cython_file,
                'actions': [(check_file, (cython_file,))],
                'targets': [cython_file],
                'verbosity': 2
            }

def task_cythonization():
    """
    This task depends on both python source file and cythonized file
    If one of them is changed, cythonization will be run.
    Otherwise cythonization will be skipped.
    """
    def cythonize_file(filename):
        cython_file = filename[:-2] + "so"
        if os.path.exists(cython_file):
            os.remove(cython_file)
        run_command(['python', r"./bldsup/setupForCython.py", 'build_ext',
                        '--inplace', '--filename=%s' % filename])
        # save cythonized file in reservoir
        buildUtils.save_cython_file(cython_file, dir_source)
        # clean up
        c_file = filename[:-2] + "c"
        if os.path.exists(c_file):
            os.remove(c_file)

    dir_source = get_var('dir_source', '')
    if len(dir_source) > 0:
        for filename in buildUtils.get_cython_source(dir_source):
            yield {
                'name': filename,
                'actions': [(cythonize_file, (filename,))],
                'file_dep': [filename, filename[:-2] + "so"],
                'verbosity': 2
            }

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

def task_build_ssim():
    COORDINATOR_FILE_FORMAT = 'Coordinator_SSIM_%s.ini'
    COORDINATOR_METADATA = 'meta.json'

    dist_dir = get_var('dist_dir')
    if dist_dir is not None:
        meta_file = os.path.join(dist_dir, "AddOns", "SSIM", COORDINATOR_METADATA)
        if os.path.exists(meta_file):
            with open(meta_file, 'r') as metaFp:
                meta = json.load(metaFp)
            targets = [COORDINATOR_FILE_FORMAT % analyzer_type for analyzer_type in meta]

            def python_build_ssim(dist_dir, meta):
                build_dir = os.path.join(dist_dir, "AddOns", "SSIM")
                old_dir = os.getcwd()
                os.chdir(build_dir)
                try:
                    # Get the current dir. Expect that we are in the SSIM folder.
                    cur_dir_path = os.getcwd()
                    cur_dir = os.path.split(cur_dir_path)[1]
                    # Windows dirs are not case-sensitive.
                    # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
                    if cur_dir.lower() != "ssim":
                        raise ValueError("Not running in expected folder 'SSIM'.")
                    env = jinja2.Environment(loader=jinja2.FileSystemLoader(
                            os.path.join('.', 'templates')))
                    t = env.get_template('Coordinator_SSIM.ini.j2')
                    for k in meta:
                        print "Generating coordinator for '%s'." % k
                        standards = [col for col in meta[k]['columns'] if col[5] == 'True']
                        with open(COORDINATOR_FILE_FORMAT % k, 'w') as coordFp:
                            coordFp.write(t.render(analyzer=meta[k],
                                                standards=standards))
                finally:
                    os.chdir(old_dir)

            yield {'actions': [(python_build_ssim,(dist_dir, meta))],
                'name':dist_dir,
                'targets' : targets,
                'file_dep': [os.path.join(dist_dir, "last_updated.txt")],
                'verbosity': 2
                }

def task_build_chem_correct_exe():
    dist_dir = get_var('dist_dir', '.')

    def python_build_chem_correct_exe(dist_dir):
        build_dir = os.path.join(dist_dir, "AddOns", "ChemCorrect")
        old_dir = os.getcwd()
        os.chdir(build_dir)
        try:
            # Get the current dir. Expect that we are in the ChemCorrect folder.
            cur_dir_path = os.getcwd()
            cur_dir = os.path.split(cur_dir_path)[1]
            # Windows dirs are not case-sensitive.
            # Logic will need to be changed slightly to support OSes that have case-sensitive directory names.
            if cur_dir.lower() != "chemcorrect":
                raise ValueError("Not running in expected folder 'ChemCorrect'.")
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
            ret_code = subprocess.call(['python.exe', 'chemcorrectSetup.py', 'py2exe'], env=build_env)
            if ret_code != 0:
                raise ValueError("chemcorrectSetup.py failed")
            dist_target = os.path.join(dist_dir, "ChemCorrectExe")
            if os.path.exists(dist_target):
                shutil.rmtree(dist_target)
            shutil.move(os.path.join(build_dir, "dist"), dist_target)

        finally:
            os.chdir(old_dir)

    yield {'actions': [(python_build_chem_correct_exe,(dist_dir,))],
           'name':dist_dir,
           'targets' : [os.path.join(dist_dir, "ChemCorrectExe")],
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

def task_build_sdm_exe():
    dist_dir = get_var('dist_dir', '.')
    build_info = [(os.path.join(dist_dir, "AddOns", "SDM", "DataProcessor"), "dataProcessorSetup.py", ("..", "..", "..")),
                  (os.path.join(dist_dir, "AddOns", "SDM", "Priming"), "primingSetup.py", ("..", "..", "..")),
                  (os.path.join(dist_dir, "AddOns", "SDM", "Sequencer"), "sequencerSetup.py", ("..", "..", ".."))]

    def python_build_sdm_exe(dist_dir, build_dir, setup_file, parent_relpath):
        # build_info specifies a list of tuples containing:
        #    the directory in which a py2exe setup file is to be run,
        #    the name of the py2exe setup file
        #    the relative path to the directory which contains the G2000 Host subtree (added to the PYTHONPATH)
        old_dir = os.getcwd()
        try:
            os.chdir(build_dir)
            # Get the current dir. Expect that we are in the Host folder.
            cur_dir_path = os.getcwd()
            # Set the PYTHONPATH environment variable so the current folder tree is used to
            # pull local libraries from.
            parent_dir = os.path.normpath(os.path.join(cur_dir_path, *parent_relpath))
            firmware_dir = os.path.join(parent_dir, "Firmware")

            # for a sanity check -- not needed in PYTHONPATH as the parent dir will already be there
            common_dir = os.path.join(parent_dir, "Host", "Common")

            # folders must exist
            folders = [parent_dir, common_dir, firmware_dir]
            for folder in folders:
                if not os.path.isdir(folder):
                    raise ValueError("Expected folder '%s' does not exist." % folder)

            build_env = dict(os.environ)
            build_env.update({'PYTHONPATH' : "%s;%s" %(parent_dir, firmware_dir)})
            ret_code = subprocess.call(['python.exe', setup_file, 'py2exe'], env=build_env)
            if ret_code != 0:
                raise ValueError("buid_sdm_exe failed")
        finally:
            os.chdir(old_dir)

    for build_dir, setup_file, parent_relpath in build_info:
        yield {'actions': [(python_build_sdm_exe,(dist_dir, build_dir, setup_file, parent_relpath))],
               'name': build_dir,
               'targets' : [os.path.join(build_dir, "dist")],
               'file_dep': [os.path.join(dist_dir, "last_updated.txt")],
               'verbosity': 2}

def task_git_set_credentials():
    return {'actions': ['git config --global credential.helper wincred',
                        'git fetch']
    }
