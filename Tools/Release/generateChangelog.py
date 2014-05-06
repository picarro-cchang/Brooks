"""
Copyright 2012 - 2014 Picarro Inc.

Generates a changelog between two tags in the repositories.

In the future, we will be using configs from git for builds. After that time, we'll only
need the git log. You can force bzr config logs to be included with the --bzrConfigs option,
just specify the proper start and end tag.

History:

2014/05/05  tw  Supports new json file filenames and format. Change log filename includes
                product name and OS. If bzr version >= 2.5, uses --include-merged option
                (--include-merges deprecated in 2.5). Outputs current time, branch name,
                product, os, start and end tags, etc. in file header.

"""

from __future__ import with_statement

import os
import sys
import time
import subprocess
import optparse
import os.path
import platform

#pylint: disable=F0401
try:
    import simplejson as json
except ImportError:
    import json
#pylint: enable=F0401


# these 2 params are not used
REPO_BASE = 's:/repository/software'
REPO = 'trunk'

CONFIG_BASE = 's:/CrdsRepositoryNew/trunk/G2000/Config'


def runCommand(command):
    """
    Run a command line command so we can capture its output.
    """
    #print "runCommand: '%s'" % command
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)

    stdout_value, stderr_value = p.communicate()
    # print "stdout:", repr(stdout_value)
    return stdout_value, stderr_value


def getGitBranch(gitDir):
    """
    Get the git branch that the gitDir is currently set to.
    """
    #print "gitDir=%s" % gitDir

    curBranch = ""

    if not os.path.isdir(gitDir):
        print "'%s' is not a directory!" % gitDir
        return curBranch

    # save off the current dir so we can get back to it when we're done
    saveDir = os.getcwd()

    # change to the git dir
    #print "cd to '%s'" % gitDir
    os.chdir(gitDir)
    #print "current dir is now '%s'" % os.getcwd()

    # run "git branch" and parse stdout for it -- the current branch name begins with a "* "
    command = "git branch"
    stdout_value, stderr_value = runCommand(command)

    branches = stdout_value.splitlines()
    for branch in branches:
        #print branch
        if branch[0] == "*" and branch[1] == " ":
            curBranch = branch[2:].rstrip("\r\n")
            #print "curBranch='%s'" % curBranch
            break

    #print "currentDir='%s'" % os.getcwd()

    # reset to the original dir
    os.chdir(saveDir)

    return curBranch


def _generateChangelogGit(logFp, startTag, endTag):
    """
    Generate verbose diffs for all of the changes between the specified tags.
    Assumes that this script is being run of out a git working copy.
    """

    logFp.write("\ngit logs for: %s\n" % os.getcwd())
    logFp.flush()

    print subprocess.list2cmdline(['git.exe',
                     'log',
                     '--name-status',
                     "%s..%s" % (startTag, endTag)])

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

    # get bzr version
    bzrVer, _ = runCommand("bzr version --short")

    # --include-merges was deprecated in bzr 2.5
    bzrVerNums = bzrVer.split(".")
    bzrNum = bzrVerNums[0] + "." + bzrVerNums[1]

    if float(bzrNum) >= 2.5:
        includeMergeCmd = "--include-merged"
    else:
        includeMergeCmd = "--include-merges"

    # bzr log -v -r tag:<tag1>..<tag2> --include-merged <path>

    for repo in repositoryNames:
        logFp.write("\nbzr logs for: %s\n" % repo)
        logFp.flush()

        print subprocess.list2cmdline(['bzr.exe',
                       'log',
                       '-v',
                       "-r%s..%s" % (startTag, endTag),
                       includeMergeCmd,
                       os.path.abspath(repo)])

        subprocess.call(['bzr.exe',
                     'log',
                     '-v',
                     "-r%s..%s" % (startTag, endTag),
                     includeMergeCmd,
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
    parser.add_option('--product', dest='product', metavar='PRODUCT', default=None, help=('The product line to generate '
                                                                                         'the release changelog for.'))
    parser.add_option('--ostype', dest='osType', metavar='OSTYPE', default=None, help=('The OS type to generate '
                                                                                       'the release changelog for (winxp or win7).'))
    parser.add_option('--bzrConfigs', dest='forceBzrConfigs', action='store_true',
                      default=False, help=('Fetch bzr logs for all configs, even if builds do '
                                           'not pull configuration files from bzr repos.'))

    options, _ = parser.parse_args()

    if options.product is None:
        print "--product option is required!"
        sys.exit(1)

    gitBranchName = getGitBranch(os.getcwd())

    if gitBranchName == "":
        print "not in a git branch!"
        sys.exit(1)

    # init bzr repos to query
    bzrReposToQuery = []

    # need OS type so we can construct a filename for the JSON config file (e.g., g2000_win7.json)
    # and the tag names
    #
    # since this is only for creating a log, allow a command line option to specify the OS
    if options.osType is None:
        # no command line option
        # returns 'XP' (WinXP) or '7' (Win7)
        osType = platform.uname()[2]

        if osType == '7':
            osType = 'win7'
        elif osType == 'XP':
            osType = 'winxp'
        else:
            osType = 'unknown'
            print "Unexpected OS type!"
            sys.exit(1)

    else:
        # command line option given for the OS
        osType = options.osType

        if osType == 'win7' or osType == 'winxp':
            pass
        else:
            print "Unexpected OS type!"
            sys.exit(1)

    productConfigs = "%s_%s.json" % (options.product, osType)

    if not os.path.isfile(productConfigs):
        print "Cannot find '%s'!" % productConfigs
        sys.exit(1)

    configInfo = {}

    with open(productConfigs, 'r') as prodsFp:
        configInfo.update(json.load(prodsFp))

    buildInfo = configInfo["buildTypes"]
    #print buildInfo

    products = []
    bzrConfigs = False      # True if any configs in bzr

    for item in buildInfo:
        itemDict = buildInfo[item]

        # default config repos to bzr
        repo = itemDict.get("configRepo", "bzr")

        if repo == "bzr" or options.forceBzrConfigs is True:
            products.append(item)
            bzrConfigs = True

    products.sort()
    #print products

    if bzrConfigs is True:
        bzrReposToQuery.append(os.path.normpath(os.path.join(CONFIG_BASE, 'CommonConfig')))

    # products will be empty if bzr not used for the configs (future)
    for p in products:
        prodDir = os.path.join(CONFIG_BASE, "%sTemplates" % p)
        bzrReposToQuery.append(os.path.normpath(os.path.join(prodDir, 'AppConfig')))
        bzrReposToQuery.append(os.path.normpath(os.path.join(prodDir, 'InstrConfig')))

    changelogFilename = "CHANGELOG_%s_%s.raw" % (options.product, osType)

    print ""
    print "changelogFilename=", changelogFilename
    print ""

    """
    print "*** bzrReposToQuery ***"
    for item in bzrReposToQuery:
        print item
    """

    #sys.exit(0)

    # writing files as binary, only \n written as line terminator
    with open(changelogFilename, 'wb') as fp:
        # TODO: write start and end tags into beginning of file?
        fp.write("Changelog created %s" % time.strftime("%Y-%m-%d %H:%M:%S %Z\n\n", time.localtime()))
        fp.write("  product    = %s\n" % options.product)
        fp.write("  os         = %s\n" % osType)
        fp.write("  git branch = %s\n" % gitBranchName)
        fp.write("  bzrConfigs = %s\n" % str(bzrConfigs))
        fp.write("  startTag   = %s\n" % options.startTag)
        fp.write("  endTag     = %s\n" % options.startTag)

        if len(bzrReposToQuery) > 0:
            fp.write("\n*************************************\n")
            # get logs for bzr config repos
            _generateChangelogBzr(fp, bzrReposToQuery, options.startTag, options.endTag)

        fp.write("\n*************************************\n")
        _generateChangelogGit(fp, options.startTag, options.endTag)


if __name__ == '__main__':
    main()
