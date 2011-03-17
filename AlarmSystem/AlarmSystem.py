#!/usr/bin/python
#
"""
File Name: AlarmSystem.py
Purpose:
    The alarm system application is responsible for monitoring of gas concentration(s) and reporting alarm(s)
    
Notes:
    An alarm is triggered if the concentration is: 
        1. higher than a configured alarm threshold,
        2. lower than configured alarm threshold,
        3. in between two configured thresholds, or
        4. outside two configured thresholds.
    An alarm is cleared if the concentration is: 
        1. lower than configured clear threshold,
        2. higher than configured clear threshold,
        3. outside two clear thresholds, or
        4. inside two configured thresholds.
        
    Each alarm is configured to operate in one and only one of the four modes listed above.

    The alarm system broadcasts the alarm status register whenever a set or clear bit of one of the alarms changes.

    The configuration info, i.e, alarm name, measurement source, enabled, alarm threshold, clear threshold, mode,
    of each alarm is stored in AlarmSystem.ini. The alarm and clear thresholds are the only configs that can be changed
    on the fly via an RPC call.  Everything else can only be changed by modifying the AlarmSystem.ini.

File History:
    06-11-xx al    In progress
    06-12-18 al    Started using AppStatus class
    06-12-19 al    Removed units and shortened Front panel display message.
    06-12-20 al    Removed local definition of MeasData
    07-04-17 sze   Changed alarm display messages to be one origin
    08-09-18 alex  Replaced SortedConfigParser with CustomConfigObj

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

####
## Set constants for this file...
####
APP_NAME = "AlarmSystem"
APP_VERSION = 1.0
APP_DESCRIPTION = "The alarm system"
_CONFIG_NAME = "AlarmSystem.ini"

ALARM_SYSTEM_RPC_SUCCESS = 0
ALARM_SYSTEM_RPC_NOT_READY = -1
ALARM_SYSTEM_RPC_FAILED = -2

import sys
import os
import getopt
import Queue
import time
import threading
import socket #for transmitting data to the fitter
import struct #for converting numbers to byte format
import time
import traceback
from inspect import isclass

from Host.Common import CmdFIFO, StringPickler, Listener, Broadcaster
from Host.Common.SharedTypes import RPC_PORT_ALARM_SYSTEM, BROADCAST_PORT_DATA_MANAGER, STATUS_PORT_ALARM_SYSTEM, RPC_PORT_INSTR_MANAGER
from Host.Common.SafeFile import SafeFile, FileExists
from Host.Common.InstErrors import *
from Host.Common.AppStatus import AppStatus
from Host.Common.MeasData import MeasData
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    from time import clock as TimeStamp
else:
    from time import time as TimeStamp

ALLOWED_MODES = ["Higher", "Lower", "Inside", "Outside"]

class Alarm(object):
    """Class to manage alarms"""
    COLUMN_WIDTH = 26
    def __init__(self):

        self.Name = ""
        self.Enabled = False
        self.SourceScript = ""
        self.Port = BROADCAST_PORT_DATA_MANAGER
        self.Mode = ""
        self.AlarmThreshold1 = 0
        self.AlarmThreshold2 = 0
        self.ClearThreshold1 = 0
        self.ClearThreshold2 = 0
        self.AlarmSet = False


    def _LoadConfig(self, cp, section):

        self.Name = cp.get(section, "name")
        self.Data = cp.get(section, "data")
        self.Enabled = cp.getboolean(section, "enabled")
        self.SourceScript = cp.get(section, "sourcescript")
        self.Port = cp.getint(section, "port")
        self.Mode = cp.get(section, "mode")

        if self.Mode == "Higher" or self.Mode == "Lower":
            # these modes only use one set of thresholds
            self.AlarmThreshold1 = cp.getfloat(section, "alarmthreshold1")
            self.ClearThreshold1 = cp.getfloat(section, "clearthreshold1")
        elif self.Mode == "Inside" or self.Mode == "Outside":
            # these modes need two sets of thresholds
            self.AlarmThreshold1 = cp.getfloat(section, "alarmthreshold1")
            self.ClearThreshold1 = cp.getfloat(section, "clearthreshold1")
            self.AlarmThreshold2 = cp.getfloat(section, "alarmthreshold2")
            self.ClearThreshold2 = cp.getfloat(section, "clearthreshold2")
        else:
            raise Exception("AlarmSystem:Invalid Mode")

    def _Monitor(self, Time, DataDict):

        action = None
        if self.Data in DataDict:
            value = DataDict[self.Data]
            if self.Mode == "Higher":
                if self.AlarmSet == False:
                    if value > self.AlarmThreshold1:
                        self.AlarmSet = True
                        action = "Set"
                else:
                    if value <= self.ClearThreshold1:
                        self.AlarmSet = False
                        action = "Clear"
            elif self.Mode == "Lower":
                if self.AlarmSet == False:
                    if value < self.AlarmThreshold1:
                        self.AlarmSet = True
                        action = "Set"
                else:
                    if value >= self.ClearThreshold1:
                        self.AlarmSet = False
                        action = "Clear"
            elif self.Mode == "Inside":
                if self.AlarmSet == False:
                    if value > self.AlarmThreshold2 and value < self.AlarmThreshold1:
                        self.AlarmSet = True
                        action = "Set"
                else:
                    if value <= self.ClearThreshold2 or value >= self.ClearThreshold1:
                        self.AlarmSet = False
                        action = "Clear"
            elif self.Mode == "Outside":
                if self.AlarmSet == False:
                    if value < self.AlarmThreshold2:
                        self.AlarmSet = True
                        action = "Set"
                        self.lowSide = True
                    elif value > self.AlarmThreshold1:
                        self.AlarmSet = True
                        action = "Set"
                        self.lowSide = False
                else:
                    if self.lowSide == True:
                        # if alarm was set as a result of being low then value has to be between
                        # clearThreshold2(low clear threshold) and AlarmThreshold1(high alarm threshold) to be cleared
                        if value >= self.ClearThreshold2 and value <= self.AlarmThreshold1:
                            self.AlarmSet = False
                            action = "Clear"
                    else:
                        # if alarm was set as a result of being high then value has to be between
                        # AlarmThreshold2(low alarm threshold) and ClearThreshold1(high clear threshold) to be cleared
                        if value >= self.AlarmThreshold2 and value <= self.ClearThreshold1:
                            self.AlarmSet = False
                            action = "Clear"

        return action

####
## Classes...
####
class AlarmSystem(object):
    """This is Alarm System object."""
    def __init__(self, configPath, noInstMgr=False):

        if __debug__: Log("Loading config options.")
        self.configPath = configPath
        self.noInstMgr = noInstMgr
        
        self.AlarmDict = {}    # contains alarm config objects for each alarm section found in the config file.
        self.SrcDict = {}      # Dictionary of source scripts which contains list of alarm names, which is used for filtering of broadcast data.
        self.PortDict = {}
        self.lastStatus = None
        self.md = MeasData()

        if __debug__: Log("Setting up RPC server.")
        #Now set up the RPC server...
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_ALARM_SYSTEM),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = APP_VERSION,
                                                threaded = True)

        if __debug__: Log("Registering RPC functions.")
        #Register the rpc functions...
        self.RpcServer.register_function(self.ALARMSYSTEM_getNameRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_getModeRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_setModeRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_isEnabledRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_enableRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_disableRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_setAlarmThresholdRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_getAlarmThresholdRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_setClearThresholdRpc)
        self.RpcServer.register_function(self.ALARMSYSTEM_getClearThresholdRpc)

        self.AppStatus = AppStatus(0,STATUS_PORT_ALARM_SYSTEM,APP_NAME)

        if not self.noInstMgr:
            #Set up instrument manager rpc connection to report errors
            self.InstrMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER,
                                                          APP_NAME,
                                                          IsDontCareConnection = True)

    def _LoadConfigFile(self):
        """Creates log dict which store DataLog object for every log section defined in confile file.
           Also creates SrcDict and PortDict which contains lists of DataLog objects for each source scripts and port number.
        """
        self.cp = CustomConfigObj(self.configPath)
        self.NumAlarms = self.cp.getint("MainConfig", "numalarms")

        count = 0
        sectionList = self.cp.list_sections()
        for section in sectionList:
            if "Alarm_" in section:
                config = Alarm()
                #load config from .ini
                try:
                    config._LoadConfig(self.cp, section)
                except:
                    tbMsg = traceback.format_exc()
                    Log("Exception occurred on Alarm load config:",Data = dict(Note = "<See verbose for debug info>"),Level = 3,Verbose = tbMsg)
                    continue

                self.AlarmDict[section]=config

                # update Source Script Dict
                if config.SourceScript not in self.SrcDict:
                    self.SrcDict[config.SourceScript] = [section]
                else:
                    self.SrcDict[config.SourceScript].append(section)

                # update Port Dict
                if config.Port not in self.PortDict:
                    self.PortDict[config.Port] = [section]
                else:
                    self.PortDict[config.Port].append(section)

                count += 1

        if self.NumAlarms != count:
            Log("Invalid number of alarm configs.", Data = dict(NumAlarms = self.NumAlarms), Level = 2)

    def _DataListener(self, dataMgrObject):

        self.md.ImportPickleDict(dataMgrObject)
        
        # check to make sure this a broadcast that I'm interested in
        if self.md.Source in self.SrcDict:
            # iterate through all alarm object found in the list
            for alarmName in self.SrcDict[self.md.Source]:
                if alarmName in self.AlarmDict:
                    if self.AlarmDict[alarmName].Enabled:
                        action = self.AlarmDict[alarmName]._Monitor(self.md.Time, self.md.Data)

                        if action == "Set":
                            num = (int(alarmName.lstrip("Alarm_"))-1)
                            bitMask = 1 << num
                            self.AppStatus._Status |= bitMask
                            self.AppStatus._SendStatus()
                            if __debug__: Log("%s Set: Alarm=%s Mode=%s Data=%s Value=%f"%(alarmName,self.AlarmDict[alarmName].Name, self.AlarmDict[alarmName].Mode, self.AlarmDict[alarmName].Data, self.md.Data[self.AlarmDict[alarmName].Data]))
                            if __debug__: Log("Alarm1=%d Alarm2=%d Clear1=%d Clear2=%d" %(self.AlarmDict[alarmName].AlarmThreshold1, self.AlarmDict[alarmName].AlarmThreshold2, self.AlarmDict[alarmName].ClearThreshold1, self.AlarmDict[alarmName].ClearThreshold2))
                            if not self.noInstMgr:
                                self.InstrMgrRpc.INSTMGR_SendDisplayMessageRpc("Alarm %d Raised" %(num+1,))
                        elif action == "Clear":
                            num = (int(alarmName.lstrip("Alarm_"))-1)
                            bitMask = 1 << num
                            self.AppStatus._Status &= ~bitMask
                            self.AppStatus._SendStatus()
                            if __debug__: Log("%s Clear: Alarm=%s Mode=%s Data=%s Value=%f"%(alarmName,self.AlarmDict[alarmName].Name, self.AlarmDict[alarmName].Mode, self.AlarmDict[alarmName].Data, self.md.Data[self.AlarmDict[alarmName].Data]))
                            if __debug__: Log("Alarm1=%d Alarm2=%d Clear1=%d Clear2=%d" %(self.AlarmDict[alarmName].AlarmThreshold1, self.AlarmDict[alarmName].AlarmThreshold2, self.AlarmDict[alarmName].ClearThreshold1, self.AlarmDict[alarmName].ClearThreshold2))
                            if not self.noInstMgr:
                                self.InstrMgrRpc.INSTMGR_SendDisplayMessageRpc("Alarm %d Cleared" %(num+1,))

            if __debug__: 
                if self.lastStatus and self.lastStatus !=self.AppStatus._Status:
                    Log("Alarm Status %d" % self.AppStatus._Status)
            self.lastStatus = self.AppStatus._Status

    def ALARMSYSTEM_start(self):
        """Called to start the alarm system."""

        if not FileExists(self.configPath):
            Log("File not found.", Data = dict(Path = self.configPath), Level = 2)
            raise Exception("File '%s' not found." % self.configPath)

        self._LoadConfigFile()

        for port,value in self.PortDict.iteritems():
            self.Listener = Listener.Listener(None, port, StringPickler.ArbitraryObject, self._DataListener, retry = True,
                                              name = "Alarm System", logFunc = Log)

        self.RpcServer.serve_forever()
        if __debug__: Log("Shutting Down Data Logger.")

    def ALARMSYSTEM_getNameRpc(self, alarmIndex):
        """Returns the name of the alarm specified by alarmIndex. Note: alarmIndex is one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                return ALARM_SYSTEM_RPC_SUCCESS, self.AlarmDict[alarmName].Name
            else:
                return ALARM_SYSTEM_RPC_FAILED, ""
        else:
            return ALARM_SYSTEM_RPC_FAILED, ""

    def ALARMSYSTEM_getModeRpc(self, alarmIndex):
        """Returns the mode of the alarm specified by alarmIndex. Note: alarmIndex is one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                return ALARM_SYSTEM_RPC_SUCCESS, self.AlarmDict[alarmName].Mode
            else:
                return ALARM_SYSTEM_RPC_FAILED, ""
        else:
            return ALARM_SYSTEM_RPC_FAILED, ""

    def ALARMSYSTEM_setModeRpc(self, alarmIndex, mode):
        """Called to set the alarm mode specified by alarmIndex. Note: alarmIndex is one based."""
        if mode not in ALLOWED_MODES:
            return ALARM_SYSTEM_RPC_FAILED
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                self.AlarmDict[alarmName].Mode = mode
                self.cp.set(alarmName, "mode", mode)
                fp = open(self.configPath,"wb")
                self.cp.write(fp)
                fp.close()
                return ALARM_SYSTEM_RPC_SUCCESS
            else:
                return ALARM_SYSTEM_RPC_FAILED
        else:
            return ALARM_SYSTEM_RPC_FAILED
            
    def ALARMSYSTEM_isEnabledRpc(self, alarmIndex):
        """Returns the enabled status of the alarm specified by alarmIndex. Note: alarmIndex is one based."""
        """Returns the mode of the alarm specified by alarmIndex. Note: alarmIndex is one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                return ALARM_SYSTEM_RPC_SUCCESS, self.AlarmDict[alarmName].Enabled
            else:
                return ALARM_SYSTEM_RPC_FAILED, False
        else:
            return ALARM_SYSTEM_RPC_FAILED, False

    def ALARMSYSTEM_enableRpc(self, alarmIndex):
        """Called to enable the alarm specified by alarmIndex. Note: alarmIndex is one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                self.AlarmDict[alarmName].Enabled = True

                self.cp.set(alarmName,"enabled", "true")
                fp = open(self.configPath,"wb")
                self.cp.write(fp)
                fp.close()

                return ALARM_SYSTEM_RPC_SUCCESS
            else:
                return ALARM_SYSTEM_RPC_FAILED
        else:
            return ALARM_SYSTEM_RPC_FAILED

    def ALARMSYSTEM_disableRpc(self, alarmIndex):
        """Called to disable the alarm specified by alarmIndex. Note: alarmIndex is one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                self.AlarmDict[alarmName].Enabled = False

                self.cp.set(alarmName,"enabled", "false")
                fp = open(self.configPath,"wb")
                self.cp.write(fp)
                fp.close()

                return ALARM_SYSTEM_RPC_SUCCESS
            else:
                return ALARM_SYSTEM_RPC_FAILED
        else:
            return ALARM_SYSTEM_RPC_FAILED

    def ALARMSYSTEM_getAlarmThresholdRpc(self, alarmIndex, thresholdIndex):
        """Called to get the alarm threshold specified by alarmIndex and thresholdIndex. Note: alarmIndex and thresholdIndex are one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                if thresholdIndex == 1:
                    threshold = self.AlarmDict[alarmName].AlarmThreshold1
                elif thresholdIndex == 2:
                    threshold = self.AlarmDict[alarmName].AlarmThreshold2
                else:
                    return ALARM_SYSTEM_RPC_FAILED, 0

                return ALARM_SYSTEM_RPC_SUCCESS, threshold
            else:
                return ALARM_SYSTEM_RPC_FAILED, 0
        else:
            return ALARM_SYSTEM_RPC_FAILED, 0

    def ALARMSYSTEM_setAlarmThresholdRpc(self, alarmIndex, thresholdIndex, threshold):
        """Called to set the alarm threshold specified by alarmIndex and thresholdIndex. Note: alarmIndex and thresholdIndex are one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                if thresholdIndex == 1:
                    self.AlarmDict[alarmName].AlarmThreshold1 = threshold
                elif thresholdIndex == 2:
                    self.AlarmDict[alarmName].AlarmThreshold2 = threshold
                else:
                    return ALARM_SYSTEM_RPC_FAILED

                self.cp.set(alarmName,"alarmthreshold%d" %thresholdIndex, threshold)
                fp = open(self.configPath,"wb")
                self.cp.write(fp)
                fp.close()

                return ALARM_SYSTEM_RPC_SUCCESS
            else:
                return ALARM_SYSTEM_RPC_FAILED
        else:
            return ALARM_SYSTEM_RPC_FAILED

    def ALARMSYSTEM_getClearThresholdRpc(self, alarmIndex, thresholdIndex):
        """Called to get the clear threshold specified by alarmIndex and thresholdIndex. Note: alarmIndex and thresholdIndex are one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                if thresholdIndex == 1:
                    threshold = self.AlarmDict[alarmName].ClearThreshold1
                elif thresholdIndex == 2:
                    threshold = self.AlarmDict[alarmName].ClearThreshold2
                else:
                    return ALARM_SYSTEM_RPC_FAILED, 0

                return ALARM_SYSTEM_RPC_SUCCESS, threshold
            else:
                return ALARM_SYSTEM_RPC_FAILED, 0
        else:
            return ALARM_SYSTEM_RPC_FAILED, 0

    def ALARMSYSTEM_setClearThresholdRpc(self, alarmIndex, thresholdIndex, threshold):
        """Called to set the clear threshold specified by alarmIndex and thresholdIndex. Note: alarmIndex and thresholdIndex are one based."""
        if alarmIndex <= self.NumAlarms:
            alarmName = "Alarm_%d" % alarmIndex
            if alarmName in self.AlarmDict:
                if thresholdIndex == 1:
                    self.AlarmDict[alarmName].ClearThreshold1 = threshold
                elif thresholdIndex == 2:
                    self.AlarmDict[alarmName].ClearThreshold2 = threshold
                else:
                    return ALARM_SYSTEM_RPC_FAILED

                self.cp.set(alarmName,"clearthreshold%d" %thresholdIndex, threshold)
                fp = open(self.configPath,"wb")
                self.cp.write(fp)
                fp.close()

                return ALARM_SYSTEM_RPC_SUCCESS
            else:
                return ALARM_SYSTEM_RPC_FAILED
        else:
            return ALARM_SYSTEM_RPC_FAILED

HELP_STRING = \
"""\
AlarmSystem.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different alarm config file.  Default = "./AlarmSystem.ini"

--no_inst_mgr  Run without Instrument Manager.
"""

def PrintUsage():
    print HELP_STRING

def HandleCommandSwitches():
    shortOpts = 'hc:'
    longOpts = ["help", "no_inst_mgr"]
    
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
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
    configFile = os.path.dirname(AppPath) + "/" + _CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        Log ("Config file specified at command line: %s" % configFile)
    
    noInstMgr = False
    if "--no_inst_mgr" in options:
        noInstMgr = True
        
    return (configFile, noInstMgr)

def main():
    #Get and handle the command line options...
    configFile, noInstMgr = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        app = AlarmSystem(configFile, noInstMgr)
        app.ALARMSYSTEM_start()
        Log("Exiting program")
    except Exception, E:
        if __debug__: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))

if __name__ == "__main__":
    try:
        main()
    except:
        tbMsg = traceback.format_exc()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
    Log("Exiting program")
    sys.stdout.flush()
