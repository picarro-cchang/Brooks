"""
Copyright 2013 Picarro Inc

Builds the 698 patch installer.
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

Builds the 698 patch installer.
"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-b', '--revision-hbds', dest='revHBDS',
                      metavar='REV_HBDS', default=0,
                      help=('The version of the HBDS AppConfig to include in '
                            'the patcher.'))
    parser.add_option('-i', '--revision-hids', dest='revHIDS',
                      metavar='REV_HIDS', default=0,
                      help=('The version of the HIDS AppConfig to include in '
                            'the patcher.'))

    options, _ = parser.parse_args()

    consts = Constants.Constants()
    assert 'ISCC' in consts
    assert 'REPO_BASE' in consts

    hbdsDir = os.path.join('.', 'HBDS', 'AppConfig')
    hidsDir = os.path.join('.', 'HIDS', 'AppConfig')

    # Branch HBDS AppConfig repository
    if os.path.exists(hbdsDir):
        shutil.rmtree(os.path.dirname(hbdsDir))

    os.makedirs(os.path.dirname(hbdsDir))

    retCode = subprocess.call(['bzr.exe',
                               'branch',
                               '-r', str(options.revHBDS),
                               os.path.join(consts['CONFIG_BASE'],
                                            'HBDSTemplates', 'AppConfig'),
                               hbdsDir])

    if retCode != 0:
        sys.exit("Unable to branch HBDS, retCode = %s" % retCode)


    # Branch HIDS AppConfig repository
    if os.path.exists(hidsDir):
        shutil.rmtree(os.path.dirname(hidsDir))

    os.makedirs(os.path.dirname(hidsDir))

    retCode = subprocess.call(['bzr.exe',
                               'branch',
                               '-r', str(options.revHIDS),
                               os.path.join(consts['CONFIG_BASE'],
                                            'HIDSTemplates', 'AppConfig'),
                               hidsDir])

    if retCode != 0:
        sys.exit("Unable to branch HIDS, retCode = %s" % retCode)

    # Copy Host.Common.Path into the local dir
    shutil.copy2(os.path.join('..', '..', '..', 'Host', 'Common', 'Path.py'),
                 '.')

    # Build the installer
    retCode = subprocess.call([consts['ISCC'],
                               '/v9',
                               'setup_698.iss'])

    if retCode != 0:
        sys.exit("Unable to build installer, retCode = %s" % retCode)


if __name__ == '__main__':
    main()
