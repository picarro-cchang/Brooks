import os
import sys
import time
import serial
import subprocess
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
NUM_PORTS = 4

class RunSerial2Socket(object):
    def __init__(self, configFile):
        self.appCo = CustomConfigObj(configFile)
        iniAbsBasePath = os.path.split(os.path.abspath(configFile))[0]
        instrConfigFile = os.path.abspath(os.path.join(iniAbsBasePath, self.appCo.get("SETUP", "INSTRCONFIG")))
        exeFile = os.path.abspath(os.path.join(iniAbsBasePath, self.appCo.get("SETUP", "EXE")))
        self.instrCo = CustomConfigObj(instrConfigFile)
        self.updateIni(self.findPorts())
        info = subprocess.STARTUPINFO()
        subprocess.Popen([exeFile, str(TCP_PORT_PERIPH_INTRF), instrConfigFile], startupinfo=info)
        
    def findPorts(self):
        portList = []
        skipPortNum = [int(i) for i in self.appCo.get("SETUP", "SKIPPORTNUM").split(",")]
        for p in range(100):
            if p not in skipPortNum:
                try:
                    ser = serial.Serial(p)
                    if len(portList) == 0 or (p-1) in portList:
                        portList.append(p)
                        if len(portList) == NUM_PORTS:
                            print "%d consecutive COM ports found" % NUM_PORTS
                            break
                    else:
                        portList = []
                except:
                    continue
        print portList
        return portList

    def updateIni(self, portList):
        if not portList:
            return
        for i in range(len(portList)):
            p = portList[i]
            self.instrCo.set("PORTS", "PORT%d" % i, r"\\.\COM%d" % (p+1))
            section = "PORT%d" % i
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