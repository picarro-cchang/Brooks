#!/usr/bin/python
#
"""
File Name: Supervisor.py
Purpose:
    This application performs the following functions:
      1. It Sequences the execution of all of the application in the CRD host
         software
      2. It supervises all launched applications after they are running.  If a
         launched application stops responding, this application will restart
         the app (and any other relevant apps) appropriately.

File History:
    05-09-28 russ  Created first release
    05-10-13 russ  Added a small sleep to monitoring to reduce (by a lot) the processor overhead
    05-10-18 russ  Added ConsoleMode to solve child process closing issues; Added clean
                   ctrl-q/ctrl-x exit code to monitoring loop; Added option checking
    05-11-09 russ  Changed timeout behavior to be more robust (removed usage of setdefaulttimeout)
    05-11-22 russ  Added Backup mode; Added an rpc server; Default times now 30s; Improved INI
                   error checking; Added ctrl-t and revamped kb handling; Improved and expanded
                   command-line options; Many other misc updates
    05-12-13 russ  Added -o switch; backup killed with --nm; Changed App.IsAlive functionality
    05-12-21 russ  Mode 3 (non-pingable yet monitored) apps and RPC via basic TCP; Restart
                   notification; TerminateApplications RPC call
    06-02-06 russ  Ping dispatcher timeout now configurable with a default of 10s (from 5s)
    06-03-28 russ  Changed/improved log calls to work with new Event Manager; Added GlobalSettings
                   option to configuration ini; Faster (threaded) app search at start; LaunchApps
                   sequence is improved to be in proper order only; Backup Supervisor kicked more
                   often; Changed default ini to PicarroPyConfig.INI
    06-04-04 russ  Fixed path referencing for App.Executable definitions
    06-04-18 russ  Fixed TerminateApplications bug (crashed when called)
    06-05-20 russ  Updated/improved event logging; Updated SharedTypes referencing
    06-06-20 russ  Ensure app is terminated when app launch fails; Logs made on ctrl-X or ctrl-T
    06-09-13 russ  Last chance exception handler; Updated Log calls
    06-10-17 sze   Get "PicarroSupervisor" mutex for benefit of installer
    06-12-11 Al    Added call to INSTMGR_ReportRestartRpc whenever an app is restarted.
    06-12-22 Al    Check that app is OK before adding it to list which is sent to INSTMGR_ReportRestartRpc
    07-03-16 sze   Allow supervisor to power off windows after terminating applications
    07-09-22 sze   Added AffinityMask attribute to App to allow process to be scheduled on specific CPUs
    08-02-20 sze   Modified GetDependents so that it computes transitive dependencies. i.e, if A depends on B which depends
                   on C, it identifies A as being dependent on C.
    08-04-30 sze   Change default on TerminateApplications so that it does not power off the computer
    08-07-07 sze   Include TerminateProcessByName which uses taskkill (on Windows) to stop processes forcibly. Apps have a
                   KillByName attribute in the INI file which selects whether existing instances of the app should be terminated
                   by name before a new copy is started. This is True by default
    08-07-23 sze   Do not use TerminateProcessByName on the backup supervisor, as this prematurely kills the real supervisor
    08-09-16 alex  Replaced ConfigParser by CustomConfigObj
                   Re-formatted supervisor ini file so it doesn't contain application indices and total number of applications -> easier to add or remove applications on the list
    08-10-08 alex  Re-ordered applications to be launched
    10-10-07 sze   Start the RPC server at once, so that we can terminate a misbehaving stack while it is loading
    11-06-24 alex  When ShutDownAll() is called, all the app names specified in SpecialKilledByNameList will be killed by name

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import sys
import ctypes
import ttyLinux
import signal # to handle SIGTERM
libc = ctypes.CDLL("libc.so.6")
sched_getaffinity = libc.sched_getaffinity
sched_setaffinity = libc.sched_setaffinity
setpriority = libc.setpriority
import os
import shlex
import time
import getopt
import threading
import Queue
import traceback
import SocketServer #for Mode 3 apps
import psutil
from os import spawnv
from os import P_NOWAIT
from os import getpid as os_getpid
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# If we are using python 2.x on Linux, use the subprocess32
# module which has many bug fixes and can prevent
# subprocess deadlocks.
#
if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess
from subprocess import Popen, call

from Host.Common import CmdFIFO
from Host.Common.SharedTypes import ACCESS_PICARRO_ONLY, RPC_PORT_LOGGER, RPC_PORT_RESTART_SUPERVISOR
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR, RPC_PORT_SUPERVISOR_BACKUP, RPC_PORT_CONTAINER
from Host.Common.SharedTypes import CrdsException
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SingleInstance import SingleInstance

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)


from time import time as TimeStamp

#Global constants...
APP_NAME = "Supervisor"
MAX_LAUNCH_COUNT = 1
DEFAULT_BACKUP_MAX_WAIT_TIME_s = 180
BACKUP_CHECK_INTERVAL_s = 1
_MAIN_SECTION = "Applications"
_DEFAULT_CONFIG_NAME = "PicarroPyConfig.INI"
_DEFAULT_PING_DISPATCHER_TIMEOUT_ms = 10000
_DEFAULT_KILL_WAIT_TIME_s = 2
_DEFAULT_PROCESS_KILL_WAIT_TIME_s = 5
_METHOD_STOPFIRST    = 1
_METHOD_KILLFIRST    = 2
_METHOD_DESTROYFIRST = 3

RPC_SERVER_PORT_MASTER = RPC_PORT_SUPERVISOR
RPC_SERVER_PORT_BACKUP = RPC_PORT_SUPERVISOR_BACKUP
_MODE3_TCP_SERVER_PORT = 23456

CONSOLE_MODE_OWN_WINDOW    = 1
CONSOLE_MODE_NO_WINDOW     = 2
CONSOLE_MODE_SHARED_WINDOW = 3 #can't get this to function.  spawnv does it, but the apps are slave to the parent: if the parent dies so do they (when they try to write to a non-existent console).

if sys.platform == "linux2":
    _PRIORITY_LOOKUP = {
        "1" : 10,
        "2" : 5,
        "3" : 0,
        "4" : -5,
        "5" : -10,
        "6" : -15
    }

# Protected applications (not shut down on normal termination)
# Lets never close SLQLiteServer also on host app quit as other application uses it
# even though hist is not running for example qtLauncher
PROTECTED_APPS = ["Driver", "SQLiteServer"]

# Only the below apps are allowed to run in the virtual mode
APPS_IN_VIRTUAL_MODE = ("EventManager", "Archiver", "DataManager", "InstMgr", "rdReprocessor", "QuickGui", "DataLogger", \
                        "BackupSupervisor", "RDFreqConverter", "AlarmSystem", "Fitter", "Fitter1", "Fitter2", "Fitter3")

#set up the main logger connection...
CRDS_EventLogger = CmdFIFO.CmdFIFOServerProxy(\
    uri = "http://localhost:%d" % RPC_PORT_LOGGER,\
    ClientName = APP_NAME, IsDontCareConnection = True)

def Log(Desc, Data = None, Level = 1, Code = -1, AccessLevel = ACCESS_PICARRO_ONLY, Verbose = "", SourceTime = 0):
    """Short global log function that sends a log to the EventLogger
    """
    if __debug__:
        if Level >= 2:
            print "*** LOGEVENT (%d) = %s; Data = %r" % (Level, Desc, Data)
    CRDS_EventLogger.LogEvent(Desc, Data, Level, Code, AccessLevel, Verbose, SourceTime)

class AppErr(CrdsException):
    "Exception raised by App object.  Base of all App errors."

class AppSocketTimeout(AppErr):
    "Socket timeout reached when connecting to application."

class AppConnectionRefused(AppErr):
    "Connection refused when attempting connection to rpc server (no listener!)."

class AppInvincable(AppErr):
    "Application cannot be terminated even with system termination calls."

class AppLaunchFailure(AppErr):
    "An application launch attempt failed for some reason."

class AppOptionErr(AppErr):
    "There is a problem with one (more more) of the configured App options."

class TerminationRequest(CrdsException):
    "Terminate all applications requested"

class IniVerifyErr(CrdsException):
    "There was a problem when iniCoordinator tried to verify .ini configuration files for all applications."

def Print(s, SuppressLineFeed = False):
    """Prints s to stdout, but only if in debug mode.
    """
    if __debug__:
        Log("PRINTED - %s" % (s,), 0)
        if SuppressLineFeed:
            print s,
        else:
            print s

def PrepareBackupAndWaitForAction(WDTWaitTime_s):
    """
    If in backup mode we just sit idly as the backup until it is determined that
    we need to take over. Then the backup becomes the supervisor.

    All of this logic is handled in this routine.

    Returns True when the backup server should take over.
    Returns False when the backup was legitimately shut down and no takeover is
    needed.
    """

    rpcPort = RPC_SERVER_PORT_BACKUP
    #Set up the RPC Server for the backup mode...
    rpcServer = BackupSupervisorRPCServer(
        addr       = ("",rpcPort),
        ServerName = "Backup_Supervisor",
        ServerDescription = "The rpc server for a Supervisor running in backup mode.")
    rpcServer.BackupWDTWaitTime = WDTWaitTime_s
    rpcServer.serve_forever()

    #we got out for one of a few reasons:
    #   - A StopServer request
    #   - A KillServer request
    #   - The backup WDT expired and we need to act as the backup!
    #The stop/kill requests were made on the backup so we should just fall
    #through and die.  If the WDT expired, we need to take over...
    if rpcServer.BackupWDTExpired:
        #There was a problem with the master and the backup (the active instance)
        #needs to take over.

        #First - we need to be sure the old master is completely gone.
        #Second - we need to take over.

        #Destroy the master (do NOT do a StopServer since this is the legitimate
        #shutdown technique which also shuts the backup down - just be nasty
        #right away).
        rpcServer.MasterApp.ShutDown(_METHOD_KILLFIRST)
        #we don't need the backup's rpc server anymore (and we want the socket
        #free for the new backup we'll be launching)...
        del rpcServer
        Log("Backup Supervisor taking over (Backup RPC server destroyed)", Level = 3)
        return True
    return False

def prompt_wait(msg=""):
    try:
        start_rawkb()
        print msg,
        while read_rawkb() == "":
            time.sleep(0.05)
    finally:
        stop_rawkb()


if sys.platform == "linux2":
    def start_rawkb():
        ttyLinux.setSpecial()

    def stop_rawkb():
        ttyLinux.setNormal()

    def read_rawkb():
        return ttyLinux.readLookAhead()

    def launchProcess(appName,exeName,exeArgs,priority,consoleMode,affinity,cwd):
        #launch the process...
        Log("Launching application", dict(appName=appName), 1)
        argList = [exeName]
        for arg in exeArgs[1:]:
            argList += shlex.split(arg)
        try:
            # There seems to be some strange interaction between Pyro4, threading,
            # Popen, and rpdb2 causing a race condition where process creation sometimes
            # locks up the code.  A tip on StackOverflow (can't find the link)
            # said sleep() before each Popen made the problem go away.
            #
            time.sleep(1.0)
            if consoleMode == CONSOLE_MODE_NO_WINDOW:
                process = Popen(argList,stderr=file('/dev/null','w'),stdout=file('/dev/null','w'),cwd=cwd)
            elif consoleMode == CONSOLE_MODE_OWN_WINDOW:
                termList = ["xterm","-hold","-T",appName,"-e"]
                process = Popen(termList+argList,bufsize=-1,stderr=file('/dev/null','w'),stdout=file('/dev/null','w'),cwd=cwd)
        except OSError:
            Log("Cannot launch application", dict(appName=appName), 2)
            raise
        except ValueError:
            Log("Parameter error while launching application", dict(appName=appName), 2)
            raise
        except Exception as e:
            Log("Caught exception in launchProcess:",e)
            raise e

        # Set the affinity
        pAffinity = ctypes.c_int64()
        sAffinity = ctypes.c_int64()
        if sched_getaffinity(process.pid,ctypes.sizeof(sAffinity),ctypes.byref(sAffinity)) == 0:
            mask = sAffinity.value & eval(affinity)
            if mask == 0: mask = sAffinity.value
            mask = ctypes.c_int32(mask)
            if sched_setaffinity(process.pid,ctypes.sizeof(mask),ctypes.byref(mask)) != 0:
                Log("Unable to set affinity for application", dict(appName=appName), 2)
            else:
                sched_getaffinity(process.pid,ctypes.sizeof(pAffinity),ctypes.byref(pAffinity))
        else:
            Log("Cannot get affinity for application", dict(appName=appName), 2)
        # Set the scheduling priority
        setpriority(0,process.pid,_PRIORITY_LOOKUP[priority])
        return process.pid,process,pAffinity.value

    def isProcessActive(processHandle):
        """Checks to see if the application is running.
        If it can't be determined whether the app is alive or not, this assumes False.
        """
        if isinstance(processHandle, Popen):
            result = processHandle.poll()
            if result == None:
                return True
        elif isinstance(processHandle, int):
            return psutil.pid_exists(processHandle)
        else:
            return psutil.pid_exists(processHandle.pid)

    def terminateProcess(processHandle):
        print "Calling terminateProcess on process %s" % (processHandle.pid,)
        # print("TerminateProcess disabled") # RSF
        os.kill(processHandle.pid, 15) # Don't kill for debug RSF

    def terminateProcessByName(name):
        [path,filename] = os.path.split(name)
        [base,ext] = os.path.splitext(filename)
        Log("Terminating process %s using pkill" % base)
        call(["pkill", "-f", base],stderr=file("NUL","w"))

    def getProcessHandle(pid):
        class ProcessHandle(object):
            def __init__(self,pid):
                self.pid = pid
        return ProcessHandle(pid)

class TcpRequestHandler(SocketServer.BaseRequestHandler):
    """Class to deal with incoming TCP requests from mode 3 applications.

    This derived class is an implementation of how to use the SocketServer.TCPServer
    implementation.
    """
    def handle(self):
        rxBuf = ""
        terminatorLoc = -1
        response = ""
        appName = ""
        while 1:
            rxBuf += self.request.recv(1024)
            if not rxBuf:
                #Print("No data received!?")
                break
            #strip out any chr(10)'s in case someone is sending CR+LF...
            rxBuf.replace(chr(10),"")
            terminatorLoc = rxBuf.find(chr(13))
            if terminatorLoc >= 0:
                #we have a message
                msg = ""
                msg = rxBuf[:terminatorLoc]
                rxBuf = rxBuf[terminatorLoc + 2:]
                splitMsg = msg.split(":")
                #should be in the form: 'AppName:Command'
                if len(splitMsg) > 2:
                    response = "Incorrect syntax for message '%s'" % (msg,)
                else:
                    appName = splitMsg[0]
                    if len(splitMsg) == 2:
                        command = splitMsg[1]
                    if not appName in self.server.AppDict:
                        response = "App name '%s' not recognized." % (appName, )
                    elif not command: #no command specified, so it is watchdog kick
                        if not self.server.AppDict[appName].Mode == 3:
                            response = "Specified App ('%s') is not running in mode 3." % (appName, )
                        else:
                            self.server.AppDict[appName]._RemotePingCount += 1
                            response = "OK"
                    else:
                        #execute the command...
                        if command == "TerminateApplications":
                            Log("TCP TerminateApplications request received", Data = appName)
                            self.server.ParentSupervisor.RPC_TerminateApplications()
                            ret = "OK"
                        elif command == "RestartApplications":
                            Log("TCP RestartApplications request received", Data=appName)
                            self.server.ParentSupervisor.RPC_RestartApplications()
                            ret = "OK"
                        else:
                            response = "Command '%s' is not recognized" % (command,)
                response += chr(13)
                self.request.send(response)
                #print "msg = ", [repr(c) for c in msg]

class SupervisorTcpServer(SocketServer.ThreadingTCPServer):
    """Simple server for accepting incoming TCP requests from Mode 3 applications.

    Derivation done primarily to avoid late-binding of the Supervisor that needs
    to be dealt with.  Deriving lets the variable be explicitly defined to be
    clear what is going on (could have just bound it anyway but it is more
    confusing).
    """
    def __init__(self, server_address, RequestHandlerClass, SupervisorParent):
        self.ParentSupervisor = SupervisorParent
        assert isinstance(self.ParentSupervisor, Supervisor)
        self.AppDict = {}
        self.AppDict = self.ParentSupervisor.AppDict
        assert RequestHandlerClass.__name__ == "TcpRequestHandler"
        SocketServer.ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)
class App(object):
    def __init__(self, AppName, Parent, DefaultSettings = None):
        """DefaultSettings is optionally a dictionary containing default App options."""
        #set property names and defaults (all attributes without a _ prefix can be
        #set via a named option in the ini file (in the section with the right
        #AppName)
        #  - keep it like this because then it is REALLY easy to add
        #    variables to the ini file

        self._AppName = AppName
        self.Executable = self._AppName + ".py"
        self.LaunchArgs = ""
        self.RestartArgs = ""
        self.Dependencies = ""
        self.Priority = "4"
        self.AffinityMask = "0xFFFFFFFF"
        self.MaxWait_ms = 30000
        self.Mode = 1
        self.Port = -1
        self.CheckInterval_ms = 2000
        self.VerifyTimeout_ms = 30000
        self.DispatcherTimeout_ms = _DEFAULT_PING_DISPATCHER_TIMEOUT_ms
        self.ConsoleMode = CONSOLE_MODE_OWN_WINDOW
        self.NotifyOnRestart = False
        self.KillByName = True
        self.ShowDispatcherWarning = 1

        # If an app fails to launch, set this variable to point to a script to run.
        # This was created to handle the unusual case where the Drive won't load
        # due to a USB communication error and the only recourse is to do a hard reset.
        self.ResetScript = ""

        # DebugMode == False runs interpreted python code with the -OO option.
        # DebugMode == True runs without -OO and sets __debug__.  In some codes
        #               this will load the rpdb2 debugger so the code can be run
        #               in winpdb.
        # DebugMode can be set for individual processes in supervisor.ini. It
        # can be set globally in [GlobalDefaults] in supervisor.ini. If the key
        # is missing debug mode is off.
        #
        self.DebugMode = False

        #now override any defaults with the passed in dictionary values...
        if DefaultSettings:
            assert isinstance(DefaultSettings, dict)
            for k in DefaultSettings.keys():
                setattr(self, k, DefaultSettings[k])

        self._SearchComplete = threading.Event()
        self._ProcessHandle = -1
        self._ProcessId = -1
        self._ServerProxy = None
        self._LastCheckTime = 0
        self._LaunchTime = 0
        self._StartedOk = False
        self._LaunchFailureCount = 0
        self._HasCmdFIFO = False
        self._RemotePingCount = 0 #for use with mode 3 apps (that ping the supervisor instead of vice versa)

        self._Stat_LaunchCount = 0
        self._Stat_FIFOResponseTime = -1
        self._Stat_DispatcherResponseTime = -1

        self._Parent = Parent
        if 0: assert isinstance(self._Parent, Supervisor) #for Wing


    def __str__(self):
        return self._AppName

    def __repr__(self):
        return "<class App: '%s' Mode = %s  Port = %s PID = %s>" % (self, self.Mode, self.Port, self._ProcessId)

    def ReadAppOptions(self, CO):
        """Reads the options from the appropriate section in the ini file.

        CO should be a CustomConfigObj pointed at the ini file.

        On success, the App (self) options will be set to the values in the ini file.
        In addition, the function returns a dictionary containing all of the loaded
        options and values.
        """
        assert isinstance(CO, CustomConfigObj)
        #First check if there are any illegal/unrecognized options in the file...
        settableOptions = [o for o in self.__dict__.keys() if not (o.startswith("_") or callable(self.__getattribute__(o)))]
        lcaseSettableOptions = []
        for o in settableOptions:
            lcaseSettableOptions.append(o.lower())
        for o in CO.list_options(self._AppName):
            if not o.lower() in lcaseSettableOptions:
                raise AppOptionErr("Option '%s' found in section '%s' is not a supported option." % (o, self._AppName))
                raise "Option '%s' found in section '%s' is not a supported option." % (o, self._AppName)
        #Now try and retrieve the options we care about (do it by looking for options
        #rather than checking the now-known-good options so that we can preserve
        #case in the code and be case-insensitive in the file)...
        loadedOptions = {}
        for optionName in settableOptions:
            try:
                option = CO.get(self._AppName, optionName)
                if isinstance(self.__getattribute__(optionName), bool):
                    option = bool(option)
                elif isinstance(self.__getattribute__(optionName), int):
                    option = int(option)
                self.__setattr__(optionName, option)
                #add it to the dictionary we're using to keep track of what was loaded...
                loadedOptions[optionName] = option
            except KeyError:
                pass

        #put Executable path correction here (and fix the other Executable path corrections with AppPath)
        if self.Mode == 0:
            #It is a backup supervisor...
            appOptions = CO.list_options(self._AppName)
            if len(appOptions) != 1:
                raise AppOptionErr("The backup supervisor application ('%s' with Mode == 0) only accepts a 'Mode' option.  Other options have been specified: %r" % (self._AppName, appOptions))
            self.Port = RPC_SERVER_PORT_BACKUP
            self.Executable = os.path.basename(AppPath)
            #The -t switch will never actually be different, it is ONLY there for debugging purposes
            #where I can change the value to what I want from the command line.
            self.LaunchArgs = "-c%s -t%f --backup" % (self._Parent.FileName, DEFAULT_BACKUP_MAX_WAIT_TIME_s)
        if str(self.Priority) not in _PRIORITY_LOOKUP.keys():
            raise AppOptionErr("Priority level specified for app '%s' is not valid.  Priority = '%s'." % (self._AppName, self.Priority))
        if self.ConsoleMode not in [CONSOLE_MODE_NO_WINDOW, CONSOLE_MODE_OWN_WINDOW]:
            raise AppOptionErr("Console mode specified for app '%s' is not valid.  Mode = '%s'." % (self._AppName, self.ConsoleMode))
        if self.MaxWait_ms > self.VerifyTimeout_ms:
            raise AppOptionErr("The VerifyTimeout_ms specified for app '%s' is not valid.  It cannot be < MaxWaitTime_ms (%s < %s)" % (self._AppName, self.VerifyTimeout_ms, self.MaxWait_ms))

        #Now that we're loaded, for many things we'll need an rpc connection.  Although the app
        #does not necessarily exist yet, it should (can still be) be set up now...
        if self.Port > 0:
            proxyURL = "http://localhost:%s" % (self.Port,)
            self._ServerProxy = CmdFIFO.CmdFIFOServerProxy( \
                uri = proxyURL, \
                ClientName = APP_NAME, \
                CallbackURI = "", \
                Timeout_s = self.MaxWait_ms/100)
        if self.Mode in [0,1,4]:
            self._HasCmdFIFO = True
        return loadedOptions

    def Launch(self, supervisor, IsRestart = False):
        """Launches the app and does other setup.

        If self.VerifyTimeout_ms is > 0 the routine will wait for the application
        to be up and running (serving rpc requests) before exiting.
        """
        assert(isinstance(supervisor,Supervisor))

        exeArgs = []
        root, ext = os.path.splitext(self.Executable)

        launchArgs = self.LaunchArgs
        if self.NotifyOnRestart and IsRestart:
            if launchArgs != "":
                launchArgs += " "
            launchArgs += "--restarted"

        if ext in [".py", ".pyc", ".pyo"]:
            # Set the python interpreter to use if we are running a
            # *.py or *.pyc.  If the optimize flag is set (i.e. python -O Supervisor.py)
            # use the optimize flag on the subprocesses.
            exeName = sys.executable
            exeArgs.append(exeName) #first arg must be the appname as in sys.argv[0]
            #if sys.flags.optimize:
            #    if not self.DebugMode:
            #        exeArgs.append("-OO")
            if not self.DebugMode and sys.flags.optimize:
                exeArgs.append("-OO")
            if os.path.isabs(self.Executable):
                launchPath = "%s" % (self.Executable,)
            else:
                #The path will be relative to the location of the supervisor app...
                launchPath = os.path.join(os.path.dirname(AppPath), self.Executable)
            launchPath = os.path.normpath(launchPath)
            exeArgs.append(launchPath)
            exeArgs.append(launchArgs)
        else:
            # Make sure the (non-supervisor) process does not currently exist
            if self.KillByName and self.Executable.lower().find("supervisor") < 0:
                # print "Calling terminateProcessByName %s" % self.Executable
                terminateProcessByName(self.Executable)
            #
            if os.path.isabs(self.Executable):
                exeName = "%s" % (self.Executable,)
            else:
                #The path will be relative to the location of the supervisor app...
                exeName = os.path.join(os.path.dirname(AppPath), self.Executable)
            exeName = os.path.normpath(exeName)
            exeArgs.append(exeName) #first arg must be the appname as in sys.argv[0]
            exeArgs.append(launchArgs)

        appStarted = False

        if supervisor.CheckForStopRequests():
            raise TerminationRequest

        r = launchProcess(self._AppName,exeName,exeArgs,self.Priority,self.ConsoleMode,self.AffinityMask,os.path.dirname(AppPath))
        self._ProcessId, self._ProcessHandle, pAffinity = r

        #self._ProcessHandle = hProcess.handle
        print "%s %-20s, port = %5s, pid = %4s, aff = %s" % (time.strftime("%d-%b-%y %H:%M:%S"),"'%s'" % self._AppName, self.Port, self._ProcessId, pAffinity)

        Log("Application started", Data = dict(App = self._AppName,
                                               Port = self.Port,
                                               PID = self._ProcessId,
                                               Affinity = pAffinity))
        self._Stat_LaunchCount += 1 #we're tracking launch attempts, not successful launches


        if self.VerifyTimeout_ms > 0 and self.Port > 0: # and self.Mode in [0,1,4]:
            #mode 1 & 4 = normal apps to be monitored
            #mode 0 = a unique mode for the backup supervisor app
            #we're supposed to verify that the application started successfully.  We'll do so with a FIFO ping..
            startTime = TimeStamp()
            appStarted = False
            while (TimeStamp() - startTime) < (self.VerifyTimeout_ms/1000.):
                if supervisor.CheckForStopRequests():
                    raise TerminationRequest
                try:
                    self.CheckFIFO() #should be quick since the Rx timeout is only when the dispatcher has responded, and if it has the Ping should work fine.
                    #only gets here if the FIFO responded
                    appStarted = True
                    Log("Application start confirmed", self._AppName, Level = 1)
                    break
                except AppErr, E:
                    #Just sucking it up since we're waiting for the app to start and we do expect errors.
                    #Log("Trapped Exception","%s %r" % (E,E), 0)
                    pass
                time.sleep(0.5)
        else:
            #Not verifying, so assume it did start...
            appStarted = True

        if appStarted and self.Mode == 0:
            #It is a backup supervisor.  We need to let it know our (we're the master right now) process ID...
            self._ServerProxy.SetMasterProcessID(os_getpid())

        if appStarted:
            self._StartedOk = True
            self._LaunchFailureCount = 0
        else:
            self._LaunchFailureCount += 1
            #Make sure that the application is completely gone...
            self.LaunchFailureHandler()
            self.ShutDown(_METHOD_DESTROYFIRST)
            raise AppLaunchFailure("Application '%s' did not start within specified timeframe of %s ms." % (self._AppName, self.VerifyTimeout_ms))
        self._LaunchTime = TimeStamp()

    def IsProcessActive(self):
        return isProcessActive(self._ProcessHandle)

    def LaunchFailureHandler(self):
        """
        If an app fails to start, run some external program before attempting to start the app again.
        """
        # The original intent here is to call a script that will power cycle the analyzer and start over
        # instead trying to restart a single app.  We did this because we are getting USB errors and
        # can't load the Driver.  The only solution that works is to reboot.
        # The script to run is set with the 'ResetScript' option in the supervisor ini file.  The
        # script can be set globally so that any app failure will trigger running the script, or 
        # 'ResetScript' can be defined for individual processes so that the event is triggered only
        # for critical subsystems, like the Driver.  If you set it for individual processes you can
        # create different handlers.
        #
        if len(self.ResetScript):
            Log("Application won't start... rebooting NOW", self._AppName, Level = 3)
            print("running:", self.ResetScript.split())
            subprocess.Popen(self.ResetScript.split())
        return

    def ShutDown(self, StopMethod = _METHOD_STOPFIRST, StopWaitTime_s = -1, KillWaitTime_s = -1, NoKillByName = False,
                       NoWait = False):
        """Shuts down the application.  If NoWait is True, return immediately after performing StopMethod.
           If NoWait is False, keep escalating severity of kill method so that the application WILL be dead by the
           end of call.
        """
        #See if our work is already done somehow... if so we just get out...
        if not self.IsProcessActive():
            if self.ShowDispatcherWarning:
                Log("App shutdown attempted, but app already closed", self._AppName, 2)
            return

        #Now sort out our args...
        if StopWaitTime_s == -1:
            #Wait for the same time we would wait for the application to respond to a FIFO ping...
            StopWaitTime_s = self.MaxWait_ms / 1000.
        if KillWaitTime_s == -1:
            KillWaitTime_s = _DEFAULT_KILL_WAIT_TIME_s

        #Now get to our multi-tier shtdown attempts

        appLives = True #start with this assumption

        msg = ""

        #First - the weakest shutdown is a simple StopServer request...
        if appLives and self._HasCmdFIFO and StopMethod not in [_METHOD_KILLFIRST, _METHOD_DESTROYFIRST]:
            Log("Stopping application",self._AppName, 2)
            startTime = TimeStamp()
            #Politely request a shutdown...
            try:
                self._ServerProxy.CmdFIFO.StopServer()
                if NoWait: return
                #Wait for it to disappear...
                while (TimeStamp() - startTime) < StopWaitTime_s:
                    time.sleep(0.05) #without this we pin the processor while we poll
                    if not self.IsProcessActive():
                        appLives = False
                        break
            except Exception, E:
                Log("Exception raised during StopServer attempt", str(self), Verbose = "Exception = %r %s" % (E,E))
                if NoWait: return
                #assume that it still lives to be safe.

        #Second - a KillServer request is a bit more rough...
        if appLives and self._HasCmdFIFO and StopMethod not in [_METHOD_DESTROYFIRST]:
            if StopMethod in [_METHOD_STOPFIRST]:
                Log("Application Stop attempt failed", str(self), 2)
            Log("Killing application", str(self), 2)
            startTime = TimeStamp()
            #Request instant seppuku...
            try:
                self._ServerProxy.CmdFIFO.KillServer('please')
                if NoWait: return
                #Wait for it to disappear...
                while (TimeStamp() - startTime) < KillWaitTime_s:
                    if not self.IsProcessActive():
                        appLives = False
                        break
            except Exception, E:
                Log("Exception raised during KillServer attempt", str(self), Verbose = "Exception = %r %s" % (E,E))
                if NoWait: return
                #assume that it still lives to be safe.

        #Third - if the app is not responding, now we brutally axe it with a system call...
        if appLives:
            if StopMethod in [_METHOD_STOPFIRST, _METHOD_KILLFIRST] and self._HasCmdFIFO:
                Log("Application Kill attempt failed", str(self), 2)
            Log("Terminating application", str(self), 2)
            startTime = TimeStamp()
            #Smite with extreme prejudice (and a nice meaningless but identifiable error code of 42)...
            try:
                terminateProcess(self._ProcessHandle)
                if NoWait: return
                #Wait for it to disappear...
                while (TimeStamp() - startTime) < _DEFAULT_PROCESS_KILL_WAIT_TIME_s:
                    if not self.IsProcessActive():
                        appLives = False
                        break
            except Exception, E:
                #It is possible we tried to destroy a process that is already gone - so check...
                if NoWait: return
                if self.IsProcessActive():
                    Log("Exception raised during TerminateProcess attempt", str(self), Verbose = "Exception = %r %s" % (E,E))
                    #app is still considered alive at this point
                else:
                    #'tis dead!
                    appLives = False

        # Try killing by process name as a last resort, if this option is selected
        if appLives and self.KillByName and not NoKillByName:
            print "Calling KillByName for application %s (appLives = %s)" % (self.Executable,appLives)
            terminateProcessByName(self.Executable)
            if NoWait: return

        if appLives: #shouldn't be possible by here!
            #the #$@#$!!! operating system can't even kill it... we're screwed.
            Log("Unable to terminate application", self._AppName, 3)
            ## raise AppInvincable("Fatal error.  Unable to terminate application '%s'." % (self._AppName,))

    def CheckDispatcher(self):
        """Checks the app to see that the dispatcher is functioning.

        Raises exception on failure.
        Return value is irrelevant on success (but it is True)
        """
        if self._ServerProxy == None:
            raise AppErr("No RPC server present - check configuration")
        waitTime = self._Parent.PingDispatcherTimeout_ms/1000.
        oldWaitTime = self._ServerProxy.GetTimeout()
        try:
            self._ServerProxy.SetTimeout(waitTime)
            responseTime = waitTime #assume a long time to start with
            startTime = TimeStamp()
            try:
                ret = self._ServerProxy.CmdFIFO.PingDispatcher()
                if ret == "Ping OK":
                    responseTime = TimeStamp() - startTime
                    self._Stat_DispatcherResponseTime = responseTime
                    return True
                else:
                    raise AppErr("Unexpected ping response after %.1fs from dispatcher. ('%s')" % (TimeStamp()-startTime,ret,))
            except CmdFIFO.TimeoutError:
                raise AppSocketTimeout("Ping to application dispatcher timed out after %.1fs." % (TimeStamp()-startTime,))
            except Exception, E:
                raise AppErr("Unexpected exception raised after %.1fs in call to dispatcher: %s" % (TimeStamp()-startTime,str(E),))
        finally:
            #be sure to restore the old rx timeout time...
            self._ServerProxy.SetTimeout(oldWaitTime)

    def CheckFIFO(self):
        """Checks the app to see that the FIFO is being serviced.

        Exception raised on failure.
        Returns True on success (although this isn't much help).

        This does NOT do any retries.  It just tells if the FIFO is currently working.
          - If there is no server, this will return quickly with a False.
          - If the dispatcher is working, this call will block for self.MaxWait_ms while
            it waits for the response that should be coming (this behaviour is handled by
            the special transport that has been set up)
        """
        responseTime = self.MaxWait_ms #assume a long time to start with (for stats purposes)
        startTime = TimeStamp()
        fifoOk = False
        try:
            ret = self._ServerProxy.CmdFIFO.PingFIFO()
            if ret == "Ping OK":
                fifoOk = True
                #calc some stats...
                responseTime = TimeStamp() - startTime
                self._Stat_FIFOResponseTime = responseTime
                return True
            else:
                raise AppErr("Unexpected ping response after %.1fs from FIFO handler." % (TimeStamp() - startTime,))
        except CmdFIFO.TimeoutError:
            raise AppSocketTimeout("Ping to FIFO queue timed out after %.1fs." % (TimeStamp() - startTime,))
        except Exception, E:
            raise AppErr("Unexpected exception after %.1f raised in FIFO ping attempt: %s" % (TimeStamp()-startTime,str(E),))

    def UpTime(self):
        """Returns the applications uptime since launch (in hrs).
        """
        return (TimeStamp() - self._LaunchTime)/60.

    def FindAndAttach(self):
        try:
            appExists = False
            #First do a quick check if it exists (on the off chance that we somehow have
            #a handle to it already)...
            if self._ProcessHandle != -1:
                appExists = self.IsProcessActive()
            if not appExists:
                #if we don't think it is alive there is still chance the handle was wrong, so
                #we'll check another way...
                if self.Port <= 0:
                    #No handle AND no port to check... we're out of luck. No port == no easy way to check!
                    #could try checking by process name I suppose... maybe later.  Could be risky, though.
                    #Value add of this?  Only if we have applications we launched that have no CmdFIFOServer
                    #and we didn't retain the process handle.
                    pass
                else:
                    #We have a port to check, so we'll check this way.
                    pid = -1
                    try:
                        self.CheckDispatcher()
                        #if we get here we got a response, so the app exists...
                        appExists = True
                    except AppErr, E:
                        #Exception thrown when checking for a dispatcher.  ie: no such app
                        #If there is no App, this is fine since it is what we were checking, so
                        #just indicate the app isn't there.
                        appExists = False
                    if appExists:
                        #Now to get a handle to it in case we need to terminate it with the OS...
                        try:
                            pid = int(self._ServerProxy.CmdFIFO.GetProcessID())
                            self._ProcessId = pid
                            #Need to set the process handle in order to enable use of all aspects of APP.ShutDown()...
                            self._ProcessHandle = getProcessHandle(pid)
                        except Exception, E:
                            if pid == -1: #we didn't get a pid to figure out who was listening :(
                                raise AppErr("Unable to determine pid for existing app '%s' on port '%s'. (in FindExistingApps) <%s %r>" % (self, self.Port, E, E))
                            else:
                                raise AppErr("Unexpected Exception when getting handle to existing app '%s' with process id '%s'." % (self, pid))
            if appExists:
                self._Parent.messageQueue.put("  %-20s has been found!  (pid = %s)" %("'%s'" % self, self._ProcessId))
                Log("Application found and attached to", self._AppName)
            else:
                self._Parent.messageQueue.put("  %-20s NOT found." % ("'%s'" % self,))
                Log("Application not found", self._AppName)
        finally:
            self._SearchComplete.set()

class WorkerThread(threading.Thread):
    """A simple Thread class that is daemonic and acquires a semaphore on run if needed.
    """
    def __init__(self, target, args = (), kwargs ={}, Semaphore = None):
        threading.Thread.__init__(self, target = target, args = args, kwargs = kwargs)
        self.setDaemon(1)
        assert isinstance(Semaphore, threading.Semaphore)
        self._semaphore = Semaphore
    def run(self):
        if self._semaphore:
            self._semaphore.acquire()
        threading.Thread.run(self)
        if self._semaphore:
            self._semaphore.release()
class Supervisor(object):
    def __init__(self, FileName, viFileName = ""):
        if not os.path.exists(FileName):
            raise Exception("File '%s' not found" % FileName)
        if len(viFileName) > 0: # viFileName contains information for rdReprocessor
            self.virtualMode = True
            if not os.path.exists(viFileName):
                raise Exception("File '%s' not found" % viFileName)
        else:
            self.virtualMode = False
        self.FileName = FileName
        co = CustomConfigObj(FileName)
        self.RPCServer = None
        if 0: assert isinstance(self.RPCServer, CmdFIFO.CmdFIFOServer) #For Wing
        self.RPCServerProblem = False
        self.restartSurveyor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_RESTART_SUPERVISOR, APP_NAME, IsDontCareConnection=False)
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR, APP_NAME, IsDontCareConnection=False)
        self.AppMonitorCount = 0
        self.AppNameList = [] #keeps the app ordering intact
        self.AppDict = {}
        self.PrintMessages = True
        self._ShutdownRequested = False
        self._TerminateAllRequested = False
        self._TerminateProtected = False
        self.BackupExists = False
        self.BackupApp = None
        self.Mode3Exists = False
        self._TcpServer = None
        self._TcpServerThread = None
        self.powerDownAfterTermination = False
        self.appList = None
        self.messageQueue = Queue.Queue(100)

        # Linux helper:
        # If there is no tty to use ^T, terminate Supervisor and its
        # subprocesses with 'kill -USR1 <supervisor_pid>
        if sys.platform == "linux2":
            signal.signal(signal.SIGUSR1, self.sigint_handler)
            # initialize utility for shutting down container
            def getHostIp():
                """Within a docker container, get the IP of the host (for bridge networking)"""
                for line in subprocess.check_output(["netstat", "-nr"]).split("\n"):
                    if line.startswith('0.0.0.0'):
                        return line.split()[1]

            hostIp = getHostIp()
            self.ContainerServer = CmdFIFO.CmdFIFOServerProxy(
                "http://%s:%d" % (hostIp, RPC_PORT_CONTAINER),
                "Container Client", IsDontCareConnection=False)
        print("Supervisor PID:", os.getpid())

        # start to use CustomConfigObj
        try:
            self.PingDispatcherTimeout_ms = co.getint("GlobalDefaults", "DispatcherTimeout_ms")
        except KeyError:
            self.PingDispatcherTimeout_ms = _DEFAULT_PING_DISPATCHER_TIMEOUT_ms

        try:
            self.SpecialKilledByNameList = [c.strip() for c in co.get("SpecialKilledByNameList", "List").split(",")]
        except:
            self.SpecialKilledByNameList = []

        #Read any global defaults that are to be applied..
        defaultSettings = None
        if co.has_section("GlobalDefaults"):
            bogusApp = App("GlobalDefaults", self)
            defaultSettings = bogusApp.ReadAppOptions(co)
            del bogusApp

        # Splash screen settings. Default is not to show one for legacy systems.
        # splashEnable : If true show the splash screen.
        # splashPicture : Full pathname to the splash screen image (gif,jpg,png).
        # splashShowProcessNames : If true show the name of each process as they start. If false show dots or
        #    progress counter.
        #
        self.splashEnable = False
        self.splashImage = None
        self.splashTitle = "Picarro Inc."
        self.splashFontColor = "white"
        self.splashShowProcessNames = False
        if co.has_section("SplashScreen"):
            self.splashEnable = co.getboolean("SplashScreen","Enable")
            self.splashImage = co.get("SplashScreen","Image")
            self.splashTitle = co.get("SplashScreen","Title")
            self.splashFontColor = co.get("SplashScreen","FontColor")

        #Cruise through the application names (and port shortcut values)...
        for appInfo in co[_MAIN_SECTION].items():
            appName = appInfo[0]
            if self.virtualMode:
                if appName not in APPS_IN_VIRTUAL_MODE:
                    continue
            appPort = appInfo[1].strip()
            self.AppNameList.append(appName)
            #generate the defaults for the app...
            self.AppDict[appName] = App(appName, self, defaultSettings)
            assert isinstance(self.AppDict[appName], App) #for Wing
            if appPort != "":
                self.AppDict[appName].Port = int(appPort)

        #Now read the options for each listed app from the named sections...
        for appName in self.AppNameList:
            A = self.AppDict[appName]
            assert isinstance(A, App) #for Wing
            #see if there are overrides to the default options...
            A.ReadAppOptions(co)

        #Append rdReprocessor for virtual mode, just before the first Fitter
        if self.virtualMode and "rdReprocessor" not in self.AppNameList:
            firstFitter = next(a for a in self.AppNameList if a.startswith("Fitter"))
            firstFitterIndex = self.AppNameList.index(firstFitter)
            self.AppNameList.insert(firstFitterIndex, "rdReprocessor")
            self.AppDict["rdReprocessor"] = App("rdReprocessor", self, defaultSettings)
            assert isinstance(self.AppDict["rdReprocessor"], App)
            #Read options for rdReprocessor if in virtual mode
            co_vi = CustomConfigObj(viFileName)
            self.AppDict["rdReprocessor"].ReadAppOptions(co_vi)

        #Now check the options...
        for appName in self.AppNameList:
            A = self.AppDict[appName]
            assert isinstance(A, App) #for Wing
            #Make sure the executable exists!
            exePath = os.path.normpath(os.path.join(os.path.dirname(AppPath), A.Executable))
            if not os.path.exists(exePath):
                raise AppErr("File '%s' does not exist for AppName '%s'." % (exePath, appName))

            #Launch apps in virtual mode
            if self.virtualMode and appName in ["InstMgr", "RDFreqConverter"]:
                A.LaunchArgs += " --vi"

            #check the dependency list...
            if not self.virtualMode:
                for a in [s.strip() for s in A.Dependencies.split("|") if not s == '']:
                    if not a in self.AppNameList:
                        raise AppErr("Unrecognized dependency listed for application (D = '%s' for A = '%s')." % (a, appName))

            if A.Mode in [0,1,3,4]:
                self.AppMonitorCount += 1

            if A.Mode == 0:
                if self.BackupExists:
                    raise AppErr("There can only be one backup supervisor.  '%s' is an additional app illegally specified as mode 0." % (appName, ))
                else:
                    self.BackupExists = True
                    self.BackupApp = A
            elif A.Mode == 3:
                self.Mode3Exists = True

        if self.BackupExists:
            #We'll check that the backup WDT time makes sense...
            wdtTimeOk = True
            for appName in self.AppNameList:
                A = self.AppDict[appName]
                if (DEFAULT_BACKUP_MAX_WAIT_TIME_s < (2.5 * A.MaxWait_ms / 1000)):
                    wdtTimeOk = False
                    print "Backup WDT too short.  WDT = %3s s  MaxWait for '%s' = %s s" % (DEFAULT_BACKUP_MAX_WAIT_TIME_s, appName, A.MaxWait_ms/1000)
                if (DEFAULT_BACKUP_MAX_WAIT_TIME_s < (2.5 * A.VerifyTimeout_ms / 1000)):
                    wdtTimeOk = False
                    print "Backup WDT too short.  WDT = %3s s  VerifyTimeout for '%s' = %s s" % (DEFAULT_BACKUP_MAX_WAIT_TIME_s, appName, A.VerifyTimeout_ms/1000)
            if not wdtTimeOk:
                raise AppErr("CODE ERROR - The WDT duration for the backup Supervisor is too short and must be lengthened.")

        #We need to set up a TCP server to listen to incoming kicks/pings from Mode 3 apps...
        #   - set it up even if here are no mode 3 apps to make development of 'potential'
        #     mode 3 apps a bit easier.
        if self.Mode3Exists:
            self._TcpServer = SupervisorTcpServer(('',_MODE3_TCP_SERVER_PORT), TcpRequestHandler, self)
            self._TcpServerThread = threading.Thread(target = self._TcpServer.serve_forever)
            self._TcpServerThread.setDaemon(True)
            self._TcpServerThread.start()
    def AddExtraArgs(self, ExtraAppArgs):
        """Appends any options to the application LaunchArgs.

         Coded to work with the -o command-line switch.
        """
        if 0: assert isinstance(ExtraAppArgs, dict)

        if ExtraAppArgs:
            for k in ExtraAppArgs:
                if k in self.AppDict:
                    self.AppDict[k].LaunchArgs += (" " + ExtraAppArgs[k])
                else:
                    print "Unrecognized application used with -o switch: '%s'" %(k,)
                    sys.exit(1)
    def FindExistingApps(self):
        """Finds any existing applications that are open and attaches to them.

        The meaning of "attaches to them" is that it when complete it will appear
        to the supervisor as if it had launched them in the first place.

        Return value is a list of the found apps (from the top down).
        """
        foundApps = []
        checkingSemaphore = threading.Semaphore(len(self.AppNameList))
        #Go through each app, check if anyone listening on the port...
        print "Checking for existing applications..."
        if 0: assert isinstance(A, App)
        for appName in self.AppNameList[::-1]:
            A = self.AppDict[appName]
            threading.Thread(target = A.FindAndAttach).start()
        #Now wait for the searches to complete...
        for appName in self.AppNameList[::-1]:
            A = self.AppDict[appName]
            A._SearchComplete.wait()
        while not self.messageQueue.empty():
            print self.messageQueue.get()
        #Now build our list of found apps...
        for appName in self.AppNameList[::-1]:
            A = self.AppDict[appName]
            if A._ProcessHandle != -1:
                foundApps.append(appName)
        return foundApps

    def LaunchApps(self, AppList, ExclusionList = [], IsRestart = False):
        """Launches all apps in the list in order of the list index.
        """
        if self.appList == None:
            # Use the first complete list as the standard list
            self.appList = AppList
        else:
            # Make sure the applications to be launched are in the original order
            sortedList = []
            for app in self.appList:
                if app in AppList:
                    sortedList.append(app)
            AppList = sortedList
        Log("Launch list: %s" % AppList)

        failedAppDependents = []

        appsToLaunch = [a for a in AppList if a not in ExclusionList]
        qapp = QApplication(sys.argv)
        splashPix = None
        if self.splashImage and os.path.isfile(self.splashImage):
            # QSplashScreen is not modal and so users can interaction with windows behind
            # the splash screen.  We run the splash screen as full screen to keep the focus
            # only on the splash screen.  The splash screen graphic is small so we create
            # a single color full screen pic based upon the current resolution and add
            # our desired pic to it.  I found an example at this url:
            # https://forum.qt.io/topic/8558/solved-full-screen-qsplashscreen-on-mobile/6
            splashPix = QPixmap(self.splashImage)
            desktop = QApplication.desktop()
            desktopRect = desktop.availableGeometry()
            fillPixmap = QPixmap(desktopRect.width(), desktopRect.height())
            fillPixmap.fill(QColor(30,30,30))
            p = QPainter()
            p.begin(fillPixmap)
            targetRect = QRect((fillPixmap.width() - splashPix.width())/2,
                               (fillPixmap.height() - splashPix.height())/2,
                               splashPix.width(), splashPix.height())
            p.drawPixmap(targetRect, splashPix)
            p.end()
        else:
            fillPixmap = QPixmap(500,500)
            fillPixmap.fill(Qt.black)
        splash = QSplashScreen(fillPixmap, Qt.WindowStaysOnTopHint)
        splash.setWindowState(Qt.WindowFullScreen)
        progressCounter = 0
        updateSplash = True
        for appName in appsToLaunch:

            if self.splashEnable and updateSplash:
                splash.show()
                myAlignment = Qt.AlignCenter # Alignment doesn't work right if the msg has html in it.
                progressCounter += 1
                str = QString(self.splashTitle)
                str += QString("\n\nLoading %1 of %2\n%3").arg(progressCounter, 2).arg(len(appsToLaunch)).arg(appName)
                splash.showMessage(str, myAlignment, Qt.white)
            else:
                splash.close()
            if "QuickGui" in appName:
                updateSplash = False
                #splash.close()

            failedAppDependent = False
            #check to make sure they are not dependents of apps that failed to launch
            for failedAppName in failedAppDependents:
                if appName == failedAppName:
                    failedAppDependent = True
                    break

            if not failedAppDependent:
                Log("Attempting to launch application",dict(AppName = appName))
                appStarted = False
                for i in range(MAX_LAUNCH_COUNT):
                    try:
                        self.AppDict[appName].Launch(self, IsRestart)
                        appStarted = True
                        break
                    except AppLaunchFailure, E:
                        Log("Failed to launch application",
                            dict(AppName = appName, AttemptNum = self.AppDict[appName]._LaunchFailureCount),
                            Level = 2)
                        #Sleep a short time before trying again...
                        #time.sleep(1)
                    except TerminationRequest:
                        Log("Terminate requested during application launch process",dict(AppName = appName),Level=2)
                        self.ShutDownAll()
                        raise

                if not appStarted:
                    if not self.virtualMode: failedAppDependents = failedAppDependents + self.GetDependents(appName)
                    Log("FATAL - Unable to successfully launch application",
                        "App = %s, NumAttempts = %s" % (appName, MAX_LAUNCH_COUNT))
                    # errMsg = "FATAL ERROR - Launching the '%s' application failed after %s attempts." % (appName, MAX_LAUNCH_COUNT)
                    # raise Exception(errMsg)
            else:
                Log("Not launching because of dependence on app which is not launched", dict(AppName = appName), Level = 2)

            self.KickBackup()

    def GetDependents(self, MasterAppName):
        """Determines the dependent app list.  Returns a list ordered from top down.

        The returned list is the list of applications that depend on the application
        being asked about.

        Launching/restarting of apps should be done from the bottom up.
        Closing of apps should be done from the top down.
        """
        dependentList = [MasterAppName]
        continueFlag = True
        # Find dependents of dependents as necessary
        while continueFlag:
            continueFlag = False
            for appName in self.AppNameList:
                app = self.AppDict[appName]
                assert isinstance(app, App)
                appDependencies = [s.strip() for s in app.Dependencies.split("|")]
                for d in dependentList:
                    if d in appDependencies:
                        if appName not in dependentList:
                            dependentList.append(appName)
                            continueFlag = True
        # Remove MasterAppName from list
        dependentList = dependentList[1:]
        Log("Application dependents identified", dict(Master = MasterAppName,
                                                      Dependents = dependentList))
        return dependentList

    def RestartApp(self, AppName, RestartDependents = True, StopMethod = _METHOD_STOPFIRST):
        """Restarts the named application.  Also restarts dependents if specified.

        To figure out:
          - If dependent is not mode 1 (CmdFIFO), how to close?
        """

        assert isinstance(self.AppDict[AppName], App) #for Wing

        # before restarting, make sure the app is not a dependent of an app which isn't running
        restartApp = True
        for a in self.AppNameList:
            if self.AppDict[a]._LaunchFailureCount > 0:
                appDependents = []
                appDependents = self.GetDependents(a)
                for d in appDependents:
                    if d == AppName:
                        restartApp = False

        if restartApp:
            if self.AppDict[AppName].Mode == 4:
                # Mode = 4 means the app communicates with P.S.A., so everything needs to be restarted and connections need to be re-established.
                if self.restartSurveyor.CmdFIFO.PingDispatcher() == "Ping OK":
                    Log("About to restart the whole system")
                    self.restartSurveyor.restart()  # call restartSurveyor to restart the whole system
                    return 0
                Log("RestartSurveyor is NOT running. Only %s and its dependents will be restarted." % AppName)

            appDependents = []

            #first get all the dependents shut (politely) down, if needed...
            if RestartDependents:
                appDependents = self.GetDependents(AppName)
                for a in appDependents:
                    assert isinstance(self.AppDict[a], App)
                    self.AppDict[a].ShutDown() #blocks until it IS shut down

            #Now shut down the app in question (as brutally as was requested)...
            self.AppDict[AppName].ShutDown(StopMethod = StopMethod)

            #the app (and all dependents) are now shut down... we're ready to re-launch...
            Log("Application and all dependents successfully shut down.  Restarting from bottom up.", dict(AppName = AppName, Dependents = appDependents))

            launchList = [AppName] + appDependents
            self.LaunchApps(launchList, IsRestart = True)

            # report restart of apps to Instrument Manager
            if 'InstMgr' not in launchList:
                portList = []
                for a in launchList:
                    try:
                        if self.AppDict[a].CheckDispatcher():
                            portList.append(self.AppDict[a].Port)
                    except:
                        pass
                try:
                    self.AppDict['InstMgr']._ServerProxy.INSTMGR_ReportRestartRpc(portList)
                except:
                    Log("Report Restart Rpc failed")

        else:
            Log("Not restarting because of dependence on app which is not launched", dict(AppName = AppName), Level = 2)

    def RPC_TerminateApplications(self,powerDown=False,stopProtected=False):
        """Terminates all applications (in the proper order) and closes the Supervisor. Optionally powers down
        (by shutting down Windows) after termination. If stopProtected is True, protected applications (currently the
        Driver) are also terminated. """
        Log("TerminateApplications request received via RPC",
            dict(Client = self.RPCServer.CurrentCmd_ClientName),
            Level = 2)
        self._TerminateAllRequested = True
        self.powerDownAfterTermination = powerDown
        self._TerminateProtected = stopProtected
        return "OK"

    def RPC_RestartApplications(self, AppName, RestartDependants):
        Log("RestartApplications request received via RPC",
            dict(Client=self.RPCServer.CurrentCmd_ClientName),
            Level=2)
        try:
            self.RestartApp(self, AppName, RestartDependants)
        except Exception, e:
            Log("Error Restarting %s %s: " % AppName % e)
        return "OK"

    def LaunchMasterRPCServer(self):
        """Configures the Master RPC server and launches it on it's own thread.

        It is on it's own thread because this is an auxiliary function of the
        supervisor app.  It is simpler to do this then it is to re-bind the rpc
        functionilty to do Supervisor stuff.

        NOTE - This RPC server is not required for operation!  If it crashes it will
               NOT affect operation in any way.
        """
        #Set up the Master RPC Server... going to launch it on a thread so it can run in
        #the background while we do the monitoring in the main thread/loop...
        try:
            self.RPCServer = CmdFIFO.CmdFIFOServer(
                addr       = ("", RPC_SERVER_PORT_MASTER),
                ServerName = "Supervisor",
                ServerDescription = "The rpc server for the master Supervisor application.")

            #register any RPC calls here...
            self.RPCServer.register_function(self.RPC_TerminateApplications, NameSlice = 4)

            #Launch the server on its own thread...
            th = threading.Thread(target = self.RPCServer.serve_forever)
            th.setDaemon(True)
            th.start()
        except Exception, E:
            Log("Exception trapped when configuring and launching the Master RPC server", Verbose = "Exception = %s %r" % (E, E))

    def sigint_handler(self, signum, frame):
        self._TerminateAllRequested = True

    def CheckForStopRequests(self):
        """
        Set Ctrl-X to tell Supervisor to exit the code, Ctrl-T to terminate.
        These two should shutdown all the other Host sub-processes.
        Ctrl-C will kill the Supervisor and leave the sub-processes as
        zombies you'll have to kill manually.

        In Linux, the keyboard shortcut is set with ttyLinux.py which
        requires to run in a valid tty terminal like x-term.  If the
        code is run in an IDE with a pseudo terminal, ttyLinux will
        throw an exception and terminate the Supervior.
        """

        if sys.stdout.isatty():
            try:
                start_rawkb()
                while True:
                    key = read_rawkb()
                    if key == "": break
                    if len(key) > 1: break
                    if ord(key) in [17, 24]: #ctrl-q and ctrl-x
                        Log("Exit request received via keyboard input (Ctrl-X)")
                        self._ShutdownRequested = True
                    elif ord(key) == 20: #ctrl-t
                        Log("Terminate request received via keyboard input (Ctrl-T)")
                        self._TerminateAllRequested = True
                        self.powerDownAfterTermination = False
            finally:
                stop_rawkb()

        if self._ShutdownRequested or self._TerminateAllRequested:
            #In addition to being set above, these could also have been set somewhere else (eg: RPC server)...
            return True
        if self.RPCServer is not None and not self.RPCServerProblem:
            try:
                if self.RPCServer.ServerStopRequested:
                    self._ShutdownRequested = True
                    return True
            except Exception, E:
                #don't want ANY rpc server problems to cause us grief...
                Log("Exception trapped when checking the Master RPC Server.  Ignoring server from now on.", Level = 2, Verbose = "Exception = %s %r" % (E, E))
                self.RPCServerProblem = True #so we don't keep reporting it
        return False

    def KickBackup(self):
        if self.BackupExists and self.BackupApp._StartedOk:
            #give it a kick - need to make sure it doesn't get left alone...
            try:
                self.BackupApp.CheckFIFO()
            except Exception, E:
                #ignoring it at this point.  We'll deal with it come time to
                #actually check the backup (this is just a kick)
                Log("Exception occurred when kicking the backup Supervisor", Level = 1, Verbose = "Exception = %s %r" % (E,E))

    def MonitorApps(self):
        """Eternal loop that monitors/restarts-if-needed appropriate applications.

        Loop can be exited by pressing Ctrl-q , Ctrl-x, or Ctrl-t. The latter
        terminates all monitored applications before exiting.
        """
        Log("Application monitoring loop started")
        appsToMonitor = [self.AppDict[a] for a in self.AppNameList if self.AppDict[a].Mode in [0, 1, 3, 4]]
        while (not self._ShutdownRequested) and (not self._TerminateAllRequested): #we'll monitor until it is time to stop!
            sys.stdout.flush()
            for app in appsToMonitor:
                time.sleep(0.1)
                if self.CheckForStopRequests():
                    break
                assert isinstance(app, App) #for Wing
                curTime = TimeStamp()
                if (curTime - app._LastCheckTime) > (app.CheckInterval_ms / 1000.):
                    app._LastCheckTime = curTime
                    #Log("Checking application", app._AppName, 0)
                    #We are due to check this app.
                    #  - check the RPC dispatcher first
                    #  - then check that the FIFO queue is being serviced
                    #  - If any problems are found, restart the app (and dependents)
                    #    - The next app will NOT be checked until we're fully recovered
                    if app.Mode == 3:
                        #Mode 3 means the app should be checking in with us over TCP.  We'll wait
                        #here until it happens OR if it has happened since we last checked that is
                        #also fine...
                        pingArrived = False
                        startTime = TimeStamp()
                        while (TimeStamp() - startTime) < (app.MaxWait_ms/1000):
                            if app._RemotePingCount > 0: # Incremented in TcpRequestHandler.handle
                                pingArrived = True
                                app._RemotePingCount = 0
                                break
                            time.sleep(0.1)
                        if not pingArrived:
                            Log("Ping timeout with mode 3 (TCP pinging) application",
                                dict(App = app._AppName, Timeout_s = app.MaxWait_ms/1000),
                                Level = 3)
                            self.RestartApp(app._AppName, RestartDependents = True, StopMethod = _METHOD_DESTROYFIRST)
                    else:
                        dispatcherProblem = False
                        fifoProblem = False
                        self.KickBackup()
                        curTime = TimeStamp()
                        try:
                            app.CheckDispatcher()
                        except AppErr, E:
                            dispatcherProblem = True
                            #If the dispatcher is toast, we need to kill the process completely...
                            stopMethod = _METHOD_DESTROYFIRST
                        dispatcherPingTime = TimeStamp()-curTime
                        if not dispatcherProblem:
                            curTime = TimeStamp()
                            try:
                                app.CheckFIFO()
                            except AppErr, E:
                                Log("Exception raised during application FIFO check",
                                    dict(AppName = app._AppName),
                                    Verbose = "Exception = %s %r" % (E,E))
                                fifoProblem = True
                                #If the CmdFIFO is hung, we may still be able to do a kill...
                                stopMethod = _METHOD_KILLFIRST
                        fifoPingTime = TimeStamp()-curTime
                        if dispatcherProblem or fifoProblem:
                            if dispatcherProblem and app.ShowDispatcherWarning:
                                Log("Dispatcher problem %s detected with monitored application" % (E,), app._AppName, 3)
                            elif fifoProblem:
                                Log("FIFO problem %s detected with monitored application" % (E,), app._AppName, 3)
                            self.RestartApp(app._AppName, RestartDependents = True, StopMethod = stopMethod)

        try:
            self.RPCServer._CmdFIFO_StopServer()
        except Exception, E:
            Log("Exception trapped when trying to stop the Master RPC Server", Level = 2, Verbose = "Exception = %s %r" % (E, E))
            self.RPCServerProblem = True

        if self._TerminateAllRequested:
            Log("Shutting down all applications ('terminate all' request received while monitoring)", Level = 2)
            self.ShutDownAll()
        elif self._ShutdownRequested:
            Log("Supervisor shutting down.  Apps will stay alive.", Level = 2)
            #All stay alive... except the backup supervisor!
            #In this case we have a legit stop request, we don't want the backup to
            #enable and have us caught in an eternal backup recovery loop!
            if self.BackupExists: #may not exist if no Mode 0 specified
                assert isinstance(self.BackupApp, App)
                Log("Closing backup supervisor")
                self.BackupApp.ShutDown()

    def ShutDownAll(self):
        """Shuts down all monitored applications and then itself.
        """
        #Get rid of any backup supervisor first...
        if self.BackupExists:
            self.BackupApp.ShutDown(_METHOD_KILLFIRST,NoKillByName=True,NoWait=True)

        # If running on Windows initiate system shutdown.
        # If running on Linux, OS shutdown is managed by a script
        # that starts the Supervisor.
        if self.powerDownAfterTermination:
            if  sys.platform == "linux2":
                #os.system("sleep 60; shutdown now")
                os.system("shutdown -h 1")
            else:
                pass

        #Now shut applications down in the reverse order of launching...
        #for severity in [_METHOD_STOPFIRST,_METHOD_KILLFIRST,_METHOD_DESTROYFIRST]:
        for severity in [_METHOD_KILLFIRST,_METHOD_DESTROYFIRST]:
            anyAlive = False
            for appName in self.AppNameList[::-1]:
                if not (self.AppDict[appName] is self.BackupApp) and not appName in PROTECTED_APPS:
                    # terminate the application
                    if self.AppDict[appName].IsProcessActive():
                        anyAlive = True
                        self.AppDict[appName].ShutDown(severity,NoWait=True)
            if anyAlive:
                time.sleep(_DEFAULT_KILL_WAIT_TIME_s)

        if self._TerminateProtected:
            for appName in self.AppNameList[::-1]:
                if appName in PROTECTED_APPS:
                    self.AppDict[appName].ShutDown()

        if self.SpecialKilledByNameList:
            # Kill all the processes with the specified name
            namesToBeKilled = [n.lower() for n in self.SpecialKilledByNameList]
            for p in psutil.process_iter():
                try:
                    if callable(p.name):
                        name = p.name()
                    else:   # name is not an instance method in psutil 1.2.1
                        name = p.name
                    if name.lower() in namesToBeKilled:
                        p.kill()
                except:
                    pass

        self._ShutdownRequested = True

    def GetAppStats(self, PrintStats = False):
        """Prints the supervisory stats for each application.
        """
                #    Print("---")
                #    Print("Application Stats:")
                #    Print("---")
        s = ""
        s += 50 * "-" + "\n"
        s += "%s%s%s%s" % ("App Name".ljust(20), "PID".ljust(8), "Uptime".ljust(11), "# Restarts".ljust(10)) + "\n"
        s += 50 * "-" + "\n"
        for appName in self.AppNameList:
            app = self.AppDict[appName]
            assert isinstance(app, App)
            s += "%20s%8s%8.2f%10s" % (appName.ljust(20), app._ProcessHandle, app.UpTime, app._Stat_LaunchCount-1)
        Print("-" * 50)

    def Execute(self, KillExistingApps = False, LaunchNonExistent = True, DoMonitoring = True):
        """Launches all applications in order and proceeds to appropriate monitoring.
        """
        existingApps = self.FindExistingApps()
        if KillExistingApps:
            for a in existingApps:
                self.AppDict[a].ShutDown()
            existingApps = []

        if LaunchNonExistent:
            self.LaunchApps(self.AppNameList, ExclusionList = existingApps)

        if DoMonitoring:
            self.MonitorApps() #will monitor all that need it (mode 1 apps)
        else:
            if self.BackupExists:
                self.BackupApp.ShutDown()

class MasterSupervisorRPCServer(CmdFIFO.CmdFIFOServer):
    """
    """
    def __init__(self, *args, **kwargs):
        if kwargs.has_key("threaded"):
            raise Exception("It is illegal to set the threaded parameter in an instance of MasterSupervisorRPCServer")

        #The entire Supervisor app is to be left with a single thread, so we force
        #threading to be false here.
        CmdFIFO.CmdFIFOServer.__init__(self, threaded = False, *args, **kwargs)

class BackupSupervisorRPCServer(CmdFIFO.CmdFIFOServer):
    """Supervisor server class to get special behaviour needed for running as a backup.
    """
    def __init__(self, *args, **kwargs):
        self.BackupWDTWaitTime = DEFAULT_BACKUP_MAX_WAIT_TIME_s
        self.BackupWDTTimeStamp = TimeStamp()
        self.BackupWDTExpired = False
        self.BackupWDTWarningCount = 0
        self.BackupWDTWarningInterval = round(self.BackupWDTWaitTime / 3)
        self.BackupWDTWarningStamp = self.BackupWDTTimeStamp

        self.MasterApp = App("Master_Supervisor", self)

        #The entire Supervisor app is to be left with a single thread.  Setting
        #threaded = false here shouldn't matter since we don't use it due to the
        #server_forever replacement, but it makes the point and is just in case.
        CmdFIFO.CmdFIFOServer.__init__(self, threaded = False, *args, **kwargs)

        self._register_priority_function(self._SetMasterProcessID, "SetMasterProcessID")

    def _SetMasterProcessID(self, PID):
        """Gives the backup server access to the Master process.

        This access is needed to enable the backup server to obliterate the
        misbehaving master so that it can take over.

        NOTE - THIS IS ONLY TO BE USED BY THE MASTER SUPERVISOR.
        """
        Log("Process ID received from Master Supervisor", dict(PID = PID), Level = 1)
        self.MasterApp._ProcessId = PID
        self.MasterApp._ProcessHandle = getProcessHandle(PID)


    def _CmdFIFO_Ping(self):
        #reset the WDT seed...

        #Print("Ping received - resetting WDT after %.2f s.  WDT stamp = %.2f" % (TimeStamp() - self.BackupWDTTimeStamp, self.BackupWDTTimeStamp))
        self.BackupWDTTimeStamp = TimeStamp()
        self.BackupWDTWarningStamp = self.BackupWDTTimeStamp
        if self.BackupWDTWarningCount > 0:
            self.BackupWDTWarningCount = 0
            self.BackupWDTWarningStamp = self.BackupWDTTimeStamp
            Log("WDT Warning state cleared (ping arrived)", Level = 1)
        return CmdFIFO.CmdFIFOServer._CmdFIFO_Ping(self)

    def serving_action(self):
        """Override to enable backup server code during the main monitoring loop.
        """
        #We will break out of this loop if our backup WDT has expired...
        timeNow = TimeStamp()
        wdtElapsedTime = timeNow - self.BackupWDTTimeStamp
        #print "Looping", self.ServerKillRequested, self.ServerStopRequested, round(wdtElapsedTime,1),  round(self.BackupWDTWaitTime,1), (wdtElapsedTime > self.BackupWDTWaitTime)
        if wdtElapsedTime > self.BackupWDTWaitTime:
            Log("WatchDog Timer Expired - There is a problem with the Master Supervisor",
                dict(Timeout_s = self.BackupWDTWaitTime), Level = 3)
            self.BackupWDTExpired = True
            self.ServerStopRequested = True #to get out of the serve_forever loop
        elif (timeNow - self.BackupWDTWarningStamp) > self.BackupWDTWarningInterval:
            Log("WDT Warning", dict(ElapsedTime_s = int(round(wdtElapsedTime, 0))), Level = 2)
            self.BackupWDTWarningCount += 1
            self.BackupWDTWarningStamp = timeNow

class BackupSupervisor(object):
    pass
def PrintUsage():
    print """\
          Usage:
          %s.py [-i|-f|-k] [-c<FILENAME>] [-o<APPNAME>:<ARGS>]
          %s.py [--ke] [--nl] [--nm] [--inilog] [-c<FILENAME>] [-o<APPNAME>:<ARGS>]

          With no switches, this application does the following:
          1.  Determines what applications are to be supervised by reading the config
          file: '%s'
          2.  Identifies whether any of the applications are already running
          3.  Launches any applications that are missing
          4.  Enters an eternal supervisory loop that monitors all apps.

          The command line options are as follows:
          -c         Specify a different config file.  Usage is -c<FILENAME>
          -i         Identify existing apps only.  ie: stop after step 2.  This is equivalent
          to using both --nl and --nm
          -f         Do a fresh start.  This is equivalent to only using the --ke switch.
          -k         Kill any existing apps only.  Equivalent to using '--ke --nl --nm'
          --ke        Kill Existing.  Kills existing apps at the start (between steps 2 & 3)
          --nl        No Launch. Suppress all apps from being launched (suppresses step 3)
          --nm        No Monitoring. Don't enter the monitoring loop (suppresses step 4)
          --inilog    Create a log of the INI Coordinator verification results
          --vi        Trigger virtual mode and specify an ini file. Usage is --vi <FILENAME>
          -o         Add command-line args to a particular app.  Use quotes if using spaces.
          eg:  -oDriver:"--nokeepalive --otherarg"

          To exit the Supervisor when it is in monitoring mode:
          - Ctrl-q (or Ctrl-x) cleanly exits and leave the applications running.
          - Ctrl-t terminates all monitored applications and then shuts down.
          """ % (APP_NAME, APP_NAME, _DEFAULT_CONFIG_NAME)

def HandleCommandSwitches():
    shortOpts = 'hc:ifkt:o:'
    longOpts = ["ke", "nl", "nm", "backup", "inilog", "vi="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    extraAppArgs = {}
    appName = ""
    appArgs = ""
    for o,a in switches:
        if o == "-o":
            #multiple occurrences of -o can exist
            try:
                appName, appArgs = a.split(":")
                quoteCount = appArgs.count('"')
                if not((quoteCount == 2) or (quoteCount == 0)): raise
                if not appName in extraAppArgs:
                    extraAppArgs[appName] = appArgs
                else:
                    extraAppArgs[appName] += (" " + appArgs)
            except Exception, E:
                print "Parameter format incorrect - '-o%s'" % (a,)
                sys.exit(1)
        else:
            options.setdefault(o,a)

    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")

    #Start with option defaults...
    backupMode = False
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME
    killExisting = False
    suppressLaunch = False
    suppressMonitoring = False
    waitTime = DEFAULT_BACKUP_MAX_WAIT_TIME_s

    listMode = False
    freshStartMode = False
    killOnlyMode = False
    viConfigFile = ""

    macroModeSetCount = 0
    flagCount = 0

    if '-h' in options:
        PrintUsage()
        sys.exit()

    if "--backup" in options:
        backupMode = True
    if "-t" in options:
        waitTime = float(options["-t"])

    if '-c' in options:
        configFile = options["-c"]
        # print "Config file specified at command line: %s" % configFile
        Log("Config file specified at command line", dict(Path = configFile))
    else:
        print "No config file specified.  Using default: '%s'." % os.path.basename(configFile)

    if "-i" in options:
        macroModeSetCount += 1
        print "'Identify Apps' macro mode requested on commandline."
        listMode = True
    if "-f" in options:
        macroModeSetCount += 1
        print "'Fresh Start' macro mode requested on commandline."
        freshStartMode = True
    if "-k" in options:
        macroModeSetCount += 1
        print "'Kill Only' macro mode requested on commandline."
        killOnlyMode = True
    if macroModeSetCount > 1:
        print "\nOPTION ERROR: You can only set one macro mode at a time."
        sys.exit()

    if "--ke" in options:
        flagCount += 1
        print "'Kill Existing' flag set."
        killExisting = True
    if "--nl" in options:
        flagCount += 1
        print "'No Launch' flag set."
        suppressLaunch = True
    if "--nm" in options:
        flagCount += 1
        print "'No Monitoring' flag set."
        suppressMonitoring = True
    if flagCount > 0 and macroModeSetCount > 0:
        print "\nOPTION ERROR: You cannot set macro modes and flags at the same time."
        sys.exit()
    if "--vi" in options:
        viConfigFile = options["--vi"]
        print "'Virtual Mode' macro mode requested on commandline."

    #if here, the options make sense...
    if listMode:
        killExisting = False
        suppressLaunch = True
        suppressMonitoring = True
    elif freshStartMode:
        killExisting = True
        suppressLaunch = False
        suppressMonitoring = False
    elif killOnlyMode:
        killExisting = True
        suppressLaunch = True
        suppressMonitoring = True
    return (configFile, killExisting, suppressLaunch, suppressMonitoring, backupMode, waitTime, extraAppArgs, viConfigFile)

def GetConfigFileAndIniLog():
    # default configFile
    configFile = os.path.dirname(AppPath) + "/" + _DEFAULT_CONFIG_NAME
    # Get configFile from command line
    shortOpts = 'hc:ifkt:o:'
    longOpts = ["ke", "nl", "nm", "backup", "inilog", "vi="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    switchDict = dict(switches)
    if switchDict.has_key("-c"):
        configFile = switchDict["-c"]
    if switchDict.has_key("--inilog"):
        printIniLog = True
    else:
        printIniLog = False
    return (configFile, printIniLog)

def main():
    try:
        performDuties = False
        #Get and handle the command line options...
        configFile, killExisting, suppressLaunch, suppressMonitoring, backupMode, waitTime, extraAppArgs, viConfigFile = HandleCommandSwitches()

        if backupMode:
            try:
                #The instance we are running right now is a backup!
                performDuties = PrepareBackupAndWaitForAction(waitTime)
            except Exception, E:
                Log("Exception trapped when preparing the backup Supervisor", Level = 3, Verbose = "Exception = %s %r" % (E, E))
                sys.stdout.flush()
                #x = prompt_wait("Problem detected!!")
        else:
            performDuties = True

        #Now get to the actual program...
        if performDuties:
            # Grab the mutex, as we should be the only one up at this stage
            supervisorApp = SingleInstance("PicarroSupervisor")
            if supervisorApp.alreadyrunning():
                sys.exit(0)
            try:
                #splashPix = QPixmap("/home/picarro/Pictures/Picarro.jpg")
                #supervisorSplash = QSplashScreen(splashPix, Qt.WindowStaysOnTopHint)
                #supervisorSplash.show()
                supe = Supervisor(FileName = configFile, viFileName = viConfigFile) #loads all the app info
                supe.AddExtraArgs(extraAppArgs)
                supe.LaunchMasterRPCServer() # in separate thread, only supports TerminateApplications RPC
                supe.Execute(KillExistingApps = killExisting,
                             LaunchNonExistent = (not suppressLaunch),
                             DoMonitoring = (not suppressMonitoring))
            except AppErr, E:
                print "Exception trapped outside Supervisor execution: %s %r" % (E, E)
                Log("Exception trapped outside Supervisor execution", Level = 3, Verbose = "Exception = %s %r" % (E, E))
            except TerminationRequest:
                pass
            #PUT NO MORE CODE HERE - code above relies on falling through.

    finally:
        #Print("'FINALLY' catch in module Supervisor.py reached!")
        sys.stdout.flush()
        #x = prompt_wait("At final!")

if __name__ == "__main__":
    # Run iniCoordinator to verify the configurations of all applications
    configFile, printIniLog = GetConfigFileAndIniLog()
    try:
        main()
    except SystemExit:
        pass
    except:
        # tbMsg = BetterTraceback.get_advanced_traceback()
        tbMsg = traceback.format_exc()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
        print tbMsg
        Log("Exiting program")
