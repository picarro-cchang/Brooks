"""
Copyright 2013 Picarro Inc

Builds the 20120925 patch installer.

Installer is for CFFDS. Should also be run for CFGDS, which does not have its own installer.
"""

import os
import sys
import shutil
import subprocess
import optparse
import os.path

from Tools import Constants


def main():
    usage = """
%prog [options]

Builds the 20130925 patch installer.
"""

    # CFFDS AppConfig on 20130925 is version 22
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-b', '--revision-cffds', dest='revCFFDS',
                      metavar='REV_CFFDS', default=22,
                      help=('The version of the CFFDS AppConfig to include in '
                            'the patcher. Default=22, the version as of 20130925.'))

    options, _ = parser.parse_args()

    consts = Constants.Constants()
    assert 'ISCC' in consts
    assert 'REPO_BASE' in consts

    # create the .\CFFDS\AppConfig folder to hold files from bzr
    cffdsDir = os.path.join('.', 'CFFDS', 'AppConfig')

    print "Building 20130925 patch installer using CFFDS AppConfig version %d" % options.revCFFDS

    # Branch CFFDS AppConfig repository
    if os.path.exists(cffdsDir):
        shutil.rmtree(os.path.dirname(cffdsDir))

    os.makedirs(os.path.dirname(cffdsDir))

    retCode = subprocess.call(['bzr.exe',
                               'branch',
                               '-r', str(options.revCFFDS),
                               os.path.join(consts['CONFIG_BASE'],
                                            'CFFDSTemplates', 'AppConfig'),
                               cffdsDir])

    if retCode != 0:
        sys.exit("Unable to branch CFFDS, retCode = %s" % retCode)

    # Copy Host.Common.Path into the local dir
    #shutil.copy2(os.path.join('..', '..', '..', 'Host', 'Common', 'Path.py'), '.')

    # Build the installer
    retCode = subprocess.call([consts['ISCC'],
                               '/v9',
                               'setup_20130925.iss'])

    if retCode != 0:
        sys.exit("Unable to build installer, retCode = %s" % retCode)


if __name__ == '__main__':
    main()
