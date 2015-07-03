from configobj import ConfigObj
from hashlib import sha1
import os

from pybuilder.core import after, before, use_plugin, init, task
from pybuilder.errors import BuildFailedException

import shlex
import subprocess
import sys

curdir = os.path.dirname(os.path.abspath(__file__))
if curdir not in sys.path:
    sys.path.insert(0,curdir)

from BuildG2000 import BuildG2000

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

@init
def initialize(project, logger):
    BuildClasses = dict(g2000 = BuildG2000)
    # official removes "INTERNAL" from version number
    official = project.get_property("official", "False")
    official = official.lower() in ("yes", "true", "t", "1")
    project.set_property("official", official)
    # product specifies which installer to produce, currently supported values are g2000
    product = project.get_property("product", "g2000").strip().lower()
    project.set_property("product", product)
    builder = BuildClasses[product.lower()](project, logger)
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
def publish(project, logger):
    builder = project.get_property("builder")
    builder.publish()

@task
def make_installers(project, logger):
    builder = project.get_property("builder")
    builder.make_installers()


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
