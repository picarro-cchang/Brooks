import datetime
from filecmp import dircmp
from fnmatch import fnmatch
import json
import os
import shlex
import subprocess
import time
from pybuilder.errors import BuildFailedException
from pybuilder.plugins.python.core_plugin import copy_python_sources, copy_scripts, init_dist_target

def is_contained_in(dcmp, logger):
    """Returns True if every file in the left directory tree of dcmp is present in the
        right directory tree of dcmp and the file contents match
    """
    for name in dcmp.left_only:
        if fnmatch(name, '*.pyc') or fnmatch(name, '.*'):
            continue
        logger.info('File missing: %s' % name)
        return False
    for name in dcmp.diff_files:
        if fnmatch(name, '*.pyc') or fnmatch(name, '.*'):
            continue
        logger.info('File difference: %s' % name)
        return False
    for sub_dcmp in dcmp.subdirs.values():
        if not is_contained_in(sub_dcmp, logger):
            return False
    return True

def run_command(command, ignore_status=False):
    """
    Run a command and return a string generated from its output streams and
    the return code. If ignore_status is False, raise a RuntimeError if the
    return code from the command is non-zero.
    """
    args = shlex.split(command, posix=False)
    p = subprocess.Popen(args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    stdout_value, stderr_value = p.communicate()
    if (not ignore_status) and p.returncode != 0:
        raise RuntimeError("%s returned %d" % (command, p.returncode))
    return stdout_value.replace('\r\n','\n').replace('\r','\n'), p.returncode

class Builder(object):
    def __init__(self, project, logger):
        self.logger = logger
        self.project = project
        self.git_hash = None

    def _remove_python_version_files(self):
        project = self.project
        logger = self.logger
        source_dir = project.expand_path('$dir_source_main_python')
        for root, dirs, files in os.walk(source_dir):
            for fname in files:
                if fname in ['release_version.py', 'setup_version.py', 'build_version.py']:
                    try:
                        os.remove(os.path.join(root, fname))
                    except WindowsError:
                        pass

    def _verAsNumString(self, ver):
        """
        Convert a version dict into a string of numbers in this format:
            <major>.<minor>.<revision>.<build>
        """
        number = "%(major)s.%(minor)s.%(revision)s.%(build)s" % ver
        return number

    def _verAsString(self, product, ver, osType=None):
        """
        Convert a version dict into a human-readable string.
        """
        number = self._verAsNumString(ver)
        if osType is not None:
            return "%s-%s-%s (%s)" % (product, osType, number, ver["git_hash"])
        else:
            return "%s-%s (%s)" % (product, number, ver["git_hash"])

    def log_selected_project_properties(self, prop_list):
        formatted = ""
        for key in sorted(self.project.properties):
            if key in prop_list:
                formatted += "\n%40s : %s" % (key, self.project.get_property(key))
        self.logger.info("Project properties: %s", formatted)

    def initialize(self, product):
        logger = self.logger
        logger.warn("Initialize should be overridden by build class")

    def after_clean(self):
        logger = self.logger
        logger.info("Cleaning compiled sources")
        stdout, return_code = run_command("doit clean", True)
        if return_code != 0:
            raise BuildFailedException("Error while executing doit clean")

    def after_prepare(self):
        return

    def copy_sources(self):
        project = self.project
        logger = self.logger
        python_source =  project.expand_path("$dir_source_main_python")
        scripts_source = project.expand_path("$dir_source_main_scripts")
        python_target = project.expand_path("$dir_dist")
        scripts_target = project.expand_path("$dir_dist/$dir_dist_scripts")
        logger.info("Comparing source directory and build directory")
        python_ok = True
        if os.path.exists(python_source):
            if os.path.exists(python_target):
                dcmp1 = dircmp(python_source, python_target)
                python_ok = is_contained_in(dcmp1, logger)
            else:
                logger.info("No Python files in build directory")
                python_ok = False
        scripts_ok = True
        if os.path.exists(scripts_source):
            if os.path.exists(scripts_target):
                dcmp2 = dircmp(scripts_source, scripts_target)
                scripts_ok = is_contained_in(dcmp2, logger)
            else:
                logger.info("No script files in build directory")
                scripts_ok = False

        if python_ok and scripts_ok:
            logger.info("Sources already copied to {0}".format(project.expand_path("$dir_dist")))
        else:
            init_dist_target(project, logger)
            logger.info("Copying sources to {0}".format(project.expand_path("$dir_dist")))
            copy_python_sources(project, logger)
            copy_scripts(project, logger)
            with open(os.path.join(python_target,'last_updated.txt'),"w") as fp:
                print>>fp, time.asctime()

    def compile_sources(self):
        return

    def publish(self):
        return

    def make_installers(self):
        return

    def get_report_file_path(self, basename):
        project = self.project
        reports_dir = project.expand_path("$dir_reports/%s" % basename)
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        return os.path.join(reports_dir, '%s_%s.txt' %
                            (datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), basename))

    def handle_types(self, types, build_info):
        # Types is a comma-separated string of device types
        #  which may be preceeded by an "!" to indicate that those
        #  types are to be excluded.
        project = self.project
        logger = self.logger
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
        project.set_property('types_to_build', types_to_build)

    def handle_set_version(self, version, version_file):
        project = self.project
        logger = self.logger
        # First check that the version is in the correct format
        fields = ["major", "minor", "revision", "build"]
        major, minor, revision, build = [int(v) for v in version.split(".")]
        new_ver = dict(major=major, minor=minor, revision=revision, build=build)
        new_ver_list = [int(new_ver[field]) for field in fields]
        if os.path.exists(version_file):
            with open(version_file,"r") as fp:
                old_ver = json.load(fp)
                old_ver_list = [int(old_ver[field]) for field in fields]
                if new_ver_list <= old_ver_list:
                    raise ValueError("Version to set must exceed current version: %s" %
                                     ".".join(["%d" % f for f in old_ver_list]))
        with open(version_file,"w") as outp:
            ver_json = json.dumps(new_ver)
            if logger:
                logger.info("Setting version to %s" % ".".join(["%d" % f for f in new_ver_list]))
            outp.write(ver_json)

    def handle_incr_version(self, field, version_file):
        project = self.project
        logger = self.logger
        # First check that the version is in the correct format
        fields = ["major", "minor", "revision", "build"]
        field = field.strip().lower()
        if field not in fields:
            raise ValueError("incr_version field should be one of %s" % ", ".join(fields))
        with open(version_file,"r") as fp:
            version = json.load(fp)
        # Increment the specified field and reset fields of lesser significance
        reset = False
        for f in fields:
            version[f] = int(version[f])
            if f == field:
                version[f] += 1
                reset = True
            elif reset:
                version[f] = 0
        version_list = [int(version[field]) for field in fields]
        with open(version_file,"w") as fp:
            ver_json = json.dumps(version)
            if logger:
                logger.info("Setting version to %s" % ".".join(["%d" % f for f in version_list]))
            fp.write(ver_json)

    def handle_version(self, version_file):
        project = self.project
        logger = self.logger
        official = project.get_property("official")
        product = project.get_property("product")

        new_version = False
        # set_version is a string of the form major.minor.revision.build. If present, this causes the
        #  version of the installer to be set to the specified value, replacing the current value in the
        #  json version file
        if project.has_property("set_version"):
            if project.has_property("incr_version"):
                raise ValueError("Cannot use both set_version and incr_version")
            self.handle_set_version(project.get_property("set_version"), version_file)
            new_version = True

        # incr_version is one of the strings "major", "minor", "revision" or "build". If present, this
        #  causes the version of the installer to be incremented from the value in the json
        #  version file
        if project.has_property("incr_version"):
            self.handle_incr_version(project.get_property("incr_version"), version_file)
            new_version = True

        if new_version:
            out, retcode = run_command("git add %s" % version_file, False)
            """TO DO: Commit to git and push to github as well"""
            logger.info("Updating version on git\n%s", out)

        # At this point, no more changes can be made to the repository, so we get fetch the git hash
        self.git_hash = run_command("git.exe log -1 --pretty=format:%H")[0]

        with open(version_file,"r") as inp:
            ver = json.load(inp)
            project.name = product
            raw_version = ("%s.%s.%s.%s%s" %
                (ver["major"], ver["minor"], ver["revision"], ver["build"], "" if official else "-INTERNAL" ))
            project.version = "%s-%s" % (raw_version , self.git_hash[:8])
            project.set_property('raw_version', raw_version)
            project.set_property('installer_version',"%s.%s.%s.%s" % (ver["major"], ver["minor"], ver["revision"], ver["build"]))
        # Need to set the directory into which the output distribution is placed
        project.set_property('dir_dist','$dir_target/dist/%s-%s' % (project.name, raw_version))


