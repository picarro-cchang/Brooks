"""
Copyright 2012 Picarro Inc.

Driver for building the SSIM AddOn installer package.
"""

from __future__ import with_statement

import sys
import os
import pprint
import optparse
import subprocess
import re
import shutil
import os.path

import jinja2
import simplejson as json

from Host.Common import OS


SANDBOX_DIR = 'c:/temp/sandbox'

COORDINATOR_FILE_FORMAT = 'Coordinator_SSIM_%s.ini'
COORDINATOR_METADATA = 'meta.json'

if 'ProgramFiles(x86)' in os.environ:
    ISCC = os.environ['ProgramFiles(x86)']
else:
    ISCC = os.environ['ProgramFiles']
ISCC = os.path.join(ISCC, 'Inno Setup 5', 'ISCC.exe')

VERSION_METADATA = 'version.json'

REPO_BASE = 's:/repository/software'
REPO = 'trunk'

DISTRIB_BASE = 's:/CRDS/CRD Engineering/Software/G2000/Installer'


def makeInstaller(opts):
    """
    Build the SSIM AddOn installer.
    """

    # Load metadata for all of the coordinators.
    if not os.path.isfile(COORDINATOR_METADATA):
        print "%s is missing!" % COORDINATOR_METADATA
        sys.exit(1)

    meta = {}
    with open(COORDINATOR_METADATA, 'r') as metaFp:
        meta.update(json.load(metaFp))

    # Load version metadata
    if not os.path.isfile(VERSION_METADATA):
        print "%s is missing!" % VERSION_METADATA

    version = {}
    with open(VERSION_METADATA, 'r') as verFp:
        version.update(json.load(verFp))

    if opts.version:
        m = re.compile(r'(\d+)\.(\d+)\.(\d+)').search(opts.version)
        version['major'] = m.group(1)
        version['minor'] = m.group(2)
        version['revision'] = m.group(3)
        version['build'] = '0'
    else:
        # Bump the build number if we are continuing with the previous version.
        version['build'] = "%s" % (int(version['build']) + 1)

    pprint.pprint(version)

    with open(VERSION_METADATA, 'w') as verFp:
        json.dump(version, verFp)

    # Commit and push new version metadata
    retCode = subprocess.call(['bzr.exe',
                               'ci',
                               '-m',
                               'release.py version update.'])

    if retCode != 0:
        print 'Error committing new version metadata to local repo.'
        sys.exit(retCode)

    retCode = subprocess.call(['bzr.exe',
                               'push',
                               os.path.join(REPO_BASE, REPO)])

    if retCode != 0:
        print 'Error pushing new version metadata to repo.'
        sys.exit(retCode)

    _branchFromRepo(REPO)
    _generateCoordinators(REPO, meta)
    _compileInstaller(REPO, version)

    if opts.createTag:
        _tagRepository(REPO, version)
        _copyInstaller(version)

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
        subprocess.call(['bzr.exe', 'branch', os.path.join(REPO_BASE, name)])

def _generateCoordinators(name, meta):
    """
    Autogenerate all of the coordinators listed in the metadata package.
    """

    with OS.chdir(os.path.join(SANDBOX_DIR, name, 'AddOns', 'SSIM')):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(
                os.path.join('.', 'templates')))
        t = env.get_template('Coordinator_SSIM.ini.j2')

        for k in meta:
            print "Generating coordinator for '%s'." % k
            with open(COORDINATOR_FILE_FORMAT % k, 'w') as coordFp:
                coordFp.write(t.render(analyzer=meta[k]))

def _compileInstaller(name, ver):
    """
    Builds the installer and stores it in the 'Installer' subdirectory.
    """

    print 'Compiling the installer...'

    args = [ISCC,
            "/dversion=%s" % _verAsString(ver),
            "/dsandboxDir=%s" % SANDBOX_DIR,
            '/v9',
            "/O%s" % os.path.abspath(os.path.join(SANDBOX_DIR, 'Installers')),
            'setup_SSIM.iss']

    print subprocess.list2cmdline(args)

    with OS.chdir(os.path.join(SANDBOX_DIR, name, 'AddOns', 'SSIM')):
        retCode = subprocess.call(args)

        if retCode != 0:
            print 'Compile failed!'
            sys.exit(retCode)

def _verAsString(ver):
    """
    Convert a version dict into a human-readable string.
    """

    return "%(major)s.%(minor)s.%(revision)s-%(build)s" % ver

def _tagRepository(name, ver):
    """
    Tags the repository
    """

    subprocess.call(['bzr.exe', 'tag', "--directory=%s" %
                     os.path.join(REPO_BASE, name), _verAsString(ver)])

def _copyInstaller(ver):
    """
    Move the installer to its distribution location where manufacturing can
    find it.
    """

    installerCurrent = 'setup_SSIM.exe'
    installer = "setup_SSIM_%s.exe" % _verAsString(ver)

    targetDir = os.path.join(DISTRIB_BASE, 'AddOns')

    shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                    os.path.join(targetDir, 'Archive', installer))
    shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                    os.path.join(targetDir, 'Archive', installerCurrent))


def main():
    usage = """
%prog [options]

Builds a new release of the SSIM AddOn installer.
"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-v', '--version', dest='version', metavar='VERSION',
                      default=None, help=('Specify a version for this release '
                                          'and tag it as such in the '
                                          'repository.'))
    parser.add_option('--skip-tag', dest='createTag', action='store_false',
                      default=True, help=('Skip creating a tag, even if a '
                                          'version # is specified.'))

    options, _ = parser.parse_args()

    makeInstaller(options)


if __name__ == '__main__':
    main()
