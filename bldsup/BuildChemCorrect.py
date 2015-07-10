from Builder import Builder, run_command
import json
import os
from pybuilder.errors import BuildFailedException
import shutil
import textwrap
import time

ISCC_WIN7 = 'c:/program files (x86)/Inno Setup 5/ISCC.exe'
INSTALLER_SCRIPTS_DIR = ('src', 'main', 'python', 'AddOns', 'ChemCorrect', 'InstallerScriptsWin7')

RELEASE_VERSION_FILES = [('src', 'main', 'python', 'AddOns', 'ChemCorrect', 'release_version.py')]
INTERNAL_VERSION_FILES = [('src', 'main', 'python', 'AddOns', 'ChemCorrect', 'setup_version.py')]

JSON_VERSION_FILE = ('src', 'main', 'python', 'AddOns', 'ChemCorrect', 'version.json')

class BuildChemCorrect(Builder):
    def __init__(self, project, logger):
        super(BuildChemCorrect, self).__init__(project, logger)
        logger.info("Instantiating BuildChemCorrect")

    def initialize(self, product):
        project = self.project
        logger = self.logger
        assert product.lower() == "chem_correct"
        project = self.project
        version_file = os.path.join(*JSON_VERSION_FILE)
        self.handle_version(version_file)
        logger.info("Distribution directory: %s" % project.get_property("dir_dist"))
        self.log_selected_project_properties(['product', 'official', 'incr_version', 'set_version'])

    def publish(self):
        project = self.project
        logger = self.logger
        logger.info("Running py2exe in %s", project.expand_path("$dir_dist"))
        reports_dir = project.expand_path("$dir_reports")
        output_file_path = self.get_report_file_path("build_chem_correct_exe")
        with open(output_file_path, "a") as output_file:
            output_file.write("=== %s ===\n" % time.asctime())
            cmd = "doit dist_dir=%s build_chem_correct_exe" % project.expand_path("$dir_dist")
            stdout, return_code = run_command(cmd, True)
            output_file.write(stdout)
            if return_code != 0:
                raise BuildFailedException("Error while executing run_py2exe/build_chem_correct_exe")

    def _make_python_version_files(self):
        project = self.project
        official = project.get_property("official")
        product = project.get_property("product")
        contents = textwrap.dedent("""\
        # autogenerated by PyBuilder

        def versionString():
            return '%s'

        def versionNumString():
            return '%s'

        def buildType():
            # Empty string indicates official release
            return '%s'
        """)
        src_file = os.path.join(*JSON_VERSION_FILE)
        ver = {"git_hash":self.git_hash[:8]}

        version_file_list = RELEASE_VERSION_FILES if official else INTERNAL_VERSION_FILES
        for version_file in version_file_list:
            target = os.path.join(*version_file)
            with open(src_file,"r") as inp:
                ver.update(json.load(inp))
            with open(target,"w") as outp:
                outp.write(contents % (self._verAsString(product, ver),
                                       self._verAsNumString(ver), '' if official else 'INTERNAL'))

    def after_prepare(self):
        logger = self.logger
        logger.info("Writing version files into source tree")
        self._remove_python_version_files()
        self._make_python_version_files()

    def make_installers(self):
        project = self.project
        logger = self.logger
        raw_version = project.get_property('raw_version')
        sandbox_dir = project.expand_path('$dir_source_main_python')
        resource_dir = project.expand_path('$dir_target/Installers/%s-%s' % (project.name, raw_version))
        dist_dir = project.expand_path('$dir_dist')

        iss_filename = "setup_ChemCorrect.iss"
        setup_file_path = os.path.join(*(INSTALLER_SCRIPTS_DIR + (iss_filename,)))
        logger.info("Building from %s" % setup_file_path)
        #
        # Build a fully qualified path for the scripts folder, so ISCC can find
        # the include files (can't find them using a relative path here)
        # Notes:
        #
        # installerVersion: must be of the form x.x.x.x, for baking version number
        #                   into setup_xxx.exe metadata (for Explorer properties)
        # productVersion:   used for displaying Product version in Explorer properties
        current_year = time.strftime("%Y")
        logger.info('Project version: %s' % project.version)
        args = [ISCC_WIN7,
                "/dchemcorrectVersion=%s" % raw_version,
                "/dinstallerVersion=%s" % project.get_property('installer_version'),
                "/dproductVersion=%s" % project.version,
                "/dproductYear=%s" % current_year,
                "/dsandboxDir=%s" % sandbox_dir,
                "/ddistDir=%s" % dist_dir,
                "/v9",
                "/O%s" % resource_dir,
                setup_file_path]
        output_file_path = self.get_report_file_path("make_chem_correct_installer")
        with open(output_file_path, "a") as output_file:
            stdout, return_code = run_command(" ".join(args), True)
            output_file.write(stdout)
            if return_code != 0:
                raise BuildFailedException("Error while making ChemCorrect installer")

