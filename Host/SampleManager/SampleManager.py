# File Name: SampleManager.py
#
# Purpose: This is the module responsible for managing sample gas flow and
#          cavity pressure.
#
# File History:
# 06-11-06 ytsai   Created file
# 07-01-17 Sze   Corrected bug in pressure stabilization loop
# 08-09-18 alex  Replaced ConfigParser with CustomConfigObj
# 08-12-10 alex  Made constant InletValve and OutletValve all uppercase
# 08-12-23 alex  Added RPC call to skip pressure check in _Monitor() (in order to run pulse holder)

APP_NAME = 'SampleManager'

import os, sys, time, getopt, ctypes
if "../Common" not in sys.path: sys.path.append("../Common")
if "../SampleManager" not in sys.path: sys.path.append("../SampleManager")

import socket
from inspect import isclass
from operator import isNumberType
from CustomConfigObj import CustomConfigObj
import sets
import CmdFIFO
from InstErrors import INST_ERROR_OKAY
from SharedTypes import RPC_PORT_DRIVER, RPC_PORT_SAMPLE_MGR, BROADCAST_PORT_SENSORSTREAM, STATUS_PORT_SAMPLE_MGR
import Host.autogen.interface as GlobalDefs
from Listener import Listener
import threading, Queue
from StringPickler import StringAsObject
import AppStatus

from EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

__version__              = 1.0

MAX_COMMAND_QUEUE_SIZE   = 2
HEADER_SECTION           = 'MAIN'
DEFAULT_INI_FILE         = 'SampleManager.ini'
DEFAULT_CONFIGS          = 'DEFAULT_CONFIGS'
INLETVALVE               = 0
OUTLETVALVE              = 1

DEFAULT_SLEEP_INTERVAL   = 1

MAX_SOLENOID_VALVES_QUEUE_SIZE = 6

# Status bits of for Sample Manager
SAMPLEMGR_STATUS_STABLE         = 0x0010
SAMPLEMGR_STATUS_FLOWING        = 0x0020
SAMPLEMGR_STATUS_FLOW_STARTED   = 0x0040
SAMPLEMGR_STATUS_PARKED         = 0x0080
SAMPLEMGR_STATUS_PURGED         = 0x0100
SAMPLEMGR_STATUS_PREPARED       = 0x0200
SAMPLEMGR_STATUS_PRESSURE_LOW   = 0x0400
SAMPLEMGR_STATUS_PRESSURE_HIGH  = 0x0800
SAMPLEMGR_STATUS_VALVE_DAC_LOW  = 0x1000
SAMPLEMGR_STATUS_VALVE_DAC_HIGH = 0x2000

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

###############################################################################
class SampleManagerBaseMode(object):
    """ Base class for various Sample Manager modes. All 'scripts' must use this base class.

        Important Notations:
        * Functions with prefix _RPC_ will be exported (read-type routines)
        * Functions with prefix _LPC_ are routines that modifies valves/pressure (ie. write-type routines
          that changes states). We do not want to export these to limit direct access, but allow calls
          locally and from inherit classes (inside scripts).

        Variables:
        * _terminateCalls: Used to terminate 'verify-only'/long running RPC.
                      If _terminateCalls is true, any call to _LPC routines will abort when invoked.
                      Any long running RPC should insert check for _terminateCalls and abort when true.
        """

    def __init__(self,config):
        """Initialize"""
        self._DriverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "SampleManager")
        self.config     = dict(config)
        self._create_var_from_config( self.config )
        self._terminateCalls   = False
        self.debug  = True
        self.verbose = False
        self._pressure = 0
        self._inletDacValue = ''
        self._outletDacValue = ''
        self._status = AppStatus.AppStatus( 0, STATUS_PORT_SAMPLE_MGR, APP_NAME)

        # Solenoid valves variables
        self._valveEvent = threading.Event()    # Event to run script
        self._valveEvent.clear()
        self._valveScript              = '',0,0     # Script name
        self._valveConcentration       = 0      # Current concentration of valve
        self._valveOpened              = 0      # Current valve opened
        self._terminateSolenoidControl = False  # Used to terminate script early

        self._pressureLockCount      = 0
        self._pressureLockIterations = 10
        self._valveLockCount         = 0
        self._valveLockIterations    = 10
        self._skipPressureCheck      = False

        vlvcntrl = self._DriverRpc.getVlvcntrlInfo()
        self._valveEnabled = (vlvcntrl['ValveState'] != GlobalDefs.VLVCNTRL_DisabledState and
          vlvcntrl['ValveState'] != GlobalDefs.VLVCNTRL_ManualControlState)
              
    def _create_var_from_config(self,config):
        for k,v in config.items():
            #this is ugly but, cant seem to check type.
            #if isNumberType(v) == False and (v == 'True' or  v == 'False' or v.isdigit()):
            try:
                nv = eval(v)
            except:
                nv = v
            setattr( self, k, nv )

    def _setStatus( self, bits, excl=False ):
        if excl:
            self._status.UpdateStatusBit( 0xFFF0, False )
        self._status.UpdateStatusBit( bits, True )
        #if self.debug==True: print ("SetStatus: bits %X = %X, excl %r" % (bits,self._status._Status, excl) )

    def _clearStatus( self, bits=0 ):
        if bits==0:
            #self.status = 0
            self._status.UpdateStatusBit( 0xFFF0, False )
        else:
            #self.status &= ~bits
            self._status.UpdateStatusBit( bits, False )
        #if self.debug==True: print("ClearStatus: bits %X = %X" % (bits,self._status._Status) )

    def _RPC_GetStatus( self ):
        return self._status._Status

    def _RPC_ReadPressure(self):
        """Get pressure readings"""
        #return self._DriverRpc.rdDasReg(GlobalDefs.IOMGR_FLOAT_CAVITY_PRESSURE_REGISTER)
        return self._pressure

    def LpcWrapper(func):
        def wrapper(self,*args,**kwargs):
            if self._terminateCalls == True: return
            print "Lpc: %s,%r,%r" % (func.__name__,args,kwargs)
            ret = func(self, *args,** kwargs)
            return ret
        wrapper.__name__ = func.__name__
        wrapper.__dict__ = func.__dict__
        wrapper.__doc__ = func.__doc__
        return wrapper

    @LpcWrapper
    def _LPC_WritePressureSetpoint(self, pressure):
        """Write pressure setpoint"""
        self._DriverRpc.wrDasReg( GlobalDefs.VLVCNTRL_CAVITY_PRESSURE_SETPOINT, pressure )

    def _RPC_ReadPressureSetpoint(self):
        """Read pressure setpoint"""
        return self._DriverRpc.rdDasReg( GlobalDefs.VLVCNTRL_CAVITY_PRESSURE_SETPOINT )

    @LpcWrapper
    def _LPC_SetValveControl(self, control ):
        """ Set Valve Control """
        if control != self._RPC_GetValveControl():
            self._DriverRpc.wrDasReg( GlobalDefs.VLVCNTRL_CMD_REGISTER, GlobalDefs.VLVCNTRL_Disable)
        self._DriverRpc.wrDasReg( GlobalDefs.VLVCNTRL_CMD_REGISTER, control )

    def _RPC_GetValveControl(self):
        """Get Valve Control State"""
        return self._DriverRpc.rdDasReg(GlobalDefs.VLVCNTRL_STATE_REGISTER)

    @LpcWrapper
    def _LPC_StopValveControl(self):
        """ Stop Valve Control """
        self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_CMD_REGISTER,GlobalDefs.VLVCNTRL_Disable)

    @LpcWrapper
    def _LPC_SetValve(self, valve, value):
        """Set inlet/outlet valve positions """
        if valve == INLETVALVE:
            self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_INLET_CONTROL_DAC_VALUE_REGISTER, value)
            self._inletDacValue = value
        elif valve == OUTLETVALVE:
            self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_OUTLET_CONTROL_DAC_VALUE_REGISTER, value)
            self._outletDacValue = value

    def _RPC_GetValve(self, valve ):
        """Get Valve DAC for specified valve """
        if valve == INLETVALVE:
            if self._inletDacValue=='':
                self._inletDacValue = self._DriverRpc.rdDasReg(GlobalDefs.VLVCNTRL_INLET_CONTROL_DAC_VALUE_REGISTER)
            return self._inletDacValue
        elif valve == OUTLETVALVE:
            if self._outletDacValue=='':
                self._outletDacValue = self._DriverRpc.rdDasReg(GlobalDefs.VLVCNTRL_OUTLET_CONTROL_DAC_VALUE_REGISTER)
            return self._outletDacValue

    @LpcWrapper
    def _LPC_CloseValve(self, valve):
        """Close specified valve"""
        self._LPC_SetValve(valve, 0)

    @LpcWrapper
    def _LPC_StartPump(self):
        """ Start the pump"""
        self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_PUMP_CMD_REGISTER,GlobalDefs.VLVCNTRL_PumpEnable)

    @LpcWrapper
    def _LPC_StopPump(self):
        """Stop the pump"""
        self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_PUMP_CMD_REGISTER,GlobalDefs.VLVCNTRL_PumpDisable)

    def _RPC_FlowStatus(self):
        """Check status of flow """
        return (self._status._Status & SAMPLEMGR_STATUS_STABLE ) != 0

    @LpcWrapper
    def _LPC_WaitPressureStabilize( self, setpoint, tolerance, timeout, checkInterval, lockCount=1 ):
        """ Wait for pressure to stabilize """
        inRange      = False
        index        = 0
        inRangeCount = 0
        while index<timeout and self._terminateCalls==False:
            pressure = self._RPC_ReadPressure()
            inRange  = ( pressure >= (1-tolerance)*setpoint and pressure <= (1+tolerance)*setpoint)
            if inRange:
                inRangeCount+=1
            else:
                inRangeCount=0
            time.sleep(checkInterval)
            index+=1
            if inRangeCount >= lockCount:
                break
        if self.debug==True:
            print "i:%d, p:%f, r:%r\n" % (index,pressure,inRange)
        return inRange

    @LpcWrapper
    def _LPC_StepValve( self, valve, start, step, iterations, interval, maxPressureChange=10 ):
        try:
            maxPressureChange = self.max_pressure_change
        except:
            pass
        print "maxPressureChange=",  maxPressureChange
        index = 0
        value = start
        prevPressure = self._RPC_ReadPressure()
        while index < iterations and self._terminateCalls==False:
            pressure = self._RPC_ReadPressure()
            # check pressure, we do not want to harm cavity
            if abs(pressure-prevPressure) < maxPressureChange:
                self._LPC_SetValve( valve, value )
                value += step
                index+=1
            time.sleep(interval)
            prevPressure = pressure

    @LpcWrapper
    def _LPC_PumpDownCavity( self, tolerance=0.2, timeout=300,interval=DEFAULT_SLEEP_INTERVAL, lockCount=1 ):
        """ Use outlet valve to pump down cavity """
        self._setStatus( SAMPLEMGR_STATUS_FLOWING )

        self._LPC_CloseValve(INLETVALVE)
        self._LPC_CloseValve(OUTLETVALVE)
        self._LPC_SetValveControl(GlobalDefs.VLVCNTRL_EnterOutletControl)

        pressure = self._RPC_ReadPressureSetpoint()
        status = self._LPC_WaitPressureStabilize( pressure, tolerance=tolerance, timeout=timeout, checkInterval=interval, lockCount=lockCount )
        if status==False:
            print "Pressure failed to stabilize."
            return False
        return True
        
    def _RPC_SetValveMode(self, valveMode):
        if valveMode <= 1:
            self.valve_mode = valveMode

    def _RPC_GetValveMode(self):
        return self.valve_mode

    def _Sleep(self, duration, interval = DEFAULT_SLEEP_INTERVAL):
        iterations = duration / interval
        i = 0
        while i < iterations and self._terminateCalls==False:
            time.sleep(interval)
            i+=1

    # THIS SECTION DEALS WITH SOLENOID VALVES

    @LpcWrapper
    def _LPC_OpenSolenoidValves(self, valves):
        """Open Solenoid Valve(s).
           valves - solenoid valves is string delimited by comma (one based)"""
        valveMask = 0
        for v in valves.split(','):
            if v!='': valveMask += 1 << (int(v)-1)
        self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_SOLENOID_VALVE_OPEN_REGISTER,valveMask)

    @LpcWrapper
    def _LPC_CloseSolenoidValves(self, valves=None):
        """Close Solenoid Valve(s)
           valves - solenoid valves is string delimited by comma (one based)"""
        if valves==None:
            self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_SOLENOID_VALVE_CLOSE_REGISTER, 0x3F )
            return

        valveMask = 0
        for v in valves.split(','):
            if v!='': valveMask += 1 << (int(v)-1)
        if valveMask != 0:
            self._DriverRpc.wrDasReg(GlobalDefs.VLVCNTRL_SOLENOID_VALVE_CLOSE_REGISTER, valveMask)

    def _RPC_GetSolenoidValves(self):
        """Get bits of Solenoid Valves opened"""
        return self._DriverRpc.rdDasReg(GlobalDefs.VLVCNTRL_SOLENOID_VALVE_STATUS_REGISTER)

    def _RPC_GetConcentration(self):
        """Get concentration of valves currently opened"""
        return self._valveConcentration

    def _RPC_GetSolenoidValveOpened(self):
        """Get valve currently opened"""
        return self._valveOpened

    def _RPC_SetVerbose(self,flag):
        self.verbose = flag
        
    def _LPC_OpenCloseSolenoidValves( self, valve, duration, concentration ):
        """ WARNING: This routine blocks until completes or terminated by control flag!!
            Open solenoid valves for specified durations in seconds and then close it.

            valve    = int value of valve
            duration = mins
        """
        self._valveOpened        = valve
        self._valveConcentration = concentration
        self._LPC_CloseSolenoidValves()
        self._LPC_OpenSolenoidValves( str(valve) )
        startTime = time.time()
        if self.debug==True: print "Start: %r" % (startTime)
        durationS = duration * 60
        while ( self._terminateSolenoidControl == False ):
            delta = time.time()-startTime
            if (time.time()-startTime) > durationS:
                break
            time.sleep(DEFAULT_SLEEP_INTERVAL)
        if self.debug==True: print "Stop : %r" % (time.time())
        self._LPC_CloseSolenoidValves()
        self._valveConcentration = 0
        self._valveOpened        = ''

    def _LPC_StartSolenoidValveControl(self, scriptName, functionName, configName='VALVES' ):
        self._clearStatus( SAMPLEMGR_STATUS_PREPARED )
        self._terminateSolenoidControl = True
        self._valveScript = scriptName,functionName,configName
        self._valveEvent.set()

    def _LPC_StopSolenoidValveControl(self):
        self._terminateSolenoidControl = True

    def _RPC_SkipPressureCheck(self):
        """Skip the pressure check in _Monitor()"""
        self._skipPressureCheck = True

    def _RPC_ResumePressureCheck(self):
        """Resume the pressure check in _Monitor()"""
        self._skipPressureCheck = False
        self._clearStatus( SAMPLEMGR_STATUS_STABLE )
        
    def _HandleSolenoidValves(self,config):
        """ Solenoid valve script execution thread """
        self._terminateSolenoidControl = False
        self._valveEvent.wait()
        self._valveEvent.clear()
        if self._terminateSolenoidControl: return
        try:
            # Execute script
            moduleName, funcName, configSection = self._valveScript
            if moduleName == '' :
                return
            module    = __import__( moduleName )
            nconfig   = config.list_items( configSection )
            function  = getattr( module, funcName )
            function ( self, dict(nconfig) )
        except:
            msg = "_HandleSolenoidValves Exception %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print(msg)
            Log(msg)

    def _Terminate(self, flag=True):
        print "Terminate ", flag
        self._terminateCalls = flag
        self._terminateSolenoidControl = flag
        if flag:
            self._valveEvent.set()
        else:
            self._valveEvent.clear()

    def _Monitor(self):
        try:
            if self._skipPressureCheck:
                self._clearStatus()
                self._setStatus( SAMPLEMGR_STATUS_STABLE )
                self._setStatus( SAMPLEMGR_STATUS_FLOWING )                    
                return
            vlvcntrl = self._DriverRpc.getVlvcntrlInfo()
            self._pumpEnabled = ( vlvcntrl['PumpState'] == GlobalDefs.VLVCNTRL_PumpEnabledState)
            self._valveEnabled = (vlvcntrl['ValveState'] != GlobalDefs.VLVCNTRL_DisabledState and
              vlvcntrl['ValveState'] != GlobalDefs.VLVCNTRL_ManualControlState)
            if self._pumpEnabled and self._valveEnabled:
                self._setStatus( SAMPLEMGR_STATUS_FLOWING )
            else:
                self._clearStatus( SAMPLEMGR_STATUS_FLOWING )

            if self._valveEnabled == False:
                self._inletDacValue = self._DriverRpc.rdDasReg(GlobalDefs.VLVCNTRL_INLET_CONTROL_DAC_VALUE_REGISTER)
                self._outletDacValue = self._DriverRpc.rdDasReg(GlobalDefs.VLVCNTRL_OUTLET_CONTROL_DAC_VALUE_REGISTER)

            if self._status._Status & SAMPLEMGR_STATUS_FLOWING:

                # Check control valve
                valveInRange = False
                if self.valve_mode == INLETVALVE:
                    dacValue    = self._inletDacValue
                    dacMin      = self.inlet_valve_min
                    dacMax      = self.inlet_valve_max
                elif self.valve_mode == OUTLETVALVE:
                    dacValue    = self._outletDacValue
                    dacMin      = self.outlet_valve_min
                    dacMax      = self.outlet_valve_max
                else:
                    Log("Invalid mode")
                    return

                # Check open valve
                if self.valve_mode == INLETVALVE and self._outletDacValue == self.outlet_valve_target:
                    valveOpened = True
                elif self.valve_mode == OUTLETVALVE and self._inletDacValue == self.inlet_valve_target:
                    valveOpened = True
                else:
                    valveOpened = False

                #if self.verbose: print "dacValue %r, %r %r" % (dacValue,dacMin,dacMax)

                if dacValue < dacMin :
                    self._valveLockCount = 0
                    self._setStatus( SAMPLEMGR_STATUS_VALVE_DAC_LOW )
                    self._clearStatus( SAMPLEMGR_STATUS_VALVE_DAC_HIGH )
                elif dacValue > dacMax:
                    self._valveLockCount = 0
                    self._setStatus( SAMPLEMGR_STATUS_VALVE_DAC_HIGH )
                    self._clearStatus( SAMPLEMGR_STATUS_VALVE_DAC_LOW )
                else:
                    if self._valveLockCount > self._valveLockIterations:
                        self._clearStatus( SAMPLEMGR_STATUS_VALVE_DAC_LOW | SAMPLEMGR_STATUS_VALVE_DAC_HIGH )
                        valveInRange = True
                    else:
                        self._valveLockCount+=1

                # Check pressure (if not set skipped)   
                pressureLocked = False
                pressure = self._RPC_ReadPressure()
                pressureTol = self.pressure_tolerance_per
                pressureSetpoint = vlvcntrl['PressureSetpoint']
                if pressure < (1-pressureTol)*pressureSetpoint:
                    self._pressureLockCount = 0
                    self._setStatus( SAMPLEMGR_STATUS_PRESSURE_LOW )
                    self._clearStatus( SAMPLEMGR_STATUS_PRESSURE_HIGH )
                elif pressure > (1+pressureTol)*pressureSetpoint:
                    self._pressureLockCount = 0
                    self._setStatus( SAMPLEMGR_STATUS_PRESSURE_HIGH )
                    self._clearStatus( SAMPLEMGR_STATUS_PRESSURE_LOW )
                else:
                    if self._pressureLockCount > self._pressureLockIterations:
                        self._clearStatus( SAMPLEMGR_STATUS_PRESSURE_HIGH | SAMPLEMGR_STATUS_PRESSURE_LOW )
                        pressureLocked = True
                    else:
                        self._pressureLockCount+=1

                if valveOpened and pressureLocked and valveInRange and (self._status._Status & SAMPLEMGR_STATUS_FLOWING) \
                   and (self._status._Status & SAMPLEMGR_STATUS_FLOW_STARTED):
                    self._setStatus( SAMPLEMGR_STATUS_STABLE )
                else:
                    self._clearStatus( SAMPLEMGR_STATUS_STABLE )
                if self.verbose: print "%r %r %r"  % (pressureLocked,valveInRange,self._status._Status)
        except:
            msg = "MonitorException:  %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print (msg)
            Log(msg)

    def _HandleStreamCast(self,obj):
        try:
            sensorName = obj.streamType
            sensorValue = obj.value.asFloat
            if sensorName == GlobalDefs.STREAM_CavityPressure:
                self._pressure = sensorValue
            elif sensorName == GlobalDefs.STREAM_InletDacValue:
                if self._valveEnabled == True:
                    self._inletDacValue = sensorValue
            elif sensorName == GlobalDefs.STREAM_OutletDacValue:
                if self._valveEnabled == True:
                    self._outletDacValue = sensorValue
            else:
                return
            if self.verbose: 
                print "pressure: %r, inletdac %r, outletdac %r" % (self._pressure, self._inletDacValue, self._outletDacValue )
        except:
            msg = "HandleStreamException:  %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print (msg)
            Log(msg)


###############################################################################
class SampleManager(object):
    def __init__(self, IniPath):
        """ Initialize Sample Manager """
        self.state     = 'Idle'
        self.debug     = True
        self.terminate = False
        self.mode      = None
        # load configurations
        print "loading filename %s" % IniPath
        if self.LoadConfig(IniPath) == False:
            Log("Failed to load config %s" % IniPath )
            return

        # find abs path to Ini file
        self.iniAbsBasePath = os.path.split(os.path.abspath(IniPath))[0]
        
        self.defaultConfig = self.config.list_items( DEFAULT_CONFIGS )

        # create thread for processing requests
        self.cmdQueue   = Queue.Queue( MAX_COMMAND_QUEUE_SIZE )
        self.cmdThread  = threading.Thread( target = self.CmdHandler )
        self.cmdThread.setDaemon(True)
        self.cmdTimeout = 60

        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_SAMPLE_MGR),
          ServerName = "SampleManager", ServerDescription = "Sample Manager.",
          ServerVersion = __version__, threaded = True)

        modeName   = self.config.get( HEADER_SECTION,'Mode')
        self.RPC__SetMode( modeName )

        if modeName == "BatchMode":
            self.mode._RPC_SkipPressureCheck()
            
        self.streamListener = Listener(None,
                                       BROADCAST_PORT_SENSORSTREAM,
                                       GlobalDefs.STREAM_ElementType,
                                       self.StreamFilter,
                                       retry = True,
                                       name = "Sample Manager sensor stream listener",logFunc = Log)

        # create thread for handling solenoid valves.
        self.scriptThread  = threading.Thread( target = self.SolenoidHandler )
        self.scriptThread.setDaemon(True)

        self.monitorThread  = threading.Thread( target = self.Monitor )
        self.monitorThread.setDaemon(True)

    def LoadConfig(self, filename ):
        """ Loads configuration file """
        try:
            self.config = CustomConfigObj(filename)
        except:
            msg = "Unable to open config. %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print (msg)
            Log(msg)
            return False

    def RegisterRpcServer(self):
        """ Starts up rpc server """
        self.RegisterRPCs( self.mode )
        self.RegisterBPCs( self.mode )
        self.RegisterRPCs( self )

    def RegisterBPCs(self, obj ):
        """ Register base class routines """
        for k in dir(obj):
            v = getattr(obj, k)
            if callable(v) and (not isclass(v)):
                if v.__name__.startswith("_RPC_"):
                    self.RpcServer.register_function( v, name = k[1:], NameSlice = 4 )

    def RegisterRPCs( self, obj ):
        """ Register class RPC routines """
        for k in dir(obj):
            v = getattr(obj, k)
            if callable(v) and (not isclass(v)):
                if v.__name__.startswith("RPC_"):
                    self.RpcServer.register_function( v, k, NameSlice = 4 )

    def CmdHandler(self):
        while ( self.terminate==False ):
            try:
                cmd,args,kwargs = self.cmdQueue.get( block=True, timeout=self.cmdTimeout )
                if self.mode != None:
                    self.mode._terminateCalls = False
                    self.state = (cmd.__name__,args,kwargs)
                    func = getattr( self.mode,cmd.__name__ )
                    if self.debug: print "B: %s" % func.__name__
                    func(*args,**kwargs)
                    if self.debug: print "E: %s" % func.__name__
                self.state = 'Idle'
            except Queue.Empty:
                pass
            except:
                msg = "CmdHandler  %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                print (msg)
                Log(msg)
            time.sleep(0.01)

    def SolenoidHandler(self):
        """Handle solenoid valve control request if any"""
        while self.terminate==False:
            if self.mode!=None:
                try:
                    self.mode._HandleSolenoidValves( self.config )
                except:
                    msg = "SolenoidHandler: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                    print (msg)
                    Log(msg)
            time.sleep(0.5)

    def StreamFilter(self, obj):
        try:
            if self.mode != None:
                self.mode._HandleStreamCast(obj)
        except:
            msg = "StreamFilter:  %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print (msg)
            Log(msg)

    def Monitor(self):
        while self.terminate==False:
            if self.mode!=None:
                try:
                    self.mode._Monitor()
                except:
                    msg = "Monitor: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                    print (msg)
                    Log(msg)
            time.sleep(1)

    def Run(self):

        self.cmdThread.start()
        self.scriptThread.start()
        self.monitorThread.start()
        self.RegisterRpcServer()
        self.RpcServer.serve_forever()

        # Terminate threads
        self.terminate = True
        self.cmdQueue.put( (0, None, None) )
        self.mode._Terminate(True)

    def RpcWrapStateChangeCalls(func):
        def wrapper(self,*args,**kwargs):
            if self.state[0] == func.__name__:
                return INST_ERROR_OKAY
            if self.mode != None:
                self.mode._terminateCalls  = True
            if self.debug==True: print "Q: %s" % func.__name__
            self.cmdQueue.put( (func, args, kwargs) )
            return INST_ERROR_OKAY
        wrapper.__name__ = func.__name__
        wrapper.__dict__ = func.__dict__
        wrapper.__doc__ = func.__doc__
        return wrapper

    # RPCs exported

    def RPC__SetMode( self, modeName ):

        if self.mode != None:

            if modeName == self.modeName:
                return True

            try:
                self.mode._Terminate(True)
            except:
                msg = "SetModeTerm: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
                print (msg)
                Log(msg)
            time.sleep(1)

        try:
            modeConfig    = self.config.list_items( modeName )
            (modePath, modeFile) = os.path.split(dict(modeConfig)['script_filename'])

            # Add path to Python script
            scriptPath =  os.path.join(self.iniAbsBasePath, modePath) 
            if scriptPath not in sys.path: sys.path.append(scriptPath)

            print "Importing: >>%s<<" % (modeFile,)
            print sys.path
            modeModule    = __import__( modeFile )
            modeClass     =  getattr( modeModule, modeFile )

            self.modeName = modeName
            self.mode     = modeClass(self.defaultConfig + modeConfig)
            self.state    = 'Idle'

            self.mode._Terminate(False)

            self.RegisterBPCs( self.mode )
            self.RegisterRPCs( self.mode )

        except:
            msg = "Setmode: %s %s" % (sys.exc_info()[0], sys.exc_info()[1])
            print (msg)
            Log(msg)
            return False

        return True

    def RPC__GetMode(self):
        return self.modeName

    def RPC__GetState(self):
        return self.state

    def RPC_Error_Clear(self):
        """Clears the current error state """
        return INST_ERROR_OKAY

    # Skeleton RPCs, wrapped with

    @RpcWrapStateChangeCalls
    def RPC_FlowStart(self):
        """START FLOW"""

    @RpcWrapStateChangeCalls
    def RPC_FlowStop(self):
        """STOP FLOW"""

    @RpcWrapStateChangeCalls
    def RPC_FlowPumpDisable(self):
        """STOP FLOW & PUMP"""

    @RpcWrapStateChangeCalls
    def RPC_Park(self):
        """PARK"""

    @RpcWrapStateChangeCalls
    def RPC_Prepare(self):
        """PREPARE"""

    @RpcWrapStateChangeCalls
    def RPC_Purge(self):
        """PURGE"""

def Usage():
    print "[-h] [-c configfile]"

def Main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:", ["help", "config="])
    except getopt.GetoptError:
        # print help information and exit:
        Usage()
        sys.exit(2)

    filename = os.path.dirname(AppPath) + "/" + DEFAULT_INI_FILE

    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()
        if o in ("-c", "--config"):
            filename = a

    app = SampleManager(filename)
    app.Run()

if __name__ == "__main__" :
    Main()
