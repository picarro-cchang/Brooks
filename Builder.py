import json
import os
import shlex
import subprocess

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
    return stdout_value, p.returncode

class Builder(object):
    def __init__(self, project, logger):
        self.logger = logger
        self.project = project

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

    def initialize(self, product):
        logger = self.logger
        logger.warn("Initialize should be overridden by build class")

    def after_prepare(self):
        return

    def compile_sources(self):
        return

    def publish(self):
        return

    def make_installers(self):
        return

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

        with open(version_file,"r") as inp:
            ver = json.load(inp)
            project.name = product
            project.version = ("%s.%s.%s.%s%s" %
                (ver["major"], ver["minor"], ver["revision"], ver["build"], "" if official else "-INTERNAL" ))
            project.set_property('installer_version',"%s.%s.%s.%s" % (ver["major"], ver["minor"], ver["revision"], ver["build"]))
        # Need to set the directory into which the output distribution is placed
        project.set_property('dir_dist','$dir_target/dist/%s-%s' % (project.name, project.version))
