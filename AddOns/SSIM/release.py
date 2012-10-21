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
import os.path

import jinja2
import simplejson as json

from Host.Common import OS


SANDBOX_DIR = 'c:/temp/sandbox'

COORDINATOR_FILE_FORMAT = 'Coordinator_SSIM_%s.ini'
COORDINATOR_METADATA = 'meta.json'

ISCC = 'c:/program files/Inno Setup 5/ISCC.exe'

VERSION_METADATA = 'version.json'

REPO_BASE = 's:/repository/software'
REPO = 'trunk'


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
        VERSION['major'] = m.group(1)
        VERSION['minor'] = m.group(2)
        VERSION['revision'] = m.group(3)
        VERSION['build'] = '0'
    else:
        # Bump the build number if we are continuing with the previous version.
        VERSION['build'] = "%s" % (int(VERSION['build']) + 1)

    pprint.pprint(VERSION)

    with open(VERSION_METADATA, 'w') as ver:
        json.dump(VERSION, ver)

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

def _compileInstaller(ver):
    """
    Builds the installer and stores it in the 'Installer' subdirectory.
    """

    print 'Compiling the installer...'

    args = [ISCC,
            "/dversion=%s" % _verAsString(ver),
            '/v9',
            "/O%s" % os.path.abspath(os.path.join(SANDBOX_DIR, 'Installers')),
            'setup_SSIM.iss']

    print subprocess.list2cmdline(args)

    retCode = subprocess.call(args)

    if retCode != 0:
        print 'Compile failed!'
        sys.exit(retCode)


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

    options, _ = parser.parse_args()

    makeInstaller(options)


if __name__ == '__main__':
    main()
