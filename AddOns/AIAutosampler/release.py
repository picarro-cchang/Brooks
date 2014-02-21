"""
Copyright 2012 Picarro Inc.

Driver for building the Autosampler installer package.
"""

from __future__ import with_statement

import sys
import os
#import pprint
import optparse
import subprocess
import re
import shutil
import os.path
import platform
import time

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

INSTALLER_SCRIPTS_DIR = 'InstallerScripts'

VERSION = {}
VERSION_METADATA = 'version.json'

REPO_BASE = 'https://github.com/picarro/host.git'
REPO = 'g2000'

# For now I'm putting this in the staging area
DISTRIB_BASE = 'S:/CRDS/CRD Engineering/Software/G2000/Installer_Staging'


def _getOsType():
    osType = platform.uname()[2]

    if osType == '7':
        osType = 'win7'
    elif osType == 'XP':
        osType = 'winxp'
    else:
        osType = 'unknown'
        print "Unexpected OS type!"

    return osType


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


def _buildDoneMsg(message, startSec):
    """
    Output the ending time, elapsed time, and a build completed message
    """
    print "Build script end: %s" % time.strftime("%Y/%m/%d %H:%M:%S %p", time.localtime())

    if startSec is not None:
        # we don't really care about fractional seconds
        elapsed = int(time.time() - startSec)

        hours = elapsed / 3600
        seconds = elapsed % 3600
        minutes = seconds / 60
        seconds = seconds % 60

        print "Elapsed time: %d hours, %d min, %d sec" % (hours, minutes, seconds)

    print "******** %s COMPLETE ********" % message


def _printSummary(opts, osType):
    print ""
    print "branch            =", opts.branch
    print "OS type           =", osType

    print "version           = %s.%s.%s.%s" % (VERSION['major'], VERSION['minor'], VERSION['revision'], VERSION['build'])

    if opts.local:
        print ""
        print "local build       =", "YES"

        if opts.cloneHostRepo:
            print "  clone host repo (git)     =", "YES"
        else:
            print "  clone host repo (git)     =", "NO"

        if opts.buildExes:
            print "build exes        =", "YES"
        else:
            print "build exes        =", "NO"

    else:
        print ""
        print "local build       =", "NO"

    print "  DISTRIB_BASE             =", DISTRIB_BASE

###############################################################################

def makeInstaller(opts):
    """
    Build the Autosampler installer from a clean checkout.
    """

    """
    # Load metadata for all of the coordinators.
    if not os.path.isfile(COORDINATOR_METADATA):
        print "%s is missing!" % COORDINATOR_METADATA
        sys.exit(1)

    meta = {}
    with open(COORDINATOR_METADATA, 'r') as metaFp:
        meta.update(json.load(metaFp))
    """

    osType = _getOsType()

    if osType == "unknown":
        print "Unsupported OS type!"
        sys.exit(1)

    # -------- validate some of the arguments --------
    if not opts.cloneHostRepo and not opts.local:
        print "--debug-skip-host-clone option allowed only with --debug-local option!"
        sys.exit(1)

    # get the branch for this script that is executing
    branchScriptCur = getGitBranch(os.getcwd())

    # it must match the branch command line option
    if opts.branch != branchScriptCur:
        print "current git branch must be same as build target branch!"
        sys.exit(1)


    # productFamily incorporates the OS type ('autosampler_win7' for example)
    productFamily = "autosampler_%s" % osType

    # Tweak output folder path for installer
    global DISTRIB_BASE
    DISTRIB_BASE = os.path.normalize(os.path.join(DISTRIB_BASE, productFamily))

    # Set dir containing the installer scripts
    global INSTALLER_SCRIPTS_DIR
    if osType == "win7":
        INSTALLER_SCRIPTS_DIR = INSTALLER_SCRIPTS_DIR + "Win7"
    elif osType == "winxp":
        INSTALLER_SCRIPTS_DIR = INSTALLER_SCRIPTS_DIR + "WinXP"


    # Load version metadata from version.json
    if not os.path.isfile(VERSION_METADATA):
        print "%s is missing!" % VERSION_METADATA

    with open(VERSION_METADATA, 'r') as verFp:
        VERSION.update(json.load(verFp))

    if opts.version:
        m = re.compile(r'(\d+)\.(\d+)\.(\d+)').search(opts.version)
        VERSION['major'] = m.group(1)
        VERSION['minor'] = m.group(2)
        VERSION['revision'] = m.group(3)
        VERSION['build'] = '0'
    else:
        # For local builds, don't bother to bump the version number
        if opts.local is True:
            VERSION['build'] = "%s" % int(VERSION['build'])
            changedVersion = False

        else:
            # Bump the build number if we are continuing with the previous version.
            VERSION['build'] = "%s" % (int(VERSION['build']) + 1)

    #pprint.pprint(version)

    #with open(VERSION_METADATA, 'w') as verFp:
    #    json.dump(version, verFp)

    # print summary of build info so user can review it
    _printSummary(opts, osType)

    # ask user for build confirmation before proceeding
    if not opts.skipConfirm:
        print ""
        response = raw_input("OK to continue? Y or N: ")

        if response == "Y" or response == "y":
            print "Y typed, continuing"
        else:
            print "Build canceled"
            sys.exit(0)

    # for timing builds
    startSec = time.time()
    startTime = time.localtime()

    print "Build script start: %s" % time.strftime("%Y/%m/%d %H:%M:%S %p", startTime)

    # Commit and push new version number if it was changed
    if changedVersion is True:
        retCode = subprocess.call(['git.exe',
                                   'add',
                                   VERSION_METADATA])

        retCode = subprocess.call(['git.exe',
                                   'commit',
                                   '-m',
                                   'release.py version update (%s).' % productFamily])

        if retCode != 0:
            print 'Error committing new version metadata to local repo.'
            sys.exit(retCode)

        retCode = subprocess.call(['git.exe',
                                   'push'])

        if retCode != 0:
            print 'Error pushing new version metadata to repo.'

    time.sleep(1.0)

    _branchFromRepo(REPO)

    # TODO: build the executables in the dist folder

    # TODO: would be cool to autobuild Autosampler Coordinators but no
    # time to develop right now...
    #_generateCoordinators(REPO, meta)


    _compileInstaller(REPO, VERSION, osType, productFamily)

    if opts.createTag:
        _tagRepository(REPO, VERSION)
        _copyInstaller(VERSION, productFamily)

    _buildDoneMsg("BUILD", startSec)


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
        retCode = subprocess.call(['git.exe',
                                   'clone',
                                   REPO_BASE])

        if retCode != 0:
            print "Error cloning '%s'" % REPO_BASE
            sys.exit(retCode)

        with OS.chdir(os.path.join(SANDBOX_DIR, 'host')):
            retCode = subprocess.call(['git.exe',
                                       'checkout',
                                       'master'])

            if retCode != 0:
                print 'Error checking out "master".'
                sys.exit(retCode)


"""
def _generateCoordinators(name, meta):
    #
    # Autogenerate all of the coordinators listed in the metadata package.
    #

    with OS.chdir(os.path.join(SANDBOX_DIR, 'host', 'AddOns', 'SSIM')):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(
                os.path.join('.', 'templates')))
        t = env.get_template('Coordinator_SSIM.ini.j2')

        for k in meta:
            print "Generating coordinator for '%s'." % k
            standards = [col for col in meta[k]['columns'] if col[5] == 'True']
            with open(COORDINATOR_FILE_FORMAT % k, 'w') as coordFp:
                coordFp.write(t.render(analyzer=meta[k],
                                       standards=standards))
"""

def _compileInstaller(name, ver, osType, productFamily):
    """
    Builds the installer and stores it in the 'Installer' subdirectory.
    """

    print 'Compiling the installer...'

    # save off the current dir to build a path to the installer dir
    currentDir = os.getcwd()

    # Note: .iss files are coming from a subfolder under this release.py dir,
    #        NOT the sandbox tree.
    #
    # Build a fully qualified path for the scripts folder, so ISCC can find
    # the include files (can't find them using a relative path here).
    installScriptDir = os.path.join(currentDir, INSTALLER_SCRIPTS_DIR)
    setupFilePath = "%s\\setup_Autosampler.iss" % installScriptDir

    print "building from '%s'" % setupFilePath

    args = [ISCC,
            "/dversion=%s" % _verAsString(ver),
            "/dsandboxDir=%s" % SANDBOX_DIR,
            '/v9',
            "/O%s" % os.path.abspath(os.path.join(SANDBOX_DIR, 'Installers')),
            'setup_Autosampler.iss']

    print subprocess.list2cmdline(args)

    # TODO: put this chdir back in
    # For now I'm using files out of the current dir
    #with OS.chdir(os.path.join(SANDBOX_DIR, 'host', 'AddOns', 'Autosampler')):
    #    retCode = subprocess.call(args)
    if True:
        retCode = subprocess.call(args)

        if retCode != 0:
            print "Error building '%s' installer, retCode=%d." % (setupFilePath, retCode)
            sys.exit(retCode)


def _verAsString(ver):
    """
    Convert a version dict into a human-readable string.
    """

    return "%(major)s.%(minor)s.%(revision)s-%(build)s" % ver


def _verAsNumString(ver):
    """
    Convert a version dict into a string of numbers in this format:
        <major>.<minor>.<revision>.<build>
    """

    number = "%(major)s.%(minor)s.%(revision)s.%(build)s" % ver
    return number


def _tagRepository(name, ver):
    """
    Tags the repository
    """

    retCode = subprocess.call(['git.exe',
                               'tag',
                               '-a',
                               "ssim-%s" % _verAsString(ver),
                               '-m',
                               "'SSIM version %s'" % _verAsString(ver)])

    if retCode != 0:
        print 'Error tagging repository'
        sys.exit(retCode)

    retCode = subprocess.call(['git.exe',
                               'push',
                               'origin',
                               "ssim-%s" % _verAsString(ver)])

    if retCode != 0:
        print 'Error pushing tag to repository'
        sys.exit(retCode)


def _copyInstaller(ver, productFamily):
    """
    Move the installer to its distribution location where manufacturing can
    find it.
    """

    # TODO: Push to the Mfg. folder(s). For now, just copy to the staging area
    #       (path is already set in DISTRIB_BASE)
    targetDir = DISTRIB_BASE
    os.makedirs(targetDir)

    installer = "setup_%s_%s.exe" % (productFamily, _verAsString(ver))

    shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                    os.path.join(targetDir, 'Archive', installer))



    """
    # Old way - bad idea to change its filename
    installerCurrent = 'setup_SSIM.exe'
    installer = "setup_SSIM_%s.exe" % _verAsString(ver)

    targetDir = os.path.join(DISTRIB_BASE, 'AddOns')

    shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                    os.path.join(targetDir, 'Archive', installer))
    shutil.copyfile(os.path.join(SANDBOX_DIR, 'Installers', installer),
                    os.path.join(targetDir, 'Current', installerCurrent))
    """


def main():
    usage = """
%prog [options]

Builds a new release of the Autosampler installer.
"""

    parser = optparse.OptionParser(usage=usage)

    parser.add_option('-v', '--version', dest='version', metavar='VERSION',
                      default=None, help=('Specify a version for this release '
                                          'and tag it as such in the '
                                          'repository.'))

    parser.add_option('--skip-tag', dest='createTag', action='store_false',
                      default=True, help=('Skip creating a tag, even if a '
                                          'version # is specified.'))

    parser.add_option('--branch', dest='branch', metavar='BRANCH',
                      default='master', help=('The remote branch from which the '
                                              'release is built.'))

    parser.add_option('--no-confirm', dest='skipConfirm',
                      action='store_true', default=False,
                      help=('Don\'t ask for confirmation of build settings before '
                            'proceeding with the build.'))

    parser.add_option('--debug-local', dest='local',
                      action='store_true', default=False,
                      help=('Use local C: drive in place of R: or S: for '
                            'build destination paths. Useful for debugging this build '
                            'script. This option cannot be used in combination with --dry-run.'))

    parser.add_option('--debug-skip-host-clone', dest='cloneHostRepo', action='store_false',
                      default=True, help=('Skip cloning the git host repository. The sandbox git repo'
                                          'must already exist from a prior build. Allowed '
                                          'only when combined with --local. Useful for quick '
                                          'testing of minor changes or debugging this build script.'))

    parser.add_option('--debug-skip-exe', dest='buildExes', action='store_false',
                      default=True, help=('Skip building the executables. The sandbox and executables'
                                          'must already exist from a prior build. Allowed '
                                          'only when combined with --local. Useful for quick '
                                          'testing of minor changes or debugging this build script.'))


    options, _ = parser.parse_args()

    makeInstaller(options)


if __name__ == '__main__':
    main()
