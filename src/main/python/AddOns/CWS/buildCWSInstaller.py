"""
Copyright 2015 Picarro Inc.

Create an installer for CWS programs. This installer adds priming program and CWS coordinator to the analyzer
Host software must be installed before runing CWS installer
"""

from __future__ import with_statement

import os
import sys
import shutil
import subprocess
import py_compile
import re
import time
import os.path
import stat
import platform
import errno

from distutils import dir_util
from optparse import OptionParser

from Host.Common import OS

#SANDBOX_DIR = 'c:/temp/sandbox'

ISCC = 'c:/program files/Inno Setup 5/ISCC.exe'
ISCC_WIN7 = 'c:/program files (x86)/Inno Setup 5/ISCC.exe'
INSTALLER_SCRIPTS_DIR = 'InstallerScriptsWin7'


g_logMsgLevel = 0   # should be 0 for check-in


def LogErrmsg(str):
    print >> sys.stderr, str


def LogMsg(level, str):
    if level <= g_logMsgLevel:
        print str

###############################################################################

def makeInstaller(opts):
    # get OS type so we can run ISS from the appropriate path
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

    # get the version number of CWS
    version = "CWS 1.0.0"

    # version is currently something like 'DatViewer 2.0.4' so
    # extract the version number
    verNum = version.split(" ")[1]

    print "verNum='%s'" % verNum

    # build the installer
    _compileInstaller(osType, verNum)


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


def _compileInstaller(osType, ver):
    isccApp = ISCC

    if osType == 'win7':
        isccApp = ISCC_WIN7

    # save off the current dir to build a path to the installer dir
    currentDir = os.getcwd()
    SANDBOX_DIR = currentDir
    print "SANDBOX_DIR=", SANDBOX_DIR

    installScriptDir = os.path.join(currentDir, INSTALLER_SCRIPTS_DIR)
    setupFilePath = "%s\\setup_CWS.iss" % installScriptDir

    currentYear = time.strftime("%Y")

    args = [isccApp, "/dCWSVersion=%s" % ver,
            "/dproductYear=%s" % currentYear,
            "/dsandboxDir=%s" % SANDBOX_DIR,
            "/v9",
            "/O%s" % os.path.abspath(os.path.join(currentDir,
                                                    'Installers')),
            setupFilePath]

    print subprocess.list2cmdline(args)
    print "current dir='%s'" % os.getcwd()

    retCode = subprocess.call(args)

    if retCode != 0:
        LogErrmsg("Error building CWS installer, retCode=%d." % retCode)
        sys.exit(retCode)

def makeExe():
    retCode = subprocess.call(["python", "PrimerSetup.py", "py2exe"])

    if retCode != 0:
        LogErrmsg("Error making executables, retCode=%d." % retCode)
        sys.exit(retCode)

def main():
    usage = """
%prog [options]

Builds an installer for CWS.
"""

    global g_logMsgLevel

    parser = OptionParser(usage=usage)

    """
    parser.add_option('-c', '--version', dest='version', metavar='VERSION',
                      default=None, help=('Specify a version for this release '
                                          'and tag it as such in the '
                                          'repository.'))
    """

    parser.add_option('-l', '--loglevel', dest='loglevel', action='store', type='int',
                      default=g_logMsgLevel, help=('Use this option to specify logging level to '
                                                   'debug this application. 0=highest, 5=lowest (noisy)'))

    options, args = parser.parse_args()
    #print "options=", options

    g_logMsgLevel = options.loglevel
    
    makeExe()
    makeInstaller(options)
    
if __name__ == '__main__':
    main()