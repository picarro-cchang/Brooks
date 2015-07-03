from configobj import ConfigObj
from hashlib import sha1
import json
import os
import pprint

from pybuilder.core import after, before, use_plugin, init, task
from pybuilder.errors import BuildFailedException

import shlex
import shutil
import subprocess
import sys
import time

ISCC_WIN7 = 'c:/program files (x86)/Inno Setup 5/ISCC.exe'
INSTALLER_SCRIPTS_DIR = ('src', 'main', 'python', 'Tools', 'Release', 'InstallerScriptsWin7') 

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
# use_plugin("python.flake8")
# use_plugin("python.coverage")

default_task = "publish"

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
def handle_types(types, build_info, logger=None):
    # Types is a comma-separated string of analyzer types
    #  which may be preceeded by an "!" to indicate that those
    #  types are to be excluded.
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
        
    return types_to_build
def handle_set_version(version, version_file, logger=None):
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
        
def handle_incr_version(field, version_file, logger=None):
    # First check that the version is in the correct format
    fields = ["major", "minor", "revision", "build"]
    field = field.strip().lower()
    if field not in fields:
        raise ValueError("incr_version field should be one of %s" % ", ".join(fields))
    with open(version_file,"r") as fp:
        version = json.load(fp)
    # Increment the specified field and reset fileds of lesser significance
    reset = False
    for f in fields:
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
@init
def initialize(project, logger):
    # official removes "INTERNAL" from version number
    official = project.get_property("official", "False")
    official = official.lower() in ("yes", "true", "t", "1")
    # product specifies which installer to produce, currently supported values are g2000
    product = project.get_property("product", "g2000")
    # types is a comma separated list of installers to create or to exclude (if preceeded by !)
    #  Default is to include all types
    types = project.get_property("types", "!")
    # set_version is a string of the form major.minor.revision.build. If present, this causes the
    #  version of the installer to be set to the specified value, replacing the current value in the
    #  json version file
    
    # incr_version is one of the strings "major", "minor", "revision" or "build". If present, this 
    #  causes the version of the installer to be incremented from the value in the json
    #  version file
    
    version_file = os.path.join("versions","%s_version.json" % product)

    new_version = False
    if project.has_property("set_version"):
        if project.has_property("incr_version"):
            raise ValueError("Cannot use both set_version and incr_version")
        handle_set_version(project.get_property("set_version"), version_file, logger)
        new_version = True
        
    if project.has_property("incr_version"):
        handle_incr_version(project.get_property("incr_version"), version_file, logger)
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
    
    types_file = os.path.join("versions","%s_types.json" % product)
    with open(types_file,"r") as inp:
        config_info = json.load(inp)
    types_to_build = handle_types(types, config_info['buildTypes'], logger)
        
    project.set_property('types_to_build', types_to_build)
    project.set_property('config_info', config_info['buildTypes'])
        
    

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
@task
def make_installers(project, logger):
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
            process = subprocess.Popen(args,
                                       stdout=output_file,
                                       stderr=output_file,
                                       shell=False)
            return_code = process.wait()
            if return_code != 0:
                raise BuildFailedException("Error while making installer for %s" % installer_type)
                sys.exit(retCode)
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
@task
def check_config_hashes(project, logger):
    fnamec = 'current_configs.txt'
    fnameu = 'updated_configs.txt'
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
@task
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
            if new_version <= old_version:
                raise ValueError('Updated version of %s must exceed old version number: %s' % (dirname, old_revno))
            new_revno = new_revno.strip()
            if 'Version' not in ini:
                ini['Version'] = {}
            ini['Version']['revno'] = new_revno
            new_hash = get_dir_hash(config_dir)[0]
            ini['Version']['dir_hash'] = new_hash
            ini.write()
            logger.info('Updated %s to version %s' % (dirname, new_revno))
