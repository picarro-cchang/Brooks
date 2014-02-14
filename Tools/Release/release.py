"""
Copyright 2012-2013 Picarro Inc.

Replacement for makeExe.bat.
"""

from __future__ import with_statement

import os
import sys
import shutil
import subprocess
#import pprint
import re
import time
import os.path
import stat
import platform

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
ISCC_WIN7 = 'c:/program files (x86)/Inno Setup 5/ISCC.exe'
INSTALLER_SCRIPTS_DIR = 'InstallerScripts'

RESOURCE_DIR = ('s:/CRDS/SoftwareReleases/G2000Projects/G2000_PrepareInstaller/'
                'Resources')

CONFIGS = {}
INSTALLER_SIGNATURES = {}

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


# for logging stdout and stderr to a log file
class StdoutLogger(object):
    def __init__(self, f, quiet=False):
        self.terminal = sys.stdout
        self.log = f
        sys.stdout = self
        self.quiet = quiet

    def set_quiet(self, quiet):
        self.quiet = quiet

    def write(self, message):
        if not self.quiet:
            self.terminal.write(message)
        self.log.write(message)
        
    def flush(self):
        self.log.flush()
        if not self.quiet:
            self.terminal.flush()

    def close(self):
        #print "StdoutLogger::close()"
        if self.terminal is not None:
            sys.stdout = self.terminal
            self.terminal = None

    def __del__(self):
        #print "StdoutLogger::__del__()"
        pass


class StderrLogger(object):
    def __init__(self, f):
        self.stderr = sys.stderr
        self.log = f
        sys.stderr = self

    def write(self, message):
        self.stderr.write(message)
        self.log.write(message)
        
    def flush(self):
        self.log.flush()
        self.stderr.flush()

    def close(self):
        #print "StderrLogger::close()"
        #print "   self.stderr=", self.stderr

        if self.stderr is not None:
            sys.stderr = self.stderr
            self.stderr = None

    def __del__(self):
        pass
        #print "StderrLogger::__del__()"
        #self.close()


class Logger(object):
    def __init__(self, filename, quiet=False):
        self.log = open(filename, "w")
        self.stdoutLogger = StdoutLogger(self.log, quiet)
        self.stderrLogger = StderrLogger(self.log)

    def set_quiet(self, quiet):
        if self.stdoutLogger is not None:
            self.stdoutLogger.set_quiet(quiet)

    def __del__(self):
        if self.log is not None:
            self.log.close()
            self.log = None


def LogErr(message):
    sys.stderr.write(message)
    sys.stderr.write("\n")


def _buildDoneMsg(message, startSec, logfile):
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

    if logfile is not None:
        print ""
        print "logfile           =", logfile
        print ""

    print "******** %s COMPLETE ********" % message


def _printSummary(opts, osType, logfile, productFamily, productConfigs, versionConfig):
    print ""
    print "product           =", opts.product
    print "branch            =", opts.branch
    print "OS type           =", osType
    print "productFamily     =", productFamily
    print "productConfigs    =", productConfigs
    print "versionConfig     =", versionConfig

    print "version           = %s.%s.%s.%s" % (VERSION['major'], VERSION['minor'], VERSION['revision'], VERSION['build'])

    if not opts.makeOfficial:
        if opts.createTag:
            print "create tags       =", "YES"
        else:
            print "create tags       =", "NO"

        if opts.createInstallers:
            print "create installers =", "YES"
        else:
            print "create installers =", "NO"

        tmpConfigs = []
        for c in CONFIGS:
            tmpConfigs.append(c)
        tmpConfigs.sort()

        print "configs           =", tmpConfigs[0]
        for c in tmpConfigs[1:]:
            print "                   ", c

        if opts.local:
            print ""
            print "local build       =", "YES"

            if opts.cloneRepo:
                print "clone repos       =", "YES"
            else:
                print "clone repos       =", "NO"

            if opts.buildExes:
                print "build exes        =", "YES"
            else:
                print "build exes        =", "NO"

        else:
            print ""
            print "local build       =", "NO"

        print "  MFG_DISTRIB_BASE         =", MFG_DISTRIB_BASE
        print "  DISTRIB_BASE             =", DISTRIB_BASE
        print "  STAGING_MFG_DISTRIB_BASE =", STAGING_MFG_DISTRIB_BASE
        print "  STAGING_DISTRIB_BASE     =", STAGING_DISTRIB_BASE
        print ""

        # Note: local and dryRun cannot be used together, already bailed above if they were
        if opts.dryRun:
            print "dry run           =", "YES"
            print "  targetMfgDistribBase =", TEST_MFG_DISTRIB_BASE
            print "  targetDistribBase    =", TEST_DISTRIB_BASE
        else:
            print "dry run           =", "NO"
            print "  targetMfgDistribBase =", MFG_DISTRIB_BASE
            print "  targetDistribBase    =", DISTRIB_BASE

    else:
        print ""
        print "make-official     =", "YES"

        if opts.local:
            print "local build       =", "YES"
        else:
            print "local build       =", "NO"

        if opts.officialTypes is None:
            print "build types       = all"
        else:
            print "build types       =", opts.officialTypes

        print "  STAGING_DISTRIB_BASE     =", STAGING_DISTRIB_BASE
        print "   DISTRIB_BASE            =", DISTRIB_BASE

    print ""
    print "logfile           =", logfile


def runCommand(command):
    """
    # Run a command line command so we can capture its output.
    # Code is from here:
    #   http://stackoverflow.com/questions/4760215/running-shell-command-from-python-and-capturing-the-output
    """
    #print "runCommand: '%s'" % command
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')


def getGitBranch(gitDir):
    """
    Get the git branch that the gitDir is currently set to.
    """
    #print "gitDir=%s" % gitDir

    curBranch = ""

    if not os.path.isdir(gitDir):
        LogErr("'%s' is not a directory!" % gitDir)
        return curBranch

    # save off the current dir so we can get back to it when we're done
    saveDir = os.getcwd()

    # change to the git dir
    #print "cd to '%s'" % gitDir
    os.chdir(gitDir)
    #print "current dir is now '%s'" % os.getcwd()

    # run "git branch"
    command = "git branch"
    for line in runCommand(command):
        #print line
        if line[0] == "*":
            curBranch = line[2:].rstrip("\r\n")
            #print "curBranch='%s'" % curBranch

    #print "currentDir='%s'" % os.getcwd()

    # reset to the original dir
    #print "restore original cwd"
    os.chdir(saveDir)
    #print "currentDir='%s'" % os.getcwd()

    return curBranch


###############################################################################

def makeExe(opts):
    """
    Make a HostExe release from a clean checkout.
    """

    # get OS type so we can construct a filename for the JSON config file (e.g., g2000_win7.json)
    # and the log file
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

    # -------- validate some of the arguments --------
    # product argument is required
    if opts.product is None:
        LogErr("--product option is required!")
        sys.exit(1)

    if opts.local and opts.dryRun:
        LogErr("--local and --dry-run options cannot be used together!")
        sys.exit(1)

    if not opts.cloneRepo and not opts.local:
        LogErr("--debug-skip-clone is allowed only with --local option!")
        sys.exit(1)

    if not opts.buildExes and not opts.local:
        LogErr("--debug-skip-exe is allowed only with --local option!")
        sys.exit(1)

    # get the branch for this script that is executing
    branchScriptCur = getGitBranch(os.getcwd())

    # it must match the branch command line option
    if opts.branch != branchScriptCur:
        LogErr("current git branch must be same as build target branch!")
        sys.exit(1)

    # productFamily incorporates the product and OS type ('g2000_win7' for example)
    productFamily = "%s_%s" % (opts.product, osType)

    # for timing builds and default log filename 
    startSec = time.time()
    startTime = time.localtime()

    # construct a logging filename
    if opts.logfile is not None:
        logfile = opts.logfile
    else:
        logfile = "%s_log_%s" % (productFamily, time.strftime("%Y%m%d_%H%M%S.log", startTime))

    # -------- validate JSON files --------

    productConfigs = "%s_%s.json" % (opts.product, osType)
    versionConfig = "%s_version.json" % opts.product

    if not os.path.isfile(productConfigs):
        LogErr("%s is missing!" % productConfigs)
        sys.exit(1)

    if not os.path.isfile(versionConfig):
        LogErr("%s is missing!" % versionConfig)
        sys.exit(1)

    configInfo = {}

    with open(productConfigs, 'r') as prods:
        configInfo.update(json.load(prods))

    # win7 g2000 builds have categories in the JSON file but winxp g2000 and mobile don't currently.
    # override the hard-coded dir
    global INSTALLER_SCRIPTS_DIR
    global CONFIGS

    # updated JSON file format is required ()
    INSTALLER_SCRIPTS_DIR = configInfo["installerScriptsDir"]
    buildInfo = configInfo["buildTypes"]

    # CONFIGS is a dict containing analyzer types and species
    # INSTALLER_SIGNATURES is another dict containing analyzer types and installer signature text
    for item in buildInfo:
        itemDict = buildInfo[item]
        CONFIGS[item] = itemDict["species"]
        INSTALLER_SIGNATURES[item] = itemDict["installerSignature"]

    print "CONFIGS=", CONFIGS
    print ""
    print "INSTALLER_SIGNATURES=", INSTALLER_SIGNATURES


    # -------- prepare build options --------

    # version to be built
    changedVersion = True

    global MFG_DISTRIB_BASE, DISTRIB_BASE
    global STAGING_MFG_DISTRIB_BASE, STAGING_DISTRIB_BASE
    global TEST_MFG_DISTRIB_BASE, TEST_DISTRIB_BASE

    if not opts.makeOfficial:
        # version
        with open(versionConfig, 'r') as ver:
            VERSION.update(json.load(ver))

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

        if opts.local:
            # use C:\ for local build destination folder paths
            MFG_DISTRIB_BASE = 'C' + MFG_DISTRIB_BASE[1:]
            DISTRIB_BASE  = 'C' + DISTRIB_BASE [1:]
            STAGING_MFG_DISTRIB_BASE = 'C' + STAGING_MFG_DISTRIB_BASE[1:]
            STAGING_DISTRIB_BASE = 'C' + STAGING_DISTRIB_BASE[1:]

        # append productFamily to paths (it's something like "g2000_win7")
        MFG_DISTRIB_BASE = "/".join([MFG_DISTRIB_BASE, productFamily])
        DISTRIB_BASE = "/".join([DISTRIB_BASE, productFamily])
        STAGING_MFG_DISTRIB_BASE = "/".join([STAGING_MFG_DISTRIB_BASE, productFamily])
        STAGING_DISTRIB_BASE = "/".join([STAGING_DISTRIB_BASE, productFamily])

        TEST_MFG_DISTRIB_BASE = "/".join([TEST_MFG_DISTRIB_BASE, productFamily])
        TEST_DISTRIB_BASE = "/".join([TEST_DISTRIB_BASE, productFamily])

    else:
        if opts.local:
            # use C:\ for local build destination folder paths
            DISTRIB_BASE  = 'C' + DISTRIB_BASE [1:]
            STAGING_DISTRIB_BASE = 'C' + STAGING_DISTRIB_BASE[1:]

        # append product to paths used for make-official option
        DISTRIB_BASE = "/".join([DISTRIB_BASE, productFamily])
        STAGING_DISTRIB_BASE = "/".join([STAGING_DISTRIB_BASE, productFamily])

    # print summary of build info so user can review it
    _printSummary(opts, osType, logfile, productFamily, productConfigs, versionConfig)

    # ask user for build confirmation before proceeding
    if not opts.skipConfirm:
        print ""
        response = raw_input("OK to continue? Y or N: ")

        if response == "Y" or response == "y":
            print "Y typed, continuing"
        else:
            print "Build canceled"
            sys.exit(0)

    # -------- start of build --------
    #
    # init logging to stdout and stderr
    logger = Logger(logfile, quiet=False)

    # output the start time
    print "Build script start: %s" % time.strftime("%Y/%m/%d %H:%M:%S %p", startTime)

    # reiterate the build summary so it is saved in the log
    _printSummary(opts, osType, logfile, productFamily, productConfigs, versionConfig)

    # set the quiet flag if option set
    logger.set_quiet(opts.debugQuiet)

    # --local: modify base paths for testing on local C: drive
    if opts.local:
        # make sure dirs exist on the local drive
        if not os.path.exists(MFG_DISTRIB_BASE):
            os.makedirs(MFG_DISTRIB_BASE)
        if not os.path.exists(DISTRIB_BASE):
            os.makedirs(DISTRIB_BASE)
        if not os.path.exists(STAGING_MFG_DISTRIB_BASE):
            os.makedirs(STAGING_MFG_DISTRIB_BASE)
        if not os.path.exists(STAGING_DISTRIB_BASE):
            os.makedirs(STAGING_DISTRIB_BASE)

    if opts.dryRun:
        targetMfgDistribBase = TEST_MFG_DISTRIB_BASE
        targetDistribBase = TEST_DISTRIB_BASE

        # TODO: only remove the dir itself so we don't lose everything
        #       I haven't been using --dry-run so ignoring for now. tw
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
        _promoteStagedRelease(types=opts.officialTypes,
                              mfgDistribBase=targetMfgDistribBase,
                              distribBase=targetDistribBase,
                              versionConfig=versionConfig,
                              product=productFamily,
                              osType=osType)

        _buildDoneMsg("MAKE-OFFICIAL", startSec, logfile)
        return

    with open(versionConfig, 'w') as ver:
        json.dump(VERSION, ver)

    # Commit and push new version number if it was changed
    if changedVersion is True:
        retCode = subprocess.call(['git.exe',
                                   'add',
                                   versionConfig])

        if retCode != 0:
            LogErr('Error staging new version metadata in local repo, retCode=%d.' % retCode)
            sys.exit(1)

        retCode = subprocess.call(['git.exe',
                                   'commit',
                                   '-m',
                                   "release.py version update (%s)." % productFamily])

        if retCode != 0:
            LogErr('Error committing new version metadata to local repo, retCode=%d.' % retCode)
            sys.exit(1)

        retCode = subprocess.call(['git.exe',
                                   'push'])

        if retCode != 0:
            LogErr('Error pushing new version metadata to repo, retCode=%d.' % retCode)

    else:
        print "Version number was not changed, skipping update version metadata in local repo."

    if opts.cloneRepo:
        _branchFromRepo(opts.branch)
    else:
        print "Skipping cloning of repos."

        # do a quick test for existence of the sandbox dir (won't ensure build integrity though)
        if not os.path.exists(SANDBOX_DIR):
            LogErr("Sandbox directory containing repos does not exist!")
            sys.exit(1)

    _generateReleaseVersion(productFamily, VERSION)

    if opts.buildExes:
        _buildExes()
    else:
        print "Skipping building executables"

        # quick test for existence of sandbox dir and dist folders
        if not os.path.exists(SANDBOX_DIR):
            LogErr("Sandbox directory containing repos does not exist!")
            sys.exit(1)

        exeDir = os.path.join(SANDBOX_DIR, "host", "Host", "dist")
        if not os.path.exists(exeDir):
            LogErr("'%s' does not exist!" % exeDir)
            sys.exit(1)

        exeDir = os.path.join(SANDBOX_DIR, "host", "MobileKit", "dist")
        if not os.path.exists(exeDir):
            LogErr("'%s' does not exist!" % exeDir)
            sys.exit(1)

    # XXX This is likely superfluous once the configuration files have
    # been merged into the main repository.
    if opts.cloneRepo:
        _makeLocalConfig()

    if opts.createInstallers:
        _compileInstallers(productFamily, osType, VERSION)
    else:
        print "Skipping creating the installers."

    if opts.createTag:
        _tagRepository(productFamily, VERSION)

        # XXX These should be removed when we finish merging the
        # configuration file directories into the repository.
        _tagCommonConfig(productFamily, VERSION)
        _tagAppInstrConfigs(productFamily, VERSION)

    else:
        print "Skipping tagging of the repository."

    if opts.createInstallers:
        # Copy both HostExe and AnalyzerServerExe for non-installer upgrades.
        _copyBuildAndInstallers(versionConfig, productFamily, osType, VERSION)

    _buildDoneMsg("BUILD", startSec, logfile)


def _promoteStagedRelease(types=None, mfgDistribBase=None, distribBase=None,
                          versionConfig=None, product=None, osType=None):
    """
    Move the existing staged release to an official directory.
    """

    assert versionConfig

    stagingVer = os.path.join(STAGING_DISTRIB_BASE, versionConfig)

    if not os.path.isfile(stagingVer):
        LogErr("Staging %s is missing!" % versionConfig)
        sys.exit(1)

    print ""

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

    configTypes = []
    for c in CONFIGS:
        configTypes.append(c)
    configTypes.sort()

    for c in configTypes:
        doCopy = True

        if typesList is not None:
            if negate:
                doCopy = c not in typesList
            else:
                doCopy = c in typesList

        if not doCopy:
            continue

        # Installer filenames will be something like:
        #    setup_CFADS_CO2_CH4_H2O_g2000_win7-1.5.0-10.exe
        #
        # where
        #     c = CFADS
        #     CONFIGS[c] = CO2_CH4_H2O
        #     _verAsString(product, ver) = g2000_win7-1.5.0-10

        installer = "setup_%s_%s_%s.exe" % (c, CONFIGS[c],
                                            _verAsString(product, ver))

        # Poor practice to use a different filename in the Current folder, removing this.
        #installerCurrent = "setup_%s_%s.exe" % (c, CONFIGS[c])
        targetDir = os.path.join(distribBase, c)

        print "%-8s: %s" % (c, installer)

        # create destination folders if they don't already exist
        destDir = os.path.join(targetDir, 'Archive')
        if not os.path.exists(destDir):
            os.makedirs(destDir)

        shutil.copyfile(os.path.join(STAGING_DISTRIB_BASE, c, installer),
                        os.path.join(targetDir, 'Archive', installer))

        destDir = os.path.join(targetDir, 'Current')
        if not os.path.exists(destDir):
            os.makedirs(destDir)

        # Installers in Current folder now include the version number in their
        # filenames.
        #shutil.copyfile(os.path.join(STAGING_DISTRIB_BASE, c, installer),
        #                os.path.join(targetDir, 'Current', installerCurrent))
        shutil.copyfile(os.path.join(STAGING_DISTRIB_BASE, c, installer),
                        os.path.join(targetDir, 'Current', installer))


def _copyBuildAndInstallers(versionConfig, product, osType, ver):
    """
    Move the installers and the two compiled exe directories to their
    staging location so other people can find them.
    """

    # Clean the previously staged version.
    #
    # TODO: Eliminate copying to the base dirs. We need to wean Mfg from
    #       copying HostExe and AnalyzerServerExe folders. They need to
    #       use the installers.
    try:
        shutil.rmtree(STAGING_MFG_DISTRIB_BASE)
        shutil.rmtree(STAGING_DISTRIB_BASE)
    except OSError:
        # Okay if these directories don't already exist.
        pass

    # HostExe
    hostExeDir = os.path.join(STAGING_MFG_DISTRIB_BASE, 'HostExe')

    if os.path.isdir(hostExeDir):
        os.rmdir(hostExeDir)
    assert not os.path.isdir(hostExeDir)
    os.makedirs(hostExeDir)

    dir_util.copy_tree(os.path.join(SANDBOX_DIR, 'host', 'Host', 'dist'),
                       hostExeDir)

    # AnalyzerServerExe
    analyzerServerExe = os.path.join(STAGING_MFG_DISTRIB_BASE,
                                     'AnalyzerServerExe')

    if os.path.isdir(analyzerServerExe):
        os.rmdir(analyzerServerExe)
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

        if not os.path.isdir(targetDir):
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
        print "Removing sandbox tree '%s'." % SANDBOX_DIR

        # sometimes this fails with the following error:
        #    WindowsError: [Error 145] The directory is not empty: 'c:/temp/sandbox'
        # I think it takes a little time for things to settle after the chmod above
        # so make a second attempt after a short wait
        try:
            shutil.rmtree(SANDBOX_DIR)
        except:
            print "rmtree failed! sleep(5) and attempt shutil.rmtree one more time"
            time.sleep(5)
            shutil.rmtree(SANDBOX_DIR)

        print "Sandbox tree removed."

    print "Creating sandbox tree '%s'." % SANDBOX_DIR
    os.makedirs(SANDBOX_DIR)
    print "Sandbox tree creation done."
    os.makedirs(os.path.join(SANDBOX_DIR, 'Installers'))

    print "Clone git repo '%s'" % REPO_BASE
    with OS.chdir(SANDBOX_DIR):
        retCode = subprocess.call(['git.exe',
                                   'clone',
                                   REPO_BASE])

        if retCode != 0:
            LogErr("Error cloning '%s', retCode=%d" % (REPO_BASE, retCode))
            sys.exit(retCode)

        print "Check out git branch '%s'." % branch
        with OS.chdir(os.path.join(SANDBOX_DIR, 'host')):
            retCode = subprocess.call(['git.exe',
                                       'checkout',
                                       branch])

            if retCode != 0:
                LogErr("Error checking out 'origin/%s', retCode=%d." % (branch, retCode))
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
                 "    return '%s'\n" % _verAsString(product, ver),
                 "\n",
                 "def versionNumString():\n",
                 "    return '%s'\n" % _verAsNumString(ver)])


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
            LogErr("Error building MobileKit. retCode=%d" % retCode)
            sys.exit(retCode)

    with OS.chdir(os.path.join(SANDBOX_DIR, 'host', 'Host')):
        retCode = subprocess.call(['python.exe', 'PicarroExeSetup.py',
                                   'py2exe'],
                                   env=buildEnv)

        if retCode != 0:
            LogErr("Error building Host. retCode=%d" % retCode)
            sys.exit(retCode)


def _tagRepository(product, ver):
    """
    Tags the repository
    """

    print ""
    print "Tagging repository..."

    tagName = _verAsString(product, ver)
    print "  git tag -a %s -m \"Version %s\"" % (tagName, tagName)

    retCode = subprocess.call(['git.exe',
                               'tag',
                               '-a',
                               tagName,
                               '-m',
                               "Version %s" % tagName])

    if retCode != 0:
        LogErr("Error tagging repository. retCode=%d  tagName='%s'" % (retCode, tagName))
        sys.exit(retCode)

    print "  git push origin %s" % tagName
    retCode = subprocess.call(['git.exe',
                               'push',
                               'origin',
                               tagName])

    if retCode != 0:
        LogErr("Error pushing tag to repository. retCode=%d  tagName='%s'" % (retCode, tagName))
        sys.exit(retCode)


def _tagCommonConfig(product, ver):
    retCode = subprocess.call(['bzr.exe', 'tag', "--directory=%s" %
                               COMMON_CONFIG, _verAsString(product, ver)])

    if retCode != 0:
        LogErr("Error tagging CommonConfig as '%s'. retCode=%d." % (_verAsString(product, ver), retCode))
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
                LogErr("Error tagging '%s' AppConfig as '%s', retCode=%d." % \
                    (c, _verAsString(product, ver)), retCode)
                sys.exit(retCode)

            retCode = subprocess.call(['bzr.exe', 'tag',
                                       "--directory=%s" %
                                       os.path.join(configBase, 'InstrConfig'),
                                       _verAsString(product, ver)])

            if retCode != 0:
                LogErr("Error tagging '%s' InstrConfig as '%s', retCode=%d." % \
                    (c, _verAsString(product, ver)), retCode)
                sys.exit(retCode)


def _makeLocalConfig():
    """
    Adds physical copies of all of the configuration file repositories to the
    sandbox and generates the required version.ini file.
    """

    with OS.chdir(SANDBOX_DIR):
        retCode = subprocess.call(['bzr.exe', 'branch', COMMON_CONFIG])

        if retCode != 0:
            LogErr("Error cloning CommonConfig. retCode=%d" % retCode)
            sys.exit(retCode)

        with open(os.path.join('CommonConfig', 'version.ini'), 'w') as fp:
            retCode = subprocess.call(['bzr.exe', 'version-info',
                                       'CommonConfig', '--custom',
                                       "--template=%s" % VERSION_TEMPLATE],
                                       stdout=fp)

            if retCode != 0:
                LogErr("Error generating version.ini for CommonConfig. retCode=%d" % retCode)
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
                    LogErr("Error cloning '%s' AppConfig. retCode=%d" % (c, retCode))
                    sys.exit(retCode)

                with open(os.path.join('AppConfig', 'version.ini'), 'w') as fp:
                    retCode = subprocess.call(['bzr.exe', 'version-info',
                                               'AppConfig', '--custom',
                                               "--template=%s" %
                                               VERSION_TEMPLATE],
                                               stdout=fp)

                    if retCode != 0:
                        LogErr("Error generating '%s' AppConfig version.ini. retCode=%d" % (c, retCode))
                        sys.exit(retCode)

                retCode = subprocess.call(['bzr.exe', 'branch',
                                           os.path.join(CONFIG_BASE,
                                                        "%sTemplates" % c,
                                                        'InstrConfig'),
                                                        'InstrConfig'])
                if retCode != 0:
                    LogErr("Error cloning '%s' InstrConfig. retCode=%d" % (c, retCode))
                    sys.exit(retCode)

                with open(os.path.join('InstrConfig',
                                       'version.ini'), 'w') as fp:
                    retCode = subprocess.call(['bzr.exe', 'version-info',
                                               'InstrConfig', '--custom',
                                               "--template=%s" %
                                               VERSION_TEMPLATE],
                                               stdout=fp)

                    if retCode != 0:
                        LogErr("Error generating '%s' InstrConfig version.ini. retCode=%d" % (c, retCode))
                        sys.exit(retCode)


def _compileInstallers(product, osType, ver):
    """
    Compiles the installers for each variant. The original runCompInstallers.bat
    used Compil32.exe, but if we use ISCC.exe we should be able to bypass the
    requirement that each .iss file have its version string updated manually.
    """

    # build alphabetically by instrument type (nicety for monitoring build progress)
    configTypes = []
    for c in CONFIGS:
        configTypes.append(c)
    configTypes.sort()

    # save off the current dir to build a path to the installer dir
    currentDir = os.getcwd()

    for c in configTypes:
        print "Compiling '%s'..." % c

        isccApp = ISCC

        if osType == 'win7':
            isccApp = ISCC_WIN7

        # Note: .iss files are coming from a subfolder under this release.py dir,
        #        NOT the sandbox tree.
        #
        # Build a fully qualified path for the scripts folder, so ISCC can find
        # the include files (can't find them using a relative path here).
        installScriptDir = os.path.join(currentDir, INSTALLER_SCRIPTS_DIR)
        setupFilePath = "%s\\setup_%s_%s.iss" % (installScriptDir, c, CONFIGS[c])

        print "building from '%s'" % setupFilePath

        # Write the installerSignature.txt file into the sandbox config folder for this
        # analyzer type.
        sigLine = INSTALLER_SIGNATURES[c]
        sigFilePath = os.path.normpath(os.path.join(SANDBOX_DIR, c, "installerSignature.txt"))
        f = open(sigFilePath, "w")
        f.write(sigLine)
        f.close()

        #
        # TODO: add an argument for platform and maybe Python version?

        args = [isccApp, "/dinstallerType=%s" % c,
                "/dhostVersion=%s" % _verAsString(product, ver),
                "/dresourceDir=%s" % RESOURCE_DIR,
                "/dsandboxDir=%s" % SANDBOX_DIR,
                "/dcommonName=%s" % CONFIGS[c],
                "/v9",
                "/O%s" % os.path.abspath(os.path.join(SANDBOX_DIR,
                                                        'Installers')),
                setupFilePath]

        print subprocess.list2cmdline(args)
        print "current dir='%s'" % os.getcwd()

        retCode = subprocess.call(args)

        if retCode != 0:
            LogErr("Error building '%s' installer, retCode=%d." % (c, retCode))
            sys.exit(retCode)


def _verAsString(product, ver, osType=None):
    """
    Convert a version dict into a human-readable string.
    """

    number = "%(major)s.%(minor)s.%(revision)s-%(build)s" % ver

    if osType is not None:
        return "%s-%s-%s" % (product, osType, number)
    else:
        return "%s-%s" % (product, number)


def _verAsNumString(ver):
    """
    Convert a version dict into a string of numbers in this format:
        <major>.<minor>.<revision>.<build>
    """

    number = "%(major)s.%(minor)s.%(revision)s.%(build)s" % ver
    return number


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
                                          'release for. This option is required.'))
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
    parser.add_option('--debug-skip-clone', dest='cloneRepo', action='store_false',
                      default=True, help=('Skip cloning the repositories. The sandbox '
                                          'must already exist from a prior build. Allowed '
                                          'only when combined with --local. Useful for quick '
                                          'testing of minor changes or debugging this build script.'))
    parser.add_option('--debug-skip-exe', dest='buildExes', action='store_false',
                      default=True, help=('Skip building the executables. The sandbox and executables'
                                          'must already exist from a prior build. Allowed '
                                          'only when combined with --local. Useful for quick '
                                          'testing of minor changes or debugging this build script.'))
    parser.add_option('--logfile', dest='logfile', default=None,
                      help=('Use this option to specify a filename for logging '
                            'output from stdout and stderr. A default filename is '
                            'generated using the product, branch, and current time if '
                            'no filename is specified.'))
    parser.add_option('--debug-quiet', dest='debugQuiet',
                      action='store_true', default=False,
                      help=('Only output from stderr is directed to the console. '
                            'The logfile will always contain output from both '
                            'stdout and stderr.'))

    options, _ = parser.parse_args()

    makeExe(options)


if __name__ == '__main__':
    main()
