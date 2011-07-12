import os
import sys
import time
import serial
import subprocess
import win32process
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import TCP_PORT_PERIPH_INTRF
from Host.Common.SingleInstance import SingleInstance

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

DEFAULT_CONFIG_NAME = "serial2socket.ini"

class RunSerial2Socket(object):
    def __init__(self, configFile):
        self.appCo = CustomConfigObj(configFile, ignore_option_case=False)
        iniAbsBasePath = os.path.split(os.path.abspath(configFile))[0]
        exeFile = os.path.abspath(os.path.join(iniAbsBasePath, self.appCo.get("SETUP", "EXE")))
        instrConfigFile = os.path.abspath(os.path.join(iniAbsBasePath, self.appCo.get("SETUP", "INSTRCONFIG")))
        self.numPorts = len([s for s in self.appCo.list_sections() if s.startswith("PORT")])
        
        # Create the instrument config file to run serial2socket.exe
        self.autoSearch = self.appCo.getboolean("SETUP", "AUTOSEARCH", False)
        instrConfigDir = os.path.dirname(instrConfigFile)
        if not os.path.isdir(instrConfigDir):
            os.makedirs(instrConfigDir)
        if os.path.isfile(instrConfigFile):
            os.remove(instrConfigFile)
        fd = open(instrConfigFile, "w")
        fd.close()
        self.instrCo = CustomConfigObj(instrConfigFile)
        if not self.instrCo.has_section("PORTS"):
            self.instrCo.add_section("PORTS")
        self.instrCo.write()
        self.updateIni(self.findPorts())
        
        # Launch the EXE program
        affmask = self.appCo.getint("SETUP", "AFFINITYMASK", 1)
        lpApplicationName = None
        lpCommandLine = "%s %d %s" % (exeFile, TCP_PORT_PERIPH_INTRF, instrConfigFile)
        lpProcessAttributes = None
        lpThreadAttributes = None
        bInheritHandles = False
        dwCreationFlags = win32process.HIGH_PRIORITY_CLASS
        dwCreationFlags += win32process.CREATE_NO_WINDOW
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
        win32process.SetProcessAffinityMask(hProcess, affmask)
        #subprocess.Popen([exeFile, str(TCP_PORT_PERIPH_INTRF), instrConfigFile], startupinfo=lpStartupInfo, creationflags = dwCreationFlags)
        
    def findPorts(self):
        try:
            assignPortNum = [int(i) for i in self.appCo.get("SETUP", "ASSIGNPORTNUM").split(",")]
        except:
            assignPortNum = []
        try:
            skipPortNum = [int(i) for i in self.appCo.get("SETUP", "SKIPPORTNUM").split(",")]
        except:
            skipPortNum = []
            
        if self.numPorts <= len(assignPortNum):
            portList = assignPortNum[:self.numPorts]
        else:
            portList = assignPortNum[:]
            if self.autoSearch:
                for p in range(100):
                    if p not in (skipPortNum+assignPortNum):
                        try:
                            ser = serial.Serial(p)
                            portList.append(p)
                            if len(portList) == self.numPorts:
                                print "%d COM ports found" % self.numPorts
                                break
                        except:
                            continue
        assignList = [p for p in portList if p in assignPortNum]
        print "Auto-search: %s; %s were found; %s were assigned" % (self.autoSearch, portList, assignList)
        return portList

    def updateIni(self, portList):
        if not portList:
            return
        for i in range(len(portList)):
            p = portList[i]
            self.instrCo.set("PORTS", "PORT%d" % i, r"\\.\COM%d" % (p+1))
            section = "PORT%d" % i
            if not self.instrCo.has_section(section):
                self.instrCo.add_section(section)
            for option in self.appCo.list_options(section):
                if option.upper() in ["BAUD", "STOPBITS", "PARITY", "HANDSHAKE", "BLOCKSIZE", "DELIM"]:
                    self.instrCo.set(section, option, self.appCo.get(section, option))
        self.instrCo.write()
            
HELP_STRING = \
"""

RunSerial2Socket.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
  
    return configFile
    
if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    app = SingleInstance("RunSerial2Socket")
    if not app.alreadyrunning():
        RunSerial2Socket(configFile)