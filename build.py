import json
import os
import pprint

from pybuilder.core import after, before, use_plugin, init, task
from pybuilder.errors import BuildFailedException

import shutil
import subprocess
import sys
import time

ISCC_WIN7 = 'c:/program files (x86)/Inno Setup 5/ISCC.exe'
INSTALLER_SCRIPTS_DIR = ('src', 'main', 'python', 'Tools', 'Release', 'InstallerScriptsWin7') 

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
# use_plugin("python.flake8")
# use_plugin("python.coverage")

default_task = "publish"

def handle_types(types, build_info, logger=None):
    types = types.strip()
    negate = (types[0] == "!")
    types_list = (types[1:] if negate else types).split(',') 
    types_list = [item.strip() for item in types_list]

    types_to_build = []
    for item in sorted(build_info.keys()):
        if negate:
            if item not in types_list:
                types_to_build.append(item)
        else:
            if item in types_list:
                types_to_build.append(item)
    if logger:
        logger.info("Installer types to build: %s" % ", ".join(types_to_build))
        
    return types_to_build
@init
def initialize(project, logger):
    # official removes "INTERNAL" from version number
    official = project.get_property("official", "False")
    official = official.lower() in ("yes", "true", "t", "1")
    # product specifies which installer to produce, currently supported values are g2000
    product = project.get_property("product", "g2000")
    # types is a comma separated list of installers to create or to exclude (if preceeded by !)
    #  Default is to include all types
    types = project.get_property("types", "!")
    
    version_file = os.path.join("versions","%s_version.json" % product)
    with open(version_file,"r") as inp:
        ver = json.load(inp)
        project.name = product
        project.version = ("%s.%s.%s.%s%s" % 
            (ver["major"], ver["minor"], ver["revision"], ver["build"], "" if official else "-INTERNAL" ))
        project.set_property('installer_version',"%s.%s.%s.%s" % (ver["major"], ver["minor"], ver["revision"], ver["build"]))
    # Need to set the directory into which the output distribution is placed        
    project.set_property('dir_dist','$dir_target/dist/%s-%s' % (project.name, project.version))
    
    types_file = os.path.join("versions","%s_types.json" % product)
    with open(types_file,"r") as inp:
        config_info = json.load(inp)
    types_to_build = handle_types(types, config_info['buildTypes'], logger)
        
    project.set_property('types_to_build', types_to_build)
    project.set_property('config_info', config_info['buildTypes'])
        
    

@after("prepare")
def setup_buildenv(project, logger):
    official = project.get_property("official", False)
    product = project.get_property("product", "g2000")

    reports_dir = project.expand_path("$dir_reports")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    output_file_path = os.path.join(reports_dir, "setup_buildenv")

    logger.info("Setting up build environment")
    cmd = ["doit", "make_release", "--product", product]
    if official:
        cmd.append(["--official"])
    with open(output_file_path, "w") as output_file:
        process = subprocess.Popen(cmd,
                                   stdout=output_file,
                                   stderr=output_file,
                                   shell=False)
        return_code = process.wait()
        if return_code != 0:
            raise BuildFailedException("Error while executing make_release")
def write_setup_script(project, logger):
    setup_script = project.expand_path("$dir_dist/Host/setup.py")
    logger.info("Writing setup.py as %s", setup_script)
    shutil.copyfile("testSetup.py", setup_script)
    os.chmod(setup_script, 0o755)

def build_binary_distribution(project, logger):
    reports_dir = project.expand_path("$dir_reports/distutils")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)

    setup_script = project.expand_path("$dir_dist/Host/buildHost.py")

    logger.info("Building binary distribution in %s",
                project.expand_path("$dir_dist"))

    command = "buildHost"
    logger.debug("Executing buildHost.py")
    output_file_path = os.path.join(reports_dir, command)
    with open(output_file_path, "w") as output_file:
        commands = [sys.executable, setup_script]
        process = subprocess.Popen(commands,
                                   cwd=project.expand_path("$dir_dist/Host"),
                                   stdout=output_file,
                                   stderr=output_file,
                                   shell=False)
        return_code = process.wait()
        if return_code != 0:
            raise BuildFailedException(
                "Error while executing setup command %s, see %s for details" % (command, output_file_path))
    shutil.move(project.expand_path("$dir_dist/Host/dist"),project.expand_path("$dir_dist/HostExe"))
@before("publish")
def run_py2exe(project, logger):
    logger.info("Running py2exe in %s", project.expand_path("$dir_dist"))
    reports_dir = project.expand_path("$dir_reports")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    output_file_path = os.path.join(reports_dir, "build_hostexe")
    with open(output_file_path, "w") as output_file:
        process = subprocess.Popen(["doit", "build_hostexe", "--build_dir", "%s" % project.expand_path("$dir_dist/Host")],
                                   stdout=output_file,
                                   stderr=output_file,
                                   shell=False)
        return_code = process.wait()
        if return_code != 0:
            raise BuildFailedException("Error while executing run_py2exe/build_hostexe")

    shutil.move(project.expand_path("$dir_dist/Host/dist"),project.expand_path("$dir_dist/HostExe"))
    
    
@task
def compile_sources(project, logger):
    reports_dir = project.expand_path("$dir_reports/compile_sources")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    output_file_path = os.path.join(reports_dir, "compile_sources")
    with open(output_file_path, "w") as output_file:
        process = subprocess.Popen(["doit", "compile_sources"],
                                   stdout=output_file,
                                   stderr=output_file,
                                   shell=False)
        return_code = process.wait()
        if return_code != 0:
            raise BuildFailedException("Error while executing compile_sources")
            
@task
def publish(project, logger):
    pass
@task
def make_installers(project, logger):
    config_info = project.get_property('config_info')
    sandbox_dir = project.expand_path('$dir_source_main_python')
    resource_dir = project.expand_path('$dir_dist/Installers')
    dist_dir = project.expand_path('$dir_dist') 
    reports_dir = project.expand_path("$dir_reports")
    logger.info("Reports_dir: %s" % reports_dir)
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    output_file_path = os.path.join(reports_dir, "make_installers")

    for installer_type in project.get_property('types_to_build'):
        species = config_info[installer_type]['species']
        iss_filename = "setup_%s_%s.iss" % (installer_type, species)
        setup_file_path = os.path.join(*(INSTALLER_SCRIPTS_DIR + (iss_filename,)))
        logger.info("Building from %s" % setup_file_path)
        config_dir = os.path.join(os.getcwd(),'Config')
        #
        # Build a fully qualified path for the scripts folder, so ISCC can find
        # the include files (can't find them using a relative path here)
        # Notes:
        #
        # installerVersion: must be of the form x.x.x.x, for baking version number
        #                   into setup_xxx.exe metadata (for Explorer properties)
        # hostVersion:      e.g., g2000_win7-x.x.x-x, displayed in the installer UI
        # productVersion:   used for displaying Product version in Explorer properties
        current_year = time.strftime("%Y")
        logger.info('Project version: %s' % project.version)
        args = [ISCC_WIN7, "/dinstallerType=%s" % installer_type,
                "/dhostVersion=%s" % project.version,
                "/dinstallerVersion=%s" % project.get_property('installer_version'),
                "/dproductVersion=%s" % project.version,
                "/dproductYear=%s" % current_year,
                "/dsandboxDir=%s" % sandbox_dir,
                "/dconfigDir=%s" % config_dir,
                "/dcommonName=%s" % species,
                "/ddistDir=%s" % dist_dir,
                "/v9",
                "/O%s" % resource_dir,
                setup_file_path]
                
        output_file_path = os.path.join(reports_dir, "make_installers")
        with open(output_file_path, "a") as output_file:
            process = subprocess.Popen(args,
                                       stdout=output_file,
                                       stderr=output_file,
                                       shell=False)
            return_code = process.wait()
            if return_code != 0:
                raise BuildFailedException("Error while making installer for %s" % installer_type)
                sys.exit(retCode)
