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
    project.set_property("dir_source_main_python", "src")
    project.set_property("dir_source_unittest_python", "src/unittest")
    project.set_property("dir_source_main_scripts", "src/scripts")

@after("package")
def write_setup_script(project, logger):
    setup_script = project.expand_path("$dir_dist/Host/setup.py")
    logger.info("Writing setup.py as %s", setup_script)
    shutil.copyfile("testSetup.py", setup_script)
    os.chmod(setup_script, 0o755)


@before("publish")
def build_binary_distribution(project, logger):
    reports_dir = project.expand_path("$dir_reports/distutils")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)

    setup_script = project.expand_path("$dir_dist/Host/setup.py")

    logger.info("Building binary distribution in %s",
                project.expand_path("$dir_dist"))

    commands = ['py2exe']

    for command in commands:
        logger.debug("Executing distutils command %s", command)
        output_file_path = os.path.join(reports_dir, command.replace("/", ""))
        with open(output_file_path, "w") as output_file:
            commands = [sys.executable, setup_script]
            commands.extend(command.split())
            process = subprocess.Popen(commands,
                                       cwd=project.expand_path("$dir_dist/Host"),
                                       stdout=output_file,
                                       stderr=output_file,
                                       shell=False)
            return_code = process.wait()
            if return_code != 0:
                raise BuildFailedException(
                    "Error while executing setup command %s, see %s for details" % (command, output_file_path))

@task
def publish(project, logger):
    print dir(project)
    print project._properties
""" 
['__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_build_dependencies', '_files_to_install', '_install_dependencies', '_manifest_include', '_manifest_included_files', '_package_data', '_properties', 'author', 'authors', 'basedir', 'build_dependencies', 'build_depends_on', 'build_depends_on_requirements', 'default_task', 'dependencies', 'depends_on', 'depends_on_requirements', 'description', 'expand', 'expand_path', 'files_to_install', 'get_mandatory_property', 'get_property', 'has_property', 'home_page', 'include_file', 'install_file', 'license', 'list_modules', 'list_packages', 'list_scripts', 'manifest_included_files', 'name', 'package_data', 'properties', 'set_property', 'set_property_if_unset', 'summary', 'url', 'validate', 'validate_dependencies', 'version', 'write_report']
{'dir_target': 'target', 
u'unittest_module_glob': u'*_tests', 
'verbose': False, 
'dir_logs': '$dir_target/logs', 
'dir_source_main_python': 'Host', 
'dir_dist_scripts': 'scripts', 
'basedir': 'C:\\GitHub\\host-reorg', 
'install_dependencies_upgrade': False, 
'dir_install_logs': '$dir_logs/install_dependencies', 
'dir_dist': '$dir_target/dist/Host-1.0.dev0', 
u'unittest_test_method_prefix': None, 
'install_dependencies_index_url': None, 
u'dir_source_unittest_python': 'unittest', 
'install_dependencies_local_mapping': {}, 
'dir_source_main_scripts': 'scripts', 
'dir_reports': '$dir_target/reports', 
'install_dependencies_extra_index_url': None, 
u'unittest_file_suffix': None}
-----------------------------------------------------
"""
