from pybuilder import bootstrap

bootstrap()

import os
from pybuilder.core import after, before, depends, use_plugin, init, task, optional
from pybuilder.errors import BuildFailedException
from pybuilder.core import use_bldsup

use_bldsup(build_support_dir="bldsup")
import Builder
from BuildAiAutosampler import BuildAiAutosampler
from BuildChemCorrect import BuildChemCorrect
from BuildSI2000 import BuildSI2000
from BuildMobile import BuildMobile
from BuildSDM import BuildSDM
from BuildSSIM import BuildSSIM
from BuildVaporizerCleaner import BuildVaporizerCleaner
from BuildDatViewer import BuildDatViewer

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("p_func_test", plugin_module_name="Host.Utilities.BuildHelper.functional_test_plugin")
use_plugin("picarro", plugin_module_name="Host.Utilities.BuildHelper.integration_test_plugin")
use_plugin("python.install_dependencies")
# use_plugin("python.flake8")
# use_plugin("python.coverage")

default_task = "make_installers"

@init
def initialize(project, logger):
    BuildClasses = dict(ai_autosampler = BuildAiAutosampler,
                        chem_correct = BuildChemCorrect,
                        si2000 = BuildSI2000,
                        mobile = BuildMobile,
                        sdm = BuildSDM,
                        ssim = BuildSSIM,
                        vaporizer_cleaner=BuildVaporizerCleaner,
                        datviewer=BuildDatViewer)
    ### Normalize input ###

    # official removes "INTERNAL" from version number
    official = project.get_property("official", "False")
    official = official.lower() in ("yes", "y", "true", "t", "1")
    project.set_property("official", official)
    # product specifies which installer to produce, currently supported values are si2000
    product = project.get_property("product", "si2000").strip().lower()
    project.set_property("product", product)
    builder = BuildClasses[product.lower()](project, logger)
    # check_woking_tree ensures working tree is clean before doing build
    check_working_tree = project.get_property("check_working_tree", "False")
    check_working_tree = check_working_tree.lower() in ("yes", "y", "true", "t", "1")
    if check_working_tree:
        logger.info("Calling git to check if working tree is clean")
        if not builder.is_working_tree_clean():
            raise RuntimeError("Working tree is not consistent with repository.")
    # tag determines if the repository is to be tagged after the build
    tag = project.get_property("tag", "True" if official else "False")
    tag = tag.lower() in ("yes", "y", "true", "t", "1")
    project.set_property("tag", tag)
    # push determines if the repository is to be pushed to GitHub after the build
    push = project.get_property("push", "True" if official else "False")
    push = push.lower() in ("yes", "y", "true", "t", "1")
    project.set_property("push", push)
    # force determines if we are to ignore version number ordering
    force = project.get_property("force", "False")
    force = force.lower() in ("yes", "y", "Y", "true", "t", "1")
    project.set_property("force", force)
    # upload determines if we are to upload installers to artifactory
    upload = project.get_property("upload_artifactory", "False")
    upload = upload.lower() in ("yes", "y", "Y", "true", "t", "1")
    project.set_property("upload_artifactory", upload)
    
    # branch, if specified, checks that the correct branch has been checked out
    if project.has_property("branch"):
        branch = project.get_property("branch").strip()
        output, retcode = builder.run_command("git symbolic-ref --short -q HEAD")
        output = output.strip()
        if output != branch:
            raise RuntimeError("Incorrect branch: %s" % output)
    project.set_property("builder", builder)
    builder.initialize(product)

@after("prepare")
def after_prepare(project, logger):
    builder = project.get_property("builder")
    builder.after_prepare()
    
@task
def compile_sources(project, logger):
    builder = project.get_property("builder")
    builder.compile_sources()
    
@task
@depends('compile_sources', optional('run_unit_tests'))
def cythonize_sources(project, logger):
    builder = project.get_property("builder")
    builder.cythonize_sources()

@task
@depends('cythonize_sources')
def copy_sources(project, logger):
    builder = project.get_property("builder")
    builder.copy_sources()

@task
@depends('copy_sources')
def compile_sources_to_pyo(project, logger):
    builder = project.get_property("builder")
    builder.compile_sources_to_pyo()

@task
@depends('compile_sources_to_pyo', optional('run_integration_testing'))
def make_installers(project, logger):
    builder = project.get_property("builder")
    builder.make_installers()
    
@after('make_installers')
def tidy_repo(project, logger):
    builder = project.get_property("builder")
    builder.upload_to_artifactory()
    builder.tidy_repo()

@after('clean')
def after_clean(project, logger):
    builder = project.get_property("builder")
    builder.after_clean()
   
@task
def check_config_hashes(project, logger):
    return Builder.check_config_hashes(project, logger)

@task
def update_config_hashes(project, logger):
    return Builder.update_config_hashes(project, logger)