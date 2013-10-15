"""
Copyright 2012-2013 Picarro Inc.

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
import stat

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

REPO_BASE = 'https://github.com/picarro/host.git'

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

# For dry-run testing
TEST_MFG_DISTRIB_BASE = 'c:/temp/tools/release/mfg_distrib_base'
TEST_DISTRIB_BASE = 'c:/temp/tools/release/distrib_base'

# Where new releases are put for testing.
STAGING_MFG_DISTRIB_BASE = 'r:/G2000_HostSoftwareInstallers_Staging'
STAGING_DISTRIB_BASE = 's:/CRDS/CRD Engineering/Software/G2000/Installer_Staging'


def makeExe(opts):
    """
    Make a HostExe release from a clean checkout.
    """

    pprint.pprint(opts)

    productConfigs = "%s.json" % opts.product
    versionConfig = "%s_version.json" % opts.product

    if not os.path.isfile(productConfigs):
        print "%s is missing!" % productConfigs
        sys.exit(1)

    if not os.path.isfile(versionConfig):
        print "%s is missing!" % versionConfig
        sys.exit(1)

    with open(productConfigs, 'r') as prods:
        CONFIGS.update(json.load(prods))

    pprint.pprint(CONFIGS)

    if opts.dryRun:
        targetMfgDistribBase = TEST_MFG_DISTRIB_BASE
        targetDistribBase = TEST_DISTRIB_BASE

        if os.path.isdir(targetMfgDistribBase):
            shutil.rmtree(targetMfgDistribBase)

        if os.path.isdir(targetDistribBase):
            shutil.rmtree(targetDistribBase)

        os.makedirs(targetMfgDistribBase)
        os.makedirs(targetDistribBase)

        for c in CONFIGS:
            os.makedirs(os.path.join(targetDistribBase, c, 'Archive'))
            os.makedirs(os.path.join(targetDistribBase, c, 'Current'))

    else:
        targetMfgDistribBase = MFG_DISTRIB_BASE
        targetDistribBase = DISTRIB_BASE

    if opts.makeOfficial:
        _promoteStagedRelease(opts.officialTypes, targetMfgDistribBase,
                              targetDistribBase, versionConfig, opts.product)
        return


    with open(versionConfig, 'r') as ver:
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

    with open(versionConfig, 'w') as ver:
        json.dump(VERSION, ver)

    # Commit and push new version number
    retCode = subprocess.call(['git.exe',
                               'add',
                               versionConfig])

    if retCode != 0:
        print 'Error staging new version metadata in local repo.'
        sys.exit(1)

    retCode = subprocess.call(['git.exe',
                               'commit',
                               '-m',
                               "release.py version update (%s)." % opts.product])

    if retCode != 0:
        print 'Error committing new version metadata to local repo.'
        sys.exit(1)

    retCode = subprocess.call(['git.exe',
                               'push'])

    if retCode != 0:
        print 'Error pushing new version metadata to repo.'

    _branchFromRepo(opts.branch)
    _generateReleaseVersion(opts.product, VERSION)
    _buildExes()

    # XXX This is likely superfluous once the configuration files have
    # been merged into the main repository.
    _makeLocalConfig()

    if opts.createInstallers:
        _compileInstallers(opts.product, VERSION)

    if opts.createTag:
        _tagRepository(opts.product, VERSION)

        # XXX These should be removed when we finish merging the
        # configuration file directories into the repository.
        _tagCommonConfig(opts.product, VERSION)
        _tagAppInstrConfigs(opts.product, VERSION)

    if opts.createInstallers:
        # Copy both HostExe and AnalyzerServerExe for non-installer upgrades.
        _copyBuildAndInstallers(versionConfig, opts.product, VERSION)

def _promoteStagedRelease(types=None, mfgDistribBase=None, distribBase=None,
                          versionConfig=None, product=None):
    """
    Move the existing staged release to an official directory.
    """

    assert versionConfig

    stagingVer = os.path.join(STAGING_DISTRIB_BASE, versionConfig)

    if not os.path.isfile(stagingVer):
        print "Staging %s is missing!" % versionConfig
        sys.exit(1)

    ver = {}
    with open(stagingVer, 'r') as version:
        ver.update(json.load(version))

    negate = False
    typesList = None

    if types is not None:
        if types[0] == '!':
            negate = True
            typesList = types[1:].split(',')
        else:
            typesList = types.split(',')

    for c in CONFIGS:
        doCopy = True

        if typesList is not None:
            if negate:
                doCopy = c not in typesList
            else:
                doCopy = c in typesList

        if not doCopy:
            continue

        installer = "setup_%s_%s_%s.exe" % (c, CONFIGS[c],
                                            _verAsString(product, ver))
        installerCurrent = "setup_%s_%s.exe" % (c, CONFIGS[c])
        targetDir = os.path.join(distribBase, c)

        shutil.copyfile(os.path.join(STAGING_DISTRIB_BASE, c, installer),
                        os.path.join(targetDir, 'Archive', installer))
        shutil.copyfile(os.path.join(STAGING_DISTRIB_BASE, c, installer),
                        os.path.join(targetDir, 'Current', installerCurrent))

def _copyBuildAndInstallers(versionConfig, product, ver):
    """
    Move the installers and the two compiled exe directories to their
    staging location so other people can find them.
    """

    # Clean the previously staged version.
    try:
        shutil.rmtree(STAGING_MFG_DISTRIB_BASE)
        shutil.rmtree(STAGING_DISTRIB_BASE)
    except OSError:
        # Okay if these directories don't already exist.
        pass

    # HostExe
    hostExeDir = os.path.join(STAGING_MFG_DISTRIB_BASE, 'HostExe')
    assert not os.path.isdir(hostExeDir)
    os.makedirs(hostExeDir)

    dir_util.copy_tree(os.path.join(SANDBOX_DIR, 'host', 'Host', 'dist'),
                       hostExeDir)

    # AnalyzerServerExe
    analyzerServerExe = os.path.join(STAGING_MFG_DISTRIB_BASE,
                                     'AnalyzerServerExe')
    assert not os.path.isdir(analyzerServerExe)
    os.makedirs(analyzerServerExe)

    dir_util.copy_tree(os.path.join(SANDBOX_DIR, 'host', 'MobileKit', 'dist'),
                       analyzerServerExe)

    # Copy the individual installers and update the shortcuts that are
    # used by manufacturing.
    for c in CONFIGS:
        installer = "setup_%s_%s_%s.exe" % (c, CONFIGS[c],
                                            _verAsString(product, ver))
        targetDir = os.path.join(STAGING_DISTRIB_BASE, c)
        os.makedirs(targetDir)

        shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                        os.path.join(targetDir, installer))

    shutil.copyfile(versionConfig,
                    os.path.join(STAGING_DISTRIB_BASE, versionConfig))

def _branchFromRepo(branch):
    """
    Branch the named repository into the sandbox.
    """

    if os.path.exists(SANDBOX_DIR):
        print "Removing previous sandbox at '%s'." % SANDBOX_DIR

        # First fix up the permissions on some pesky .idx and .pack files
        # If they exist, they are read-only and shutil.rmtree() will bail
        packFolder = os.path.join(SANDBOX_DIR, 'host', '.git', 'objects', 'pack')

        if os.path.isdir(packFolder):
            packFiles = os.listdir(packFolder)

            for f in packFiles:
                # fix up permissions
                print "chmod(%s)" % os.path.join(packFolder, f)
                os.chmod(os.path.join(packFolder, f),
                         stat.S_IREAD | stat.S_IWRITE)

        # now remove the sandbox tree
        shutil.rmtree(SANDBOX_DIR)

    os.makedirs(SANDBOX_DIR)
    os.makedirs(os.path.join(SANDBOX_DIR, 'Installers'))

    with OS.chdir(SANDBOX_DIR):
        retCode = subprocess.call(['git.exe',
                                   'clone',
                                   REPO_BASE])

        if retCode != 0:
            print "Error cloning '%s'" % REPO_BASE
            sys.exit(retCode)

        with OS.chdir(os.path.join(SANDBOX_DIR, 'host')):
            retCode = subprocess.call(['git.exe',
                                       'checkout',
                                       branch])

            if retCode != 0:
                print "Error checking out 'origin/%s'." % branch
                sys.exit(retCode)

def _generateReleaseVersion(product, ver):
    """
    Create the version metadata used by the executables and update the
    pretty version string.
    """

    with OS.chdir(os.path.join(SANDBOX_DIR, 'host')):
        with open(os.path.join('Host', 'Common',
                               'release_version.py'), 'w') as fp:
            fp.writelines(
                ["# autogenerated by release.py, %s\n" % time.asctime(),
                 "\n",
                 "def versionString():\n",
                 "    return '%s'\n" % _verAsString(product, ver)])

def _buildExes():
    """
    Build host executables.
    """

    buildEnv = os.environ.update({'PYTHONPATH' : "%s;%s" %
                                  (os.path.join(SANDBOX_DIR, 'host'),
                                   os.path.join(SANDBOX_DIR, 'host', 'Firmware')
                                   )})

    # MobileKit must be built first since the HostExe build will copy
    with OS.chdir(os.path.join(SANDBOX_DIR, 'host', 'MobileKit')):
        retCode = subprocess.call(['python.exe', 'setup.py', 'py2exe'],
                                  env=buildEnv)

        if retCode != 0:
            print 'Error building MobileKit.'
            sys.exit(retCode)

    with OS.chdir(os.path.join(SANDBOX_DIR, 'host', 'Host')):
        retCode = subprocess.call(['python.exe', 'PicarroExeSetup.py',
                                   'py2exe'],
                                   env=buildEnv)

        if retCode != 0:
            print 'Error building Host.'
            sys.exit(retCode)

def _tagRepository(product, ver):
    """
    Tags the repository
    """

    retCode = subprocess.call(['git.exe',
                               'tag',
                               '-a',
                               _verAsString(product, ver),
                               '-m',
                               "Version %s" % _verAsString(product, ver)])

    if retCode != 0:
        print 'Error tagging repository'
        sys.exit(retCode)

    retCode = subprocess.call(['git.exe',
                               'push',
                               'origin',
                               _verAsString(product, ver)])

    if retCode != 0:
        print 'Error pushing tag to repository'
        sys.exit(retCode)

def _tagCommonConfig(product, ver):
    retCode = subprocess.call(['bzr.exe', 'tag', "--directory=%s" %
                               COMMON_CONFIG, _verAsString(product, ver)])

    if retCode != 0:
        print "Error tagging CommonConfig as '%s'." % _verAsString(product, ver)
        sys.exit(retCode)

def _tagAppInstrConfigs(product, ver):
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

            retCode = subprocess.call(['bzr.exe', 'tag',
                                       "--directory=%s" %
                                       os.path.join(configBase, 'AppConfig'),
                                       _verAsString(product, ver)])

            if retCode != 0:
                print "Error tagging '%s' AppConfig as '%s'." % \
                    (c, _verAsString(product, ver))
                sys.exit(retCode)

            retCode = subprocess.call(['bzr.exe', 'tag',
                                       "--directory=%s" %
                                       os.path.join(configBase, 'InstrConfig'),
                                       _verAsString(product, ver)])

            if retCode != 0:
                print "Error tagging '%s' InstrConfig as '%s'." % \
                    (c, _verAsString(product, ver))
                sys.exit(retCode)

def _makeLocalConfig():
    """
    Adds physical copies of all of the configuration file repositories to the
    sandbox and generates the required version.ini file.
    """

    with OS.chdir(SANDBOX_DIR):
        retCode = subprocess.call(['bzr.exe', 'branch', COMMON_CONFIG])

        if retCode != 0:
            print 'Error cloning CommonConfig.'
            sys.exit(retCode)

        with open(os.path.join('CommonConfig', 'version.ini'), 'w') as fp:
            retCode = subprocess.call(['bzr.exe', 'version-info',
                                       'CommonConfig', '--custom',
                                       "--template=%s" % VERSION_TEMPLATE],
                                       stdout=fp)

            if retCode != 0:
                print 'Error generating version.ini for CommonConfig.'
                sys.exit(retCode)

        for c in CONFIGS:
            print "Getting configs for '%s'" % c
            os.mkdir(c)
            with OS.chdir(c):
                retCode = subprocess.call(['bzr.exe', 'branch',
                                           os.path.join(CONFIG_BASE,
                                                        "%sTemplates" % c,
                                                        'AppConfig'),
                                                        'AppConfig'])
                if retCode != 0:
                    print "Error cloning '%s' AppConfig" % c
                    sys.exit(retCode)

                with open(os.path.join('AppConfig', 'version.ini'), 'w') as fp:
                    retCode = subprocess.call(['bzr.exe', 'version-info',
                                               'AppConfig', '--custom',
                                               "--template=%s" %
                                               VERSION_TEMPLATE],
                                               stdout=fp)

                    if retCode != 0:
                        print "Error generating '%s' AppConfig version.ini" % \
                            c
                        sys.exit(retCode)

                retCode = subprocess.call(['bzr.exe', 'branch',
                                           os.path.join(CONFIG_BASE,
                                                        "%sTemplates" % c,
                                                        'InstrConfig'),
                                                        'InstrConfig'])
                if retCode != 0:
                    print "Error cloning '%s' InstrConfig" % c
                    sys.exit(retCode)

                with open(os.path.join('InstrConfig',
                                       'version.ini'), 'w') as fp:
                    retCode = subprocess.call(['bzr.exe', 'version-info',
                                               'InstrConfig', '--custom',
                                               "--template=%s" %
                                               VERSION_TEMPLATE],
                                               stdout=fp)

                    if retCode != 0:
                        print "Error generating '%s' InstrConfig version.ini" % \
                            c
                        sys.exit(retCode)

def _compileInstallers(product, ver):
    """
    Compiles the installers for each variant. The original runCompInstallers.bat
    used Compil32.exe, but if we use ISCC.exe we should be able to bypass the
    requirement that each .iss file have its version string updated manually.
    """

    for c in CONFIGS:
        print "Compiling '%s'..." % c

        args = [ISCC, "/dinstallerType=%s" % c,
                "/dhostVersion=%s" % _verAsString(product, ver),
                "/dresourceDir=%s" % RESOURCE_DIR,
                "/dsandboxDir=%s" % SANDBOX_DIR,
                "/dcommonName=%s" % CONFIGS[c],
                "/v9",
                "/O%s" % os.path.abspath(os.path.join(SANDBOX_DIR,
                                                        'Installers')),
                "InstallerScripts\\setup_%s_%s.iss" % (c, CONFIGS[c])]

        print subprocess.list2cmdline(args)

        retCode = subprocess.call(args)

        if retCode != 0:
            print "Error building '%s' installer." % c
            sys.exit(retCode)

def _verAsString(product, ver):
    """
    Convert a version dict into a human-readable string.
    """

    number = "%(major)s.%(minor)s.%(revision)s-%(build)s" % ver
    return "%s-%s" % (product, number)

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
    parser.add_option('--make-official', dest='makeOfficial',
                      action='store_true', default=False,
                      help=('Promote the current release in staging to the '
                            'official distribution channels.'))
    parser.add_option('--types', dest='officialTypes',
                      default=None, help=('Comma-delimited list of analyzer '
                                          'types that should be moved from '
                                          'staging to the official release '
                                          'area. If the list starts with a "!" '
                                          'every type but those in the list '
                                          'will be moved.'))
    parser.add_option('--dry-run', dest='dryRun', default=False,
                      action='store_true',
                      help=('Only works with --make-official. Tests the move '
                            'to staging by using a temporary directory as the '
                            'target.'))
    parser.add_option('--product', dest='product', metavar='PRODUCT',
                      default=None, help=('The product line to generate the '
                                          'release for.'))
    parser.add_option('--branch', dest='branch', metavar='BRANCH',
                      default='master', help=('The remote branch from which the '
                                              'release is built.'))

    options, _ = parser.parse_args()

    makeExe(options)


if __name__ == '__main__':
    main()
