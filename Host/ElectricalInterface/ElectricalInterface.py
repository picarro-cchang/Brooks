# File Name: ElectricalInterface.py
#
# Purpose: This module manages Electrical Interface signals
#
# TODO: 1) Make sure config file can be restored to defaults when corrupted.
#
# File History:
# 06-11-23 ytsai   Created file
# 06-12-22 russ    Fixed RPC server launch; Added Logs
# 08-06-04 sze     Allow errorvalue and invalidvalue to lie outside the range of available voltages, to indicate that
#                              the error or invalid condition should be ignored
# 08-09-18  alex  Replace ConfigParser with CustomConfigObj
# 09-08-07  alex Clean up the code and put the physical limitation of analog output in .ini file. 
#                           Again, allow errorvalue and invalidvalue to lie outside the range of available voltages.

APP_NAME = 'EIF'

import os, sys, time, getopt
import os.path

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
    IniDir = os.path.dirname(AppPath)

else:
    AppPath = sys.argv[0]
    IniDir = os.path.normpath(os.path.join(os.path.dirname(AppPath),".."))


if "../Common" not in sys.path: sys.path.append("../Common")
import CmdFIFO
from SharedTypes import RPC_PORT_DRIVER, RPC_PORT_EIF_HANDLER, RPC_PORT_ALARM_SYSTEM, RPC_PORT_MEAS_SYSTEM, \
                        BROADCAST_PORT_DATA_MANAGER, STATUS_PORT_ALARM_SYSTEM, STATUS_PORT_INST_MANAGER
import threading, Queue
from math import sqrt
import time
import types
from CustomConfigObj import CustomConfigObj
import socket
import select
import ctypes
from StringPickler import StringAsObject,ObjAsString,ArbitraryObject
import Listener
from inspect import isclass
import MeasData
from EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)
import AppStatus
from InstMgrInc import INSTMGR_STATUS_SYSTEM_ERROR

__version__ = 1.0

_CONFIG_NAME = 'ElectricalInterface.ini'
MAIN_SECTION = 'MAIN'
SOURCE_DELIMITER = ','

EIF_OUTPUT_MODE_MANUAL    = 0
EIF_OUTPUT_MODE_TRACKING  = 1

EIF_ANALOG_DEFAULT_SLOPE    = 1
EIF_ANALOG_DEFAULT_OFFSET   = 0
EIF_ANALOG_ALLOWED_MIN      = -10
EIF_ANALOG_ALLOWED_MAX      = 10

class EifSignal(object):
    """Base EIF signal class"""
    def __init__( self, channel ):
        self.__debug__  = False
        self.name       = ''
        self.channel    = channel
        self.source     = '-'
        self.mode       = EIF_OUTPUT_MODE_MANUAL
        self.bootmode   = EIF_OUTPUT_MODE_MANUAL
        self.bootvalue  = 0
        self.errorvalue = 0

    def _SetMode( self, mode ):
        """Set output mode, 0=Manual, 1=Tracking"""
        if mode != EIF_OUTPUT_MODE_MANUAL and mode != EIF_OUTPUT_MODE_TRACKING:
            return False
        self.mode = mode
        Log("%s Mode change %d" % (self.name,self.mode) )
        return True

    def _SetSource( self, sourceName ):
        """Set signal source to monitor"""
        self.source = sourceName

    def _create_var_from_tuple_list(self,tuples):
        for k,v in tuples:
            #this is ugly but, cant seem to check type.
            #if isNumberType(v) == False and (v == 'True' or  v == 'False' or v.isdigit()):
            try:
                nv = eval(v)
            except:
                nv = v
            setattr( self, k, nv )

#
# ANALOG OUT
#
# bootmode  = What mode the output should be in on power-up [0=Manual,1=Tracking]
# bootvalue = The value that should be shown on the output on power up
# min       = The minimum possible value that the analog output can be
# max       = The maximum possible value that the analog output can be
# source    = [data manager script name], [data label]
#
class EifAnalogOutput(EifSignal):
    def __init__( self, channel, driver, config, allowedMin = EIF_ANALOG_ALLOWED_MIN, allowedMax = EIF_ANALOG_ALLOWED_MAX  ):
        """ Initialize Analog Output object"""
        EifSignal.__init__(self, channel)
        self.name   = 'AnalogOutput'
        self.driver = driver
        self.config = config
        self.slope  = EIF_ANALOG_DEFAULT_SLOPE
        self.offset = EIF_ANALOG_DEFAULT_OFFSET
        self.units  = ''
        self.allowedMin = allowedMin
        self.allowedMax = allowedMax
        
        self.configlist = ['mode', 'source', 'slope', 'offset', 'min', 'max', 'bootmode', 'bootvalue',
          'errorvalue', 'invalidvalue', 'currentvalue' ]

        tuples = self.config.list_items( 'ANALOG_OUTPUT_CHANNEL'+str(channel) )
        self._create_var_from_tuple_list(tuples)
        
        # Verify min and max values
        self._VerifyMinMax()
        
        self.mode = self.bootmode

        # set value to default
        try:
            if self.bootvalue!='':
                self._SetOutput( self.bootvalue )
        except:
            Log("Channel%d: write bootup value failed: %s %s" % ( channel, sys.exc_info()[0], sys.exc_info()[1]))
            print("Channel%d: write bootup value failed: %s %s" % ( channel, sys.exc_info()[0], sys.exc_info()[1]))

    def _ConvertMeasuredValue( self, measuredValue ):
        """Converts measured value to output value using slope and offset."""
        return (measuredValue*self.slope + self.offset)

    def SetOutputMode( self, mode ):
        """Set output mode, 0=Manual, 1=Tracking"""
        self._SetOutput( self.bootvalue )
        return self._SetMode(mode)

    def SetSource( self, sourceName ):
        """Set the source name of the variable to monitor"""
        return self._SetSource(sourceName)

    def Configure( self, filename, calSlope, calOffset, minOutput, maxOutput, bootmode, bootvalue, errorvalue, invalidvalue ):
        """This routine configures the analog output specified by channel as follows:
             CalSlope  - the calibration slope to use
             CalOffset - the calibration offset to use
             MinOutput - the minimum output to allow
             MaxOutput - the maximum output to allow
             bootmode  - the mode at system startup (manual, tracking)
             bootvalue - the value to set at system startup (if mode is manual)
             errorvalue - the output value for system errors
             invalidvalue - the output value for invalid measurement
        """
        self.slope      = calSlope
        self.offset     = calOffset
        self.min        = minOutput
        self.max        = maxOutput
        self.bootmode   = bootmode
        self.bootvalue  = bootvalue
        self.errorvalue = errorvalue
        self.invalidvalue = invalidvalue
        self._VerifyMinMax()
            
        l = [ 'slope', 'offset', 'min', 'max', 'bootmode', 'bootvalue', 'errorvalue', 'invalidvalue']
        for n in l:
            v = getattr(self, n)
            self.config.set('ANALOG_OUTPUT_CHANNEL'+str(self.channel), n, v )

        try:
            fp = open(filename,'wb')
            self.config.write(fp)
            fp.close()
        except:
            LogExc("Unable to write config file",  dict(FileName = filename))
        return True
        
    def _VerifyMinMax(self):
        # Swap the values if min > max
        if self.min > self.max:
            newMax = self.min
            self.min = self.max
            self.max = newMax
        # Make sure min and max values are within physical limitation (defined in .ini file)
        if self.min < self.allowedMin:
            self.min = self.allowedMin
        if self.max > self.allowedMax:
            self.max = self.allowedMax

    def _SetOutput(self, outputLevel, invalidOrError = False ):
        if (self.min!='') and (self.max != '') and (not invalidOrError):
            if outputLevel < self.min:
                outputLevel = self.min
            elif outputLevel > self.max:
                outputLevel = self.max
        else:
            # Use the physical limitation to control the output level
            if outputLevel < self.allowedMin:
                outputLevel = self.allowedMin
            elif outputLevel > self.allowedMax:
                outputLevel = self.allowedMax
                
        self.currentvalue = outputLevel
        if self.__debug__: print "AO:SetOutput: c:%d v:%r" % (self.channel,outputLevel)
        if self.channel == 420:
            self.driver.AIF_420_SetTx( outputLevel )
        else:
            self.driver.AIF_DAC_SetVoltage( self.channel, outputLevel )
        return True

    def _SetErrorOutput(self):
        if self.__debug__: print "SetError: c:%d v:%r" % (self.channel,self.errorvalue)
        return self._SetOutput( self.errorvalue, invalidOrError = True )

    def _SetInvalidOutput(self):
        if self.__debug__: print "SetInvalid: c:%d v:%r" % (self.channel,self.invalidvalue)
        return self._SetOutput( self.invalidvalue, invalidOrError = True )

    def _SetReference( self, measuredValue ):
        if self.__debug__: print "SetReference: c:%d v:%r" % (self.channel,measuredValue)
        outputLevel = self._ConvertMeasuredValue( measuredValue )
        return self._SetOutput( outputLevel )

    def SetOutput( self, outputLevel ):
        """Sets the analog output to the specified output level.
           Units are V for voltage outputs, and uA for current outputs.
           If not already in Manual mode, this forces manual mode.
        """
        self.mode = EIF_OUTPUT_MODE_MANUAL
        return self._SetOutput( outputLevel )

    def SetReference( self, measuredValue ):
        """Sets the analog output to the output level appropriate for the specified value. The value is determined using the calibration values currently associated with the output:
             Analog output value = (cal slope)*(measured value) + (Cal offset)
           If not already in Manual mode, this forces manual mode.
        """
        self.mode = EIF_OUTPUT_MODE_MANUAL
        return self._SetReference( measuredValue )

    def GetInfo( self, getStr=True ):
        """ Retrieves the configuration information for the specified channel.
            The returned values are as follows (in a dictionary if getStr option == False):
              CurrentState; MeasSource; CalSlope; CalOffset; MinOutput; MaxOutput; 
              bootmode; bootvalue; errorvalue; invalidvalue; CurrentValue
        """
        if not getStr:
            d = {}
            for n in self.configlist:
                v = getattr( self, n)
                d[n]=v
            return d
        else:
            retStr = ""
            for n in self.configlist:
                v = getattr( self, n)
                retStr += (str(v)+";") 
            return retStr
            
#
# DIGITAL OUT
#
class EifDigitalOutput(EifSignal):
    def __init__( self, channel, driver, config ):
        """ Initialize Digital Output object """
        EifSignal.__init__(self, channel)
        self.name   = 'DigitalOutput'
        self.driver = driver
        self.config = config

        self.configlist = ['mode', 'source', 'invert', 'bootmode', 'bootvalue', 'errorvalue', 'currentvalue']

        tuples = self.config.list_items( 'DIGITAL_OUTPUT_CHANNEL'+str(channel) )
        self._create_var_from_tuple_list(tuples)

        self.mode = self.bootmode

        try:
            if self.bootvalue!='':
                self._SetOutput( self.bootvalue )
        except:
            Log("Channel%d: write bootup value failed: %s %s" % ( channel, sys.exc_info()[0], sys.exc_info()[1]))

    def SetOutputMode( self, mode ):
        """Set output mode, 0=Manual, 1=Tracking"""
        self._SetOutput( self.bootvalue )
        return self._SetMode(mode)

    def SetSource( self, sourceName ):
        """Set the source name of the variable to monitor"""
        #TODO: do source name check
        return self._SetSource(sourceName)

    def _SetOutput( self, outputLevel ):
        """Sets the digital output to the specified output level."""
        self.currentvalue = outputLevel
        if self.__debug__: print "DO:SetOutput: c:%d v:%r" % (self.channel,outputLevel)
        self.driver.AIF_DigOut_SetSingle( self.channel, outputLevel )

    def SetOutput( self, outputLevel ):
        """Sets the digital output to the specified output level."""
        self.mode = EIF_OUTPUT_MODE_MANUAL
        return self._SetOutput ( outputLevel )

    def Configure( self, filename, invert, bootmode, bootvalue, errorvalue ):
        """Config Digital Output"""
        self.invert     = invert
        self.bootmode   = bootmode
        self.bootvalue  = bootvalue
        self.errorvalue = errorvalue

        l = [ 'invert', 'bootmode', 'bootvalue', 'errorvalue']
        for n in l:
            v = getattr(self, n)
            self.config.set('DIGITAL_OUTPUT_CHANNEL'+str(self.channel), n, v )
            
        try:
            fp = open(filename,'wb')
            self.config.write(fp)
            fp.close()
        except:
            LogExc("Unable to write config file",  dict(FileName = filename))
        return True

    def GetInfo( self, getStr=True ):
        """ Retrieves the configuration information for the specified channel."""
        if not getStr:
            d = {}
            for n in self.configlist:
                v = getattr( self, n)
                d[n]=v
            return d
        else:
            retStr = ""
            for n in self.configlist:
                v = getattr( self, n)
                retStr += (str(v)+";") 
            return retStr
            
#
# Eif MANAGER
#
class EifMgr(object):
    def __init__(self, filename):
        """ Initialize class """
        self._terminate = False
        self.__debug__=False
        
        self._measData = MeasData.MeasData()

        # driver rpc
        self._driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName = "EIF")

        # list of analog/digital objects
        self.AO={}
        self.DO={}

        self.SystemErrorFlag = False
        self.MeasurementGoodFlag = False
        
        # Load configuration file
        self.LoadConfig(filename)
        Log("ElectricalInterface application initialization complete.")
        
        # Create listener
        self.measListener  = Listener.Listener(None, BROADCAST_PORT_DATA_MANAGER,
          ArbitraryObject, self.MeasFilter, retry = True,
          name = "Electrical inteface measurement listener",logFunc = Log)

        self.alarmListener = Listener.Listener(None, STATUS_PORT_ALARM_SYSTEM,
          AppStatus.STREAM_Status, self.AlarmFilter, retry = True,
          name = "Electrical inteface alarm listener",logFunc = Log)

        self.statusListener = Listener.Listener(None, STATUS_PORT_INST_MANAGER,
          AppStatus.STREAM_Status, self.StatusFilter, retry = True,
          name = "Electrical inteface instrument status listener",logFunc = Log)

        self.tSum = 0
        self.tSumSq = 0
        self.tNum = 0

    def SetDefaults(self):
        """Setup default values"""

    def LoadConfig(self, filename ):
        """ Loads configuration file """
        self._filename = filename
        self._config = CustomConfigObj(filename)

        try:
            self.analog_outputs = eval(self._config.get(MAIN_SECTION,'analog_outputs'))
            self.digital_outputs = eval(self._config.get(MAIN_SECTION,'digital_outputs'))
            self.analog_allowedMin = self._config.getfloat(MAIN_SECTION,'analog_allowedmin',default = EIF_ANALOG_ALLOWED_MIN)
            self.analog_allowedMax = self._config.getfloat(MAIN_SECTION,'analog_allowedmax',default = EIF_ANALOG_ALLOWED_MAX)
        except:
            LogExc("Load config failed", dict(FileName = filename))
            return False

        for channel in self.analog_outputs:
            Log("Initializing analog channel", dict(Channel = channel))
            self.AO[channel] = EifAnalogOutput(channel, self._driver, self._config, self.analog_allowedMin, self.analog_allowedMax)
        for channel in self.digital_outputs:
            Log("Initializing digital channel", dict(Channel = channel))
            self.DO[channel] = EifDigitalOutput(channel, self._driver, self._config )

    def MeasFilter( self, dataDict ):
        """Filter for data broadcasts"""
        tStart = time.clock()
        try:
            self._measData.ImportPickleDict( dataDict )
            # if __debug__: print("\nSource (%s), Data (%s) %r" % (self._measData.Source, self._measData.Data, self._measData.MeasGood))
        
            for channel in self.analog_outputs:
                if self.AO[channel].mode == EIF_OUTPUT_MODE_TRACKING:
                    source,label = self.AO[channel].source.split( SOURCE_DELIMITER )

                    if source == self._measData.Source and label in self._measData.Data:
                        if self.MeasurementGoodFlag != bool(self._measData.MeasGood):
                            #if self.__debug__: print "MeasGood: %r->%r " % (self.MeasurementGoodFlag,self._measData.MeasGood)
                            self.MeasurementGoodFlag = self._measData.MeasGood
                            self.UpdateMeasGoodOutput()

                        data = float(self._measData.Data[label])
                        #if __debug__: print("Source %s, Data %s" % (source, data))

                        if self.SystemErrorFlag and self.analog_allowedMin<=self.AO[channel].errorvalue<=self.analog_allowedMax:
                            self.AO[channel]._SetErrorOutput()
                        elif self.MeasurementGoodFlag==False and self.analog_allowedMin<=self.AO[channel].invalidvalue<=self.analog_allowedMax:
                            self.AO[channel]._SetInvalidOutput()
                        else:
                            self.AO[channel]._SetReference(data)
        except:
            msg = "MeasFilter: %s %s" % ( sys.exc_info()[0], sys.exc_info()[1])
            print msg
            Log(msg)
        duration = time.clock() - tStart
        self.tSum += duration
        self.tSumSq += duration**2
        self.tNum += 1
        if self.tNum % 200 == 0:
            tMean = self.tSum/self.tNum
            tMeanSq = self.tSumSq/self.tNum
            print "Mean MeasFilter time: %.3f, Std dev: %.3f, Number: %d" % (tMean,sqrt(tMeanSq-tMean**2),self.tNum)
            self.tSum = 0
            self.tSumSq = 0
            self.tNum = 0


    def UpdateMeasGoodOutput( self ):
        """For updating Digital outputs when Measurement Good flag changes"""
        for channel in self.digital_outputs:
            if self.DO[channel].mode == EIF_OUTPUT_MODE_MANUAL:
                continue
            try:
                source = self.DO[channel].source
                if source == 'MeasurementGood':
                    value = self.MeasurementGoodFlag
                    if self.DO[channel].invert:
                        value = not(value)
                    self.DO[channel]._SetOutput( value )
            except:
                LogExc( "MeasGoodUpdate %s: Exception %s %s" % (str(channel),sys.exc_info()[0], sys.exc_info()[1]) )

    def AlarmFilter( self, data ):
        """Filter for alarm status"""
        for channel in self.digital_outputs:
            if self.DO[channel].mode == EIF_OUTPUT_MODE_MANUAL:
                continue
            try:
                source = self.DO[channel].source
                if source != 'SystemStatusError' and source != 'MeasurementGood':
                    bit = self.DO[channel].source
                    mask  = 1<<(bit-1)
                    value = (mask & data.status) > 0
                    if self.DO[channel].invert:
                        value = not(value)
                    self.DO[channel]._SetOutput( value )
            except:
                LogExc( "Invalid Source for channel" + str(channel) + " source %r" % source )

    def StatusFilter( self, data ):
        """Filter for system status"""

        #print "StatusFilter: %X" % data.status

        if data.status & INSTMGR_STATUS_SYSTEM_ERROR:
            if self.SystemErrorFlag==True:
                return
            else:
                self.SystemErrorFlag = True
        else:
            if self.SystemErrorFlag==True:
                self.SystemErrorFlag = False
            else:
                return

        # Check digital channel to see if we need to update values
        for channel in self.digital_outputs:
            if self.DO[channel].mode == EIF_OUTPUT_MODE_MANUAL:
                continue
            try:
                source = self.DO[channel].source
                if source == 'SystemStatusError':
                    value = self.SystemErrorFlag
                    if self.DO[channel].invert:
                        value = not(value)
                    if self.__debug__: print "SystemStatusError: DO channel %d" % (channel)
                    self.DO[channel]._SetOutput( value )
            except:
                LogExc( "StatusFilter%s: Exception %s %s" % (str(channel),sys.exc_info()[0], sys.exc_info()[1]) )

    def Run(self):
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_EIF_HANDLER),
          ServerName = "ElectricalInterface", ServerDescription = "EifMgr",
          ServerVersion = __version__, threaded = True)
        self.RegisterRPCs( self )
        self.RpcServer.serve_forever()

    def RegisterRPCs(self, obj ):
        """ Register base class routines """
        for k in dir(obj):
            v = getattr(obj, k)
            if callable(v) and (not isclass(v)):
                if v.__name__.startswith("RPC_"):
                    self.RpcServer.register_function( v, name = k, NameSlice = 4 )

    def RPC_AO_SetOutputMode( self, channel, mode ):
        """Set output mode, 0=Manual, 1=Tracking"""
        if channel in self.AO:
            return self.AO[channel].SetOutputMode( mode )
        else:
            return False

    def RPC_AO_SetTracking( self, channel):
        """Set output mode to be Tracking on a specified channel"""
        if channel in self.AO:
            return self.AO[channel].SetOutputMode( 1 )
        else:
            return False
            
    def RPC_AO_SetSource( self, channel, sourceName ):
        """Set the source name of the variable to monitor"""
        if channel in self.AO:
            return self.AO[channel].SetSource( sourceName )
        else:
            return False

    def RPC_AO_Configure( self, channel, calSlope, calOffset, minOutput, maxOutput, bootmode, bootvalue, errorvalue, invalidvalue ):
        """This routine configures the analog output."""
        if channel in self.AO:
            return self.AO[channel].Configure( self._filename, calSlope, calOffset, minOutput, maxOutput, bootmode, bootvalue, errorvalue, invalidvalue )
        else:
            return False

    def RPC_AO_SetOutput( self, channel, outputLevel ):
        """Sets the analog output to the specified output level.
           Units are mV for voltage outputs, and uA for current outputs.
           If not already in Manual mode, this forces manual mode."""
        if channel in self.AO:
            return self.AO[channel].SetOutput( outputLevel )
        else:
            return False

    def RPC_AO_SetReference( self, channel, measuredValue):
        """Sets the analog output to the output level appropriate for the specified value. The value is determined using the calibration values currently associated with the output:
             Analog output value = (cal slope)*(measured value) + (Cal offset)
           If not already in Manual mode, this forces manual mode."""
        if channel in self.AO:
            return self.AO[channel].SetReference( measuredValue )
        else:
            return False

    def RPC_AO_GetInfo( self, channel, getStr=True ):
        """ Retrieves the configuration information for the specified OutputName.
            The returned values are as follows:
              CurrentState; MeasSource; CalSlope; CalOffset; MinOutput; MaxOutput; bootmode; bootvalue; CurrentValue """
        if channel in self.AO:
            return self.AO[channel].GetInfo(getStr)
        else:
            return False

    def RPC_DO_SetOutputMode( self, channel, mode ):
        """Set output mode, 0=Manual, 1=Tracking"""
        if channel in self.DO:
            return self.DO[channel].SetOutputMode( mode )
        else:
            return False

    def RPC_DO_SetSource( self, channel, sourceName ):
        """Set the source name of the variable to monitor"""
        if channel in self.DO:
            return self.DO[channel].SetSource( sourceName )
        else:
            return False

    def RPC_DO_SetOutput( self, channel, outputLevel ):
        """Sets the digital output to the specified output level."""
        if channel in self.DO:
            return self.DO[channel].SetOutput( outputLevel )
        else:
            return False

    def RPC_DO_Configure( self, channel, invert, bootmode, bootvalue, errorvalue ):
        """Config Digital Output"""
        if channel in self.DO:
            return self.DO[channel].Configure( self._filename, invert, bootmode, bootvalue, errorvalue )
        else:
            return False

    def RPC_DO_GetInfo( self, channel, getStr=True ):
        """ Retrieves the configuration information for the specified channel."""
        if channel in self.DO:
            return self.DO[channel].GetInfo(getStr)
        else:
            return False

HELP_STRING = \
"""\
ElectricalInterface.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h  Print this help.
-c  Specify a different alarm config file.  Default = "./ElectricalInterface.ini"
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
    configFile = os.path.dirname(AppPath) + "/" + _CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        Log ("Config file specified at command line: %s" % configFile)

    return (configFile)

if __name__ == "__main__" :
    #Get and handle the command line options...
    ConfigFile = HandleCommandSwitches()
    Log("%s application started." % APP_NAME)
    try:
        eif = EifMgr(ConfigFile)
        eif.Run()
        Log("Application exited")

    except Exception, E:
        if __debug__: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))
