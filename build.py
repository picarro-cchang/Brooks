import os

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

name = "Host"
default_task = "publish"

@init
def set_properties(project):
    pass

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
    reports_dir = project.expand_path("$dir_reports/run_py2exe")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    output_file_path = os.path.join(reports_dir, "hostexe")
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
