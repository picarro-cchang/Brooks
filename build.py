import json
import os
import pprint

from pybuilder.core import after, before, use_plugin, init, task
from pybuilder.errors import BuildFailedException

import shutil
import subprocess
import sys

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
# use_plugin("python.flake8")
# use_plugin("python.coverage")

default_task = "publish"

@init
def initialize(project, logger):
    official = project.get_property("official", False)
    product = project.get_property("product", "g2000")
    
    version_file = os.path.join("versions","%s_version.json" % product)
    
    with open(version_file,"r") as inp:
        ver = json.load(inp)
        project.name = product
        project.version = ("%s.%s.%s.%s%s" % 
            (ver["major"], ver["minor"], ver["revision"], ver["build"], "" if official else "-INTERNAL" ))
    # Need to set the directory into which the output distribution is placed        
    project.set_property('dir_dist','$dir_target/dist/%s-%s' % (project.name, project.version))

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
