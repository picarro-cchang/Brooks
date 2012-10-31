"""
Copyright 2012 Picarro Inc.

Generates a changelog between two tags in the repositories.
"""

from __future__ import with_statement

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


def _generateChangelog(repositoryNames, startTag, endTag):
    """
    Generate verbose diffs for all of the changes for all of the
    repositories we know about between the specified tags.
    """

    with open('CHANGELOG.raw', 'wb') as changelogFp:
        for repo in repositoryNames:
            changelogFp.write("\n%s\n" % repo)
            changelogFp.flush()
            subprocess.call(['bzr.exe',
                             'log',
                             '-v',
                             "-r%s..%s" % (startTag, endTag),
                             '--include-merges',
                             os.path.abspath(repo)],
                            stdout=changelogFp)
            changelogFp.write('\n')
            changelogFp.flush()


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


    reposToQuery = [os.path.join(REPO_BASE, REPO),
                    os.path.join(CONFIG_BASE, 'CommonConfig')]

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

    _generateChangelog(reposToQuery, options.startTag, options.endTag)


if __name__ == '__main__':
    main()
