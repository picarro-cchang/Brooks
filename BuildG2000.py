from Builder import Builder, run_command
import json
import os
from pybuilder.errors import BuildFailedException
import shutil
import time
ISCC_WIN7 = 'c:/program files (x86)/Inno Setup 5/ISCC.exe'
INSTALLER_SCRIPTS_DIR = ('src', 'main', 'python', 'Tools', 'Release', 'InstallerScriptsWin7')

class BuildG2000(Builder):
    def __init__(self, project, logger):
        super(BuildG2000, self).__init__(project, logger)
        logger.info("Instantiating BuildG2000")

    def initialize(self, product):
        assert product.lower() == "g2000"
        project = self.project
        version_file = os.path.join("versions","%s_version.json" % product)
        self.handle_version(version_file)

        # types is a comma separated list of installers to create or to exclude (if preceeded by !)
        #  Default is to include all types
        types = project.get_property("types", "!")
        types_file = os.path.join("versions","%s_types.json" % product)
        with open(types_file,"r") as inp:
            config_info = json.load(inp)
        self.handle_types(types, config_info['buildTypes'])

        project.set_property('config_info', config_info['buildTypes'])

    def compile_sources(self):
        project = self.project
        reports_dir = project.expand_path("$dir_reports/compile_sources")
        if not os.path.exists(reports_dir):
            os.mkdir(reports_dir)
        output_file_path = os.path.join(reports_dir, "compile_sources")
        with open(output_file_path, "w") as output_file:
            stdout, return_code = run_command("doit compile_sources", True)
            output_file.write(stdout)
        if return_code != 0:
            raise BuildFailedException("Error while executing compile_sources")

    def publish(self):
        project = self.project
        logger = self.logger
        logger.info("Running py2exe in %s", project.expand_path("$dir_dist"))
        reports_dir = project.expand_path("$dir_reports")
        if not os.path.exists(reports_dir):
            os.mkdir(reports_dir)
        output_file_path = os.path.join(reports_dir, "build_hostexe")
        with open(output_file_path, "w") as output_file:
            cmd = "doit build_hostexe --build_dir %s" % project.expand_path("$dir_dist/Host")
            stdout, return_code = run_command(cmd, True)
            output_file.write(stdout)
            if return_code != 0:
                raise BuildFailedException("Error while executing run_py2exe/build_hostexe")
        shutil.move(project.expand_path("$dir_dist/Host/dist"),project.expand_path("$dir_dist/HostExe"))

    def after_prepare(self):
        project = self.project
        logger = self.logger
        official = project.get_property("official")
        product = project.get_property("product")

        reports_dir = project.expand_path("$dir_reports")
        if not os.path.exists(reports_dir):
            os.mkdir(reports_dir)
        output_file_path = os.path.join(reports_dir, "setup_buildenv")

        logger.info("Setting up build environment")
        cmd = "doit make_release --product %s" % product
        if official:
            cmd += " --official"
        with open(output_file_path, "w") as output_file:
            stdout, return_code = run_command(cmd, True)
            output_file.write(stdout)
            if return_code != 0:
                raise BuildFailedException("Error while executing make_release")

    def make_installers(self):
        project = self.project
        logger = self.logger
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
                stdout, return_code = run_command(" ".join(args), True)
                output_file.write(stdout)
                if return_code != 0:
                    raise BuildFailedException("Error while making installer for %s" % installer_type)
