from configobj import ConfigObj
import datetime
from filecmp import dircmp
from fnmatch import fnmatch
from hashlib import sha1
import json
import os
import sys
import shutil
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

class Builder(object):
    def __init__(self, project, logger):
        self.project = project
        self.logger = logger
        self.git_hash = None
        self.git_path = self.project.get_property("git", "")
    
    def run_command(self, command, ignore_status=False):
        """
        Run a command and return a string generated from its output streams and
        the return code. If ignore_status is False, raise a RuntimeError if the
        return code from the command is non-zero.
        """
        args = shlex.split(command, posix=False)
        if args[0] == "git" and self.git_path:
            args[0] = self.git_path
                
        p = subprocess.Popen(args,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

        stdout_value, stderr_value = p.communicate()
        if (not ignore_status) and p.returncode != 0:
            raise RuntimeError("%s returned %d" % (command, p.returncode))
        return stdout_value.replace('\r\n','\n').replace('\r','\n'), p.returncode
    
    def is_working_tree_clean(self):
        """Calls git to see if the working tree is clean (consistent with the repo)"""
        output, retcode = self.run_command("git diff-index --quiet HEAD --", ignore_status=True)
        return retcode==0
     
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
        stdout, return_code = self.run_command("doit clean", ignore_status=True)
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
        
    def cythonize_sources(self):
        project = self.project
        logger = self.logger
        logger.info("Cythonizing modules")
        out, retcode = self.run_command("python %s build_ext --inplace --basepath=%s" % 
                    (r"./bldsup/setupforPyd.py", project.expand_path("$dir_dist")))
        logger.info("Cleaning source code")
        sys.path.append("bldsup")
        from setupforPyd import get_source_list
        for f in get_source_list(project.expand_path("$dir_dist")):
            os.remove(f)
            fc = os.path.splitext(f)[0] + ".c"
            os.remove(fc)

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
                if new_ver_list <= old_ver_list and not project.get_property("force"):
                    raise ValueError("Version to set must exceed current version: %s" %
                                     ".".join(["%d" % f for f in old_ver_list]))
        with open(version_file,"w") as outp:
            ver_json = json.dumps(new_ver)
            if logger:
                logger.info("Setting version to %s" % ".".join(["%d" % f for f in new_ver_list]))
            outp.write(ver_json)
        return version

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
        return version

    def handle_version(self, version_file):
        project = self.project
        logger = self.logger
        official = project.get_property("official")
        product = project.get_property("product")

        new_version = None
        # set_version is a string of the form major.minor.revision.build. If present, this causes the
        #  version of the installer to be set to the specified value, replacing the current value in the
        #  json version file
        if project.has_property("set_version"):
            if project.has_property("incr_version"):
                raise ValueError("Cannot use both set_version and incr_version")
            new_version = self.handle_set_version(project.get_property("set_version"), version_file)

        # incr_version is one of the strings "major", "minor", "revision" or "build". If present, this
        #  causes the version of the installer to be incremented from the value in the json
        #  version file
        if project.has_property("incr_version"):
            new_version = self.handle_incr_version(project.get_property("incr_version"), version_file)

        if new_version is not None:
            out, retcode = self.run_command("git add %s" % version_file, ignore_status=False)
            raw_version = ("%s.%s.%s.%s" %
                (new_version["major"], new_version["minor"], new_version["revision"], new_version["build"]))
            out, retcode = self.run_command('git commit -m "Updating %s to version %s"' % (product, raw_version), ignore_status=False)
            logger.info("Updating version on local git repository\n%s" % out)

        # At this point, no more changes can be made to the repository, so we get fetch the git hash
        self.git_hash = self.run_command("git log -1 --pretty=format:%H")[0]

        with open(version_file,"r") as inp:
            ver = json.load(inp)
            project.name = product
            raw_version = ("%s.%s.%s.%s%s" %
                (ver["major"], ver["minor"], ver["revision"], ver["build"], "" if official else "-INTERNAL" ))
            project.version = "%s-%s" % (raw_version , self.git_hash[:8])
            project.set_property('raw_version', raw_version)
            project.set_property('installer_version',"%s.%s.%s.%s" % (ver["major"], ver["minor"], ver["revision"], ver["build"]))
        # Need to set the directory into which the output distribution is placed
        project.set_property('dir_dist','$dir_target/dist/%s-%s' % (product, raw_version))
    
    def tidy_repo(self):
        """Handle taggging and pushing of repository if these have been requested
        """
        project = self.project
        logger = self.logger
        if project.get_property('tag'):
            installer_version = project.get_property('installer_version')
            product = project.get_property('product')
            tagname = '%s-%s' % (product, installer_version)
            out, retcode = self.run_command('git tag -a %s -m %s"' % (tagname, tagname), ignore_status=False)
            logger.info('Tagged repository: %s' % tagname)
        if project.get_property('push'):
            out, retcode = self.run_command('git push origin --tags', ignore_status=False)
            logger.info('Pushed repository: %s' % out)
    
    def upload_to_artifactory(self):
        """Upload installers to artifactory using curl commands
        """
        project = self.project
        logger = self.logger
        if project.get_property('upload_artifactory'):
            installer_version = project.get_property('installer_version')
            product = project.get_property('product')
            installer_folder = os.path.join('target', 'Installers', '%s-%s' % (product, installer_version))
            for file in os.listdir(installer_folder):
                if file.endswith('.exe'):
                    src_path = os.path.join(installer_folder, file)
                    dest_path = r"https://picarro.artifactoryonline.com/picarro/picarro-generic-private/hostexe/" + installer_version + "/"
                    cmd = "curl -u %s:%s -T %s %s" % ("ci-server", "ALGP@&gNR%h", src_path, dest_path)
                    self.run_command(cmd)
                    logger.info('Upload %s installer to Artifactory' % file)
    
    def copy_installer(self):
        """Copy installers to remote directory (e.g., S drive) if this has been requested
        """
        project = self.project
        logger = self.logger
        dest_path = project.get_property('copyDir')
        if len(dest_path) > 0:
            installer_version = project.get_property('installer_version')
            product = project.get_property('product')
            installer_folder = os.path.join('target', 'Installers', '%s-%s' % (product, installer_version))
            for file in os.listdir(installer_folder):
                if file.endswith('.exe'):
                    src_path = os.path.join(installer_folder, file)
                    species = file.split('_')[1]
                    if species == os.path.split(dest_path)[1]:  # already points to the species folder
                        dst = dest_path
                    else:
                        dst = os.path.join(dest_path, species)
                        if not os.path.isdir(dst):
                            os.makedirs(dst)
                    shutil.copy(src_path, dst)
                    logger.info('Copy %s-%s installer to %s' % (species, installer_version, dst))
            
def get_dir_hash(root):
    s = sha1()
    ini = None
    hash_ok = False
    for path, dirs, files in os.walk(root):
        dirs.sort()
        for f in sorted(files):
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
        
def check_config_hashes(project, logger):
    fnamec = 'current_configs.txt'
    fnameu = 'updated_configs.txt'
    logger.info('Checking for configuration updates')
    break_build = False
    with open(fnamec, 'w') as cp:
        with open(fnameu, 'w') as fp:
            commonconfig_dir = os.path.join('Config', 'CommonConfig')
            dir_hash, hash_ok, revno = get_dir_hash(commonconfig_dir)
            if not hash_ok:
                break_build = True
                logger.info('CommonConfig hash incorrect: %s' % (dir_hash,))
                print>>fp, "%s, %s" % ("CommonConfig",revno)
            else:
                print>>cp, "%s, %s" % ("CommonConfig",revno)
            build_types = sorted(project.get_property('config_info', {}).keys())
            for build_type in sorted(build_types):
                appconfig_dir = os.path.join('Config', build_type, 'AppConfig')
                dir_hash, hash_ok, revno = get_dir_hash(appconfig_dir)
                if not hash_ok:
                    break_build = True
                    logger.info('AppConfig hash incorrect for %s: %s' % (build_type, dir_hash))
                    print>>fp, "%s/%s, %s" % (build_type, 'AppConfig' ,revno)
                else:
                    print>>cp, "%s/%s, %s" % (build_type, 'AppConfig' ,revno)
                instrconfig_dir = os.path.join('Config', build_type, 'InstrConfig')
                dir_hash, hash_ok, revno = get_dir_hash(instrconfig_dir)
                if not hash_ok:
                    break_build = True
                    logger.info('InstrConfig hash incorrect for %s: %s' % (build_type, dir_hash))
                    print>>fp, "%s/%s, %s" % (build_type, 'InstrConfig' ,revno)
                else:
                    print>>cp, "%s/%s, %s" % (build_type, 'InstrConfig' ,revno)
    if break_build:
        raise ValueError('New config version numbers needed. Please edit updated_configs.txt')
    else:
        logger.info('All configuration hashes verified')

def update_config_hashes(project, logger):
    fnameu = 'updated_configs.txt'
    with open(fnameu, 'r') as fp:
        for line in fp:
            dirname, new_revno = line.split(',')
            config_dir = os.path.join('Config', dirname)
            new_version = [int(v) for v in new_revno.split('.')]
            ini = ConfigObj(os.path.join(config_dir, 'version.ini'))
            dir_hash = None
            old_revno = '0.0.0'
            if ini:
                if 'Version' in ini and 'dir_hash' in ini['Version']:
                    dir_hash = ini['Version']['dir_hash']
                    old_revno = ini['Version'].get('revno', '0.0.0')
            old_version = [int(v) for v in old_revno.split('.')]
            if new_version <= old_version and not project.get_property("force"):
                raise ValueError('Updated version of %s must exceed old version number: %s' % (dirname, old_revno))
            new_revno = new_revno.strip()
            if 'Version' not in ini:
                ini['Version'] = {}
            ini['Version']['revno'] = new_revno
            new_hash = get_dir_hash(config_dir)[0]
            ini['Version']['dir_hash'] = new_hash
            ini.write()
            logger.info('Updated %s to version %s' % (dirname, new_revno))

