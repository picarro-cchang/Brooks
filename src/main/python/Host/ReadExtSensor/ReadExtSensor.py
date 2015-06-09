#!/usr/bin/python
#
"""
File Name: ReadExtSensor.py
Purpose: Read external sensor data and insert new data columns in analyzer output

File History:
    2010-10-29 alex  Created

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""
APP_NAME = "ReadExtSensor"
APP_DESCRIPTION = "Read External Device Data"
__version__ = 1.0
DEFAULT_CONFIG_NAME = "ReadExtSensor.ini"

import sys
import time
import os.path
import threading

from Host.Common import CmdFIFO
from Host.Common.SerIntrf import SerIntrf
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SharedTypes import RPC_PORT_MEAS_SYSTEM, RPC_PORT_READ_EXT_SENSOR
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

class ReadExtSensor(object):
    def __init__(self, configFile):
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_READ_EXT_SENSOR),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)

        self.measSystemRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % (RPC_PORT_MEAS_SYSTEM,),ClientName="ReadExtSensor")

        config = CustomConfigObj(configFile)
        self.comPort = config.get("Setup", "comPort", "")
        self.queryCommand = config.get("Setup", "queryCommand")
        self.sampleInterval = 1.0/config.getfloat("Setup", "sampleRateHz")
        self.dataColumn = config.get("Setup", "dataColumn")
        self.slope = config.getfloat("Setup", "slope")
        self.offset = config.getfloat("Setup", "offset")
        self.externalSensor = None
        self.externalSensorFound = False

        if self.comPort.strip() == "":
            # Find the dynamic COM port
            rotValve = None
            for p in range(100):
                print "Testing COM%d...\n" % (p+1)
                if self.externalSensor:
                    self.externalSensor.close()
                    self.externalSensor = None
                try:
                    self.externalSensor = SerIntrf(p)
                    self.externalSensor.open()
                    time.sleep(3)
                except:
                    continue
                try:
                    self.externalSensor.sendString("us")
                    status = self.externalSensor.getLine()
                    if "ok" in status:
                        print "External sensor found at COM%d...\n"% (p+1)
                        self.externalSensorFound = True
                        break
                except:
                    pass

            if not self.externalSensorFound:
                print "External sensor not found.\n"
                if self.externalSensor:
                    self.externalSensor.close()
                    self.externalSensor = None
                raise Exception, "External sensor not available"
        else:
            try:
                self.comPort = "COM%d" % (int(self.comPort)+1)
            except:
                pass
            self.externalSensor = SerIntrf(self.comPort)
            self.externalSensor.open()
            self.externalSensorFound = True
            print "External sensor located at %s...\n"% (self.comPort)

    def read(self):
        try:
            while True:
                try:
                    self.externalSensor.sendString(self.queryCommand)
                    reading = self.offset + float(self.externalSensor.getLine())*self.slope
                    self.measSystemRpc.Backdoor.SetData(self.dataColumn, reading)
                except Exception, err:
                    print err
                time.sleep(self.sampleInterval)
        finally:
            self.externalSensor.close()
        print "ReadExtSensor stopped."

    def runApp(self):
        rpcThread = threading.Thread(target = self.read)
        rpcThread.setDaemon(True)
        rpcThread.start()
        self.RpcServer.serve_forever()

HELP_STRING = \
""" readExtSensor.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help.
-c                   Specify a config file.  Default = "./ReadExtSensor.ini"
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt

    shortOpts = 'hc:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)

    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if '-h' in options:
        PrintUsage()
        sys.exit()

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return (configFile)

def main():
    #Get and handle the command line options...
    configFile = HandleCommandSwitches()
    Log("%s application started." % APP_NAME)
    print "%s application started." % APP_NAME
    try:
        app = ReadExtSensor(configFile)
        app.runApp()
    except Exception, E:
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))

if __name__ == "__main__":
    main()