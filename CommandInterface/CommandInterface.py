"""
File Name: CommandInterface.py
Purpose: This is the module responsible for handling ascii command interface.

File History:
    06-10-29 ytsai Created file
    08-01-18 sze   Use datetime rather than time for improved resolution
    08-09-18 alex  Replaced SortedConfigParser with CustomConfigObj
    09-07-03 alex  Tested and debugged both serial and socket interfaces
    09-07-22 alex  Supported more command sets. Supported multiple concentration reporting. Used semicolon instead of tab.  

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = "CommandInterface"
APP_DESCRIPTION = "Command interface (serial or Ethernet)"
__version__ = 1.0

import os
import sys
import time
import datetime 
import getopt
import re
import threading
import Queue
from inspect import isclass
from numpy import mean

import SerialInterface, SocketInterface
from Host.InstMgr.InstMgr import INSTMGR_SHUTDOWN_PREP_SHIPMENT, INSTMGR_SHUTDOWN_HOST_AND_DAS, MAX_ERROR_LIST_NUM
from Host.Common import CmdFIFO, Listener, TextListener
from Host.Common import MeasData
from Host.Common.SharedTypes import RPC_PORT_COMMAND_HANDLER, RPC_PORT_INSTR_MANAGER, RPC_PORT_DRIVER, \
                                    RPC_PORT_DATA_MANAGER, RPC_PORT_VALVE_SEQUENCER, RPC_PORT_MEAS_SYSTEM,\
                                    RPC_PORT_EIF_HANDLER, \
                                    BROADCAST_PORT_MEAS_SYSTEM, BROADCAST_PORT_DATA_MANAGER 
from Host.Common.StringPickler import StringAsObject,ObjAsString,ArbitraryObject
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

HEADER_SECTION               = 'HEADER'
PULSE_ANALYZER_SECTION       = 'PULSE_ANALYZER'
COMMAND_LIST_SECTION         = 'COMMAND_LIST'
ERROR_LIST_SECTION           = 'ERROR_LIST'
ERROR_MAP_SECTION            = 'INSTR_ERROR_MAP'
DEFAULT_INI_FILE             = "CommandInterface.ini"
ARG_DELIMITER                = ' '

MAX_COMMAND_QUEUE_SIZE       = 512
MAX_SCANTIME_QUEUE_SIZE      = 10

CR_CHAR         = '\r'
LF_CHAR         = '\n'
NULL_CHAR       = '\0'
SPACE_CHAR      = ' '
BACKSPACE_CHAR  = '\b'
TAB_CHAR        = '\t'
SPACE_CHAR      = ' '
ESC_CHAR        = 0x1b

PULSE_ANALYZER_STATUS_TABLE = {"waiting": "0", "armed": "1", "triggered": "2"}

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
if os.path.split(AppPath)[0] not in sys.path: sys.path.append(os.path.split(AppPath)[0])

class CommandInterface(object):
    def __init__(self):
        """ Initializes Interface """
        self.commandList   = []
        self.interface     = None
        self.terminate     = False
        self.pause         = False
        self.commandbuffer = ""
        self.echo          = False
        self.debug         = True

        # Create RPC channels
        self._DriverRpc  = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "CommandInterface")
        self._InstMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_INSTR_MANAGER, ClientName = "CommandInterface")
        self._DataMgrRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, ClientName = "CommandInterface")
        self._ValveSeqRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_VALVE_SEQUENCER, ClientName = "CommandInterface")
        self._MeasSystemRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_MEAS_SYSTEM, ClientName = "CommandInterface")
        self._EIFRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_EIF_HANDLER, ClientName = "CommandInterface")
        self.cmdThread = None
        
        # Create measurement system related variables
        self.measListener  = Listener.Listener(None, BROADCAST_PORT_DATA_MANAGER,
          ArbitraryObject, self.MeasFilter, retry = True, name="Command Interface", logFunc = Log)
        self._measData  = MeasData.MeasData()
        self._measLockDict  = {}
        self._measQueueDict = {}
        self.meas_source = None
        self.meas_label_list = []
        self.pulse_source = None
        self.pulse_label_list = []
        self.pulse_conc_list = []
        self._cdata = []
        self._ctime = 0
        self._lastctime = None
        self._scantimeLock  = threading.Lock()
        self._scantimeQueue = []

    def LoadConfig(self, filename ):
        """ Loads configuration file """
        self.config = CustomConfigObj(filename)

        # Get variables from config
        try:
            self.commandList = dict(self.config.list_items(COMMAND_LIST_SECTION))
            self.errorList   = dict(self.config.list_items(ERROR_LIST_SECTION))
            self.errorMap    = dict(self.config.list_items(ERROR_MAP_SECTION))
            interfaceName    = self.config.get(HEADER_SECTION,'interface')
            interfaceConfig  = dict(self.config.list_items(interfaceName.upper()))
            for i in interfaceConfig:
                interfaceConfig[i]=eval(interfaceConfig[i])
            self.echo     = self.config.get(HEADER_SECTION,'echo')
            self.appendLf = eval(self.config.get(HEADER_SECTION,'appendLf'))
            self.appendCr = eval(self.config.get(HEADER_SECTION,'appendCr'))
            self.meas_source =  self.config.get(HEADER_SECTION,'meas_source')
            for label in self.config.get(HEADER_SECTION,'meas_label').split(","):
                label = label.strip()
                self.meas_label_list.append(label)
                self._measQueueDict[label] = []
                self._measLockDict[label] = threading.Lock()
            self.pulse_source = self.config.get(PULSE_ANALYZER_SECTION,'analyzer_source')
            for label in self.config.get(PULSE_ANALYZER_SECTION,'analyzer_label').split(","):
                label = label.strip()
                self.pulse_label_list.append(label)
            for label in self.config.get(PULSE_ANALYZER_SECTION,'conc_label').split(","):
                label = label.strip()
                self.pulse_conc_list.append(label)
        except:
            msg = "Unable to load config. EXCEPTION: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print msg
            Log(msg, Level = 3)
            return False

        # Create error constants from config
        for name in self.errorList:
            args = tuple(self.errorList[name].split(',',1))
            setattr(__builtins__, name.upper(), "%s    %s" % args )

        # Setup response LF/CR
        self.append = ''
        if self.appendLf:
            self.append += LF_CHAR
        if self.appendCr:
            self.append += CR_CHAR

        # Load interface definitions
        try:
            interfaceModule  = __import__(interfaceName)
            interfaceClass   = getattr(interfaceModule, interfaceName)
            self.interface   = interfaceClass()
            self.interface.config( **interfaceConfig )
        except:
            msg = "Unable to configure interface. EXCEPTION: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print msg
            Log(msg, Level = 3)
            self.interface = None
            return False
        return True

    def RPC_Start(self):
        """ Starts interface """
        if self.interface == None:
            Log("Failed to start command interface.", Level = 3)
            return
        try:
            self.interface.open()
        except:
            msg = "Unable to open port for specified interface. EXCEPTION: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print msg
            Log(msg, Level = 3)
            return
        self.terminate = False
        self.pause = False
        createNewCmdThread = False
        if self.cmdThread:
            if not self.cmdThread.isAlive():
                createNewCmdThread = True
        else:
            createNewCmdThread = True
        if createNewCmdThread:
            print "Command Interface ready."
            Log("Command Interface ready.")
            self.cmdThread = threading.Thread(target = self.Run)
            self.cmdThread.setDaemon(True)
            self.cmdThread.start()

    # Not sure what this function is for
    #def RPC_Pause(self):
    #    """ Pause interface """
    #    if self.interface == None:
    #        return
    #    self.pause = True

    def RPC_Stop(self):
        """ Stops interface """
        if self.interface == None:
            return
        self.interface.close()
        self.terminate = True # This will kill self.cmdThread
        print "Stopping interface"
        Log("Stopping interface")

    def RPC_GetStatus(self):
        """ Returns status of interface """
        try:
            if self.cmdThread.isAlive():
                return "Normal operation"
            else:
                return "Interface terminated"
        except:
            return "Error"

    def RpcServerInit(self):
        """ Starts up rpc server """
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_COMMAND_HANDLER),
          ServerName = APP_NAME, ServerDescription = APP_DESCRIPTION,
          ServerVersion = __version__, threaded = True)
        for s in dir(self):
            attr = self.__getattribute__(s)
            if callable(attr) and (s.startswith("RPC_")) and (not isclass(attr)):
                self.RpcServer.register_function(attr, NameSlice = 4 )

    def Read(self):
        """ waits for a complete input line and returns command to caller """
        self.commandbuffer=""
        while self.terminate==False:
            try:
                s = self.interface.read()
                if s[0] == CR_CHAR:
                    if self.echo == True:
                        self.interface.write( CR_CHAR + LF_CHAR )
                    return self.commandbuffer
                elif s[0] == BACKSPACE_CHAR:
                    if self.echo == True:
                        self.interface.write( BACKSPACE_CHAR + SPACE_CHAR + BACKSPACE_CHAR )
                    if len(self.commandbuffer):
                        self.commandbuffer = self.commandbuffer[:-1]
                else:
                    self.commandbuffer += s
                    if self.echo == True:
                        self.interface.write( s )
            except:
                #msg = "Unable to read command. EXCEPTION: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                #print msg
                time.sleep(0.2)
                continue
                    
    def Run(self):
        """ Executes command """
        while ( self.terminate == False ):
            if self.pause == True:
                time.sleep(1)

            try:    
                cmdline = self.Read().strip(LF_CHAR)
                if len(cmdline)==0:
                    time.sleep(0.2)
                    continue
            except:
                #print "self.Read().strip(LF_CHAR) exception"
                time.sleep(0.2)
                continue

            cmdargs = cmdline.split(ARG_DELIMITER)
            cmd  = cmdargs[0].upper()
            args = cmdargs[1:]

            # Get command object
            try:
                func = getattr(self,cmd)
            except:
                if self.debug==True: print "unknown command: (%r)" % cmd
                self.PrintError( ERROR_COMMAND_NOT_RECOGNIZED )
                continue

            # Check against enable list
            if eval(self.commandList[cmd.lower()]) != 1:
                if self.debug==True: print "command disabled: (%r)" % cmd
                self.PrintError( ERROR_COMMAND_NOT_RECOGNIZED )
                continue

            # Check parameters.
            try:
                cmddef  = dict(self.config.list_items(cmd))

                if len(args) != eval(cmddef['numparameters']):
                    self.PrintError( ERROR_COMMAND_PARAMETERS )
                    continue

                matchFlag = True
                pdict = {}
                for i in range( eval(cmddef['numparameters']) ):
                    p = cmddef[ 'parameter'+str(i) ]
                    # Example:
                    # NumParameters=1
                    # Parameter0=Period,0|(\d+(.\d)?),Value between 0.1-1000s
                    pname,preg,phelp = p.split(",")
                    result = re.match(preg, args[i])
                    if result == None or len(args[i]) != result.end():
                        self.PrintError( ERROR_COMMAND_PARAMETERS )
                        self.Print("Parameter %d: expecting: %s" % (i+1,phelp))
                        matchFlag = False
                        break
                    pdict[pname]=eval(args[i])
                if matchFlag==False:
                    continue

            except:
                print "Exception %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                self.PrintError( ERROR_COMMAND_PARAMETERS )
                continue

            # Get status from Instrument Manager
            try:
                status = self._InstMgrRpc.INSTMGR_GetStatusRpc()
            except:
                print "Exception %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                self.PrintError( ERROR_COMMUNICATION_FAILED )
                status=0
                continue

            # Check status vs command configuration and return error appropriately
            errorFlag = False
            try:
                for i in range(eval(cmddef['numbits'])):
                    whichbit = eval(cmddef[ 'whichbit' + str(i) ])
                    state    = cmddef[ 'state' + str(i) ]
                    code     = eval(cmddef[ 'errorcode' + str(i) ])
                    if state == "TRUE":
                        state = 1
                    else:
                        state = 0
                    mask = 1 << whichbit
                    #print hex(status),hex(mask),hex(state),whichbit
                    if (status & mask) == state:
                        self.PrintError( code )
                        errorFlag = True
                        break
            except:
                print "Exception %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                self.PrintError( ERROR_COMMAND_FAILED )
                continue

            if errorFlag: continue

            # Execute command
            if self.debug: print ("%s:%r" % (func.__name__,pdict))
            try:
                func(**pdict)
            except:
                print "Exception %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                self.PrintError( ERROR_COMMAND_FAILED )
            if self.debug: print ("%s: done." % (func.__name__))

    def runRpcServer(self):
        self.RpcServerInit()
        self.RpcServer.serve_forever()
        
    def MeasFilter( self, dataDict ):
        """Filter for data broadcasts"""
        try:
            self._measData.ImportPickleDict( dataDict )
            if self.meas_source == self._measData.Source:
                self._ctime = self._measData.Time
                self._ctimeString = _TimeToString(datetime.datetime.fromtimestamp(self._ctime))
                self._cdata = []
                for label in self.meas_label_list:
                    if label in self._measData.Data:
                        cdata = self._measData.Data[label]
                        self._cdata.append(cdata)
                        self.addToMeasQueue(label, (self._ctimeString, cdata))
                if self._lastctime: 
                    self.addToScantimeQueue(self._ctime - self._lastctime)
                self._lastctime = self._ctime
        except:
            msg = "MeasFilter: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print msg
            Log(msg, Level = 3)

    def addToMeasQueue(self, label, timeDataTuple):
        self._measLockDict[label].acquire()
        try:
            if len(self._measQueueDict[label]) >= MAX_COMMAND_QUEUE_SIZE:
                self._measQueueDict[label].pop(0)
            self._measQueueDict[label].append(timeDataTuple)
        finally:
            self._measLockDict[label].release()

    def addToScantimeQueue(self, scantime):
        self._scantimeLock.acquire()
        try:
            if len(self._scantimeQueue) >= MAX_SCANTIME_QUEUE_SIZE:
                self._scantimeQueue.pop(0)
            self._scantimeQueue.append(scantime)
        finally:
            self._scantimeLock.release()
            
    def getAveScantime(self):
        if len(self._scantimeQueue) > 0:
            return mean(self._scantimeQueue)
        else:
            return 0

    # Measurement System functions
    def _MEAS_GETCONC(self):
        format = ("%.3f;" * len(self._cdata))[:-1]
        self.Print( format % tuple(self._cdata) )

    def _MEAS_GETCONCEX(self):
        format = "%s;" + ("%.3f;" * len(self._cdata))[:-1]
        self.Print( format % tuple([self._ctimeString]+self._cdata) )

    def _MEAS_GETBUFFER(self):
        for label in self.meas_label_list:
            count = len(self._measQueueDict[label])
            if count != 0:
                break
        self.Print("%d;" % count)
        for i in range(count):
            try:
                self._MEAS_GETBUFFERFIRST()
            except:
                break

    def _MEAS_GETBUFFERFIRST(self):
        retString = ""
        for label in self.meas_label_list:
            self._measLockDict[label].acquire()
            try:
                mtime,mdata = self._measQueueDict[label].pop(0)
                retString += ("%s;%0.3f;" % ( mtime,mdata ))
            except:
                self.PrintError( ERROR_MEAS_BUFFER_EMPTY )
            self._measLockDict[label].release()
        if retString != "":
            self.Print( retString )
                    
    def _MEAS_CLEARBUFFER(self):
        for label in self.meas_label_list:
            self._measLockDict[label].acquire()
            self._measQueueDict[label]=[]
            self._measLockDict[label].release()
        self.Print("OK")

    def _MEAS_GETSCANTIME(self):
        self.Print ( "%.3f" % self.getAveScantime() )

    def _MEAS_ENABLE(self):
        self._InstMgrRpc.INSTMGR_StartMeasureRpc()
        self.Print("OK")

    def _MEAS_DISABLE(self):
        self._InstMgrRpc.INSTMGR_StopMeasureRpc()
        self.Print("OK")

    def _MEAS_SET_TAGALONG_DATA(self, label, value):
        self._MeasSystemRpc.Backdoor.SetData(label, value)
        self.Print("OK")

    def _MEAS_GET_TAGALONG_DATA(self, label):
        (value, timeStamp) = self._MeasSystemRpc.Backdoor.GetData(label)
        self.Print(str(value))

    def _MEAS_DELETE_TAGALONG_DATA(self, label):
        self._MeasSystemRpc.Backdoor.DeleteData(label)
        self.Print("OK")

    # Instrument Manager functions
    def _INSTR_PARK(self):
        self._InstMgrRpc.INSTMGR_ShutdownRpc( INSTMGR_SHUTDOWN_PREP_SHIPMENT )
        self.Print("OK")

    def _INSTR_SHUTDOWN(self):
        self._InstMgrRpc.INSTMGR_ShutdownRpc( INSTMGR_SHUTDOWN_HOST_AND_DAS )
        self.Print("OK")

    def _INSTR_GETERROR(self):
        num = MAX_ERROR_LIST_NUM
        errorlist = self._InstMgrRpc.INSTMGR_GetErrorRpc(MAX_ERROR_LIST_NUM)
        if len(errorlist) == 0:
            self.Print( "EMPTY" )
            return

        for errortime,errorcode,errorname in errorlist:
            try:
                print "%r %r %r\n" % (errortime,errorcode,errorname)
                code = eval( self.errorMap[errorname.lower()].upper() )
                self.PrintError( code )
            except:
                print "Unknown system error %s. %s %s" % (errorname,sys.exc_info()[0], sys.exc_info()[1])
        self._InstMgrRpc.INSTMGR_ClearErrorRpc(num)

    def _INSTR_CLEARERRORS(self):
        num = MAX_ERROR_LIST_NUM
        self._InstMgrRpc.INSTMGR_ClearErrorRpc(num)
        self.Print("OK")

    def _INSTR_GETSTATUS(self):
        status = self._InstMgrRpc.INSTMGR_GetStatusRpc()
        self.Print(str(status))

    def _INSTR_GETTIME(self):
        msg = "%s" % ( _TimeToString(datetime.datetime.now()) )
        self.Print( msg )

    def _FLOW_DISABLEPUMP(self):
        self._InstMgrRpc.INSTMGR_disablePumpRpc()
        self.Print("OK")

    def _FLOW_START(self):
        self._InstMgrRpc.INSTMGR_startFlowRpc()
        self.Print("OK")

    def _FLOW_STOP(self):
        self._InstMgrRpc.INSTMGR_stopFlowRpc()
        self.Print("OK")

    # Electrical Interface functions
    def _EIF_ANALOGOUT_SETTRACKING(self, channel):
        isOK = self._EIFRpc.AO_SetTracking(int(channel))
        if isOK:
            self.Print("OK")
        else:
            self.PrintError(ERROR_EIF_INVALID_CHANNEL)
            
    def _EIF_ANALOGOUT_SETOUTPUT(self, channel, outputLevel):
        isOK = self._EIFRpc.AO_SetOutput(int(channel), float(outputLevel))
        if isOK:
            self.Print("OK")
        else:
            self.PrintError(ERROR_EIF_INVALID_CHANNEL)

    def _EIF_ANALOGOUT_SETREFERENCE(self, channel, measuredValue):
        isOK = self._EIFRpc.AO_SetReference(int(channel), float(measuredValue))
        if isOK:
            self.Print("OK")
        else:
            self.PrintError(ERROR_EIF_INVALID_CHANNEL)

    def _EIF_ANALOGOUT_CONFIGURE(self, channel, calSlope, calOffset, minOutput, maxOutput, bootmode, bootvalue, errorvalue, invalidvalue ):
        isOK = self._EIFRpc.AO_Configure( int(channel), float(calSlope), float(calOffset), float(minOutput), 
                                          float(maxOutput), int(bootmode), float(bootvalue), float(errorvalue), float(invalidvalue) )
        if isOK:
            self.Print("OK")
        else:
            self.PrintError(ERROR_EIF_INVALID_CHANNEL)

    def _EIF_ANALOGOUT_GETINFO(self, channel):
        self.Print(self._EIFRpc.AO_GetInfo( int(channel), getStr=True ))
        
    # Pulse Analyzer functions
    def _PULSE_GETBUFFERFIRST(self):
        retString = ""
        for label in self.pulse_label_list:
            try:
                (data, timeStamp) = self._DataMgrRpc.PulseAnalyzer_GetData(self.pulse_source, label, fromFirst = True, numData = 1)[0]
                self._DataMgrRpc.PulseAnalyzer_ClearDataBuffer(self.pulse_source, label, timeStamp)
                timeString = _TimeToString(datetime.datetime.fromtimestamp(timeStamp))
                retString += ("%s;%0.3f;" % (timeString, data))
            except:
                self.PrintError( ERROR_PULSE_BUFFER_EMPTY )
        if retString != "":
            self.Print( retString )

    def _PULSE_GETBUFFER(self):
        count = 0
        dataDict = {}
        for label in self.pulse_label_list:
            dataList = self._DataMgrRpc.PulseAnalyzer_GetData(self.pulse_source, label, fromFirst = True, numData = "all")
            dataDict[label] = dataList
            self._DataMgrRpc.PulseAnalyzer_ClearDataBuffer(self.pulse_source, label)
            count = max(count, len(dataList))
        self.Print("%d;" % count)
        for idx in range(count):
            retString = ""
            for label in self.pulse_label_list:
                if len(dataDict[label]) > 0:
                    try:
                        (data, timeStamp) = dataDict[label][idx]
                    except:
                        (data, timeStamp) = dataDict[label][-1]
                    timeString = _TimeToString(datetime.datetime.fromtimestamp(timeStamp))
                    retString += ("%s;%0.3f;" % (timeString, data))
            if retString != "":
                self.Print( retString )

    def _PULSE_CLEARBUFFER(self):
        for label in self.pulse_label_list:
            self._DataMgrRpc.PulseAnalyzer_ClearDataBuffer(self.pulse_source, label)
        self.Print("OK")

    def _PULSE_GETSTATUS(self):
        retString = ""
        for conc in self.pulse_conc_list:
            status = self._DataMgrRpc.PulseAnalyzer_GetStatus(self.pulse_source, conc)
            retString += "%s;" % PULSE_ANALYZER_STATUS_TABLE[status]
        if retString != "":
            self.Print( retString )

    # Valve Sequencer functions
    def _VALVES_SEQ_START(self):
        self._ValveSeqRpc.startValveSeq()
        self.Print("OK")

    def _VALVES_SEQ_STOP(self):
        self._ValveSeqRpc.stopValveSeq()
        self.Print("OK")

    def _VALVES_SEQ_READSTATE(self): 
        self.Print(self._ValveSeqRpc.getValveSeqStatus())

    def _VALVES_SEQ_SETSTATE(self, valveMask):
        self._ValveSeqRpc.stopValveSeq()
        self._ValveSeqRpc.setValves(int(valveMask))
        self._VALVES_SEQ_READSTATE()

    # Print functions
    def Print(self, msg, debug=True):
        if self.interface != None:
            try:
                self.interface.write( msg + self.append )
                if debug: print msg + self.append
            except:
                print "Failed to write to interface"
                
    def PrintError( self, code ):
        msg = ("ERR:%s\t%s"+ self.append) % ( code, _TimeToString(datetime.datetime.now()))
        if self.interface != None:
            try:
                self.interface.write( msg )
                print msg
            except:
                print "Failed to write error message to interface"

def _TimeToString( t ):
    return t.strftime("%y/%m/%d %H:%M:%S") + (".%03d" % (t.microsecond/1000,))

def Usage():
    print "[-h] [-c configfile]"

def Main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "config="])
    except getopt.GetoptError:
        # print help information and exit:
        Usage()
        sys.exit(2)

    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_INI_FILE

    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()
        if o in ("-c", "--config"):
            configFile = a

    app = CommandInterface()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        app.LoadConfig( configFile )
        app.RPC_Start()
        app.runRpcServer()
        app.RPC_Stop()
        Log("Exiting program")
    except Exception, E:
        if app.debug: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))
        
if __name__ == "__main__" :
    Main()
