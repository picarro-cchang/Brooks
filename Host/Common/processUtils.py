"""
Copyright 2009-2014 Picarro Inc.
"""

import ctypes
import os
import sys
import time
from os import path

import psutil


CONSOLE_MODE_OWN_WINDOW    = 1
CONSOLE_MODE_NO_WINDOW     = 2
CONSOLE_MODE_SHARED_WINDOW = 3


def findHandle(name):
    """
    From: https://stackoverflow.com/questions/11114492/check-if-a-file-is-not-open-not-used-by-other-process-in-python
    """
    
    procsWithHandle = []

    for proc in psutil.process_iter():
        try:
            files = proc.get_open_files()
            if files:
                for f in files:
                    if path.basename(f.path) == name:
                        procsWithHandle.append(proc.pid)

        except psutil.NoSuchProcess:
            # Process was terminated between process_iter() and get_open_files()
            pass

    return procsWithHandle

if sys.platform == "win32":
    import win32process
    from win32api import OpenProcess as win32api_OpenProcess
    windll = ctypes.windll #to get access to GetProcessId() which is not in the win32 libraries
    win32_PROCESS_ALL_ACCESS = 0x1F0FFF #for the OpenProcess call
    _STILL_ACTIVE = 259 #hopefully correct - determined by doing, not by documentation

    _PRIORITY_LOOKUP = {
      "1" : win32process.IDLE_PRIORITY_CLASS,
      "2" : win32process.BELOW_NORMAL_PRIORITY_CLASS,
      "3" : win32process.NORMAL_PRIORITY_CLASS,
      "4" : win32process.ABOVE_NORMAL_PRIORITY_CLASS,
      "5" : win32process.HIGH_PRIORITY_CLASS,
      "6" : win32process.REALTIME_PRIORITY_CLASS
      }

elif sys.platform == "linux2":
    import ttyLinux
    libc = ctypes.CDLL("libc.so.6")
    sched_getaffinity = libc.sched_getaffinity
    sched_setaffinity = libc.sched_setaffinity
    setpriority = libc.setpriority

    _PRIORITY_LOOKUP = {
      "1" : 10,
      "2" : 5,
      "3" : 0,
      "4" : -5,
      "5" : -10,
      "6" : -15
      }


if sys.platform == "win32":
    def launchProcess(appName,exeName,exeArgs=[],priority=3,consoleMode=CONSOLE_MODE_OWN_WINDOW,affinity=0xFFFFFFFF):
        #launch the process...
        #Log("Launching application", appName, 1)
        ##Used to do this with spawnv, but doing this causes the spawned apps to
        ##share the console with Supervisor.  This is normally ok, but if the
        ##Supervisor is shut down, the console disappears.  Then if any spawned app
        ##tries to use the console (eg: a print statement) the app process dies.
        #self._ProcessHandle = spawnv(P_NOWWAIT, exeName, exeArgs)
        #self._ProcessId = windll.kernel32.GetProcessId(self._ProcessHandle)
        #priority = _PRIORITY_LOOKUP[self.Priority]
        #win32process.SetPriorityClass(self._ProcessHandle, priority)
        #Now start the process using a direct win32 call. For docs on
        #CreateProcess, do a google search for 'msdn createprocess'...

        lpApplicationName = None #Better to send it all in the CommandLine
        lpCommandLine = exeName + " " + " ".join(exeArgs[1:])
        lpProcessAttributes = None
        lpThreadAttributes = None
        bInheritHandles = False
        dwCreationFlags = _PRIORITY_LOOKUP[str(priority)] #sets the process priority as requested
        if consoleMode == CONSOLE_MODE_NO_WINDOW:
            dwCreationFlags += win32process.CREATE_NO_WINDOW
        elif consoleMode == CONSOLE_MODE_OWN_WINDOW:
            dwCreationFlags += win32process.CREATE_NEW_CONSOLE
        lpEnvironment = None
        lpCurrentDirectory = None
        lpStartupInfo = win32process.STARTUPINFO()
        hProcess, hThread, dwProcessId, dwThreadId =  win32process.CreateProcess(
                                  lpApplicationName,
                                  lpCommandLine,
                                  lpProcessAttributes,
                                  lpThreadAttributes,
                                  bInheritHandles,
                                  dwCreationFlags,
                                  lpEnvironment,
                                  lpCurrentDirectory,
                                  lpStartupInfo
                                  )
        processId = dwProcessId
        processHandle = win32api_OpenProcess(win32_PROCESS_ALL_ACCESS, int(False), dwProcessId)
        pAffinity,sAffinity = win32process.GetProcessAffinityMask(hProcess)
        mask = sAffinity & eval(str(affinity))
        if mask == 0: mask = sAffinity
        #win32process.SetProcessAffinityMask(hProcess,mask)
        pAffinity,sAffinity = win32process.GetProcessAffinityMask(hProcess)
        return processId,processHandle,pAffinity

    def isProcessActive(processHandle):
        """Checks to see if the application is running.
        If it can't be determined whether the app is alive or not, this assumes False.
        """
        if processHandle == -1:
            return False
        if isinstance(processHandle, int):
            if processHandle <=0: return False
            ec = win32process.GetExitCodeProcess(processHandle)
        else: #it is a PyHANDLE
            ec = win32process.GetExitCodeProcess(processHandle.handle)
        if ec == _STILL_ACTIVE:
            return True
        return False

    def terminateProcess(processHandle):
        win32process.TerminateProcess(processHandle, 42)

    def terminateProcessByName(name):
        [path,filename] = os.path.split(name)
        [base,ext] = os.path.splitext(filename)
        if ext.lower() == ".exe":
            call(["taskkill","/im",filename],stderr=file("NUL","w"))
            # os.system("taskkill /im %s > NUL" % filename)
        else:
            #Log("Can only terminate executables by name",dict(name=name))
            pass

    def getProcessHandle(pid):
        return win32api_OpenProcess(win32_PROCESS_ALL_ACCESS, int(False), pid)

elif sys.platform == "linux2":
    def start_rawkb():
        ttyLinux.setSpecial()

    def stop_rawkb():
        ttyLinux.setNormal()

    def read_rawkb():
        return ttyLinux.readLookAhead()

    def launchProcess(appName,exeName,exeArgs=[],priority=3,consoleMode=CONSOLE_MODE_OWN_WINDOW,affinity=0xFFFFFFFF):
        #launch the process...
        #Log("Launching application", dict(appName=appName), 1)
        argList = [exeName]
        for arg in exeArgs[1:]:
            argList += arg.split()
        try:
            if consoleMode == CONSOLE_MODE_NO_WINDOW:
                process = Popen(argList,stderr=file('/dev/null','w'),stdout=file('/dev/null','w'))
            elif consoleMode == CONSOLE_MODE_OWN_WINDOW:
                termList = ["xterm","-T",appName,"-e"]
                process = Popen(termList+argList,stderr=file('/dev/null','w'),stdout=file('/dev/null','w'))
        except OSError:
            #Log("Cannot launch application", dict(appName=appName), 2)
            raise
        except ValueError:
            #Log("Parameter error while launching application", dict(appName=appName), 2)
            raise
        # Set the affinity
        pAffinity = ctypes.c_int32()
        sAffinity = ctypes.c_int32()
        if sched_getaffinity(process.pid,ctypes.sizeof(sAffinity),ctypes.byref(sAffinity)) == 0:
            mask = sAffinity.value & eval(str(affinity))
            if mask == 0: mask = sAffinity.value
            mask = ctypes.c_int32(mask)
            if sched_setaffinity(process.pid,ctypes.sizeof(mask),ctypes.byref(mask)) != 0:
                #Log("Unable to set affinity for application", dict(appName=appName), 2)
                pass
            else:
                sched_getaffinity(process.pid,ctypes.sizeof(pAffinity),ctypes.byref(pAffinity))
        else:
            #Log("Cannot get affinity for application", dict(appName=appName), 2)
            pass
        # Set the scheduling priority
        setpriority(0,process.pid,_PRIORITY_LOOKUP[str(priority)])
        return process.pid,process,pAffinity.value

    def isProcessActive(processHandle):
        """Checks to see if the application is running.
        If it can't be determined whether the app is alive or not, this assumes False.
        """
        if isinstance(processHandle, Popen):
            result = processHandle.poll()
            if result == None:
                return True
        else:
            try:
                retval = os.waitpid(processHandle.pid,os.WNOHANG)
                return retval[0] == 0   # This means that wait would have blocked            
            except OSError:
                return False
            except Exception,e:
                print "Unexpected exception: %s" % e

    def terminateProcess(processHandle):
        print "Calling terminateProcess on process %s" % (processHandle.pid,)
        os.kill(processHandle.pid,9)

    def terminateProcessByName(name):
        [path,filename] = os.path.split(name)
        [base,ext] = os.path.splitext(filename)
        #Log("terminateProcessByName not implemented")

    def getProcessHandle(pid):
        class ProcessHandle(object):
            def __init__(self,pid):
                self.pid = pid
        return ProcessHandle(pid)

if __name__ ==  "__main__":
    pid,process,affinity = launchProcess("notepad",r"c:\windows\notepad.exe")
    print "Launched notepad"
    for i in range(10):
        time.sleep(1)
        sys.stdout.write(".")
    sys.stdout.write("\n")
    print "Terminating notepad"
    terminateProcess(process)
    
