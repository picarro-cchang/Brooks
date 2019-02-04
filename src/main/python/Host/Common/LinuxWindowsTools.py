"""
This module contains little utilities that handle OS specific tasks.
The idea is that code can call these utilities through a OS
agnostic API and the utility figures out the right thing to do
based upon its environment.
"""

import os
import sys
import signal
import re
import errno

def fixpath(path, operatingsystem = sys.platform):
    """
    fixpath
    Convert a Windows or Linux path to a format compatible
    with the current OS.

    Input:
    path (string) - A relative or absolute posix or Windows path
    operatingsystem (string) - The current host operating system.
    "win32" or "linux2". If not set in the argument, a system call
    is used to determine the OS at run time.

    Output:
    string - The modified path.

    Notes:
    05SEP2016 - Probably not the best solution as I'm new to Python.
    """ 

    # Make Windows style paths posix compliant.
    # If the path starts with C: assume we want the root
    # file system. If it's any other mapped drive, you'll
    # have to hand edit the input path since we can't
    # know where the mount point is.
    #
    if operatingsystem == "linux2":
        path = re.sub(r"(\\)+",'/', path)
        if path.startswith("C:"):
            path = path[2:]

    # Make posix path work on Windows.  If the path doesn't
    # start with ~ or .. we assume an absolute path on C:
    #
    if operatingsystem == "win32":
        path = path.replace('/','\\')
        if path.startswith("\\"):
            path = "C:" + path

    return path


def __path_test():

    # Relative paths test
    windowspath = r"..\dir\subdir\subsubdir"
    unixpath = "../dir/subdir/subsubdir"

    newpath = fixpath(unixpath, operatingsystem = 'win32')
    print("Unix in:", unixpath, "Windows out:", newpath)

    newpath = fixpath(windowspath, operatingsystem = 'linux2')
    print("Windows in:", windowspath, "Unix out:", newpath)

    # Absolute path test
    windowspath = r"C:\root\dir\subdir\subsubdir"
    unixpath = "/root/dir/subdir/subsubdir"

    newpath = fixpath(unixpath, operatingsystem = 'win32')
    print("Unix in:", unixpath, "Windows out:", newpath)

    newpath = fixpath(windowspath, operatingsystem = 'linux2')
    print("Windows in:", windowspath, "Unix out:", newpath)

    return

# Notify the Supervisor of a catastrophic failure.  This can be used as a backup
# to RPC. This code can send Unix user defined signals SIGUSR1 or SIGUSR2.
#
# In the subprocess put signalFlare() at any critical points of the code such as
# where its RPC daemon is started, ini files are read, hardware resources are
# requested, directories and files are created, etc.  In other words, anywhere there
# is a failure immediate attention is mandatory.
#
# In the Supervisor add a signal handler after Supervisor's __init__ has finished.
#
#     signal.signal(signal.SIGUSR1, self.sigint_handler)
#     writeSupervisorPidFile()
#
#     def sigint_handler(self. signum, frame):
#         if signum == signal.SIGUSR1:
#             ...take emergency action...
#         if signum == signal.SIGUSR2:
#             ...take other actions...
#
#
# writeSupervisorPidFile() saves the current Supervisor PID to a file so that any
# subprocess can send a signal to the right destination.  The default action is to
# write the PID to ~/supervisor.pid.
#
# writeSupervisorPidFile() doesn't grant an exclusive lock so if Supervisor is
# accidentally started twice the second instance will overwrite the PID of the first.
# 
# writeSupervisorPidFile() doesn't delete the file when Supervisor is gracefully or
# abruptly killed.
#
def signalFlare(userSignal = 1):
    supervisorPID = getSupervisorPid()
    if userSignal == 1:
        print("Sending SIGUSR1 to Supervisor:", supervisorPID)
        os.kill(supervisorPID, signal.SIGUSR1)
    else:
        print("Sending SIGUSR2 to Supervisor:", supervisorPID)
        os.kill(supervisorPID, signal.SIGUSR2)

def writeSupervisorPidFile(pidFileName = 'supervisor.pid', pidFilePath = None):
    if pidFilePath == None:
        pidFilePath = os.path.expanduser('~')
    pid = str(os.getpid())
    f = open(os.path.join(pidFilePath, pidFileName), 'w')
    f.write(pid)
    f.close()

def getSupervisorPid(pidFileName = 'supervisor.pid', pidFilePath = None):
    if pidFilePath == None:
        pidFilePath = os.path.expanduser('~')
    f = open(os.path.join(pidFilePath, pidFileName), 'r')
    pidStr = f.readline()
    f.close()
    return int(pidStr)

def makeDirs(path):
    """
    Recursively make directories as needed.
    """
    # If the directory already exists the code will thrown
    # a EEXIST error.  See the Python errno module and
    # the "errno" Linux man page.  We ignore this exception
    # and throw anything else up to the parent.
    #
    # This idiom is discussed at
    # https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist/14364249#14364249
    # http://deepix.github.io/2017/02/02/eexists.html
    #
    # The permission 0775 is explicity set to avoid the Archiver problem where on Linux systems
    # it would create RDF destination directories as read only if makedirs() was called with the default
    # permissions.
    #
    try:
        os.makedirs(path,0775)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
    return


if __name__ == '__main__':
    __path_test()
