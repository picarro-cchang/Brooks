from Builder import Builder, check_config_hashes
import json
import os
from pybuilder.core import task
from pybuilder.errors import BuildFailedException
import shutil
import textwrap
import time
import buildUtils

INSTALLER_SCRIPTS_DIR = ('src', 'main', 'python', 'Tools', 'Release', 'InstallerScriptsWin7')
RELEASE_VERSION_FILE = ('src', 'main', 'python', 'Host', 'Common', 'release_version.py')
INTERNAL_VERSION_FILE = ('src', 'main', 'python', 'Host', 'build_version.py')

class BuildSI2000(Builder):
    def __init__(self, project, logger):
        super(BuildSI2000, self).__init__(project, logger)
        logger.info("Instantiating BuildSI2000")

    def initialize(self, product):
        project = self.project
        logger = self.logger
        assert product.lower() == "si2000"
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
        # check_configs runs check_config_hashes before build is allowed to begin
        check_configs = project.get_property("check_configs", "False")
        check_configs = check_configs.lower() in ("yes", "y", "true", "t", "1")
        project.set_property("check_configs", check_configs)
        if check_configs:
            check_config_hashes(project, logger)
        types_to_build = project.get_property('types_to_build')
        logger.info("Installer types to build: %s" % ", ".join(types_to_build))

        # Save build information in a file, so unit tests and integration tests can use
        source_dir = project.expand_path('$dir_source_main_python')
        write_file = os.path.join(source_dir, "Host", "Utilities", "BuildHelper", "BuildInfo.py")
        with open(write_file, "w") as f:
            f.write("# Auto generated by PyBuilder\n")
            f.write("buildTime = %s\n" % (time.time()))
            f.write("buildTypes = ['%s']\n" % ("', '".join(types_to_build)))
            f.write("buildFolder = '%s'" % (project.expand_path('$dir_dist')))

        self.log_selected_project_properties(['product', 'types', 'official', 'incr_version', 'set_version',
            'check_working_tree', 'check_configs', 'push', 'tag'])

    def handle_types(self, types, build_info):
        # Types is a comma-separated string of device types
        #  which may be preceeded by an "!" to indicate that those
        #  types are to be excluded.
        project = self.project
        logger = self.logger
        types = types.strip()
        negate = (types and types[0] == "!")
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
        project.set_property('types_to_build', types_to_build)

    def compile_sources(self):
        project = self.project
        logger = self.logger
        logger.info("Compiling source files")
        output_file_path = self.get_report_file_path("compile_sources")
        with open(output_file_path, "a") as output_file:
            stdout, return_code = self.run_command("doit compile_sources", True)
            output_file.write(stdout)
        if return_code != 0:
            raise BuildFailedException("Error while executing compile_sources")

    def cythonize_sources(self):
        project = self.project
        logger = self.logger
        output_file_path = self.get_report_file_path("cythonize_sources")
        # Copy cythonized files from reservoir
        logger.info("Copy cythonized files from reservoir")
        python_source =  project.expand_path("$dir_source_main_python")
        for filename in buildUtils.get_cython_source(python_source):
            buildUtils.get_cython_file(filename, python_source)
        # Cythonization
        logger.info("Cythonizing modules")
        with open(output_file_path, "a") as output_file:
            output_file.write("=== %s ===\n" % time.asctime())
            stdout, retcode = self.run_command("doit dir_source=%s cythonization" % 
                (project.expand_path("$dir_source_main_python")))
            output_file.write(stdout)
            if retcode != 0:
                raise BuildFailedException("Error while cythonizing sources")                

    def copy_sources(self):
        """
        Copy selected files to sandbox. Existing files will be overwritten.
        """
        project = self.project
        logger = self.logger
        python_source =  project.expand_path("$dir_source_main_python")
        python_target = project.expand_path("$dir_dist")
        source_list = buildUtils.get_cython_source(python_source, after_cython=True)
        source_list.extend(buildUtils.get_noncython_resource(python_source))
        # if there is a Host folder from last build, move it to target/dist/
        old_host = os.path.join(python_target, "home", "picarro", "SI2000", "Host")
        if os.path.exists(old_host):
            logger.info("Found Host folder in sandbox.")
            os.rename(old_host, os.path.join(python_target, "Host"))
        logger.info("Copying sources to {0}".format(python_target))
        for f in source_list:
            if not os.path.exists(f):
                raise BuildFailedException("File not found: %s" % f)
            else:
                relative_path = os.path.relpath(f, python_source)
                dist_file = os.path.join(python_target, relative_path)
                dist_folder = os.path.dirname(dist_file)
                if not os.path.exists(dist_folder):
                    os.makedirs(dist_folder)
                shutil.copyfile(f, dist_file)

    def compile_sources_to_pyo(self):
        return # Don't build/deploy pyo files for SI2000 v1.0 (RSF)
        self.logger.info("Compiling python sources to pyo files")
        path = os.path.join(self.project.expand_path("$dir_dist"), "Host")
        self.run_command("python -O -m compileall -x '__init__.py' %s" % path)
        # delete python source files
        for root, dirs, files in os.walk(path, topdown=False):
            for fname in files:
                if fname.endswith(".py") and fname != "__init__.py":
                    fp = os.path.join(root, fname)
                    os.remove(fp)

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
        src_file = os.path.join("versions", "%s_version.json" % product)
        ver = {"git_hash":self.git_hash[:8]}

        target = os.path.join(*RELEASE_VERSION_FILE) if official else os.path.join(*INTERNAL_VERSION_FILE)
        with open(src_file,"r") as inp:
            ver.update(json.load(inp))
        with open(target,"w") as outp:
            outp.write(contents % (self._verAsString(product, ver),
                                   self._verAsNumString(ver), '' if official else 'INTERNAL'))

    def after_prepare(self):
        logger = self.logger
        self._remove_python_version_files()
        logger.info("Writing version files into source tree")
        self._make_python_version_files()

    def make_control_file(self, debian_dir, analyzer_type):
        raw_version = self.project.get_property('raw_version')
        with open(os.path.join(debian_dir, "control"), "w") as f:
            f.write(
"""\
Package: SI2000
Version: %s
Section: science
Priority: required
Architecture: all
Depends: 
Maintainer: Picarro instrument software team
Description: Picarro Host Software for Semiconductor Industry 
 %s Analyzer
 Version: %s
"""           % (
                raw_version, analyzer_type, raw_version
                )
            )

    def make_installers(self):
        """
        Make debian package from the sandbox.
        """
        project = self.project
        logger = self.logger
        raw_version = project.get_property('raw_version')
        project_full_name = '%s-%s' % (project.name, raw_version)
        config_info = project.get_property('config_info')
        sandbox_dir = project.expand_path('$dir_source_main_python')
        output_file_path = self.get_report_file_path("make_SI2000_installers")
        dist_dir = project.expand_path('$dir_dist')
        dist_dir_temp = dist_dir + "_temp"
        dist_dir_home = os.path.join(dist_dir, 'home')
        dist_dir_new = os.path.join(dist_dir, 'home', 'picarro', 'SI2000')
        # delete home folder that is possibly left from the last build
        #
        # RSF - seeing if this leaves behind files neede to speed up
        # the build when on a few files have changed.
        if os.path.isdir(dist_dir_home):
            shutil.rmtree(dist_dir_home)
        # create the desired directory tree: home/picarro/SI2000
        os.rename(dist_dir, dist_dir_temp)
        os.makedirs(os.path.join(dist_dir, 'home', 'picarro'))
        os.rename(dist_dir_temp, dist_dir_new)
        config_dir = os.path.join(os.getcwd(),'Config')
        # copy commonconfig
        common_config_dir = os.path.join(dist_dir_new, "CommonConfig")
        if os.path.isdir(common_config_dir):
            shutil.rmtree(common_config_dir)
        shutil.copytree(os.path.join(config_dir, "CommonConfig"), common_config_dir)
        # create python path file
        pth_file_dir = os.path.join(dist_dir, 'home', 'picarro', 'anaconda2','lib','python2.7','site-packages')
        os.makedirs(pth_file_dir)
        with open(os.path.join(pth_file_dir, 'Picarro.pth'), 'w') as f:
            f.write("/home/picarro/SI2000")
        # make debian folder
        debian_dir = os.path.join(dist_dir, "DEBIAN")
        if not os.path.isdir(debian_dir):
            os.makedirs(debian_dir)
        shutil.copyfile("./bldsup/preinst", os.path.join(debian_dir, "preinst"))
        shutil.copyfile("./bldsup/postinst", os.path.join(debian_dir, "postinst"))
        os.system("chmod 755 %s" % os.path.join(debian_dir, "preinst"))
        os.system("chmod 755 %s" % os.path.join(debian_dir, "postinst"))
        # make installer directory
        resource_dir = project.expand_path('$dir_target/Installers/%s' % project_full_name)
        if not os.path.exists(resource_dir):
            os.makedirs(resource_dir)
        for installer_type in project.get_property('types_to_build'):
            logger.info("Building debian package for %s" % installer_type)
            # copy config files
            instr_config_dir = os.path.join(dist_dir_new, "InstrConfig")
            if os.path.isdir(instr_config_dir):
                shutil.rmtree(instr_config_dir)
            shutil.copytree(os.path.join(config_dir, installer_type, "InstrConfig"), instr_config_dir)
            app_config_dir = os.path.join(dist_dir_new, "AppConfig")
            if os.path.isdir(app_config_dir):
                shutil.rmtree(app_config_dir)
            shutil.copytree(os.path.join(config_dir, installer_type, "AppConfig"), app_config_dir)
            # make control file
            self.make_control_file(debian_dir, installer_type)
            logger.info('Project version: %s' % project.version)
            with open(output_file_path, "a") as output_file:
                output_file.write("=== %s ===\n" % time.asctime())
                stdout, return_code = self.run_command("dpkg-deb --build %s" % dist_dir)
                output_file.write(stdout)
                if return_code != 0:
                    raise BuildFailedException("Error while making debian package for %s" % installer_type)
            # move package to installer folder
            species = config_info[installer_type]['species']
            os.rename(dist_dir+".deb", 
                os.path.join(resource_dir, 
                    '%s_%s_%s_%s_%s.deb' % (project.name, installer_type, species, raw_version, self.git_hash[:8]) )
                )

def get_dir_hash(root):
    s = sha1()
    ini = None
    hash_ok = False
    for path, dirs, files in os.walk(root):
        dirs.sort()
        for f in files:
            fname = os.path.join(path, f)
            relname = fname[len(root)+1:]
            if relname.lower() == "version.ini":
                ini = ConfigObj(fname)
                continue
            s.update(relname)
            with open(fname,"rb") as f1:
                while True:
                    # Read file in as little chunks
                    buf = f1.read(4096)
                    if not buf : break
                    s.update(buf)
    result = s.hexdigest()
    revno = '0.0.0'
    if ini:
        if 'Version' in ini and 'dir_hash' in ini['Version']:
            hash_ok =  (ini['Version']['dir_hash'] == result)
            revno = ini['Version'].get('revno', '0.0.0')
    return result, hash_ok, revno
