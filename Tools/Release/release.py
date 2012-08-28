"""
Copyright 2012 Picarro Inc.

Replacement for makeExe.bat.
"""

from __future__ import with_statement

import os
import sys
import shutil
import subprocess
import pprint
import re
import time
import os.path

from distutils import dir_util
from optparse import OptionParser

#pylint: disable=F0401
try:
    import simplejson as json
except ImportError:
    import json
#pylint: enable=F0401

from Host.Common import OS


# Pull these out into a configuration file.
SANDBOX_DIR = 'c:/temp/sandbox'

REPO_BASE = 's:/repository/software'
REPO = 'trunk'

ISCC = 'c:/program files/Inno Setup 5/ISCC.exe'

RESOURCE_DIR = ('s:/CRDS/SoftwareReleases/G2000Projects/G2000_PrepareInstaller/'
                'Resources')

CONFIGS = {}
CONFIG_BASE = 's:/CrdsRepositoryNew/trunk/G2000/Config'
COMMON_CONFIG = os.path.join(CONFIG_BASE, 'CommonConfig')

VERSION = {}
VERSION_TEMPLATE = ("[Version]\\nrevno = {revno}\\ndate = {date}\\n"
                    "revision_id = {revision_id}")

# Where Manufacturing looks for installers and
# HostExe/AnalyzerServerExe upgrades.
MFG_DISTRIB_BASE = 'r:/G2000_HostSoftwareInstallers'
DISTRIB_BASE = 's:/CRDS/CRD Engineering/Software/G2000/Installer'


def makeExe(opts):
    """
    Make a HostExe release from a clean checkout.
    """

    pprint.pprint(opts)

    # Load configuration mapping metadata
    if not os.path.isfile('products.json'):
        print 'products.json is missing!'
        sys.exit(1)

    with open('products.json', 'r') as prods:
        CONFIGS.update(json.load(prods))

    pprint.pprint(CONFIGS)

    # Load version metadata
    if not os.path.isfile('version.json'):
        print 'version.json is missing!'
        sys.exit(1)

    with open('version.json', 'r') as ver:
        VERSION.update(json.load(ver))

    if opts.version:
        m = re.compile(r'(\d+)\.(\d+)\.(\d+)').search(opts.version)
        VERSION['major'] = m.group(1)
        VERSION['minor'] = m.group(2)
        VERSION['revision'] = m.group(3)
        VERSION['build'] = '0'
    else:
        # Bump the build number if we are continuing with the previous version.
        VERSION['build'] = "%s" % (int(VERSION['build']) + 1)

    pprint.pprint(VERSION)

    with open('version.json', 'w') as ver:
        json.dump(VERSION, ver)

    # Commit and push new version number
    bzrProc = subprocess.Popen(['bzr.exe', 'ci', '-m',
                                'release.py version update.'])
    bzrProc.wait()

    if bzrProc.returncode != 0:
        print 'Error committing new version metadata to local repo.'
        sys.exit(1)

    bzrProc = subprocess.Popen(['bzr.exe', 'push', os.path.join(REPO_BASE,
                                                                REPO)])
    bzrProc.wait()

    if bzrProc.returncode != 0:
        print 'Error pushing new version metadata to repo.'
        sys.exit(1)

    _branchFromRepo(REPO)
    _generateReleaseVersion(REPO, VERSION)
    _buildExes(REPO)

    # XXX This is likely superfluous once the configuration files have
    # been merged into the main repository.
    _makeLocalConfig()

    if opts.createInstallers:
        _compileInstallers(VERSION)

    if opts.createTag:
        _tagRepository(REPO, VERSION)

        # XXX These should be removed when we finish merging the
        # configuration file directories into the repository.
        _tagCommonConfig(VERSION)
        _tagAppInstrConfigs(VERSION)

    # Copy both HostExe and AnalyzerServerExe for non-installer upgrades.
    _copyBuildAndInstallers(REPO, VERSION)

def _copyBuildAndInstallers(name, ver):
    """
    Move the installers and the two compiled exe directories to their
    distribution location so other people can find them.
    """

    # HostExe
    hostExeDir = os.path.join(MFG_DISTRIB_BASE, 'HostExe', _verAsString(ver))
    assert not os.path.isdir(hostExeDir)
    os.mkdir(hostExeDir)

    dir_util.copy_tree(os.path.join(SANDBOX_DIR, name, 'Host', 'dist'),
                       hostExeDir)

    # AnalyzerServerExe
    analyzerServerExe = os.path.join(MFG_DISTRIB_BASE, 'AnalyzerServerExe',
                                     _verAsString(ver))
    assert not os.path.isdir(analyzerServerExe)
    os.mkdir(analyzerServerExe)

    dir_util.copy_tree(os.path.join(SANDBOX_DIR, name, 'MobileKit', 'dist'),
                       analyzerServerExe)

    # Copy the individual installers and update the shortcuts that are
    # used by manufacturing.
    for c in CONFIGS:
        installer = "setup_%s_%s_%s.exe" % (c, CONFIGS[c], _verAsString(ver))
        installerCurrent = "setup_%s_%s.exe" % (c, CONFIGS[c])
        targetDir = os.path.join(DISTRIB_BASE, c)

        shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                        os.path.join(targetDir, 'Archive', installer))
        shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                        os.path.join(targetDir, 'Current', installerCurrent))

def _branchFromRepo(name):
    """
    Branch the named repository into the sandbox.
    """

    if os.path.exists(SANDBOX_DIR):
        print "Removing previous sandbox at '%s'." % SANDBOX_DIR
        shutil.rmtree(SANDBOX_DIR)

    os.makedirs(SANDBOX_DIR)
    os.makedirs(os.path.join(SANDBOX_DIR, 'Installers'))

    with OS.chdir(SANDBOX_DIR):
        subprocess.Popen(['bzr.exe', 'branch',
                          os.path.join(REPO_BASE, name)]).wait()

def _generateReleaseVersion(name, ver):
    """
    Create the version metadata used by the executables and update the
    pretty version string.
    """

    with OS.chdir(os.path.join(SANDBOX_DIR, name)):
        with open(os.path.join('Host', 'Common',
                               'release_version.py'), 'w') as fp:
            fp.writelines(
                ["# autogenerated by release.py, %s\n" % time.asctime(),
                 "\n",
                 "def versionString():\n",
                 "    return '%s'\n" % _verAsString(ver)])

def _buildExes(name):
    """
    Build host executables.
    """

    # MobileKit must be built first since the HostExe build will copy
    with OS.chdir(os.path.join(SANDBOX_DIR, name, 'MobileKit')):
        subprocess.Popen(['python.exe', 'setup.py', 'py2exe'],
                         env=os.environ.update({'PYTHONPATH' : "%s;%s" %
                          (os.path.join(SANDBOX_DIR, 'trunk'),
                           os.path.join(SANDBOX_DIR, 'trunk',
                                        'Firmware'))})).wait()

    with OS.chdir(os.path.join(SANDBOX_DIR, name, 'Host')):
        subprocess.Popen(['python.exe', 'PicarroExeSetup.py', 'py2exe'],
                         env=os.environ.update({'PYTHONPATH' : "%s;%s" %
                          (os.path.join(SANDBOX_DIR, 'trunk'),
                           os.path.join(SANDBOX_DIR, 'trunk',
                                        'Firmware'))})).wait()

def _tagRepository(name, ver):
    """
    Tags the repository
    """

    subprocess.Popen(['bzr.exe', 'tag', "--directory=%s" %
                      os.path.join(REPO_BASE, name), _verAsString(ver)]).wait()

def _tagCommonConfig(ver):
    subprocess.Popen(['bzr.exe', 'tag', "--directory=%s" % COMMON_CONFIG,
                      _verAsString(ver)]).wait()

def _tagAppInstrConfigs(ver):
    """
    Tag the AppConfig and InstrConfig repos for each variant. Unlike
    tagOnly.bat, on which this routine is based, we will _not_ also
    tag the config branches in the sandbox. The branches in the
    sandbox will have common ancestor revisions with the master repos
    on S:. If you need the revision of a tag look at the master repo
    on S:. Eventually this will all be moot once we merge the
    configurations into the main repo.
    """

    with OS.chdir(SANDBOX_DIR):
        for c in CONFIGS:
            configBase = os.path.join(CONFIG_BASE, "%sTemplates" % c)

            subprocess.Popen(['bzr.exe', 'tag',
                              "--directory=%s" %
                              os.path.join(configBase, 'AppConfig'),
                              _verAsString(ver)]).wait()
            subprocess.Popen(['bzr.exe', 'tag',
                              "--directory=%s" %
                              os.path.join(configBase, 'InstrConfig'),
                              _verAsString(ver)]).wait()

def _makeLocalConfig():
    """
    Adds physical copies of all of the configuration file repositories to the
    sandbox and generates the required version.ini file.
    """

    with OS.chdir(SANDBOX_DIR):
        subprocess.Popen(['bzr.exe', 'branch', COMMON_CONFIG]).wait()

        with open(os.path.join('CommonConfig', 'version.ini'), 'w') as fp:
            subprocess.Popen(['bzr.exe', 'version-info', 'CommonConfig',
                              '--custom',
                              "--template=%s" % VERSION_TEMPLATE],
                             stdout=fp).wait()

        for c in CONFIGS:
            print "Getting configs for '%s'" % c
            os.mkdir(c)
            with OS.chdir(c):
                subprocess.Popen(['bzr.exe', 'branch',
                                  os.path.join(CONFIG_BASE, "%sTemplates" % c,
                                               'AppConfig'),
                                  'AppConfig']).wait()
                with open(os.path.join('AppConfig', 'version.ini'), 'w') as fp:
                    subprocess.Popen(['bzr.exe', 'version-info', 'AppConfig',
                                      '--custom',
                                      "--template=%s" % VERSION_TEMPLATE],
                                     stdout=fp)

                subprocess.Popen(['bzr.exe', 'branch',
                                  os.path.join(CONFIG_BASE, "%sTemplates" % c,
                                               'InstrConfig'),
                                  'InstrConfig']).wait()
                with open(os.path.join('InstrConfig',
                                       'version.ini'), 'w') as fp:
                    subprocess.Popen(['bzr.exe', 'version-info', 'InstrConfig',
                                      '--custom',
                                      "--template=%s" % VERSION_TEMPLATE],
                                     stdout=fp).wait()

def _compileInstallers(ver):
    """
    Compiles the installers for each variant. The original runCompInstallers.bat
    used Compil32.exe, but if we use ISCC.exe we should be able to bypass the
    requirement that each .iss file have its version string updated manually.
    """

    for c in CONFIGS:
        print "Compiling '%s'..." % c

        args = [ISCC, "/dinstallerType=%s" % c,
                "/dhostVersion=%s" % _verAsString(ver),
                "/dresourceDir=%s" % RESOURCE_DIR,
                "/dsandboxDir=%s" % SANDBOX_DIR,
                "/dcommonName=%s" % CONFIGS[c],
                "/v9",
                "/O%s" % os.path.abspath(os.path.join(SANDBOX_DIR,
                                                        'Installers')),
                "InstallerScripts\\setup_%s_%s.iss" % (c, CONFIGS[c])]

        print subprocess.list2cmdline(args)

        isccProc = subprocess.Popen(args)
        isccProc.wait()

        if isccProc.returncode != 0:
            sys.exit(isccProc.returncode)

def _verAsString(ver):
    """
    Convert a version dict into a human-readable string.
    """

    return "%(major)s.%(minor)s.%(revision)s-%(build)s" % ver

def main():
    usage = """
%prog [options]

Builds a new release of HostExe, AnalyzerServerExe and all installers.
"""

    parser = OptionParser(usage=usage)
    parser.add_option('-v', '--version', dest='version', metavar='VERSION',
                      default=None, help=('Specify a version for this release '
                                          'and tag it as such in the '
                                          'repository.'))
    parser.add_option('--skip-tag', dest='createTag', action='store_false',
                      default=True, help=('Skip creating a tag, even if a '
                                          'version # is specified.'))
    parser.add_option('--skip-installers', dest='createInstallers',
                      action='store_false', default=True,
                      help=('Skip creating installers.'))

    options, _ = parser.parse_args()

    makeExe(options)


if __name__ == '__main__':
    main()
