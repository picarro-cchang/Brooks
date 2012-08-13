# Copyright 2012 Picarro Inc.

"""
Replacement for makeExe.bat.
"""

from __future__ import with_statement

import os
import sys
import shutil
import subprocess
import os.path

from optparse import OptionParser

from Host.Common import OS


# Pull these out into a configuration file.
SANDBOX_DIR = 'c:/temp/sandbox'

REPO_BASE = 's:/repository/software'
REPO = 'trunk'

ISCC = 'c:/program files/Inno Setup 5/ISCC.exe'

RESOURCE_DIR = ('s:/CRDS/SoftwareReleases/G2000Projects/G2000_PrepareInstaller/'
                'Resources')

# XXX These can be removed when the configuration file directories are
# merged into the main repository. ASSUMES v1.4 and beyond.
CONFIGS = ['4SpeciesFlight_CFKBDS', '4Species_CFKADS', 'AEDS', 'BFADS', 'CFADS',
           'CFDDS', 'CFEDS', 'CFIDS', 'CFJDS', 'CHADS', 'CKADS', 'FCDS', 'FDDS',
           'Flux', 'HIDS', 'iCO2', 'iH2O', 'MADS', 'SuperFlux']
CONFIG_BASE = 's:/CrdsRepositoryNew/trunk/G2000/Config'
COMMON_CONFIG = os.path.join(CONFIG_BASE, 'CommonConfig')
VERSION_TEMPLATE = ("[Version]\\nrevno = {revno}\\ndate = {date}\\n"
                    "revision_id = {revision_id}")


def makeExe(opts):
    """
    Make a HostExe release from a clean checkout.
    """
    _branchFromRepo(REPO)
    _generateRepoVersion(REPO)
    _buildExes(REPO)

    # XXX This is likely superfluous once the configuration files have
    # been merged into the main repository.
    _makeLocalConfig()

    # This deviates from the original steps in that it is usually done
    # after tagging the repositories, but I would prefer to save the
    # tagging until after we are sure the installers build correctly.
    if opts.version and opts.createInstallers:
        _compileInstallers(opts.version)

    # if opts.version and opts.createTag:
    #     _tagRepository(REPO, opts.version)

    #     # XXX These should be removed when we finish merging the
    #     # configuration file directories into the repository.
    #     _tagCommonConfig(opts.version)
    #     _tagAppInstrConfigs(opts.version)

def _branchFromRepo(name):
    """
    Branch the named repository into the sandbox.
    """

    if os.path.exists(SANDBOX_DIR):
        print "Removing previous sandbox at '%s'." % SANDBOX_DIR
        shutil.rmtree(SANDBOX_DIR)

    os.makedirs(SANDBOX_DIR)

    with OS.chdir(SANDBOX_DIR):
        subprocess.Popen(['bzr.exe', 'branch',
                          os.path.join(REPO_BASE, name)]).wait()

def _generateRepoVersion(name):
    """
    Create the version metadata used by the executables.
    """

    with OS.chdir(os.path.join(SANDBOX_DIR, name)):
        with open('repoBzrVer.py', 'w') as fp:
            subprocess.Popen(['bzr.exe', 'version-info', '--python'],
                             stdout=fp).wait()

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
                      os.path.join(REPO_BASE, name), ver]).wait()

def _tagCommonConfig(ver):
    subprocess.Popen(['bzr.exe', 'tag', "--directory=%s" % COMMON_CONFIG,
                      ver]).wait()

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
                              ver]).wait()
            subprocess.Popen(['bzr.exe', 'tag',
                              "--directory=%s" %
                              os.path.join(configBase, 'InstrConfig'),
                              ver]).wait()

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
                with open(os.path.join('InstrConfig', 'version.ini'), 'w') as fp:
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
        # Preprocess config name string
        print "Compiling '%s'..." % c
        p = subprocess.Popen([ISCC, "/dinstallerType=%s" % c,
                              "/dhostVersion=%s" % ver,
                              "/dresourceDir=%s" % RESOURCE_DIR,
                              "/dsandboxDir=%s" % SANDBOX_DIR,
                              "setup_%s.iss" % c])
        p.wait()

        if p.returncode != 0:
            sys.exit(p.returncode)

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
