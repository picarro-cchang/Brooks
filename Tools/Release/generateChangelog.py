"""
Copyright 2012 Picarro Inc.

Generates a changelog between two tags in the repositories.
"""

from __future__ import with_statement

import os
import sys
import subprocess
import optparse
import os.path

#pylint: disable=F0401
try:
    import simplejson as json
except ImportError:
    import json
#pylint: enable=F0401


REPO_BASE = 's:/repository/software'
REPO = 'trunk'

CONFIG_BASE = 's:/CrdsRepositoryNew/trunk/G2000/Config'

PRODUCTS = 'products.json'


def _generateChangelogGit(logFp, startTag, endTag):
    """
    Generate verbose diffs for all of the changes between the specified tags.
    Assumes that this script is being run of out a git working copy.
    """

    logFp.write("\ngit logs for: %s\n" % os.getcwd())
    logFp.flush()
    subprocess.call(['git.exe',
                     'log',
                     '--name-status',
                     "%s..%s" % (startTag, endTag)],
                     stdout=logFp)
    logFp.write("\n")
    logFp.flush()


def _generateChangelogBzr(logFp, repositoryNames, startTag, endTag):
    """
    Generate verbose diffs for all of the changes for all of the
    specified bzr repositories we know about between the specified
    tags.
    """

    for repo in repositoryNames:
        logFp.write("\nbzr logs for: %s\n" % repo)
        logFp.flush()
        print subprocess.list2cmdline(['bzr.exe',
                       'log',
                       '-v',
                       "-r%s..%s" % (startTag, endTag),
                       '--include-merges',
                       os.path.abspath(repo)])
        subprocess.call(['bzr.exe',
                     'log',
                     '-v',
                     "-r%s..%s" % (startTag, endTag),
                     '--include-merges',
                     os.path.abspath(repo)],
                    stdout=logFp)
        logFp.write('\n')
        logFp.flush()


def main():
    usage = """
%prog [options]

Generates a raw changelog for the specified tags.
"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--start', dest='startTag', metavar='START_TAG',
                      default='', help=('The tag to start generating entries '
                                          'from.'))
    parser.add_option('--end', dest='endTag', metavar='END_TAG',
                      default='', help=('The tag to end entry generation '
                                          'with.'))

    options, _ = parser.parse_args()


    reposToQuery = [os.path.join(CONFIG_BASE, 'CommonConfig')]

    if not os.path.isfile(PRODUCTS):
        print "'%s' is missing!" % PRODUCTS
        sys.exit(1)

    products = {}
    with open(PRODUCTS, 'rb') as prodsFp:
        products.update(json.load(prodsFp))

    for p in products:
        prodDir = os.path.join(CONFIG_BASE, "%sTemplates" % p)
        reposToQuery.append(os.path.join(prodDir, 'AppConfig'))
        reposToQuery.append(os.path.join(prodDir, 'InstrConfig'))

    with open('CHANGELOG.raw', 'wb') as fp:
        _generateChangelogBzr(fp, reposToQuery, options.startTag, options.endTag)
        _generateChangelogGit(fp, options.startTag, options.endTag)


if __name__ == '__main__':
    main()
