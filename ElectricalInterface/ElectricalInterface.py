"""
File Name: ElectricalInterface.py
Purpose: This module manages Electrical Interface signals

TODO: 
    Make sure config file can be restored to defaults when corrupted.

File History:
    06-11-23 ytsai   Created file
    06-12-22 russ    Fixed RPC server launch; Added Logs
    08-06-04 sze     Allow errorvalue and invalidvalue to lie outside the range of available voltages, to indicate that
                     the error or invalid condition should be ignored
    08-09-18 alex    Replace ConfigParser with CustomConfigObj
    09-08-07 alex    Clean up the code and put the physical limitation of analog output in .ini file. 
                     Again, allow errorvalue and invalidvalue to lie outside the range of available voltages.
    10-05-03 alex    Modified the code to work with the new analog card in G2000 platform (no digital interface anymore).
                     Removed errorvalue.

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

APP_NAME = 'EIF'
__version__ = 1.0
_CONFIG_NAME = 'ElectricalInterface.ini'
MAIN_SECTION = 'MAIN'
SOURCE_DELIMITER = ','

import sys
import os
import time
import getopt
import time
import types
import socket
import select
import ctypes
import threading
import Queue
from math import sqrt
from inspect import isclass

from Host.Common import CmdFIFO, Listener
from Host.Common import MeasData
from Host.Common import AppStatus
from Host.Common.timestamp import unixTimeToTimestamp, getTimestamp
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_EIF_HANDLER, BROADCAST_PORT_DATA_MANAGER
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.StringPickler import StringAsObject,ObjAsString,ArbitraryObject
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
    IniDir = os.path.dirname(AppPath)
else:
    AppPath = sys.argv[0]
    IniDir = os.path.normpath(os.path.join(os.path.dirname(AppPath),".."))
    
EIF_OUTPUT_MODE_MANUAL    = 0
EIF_OUTPUT_MODE_TRACKING  = 1

EIF_ANALOG_DEFAULT_SLOPE    = 1
EIF_ANALOG_DEFAULT_OFFSET   = 0
EIF_ANALOG_ALLOWED_MIN      = 0
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
    def __init__( self, channel, eif, config, allowedMin = EIF_ANALOG_ALLOWED_MIN, allowedMax = EIF_ANALOG_ALLOWED_MAX  ):
        """ Initialize Analog Output object"""
        EifSignal.__init__(self, channel)
        self.name   = 'AnalogOutput'
        self.eif = eif
        self.config = config
        self.slope  = EIF_ANALOG_DEFAULT_SLOPE
        self.offset = EIF_ANALOG_DEFAULT_OFFSET
        self.units  = ''
        self.allowedMin = allowedMin
        self.allowedMax = allowedMax
        
        self.configlist = ['mode', 'source', 'slope', 'offset', 'min', 'max', 'bootmode', 'bootvalue',
          'invalidvalue', 'currentvalue' ]

        tuples = self.config.list_items( 'ANALOG_OUTPUT_CHANNEL'+str(channel) )
        self._create_var_from_tuple_list(tuples)
        
        # Verify min and max values
        self._verifyMinMax()
        
        self.mode = self.bootmode

        # set value to default
        try:
            if self.bootvalue!='':
                self._writeOutput( self.bootvalue )
        except:
            Log("Channel%d: write bootup value failed: %s %s" % ( channel, sys.exc_info()[0], sys.exc_info()[1]))
            print("Channel%d: write bootup value failed: %s %s" % ( channel, sys.exc_info()[0], sys.exc_info()[1]))

    def _convertMeasuredValue( self, measuredValue ):
        """Converts measured value to output value using slope and offset."""
        return (measuredValue*self.slope + self.offset)

    def setOutputMode( self, mode ):
        """Set output mode, 0=Manual, 1=Tracking"""
        self._writeOutput( self.bootvalue )
        return self._SetMode(mode)

    def setSource( self, sourceName ):
        """Set the source name of the variable to monitor"""
        return self._SetSource(sourceName)

    def configure( self, filename, calSlope, calOffset, minOutput, maxOutput, bootmode, bootvalue, invalidvalue ):
        """This routine configures the analog output specified by channel as follows:
             CalSlope  - the calibration slope to use
             CalOffset - the calibration offset to use
             MinOutput - the minimum output to allow
             MaxOutput - the maximum output to allow
             bootmode  - the mode at system startup (manual, tracking)
             bootvalue - the value to set at system startup (if mode is manual)
             invalidvalue - the output value for invalid measurement
        """
        self.slope      = calSlope
        self.offset     = calOffset
        self.min        = minOutput
        self.max        = maxOutput
        self.bootmode   = bootmode
        self.bootvalue  = bootvalue
        self.invalidvalue = invalidvalue
        self._verifyMinMax()
            
        l = [ 'slope', 'offset', 'min', 'max', 'bootmode', 'bootvalue', 'invalidvalue']
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
        
    def _verifyMinMax(self):
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

    def _sendOutputToBuffer(self, dasTime, outputLevel, invalidOrError = False ):
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
        return ( dasTime, self.channel, outputLevel )

    def _writeOutput(self, outputLevel):
        self.eif.writeSample( self.channel, outputLevel )
        return True

    def trackInvalidOutput(self, dasTime):
        if self.__debug__: print "SetInvalid: c:%d v:%r" % (self.channel,self.invalidvalue)
        return self._sendOutputToBuffer(dasTime, self.invalidvalue, invalidOrError = True)

    def trackMeasOutput( self, dasTime, measuredValue ):
        outputLevel = self._convertMeasuredValue( measuredValue )
        # print dasTime, measuredValue, outputLevel
        return self._sendOutputToBuffer(dasTime, outputLevel)

    def setOutput( self, outputLevel ):
        """Manually set the analog output to the specified output level.
           Units are V for voltage outputs.
           If not already in Manual mode, this forces manual mode.
        """
        self.mode = EIF_OUTPUT_MODE_MANUAL
        return self._writeOutput( outputLevel )

    def setMeasOutput( self, measuredValue ):
        """Manually set the analog output to the output level appropriate for the specified value. 
           The value is determined using the calibration values currently associated with the output:
           Analog output value = (cal slope)*(measured value) + (Cal offset)
           If not already in Manual mode, this forces manual mode.
        """
        self.mode = EIF_OUTPUT_MODE_MANUAL
        outputLevel = self._convertMeasuredValue( measuredValue )
        return self._writeOutput( outputLevel )

    def getInfo( self, getStr=True ):
        """ Retrieves the configuration information for the specified channel.
            The returned values are as follows (in a dictionary if getStr option == False):
              CurrentState; MeasSource; CalSlope; CalOffset; MinOutput; MaxOutput; 
              bootmode; bootvalue; invalidvalue; CurrentValue
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

        # list of analog objects
        self.analogOutput={}
        self.sampleBuffer = Queue.Queue(0)
        
        # Load configuration file
        self.loadConfig(filename)
        Log("ElectricalInterface application initialization complete.")
        
        # Create listener
        self.measListener  = Listener.Listener(None, BROADCAST_PORT_DATA_MANAGER,
          ArbitraryObject, self.measFilter, retry = True,
          name = "Electrical inteface measurement listener",logFunc = Log)

        self.tSum = 0
        self.tSumSq = 0
        self.tNum = 0

    def loadConfig(self, filename ):
        """ Loads configuration file """
        self._filename = filename
        self._config = CustomConfigObj(filename)

        try:
            self.analog_outputs = eval(self._config.get(MAIN_SECTION,'ANALOG_OUTPUTS'))
            self.analog_allowedMin = self._config.getfloat(MAIN_SECTION,'ANALOG_ALLOWEDMIN',default = EIF_ANALOG_ALLOWED_MIN)
            self.analog_allowedMax = self._config.getfloat(MAIN_SECTION,'ANALOG_ALLOWEDMAX',default = EIF_ANALOG_ALLOWED_MAX)
            # The data in the analog interface buffer will be sent to driver if either of the following is true:
            # 1. The first data timestamp in the buffer + ANALOG_TIME_DELAY < current time + ANALOG_TIME_MARGAIN
            # 2. The total number of data in the buffer >= ANALOG_BUFFER_SIZE
            self.analog_buffer_size = self._config.getfloat(MAIN_SECTION, 'ANALOG_BUFFER_SIZE', 250)
            self.analog_time_delay = self._config.getfloat(MAIN_SECTION, 'ANALOG_TIME_DELAY', 5.0)
            self.analog_time_margin = self._config.getfloat(MAIN_SECTION, 'ANALOG_TIME_MARGIN' , 2.0)
        except:
            LogExc("Load config failed", dict(FileName = filename))
            return False

        for channel in self.analog_outputs:
            Log("Initializing analog channel", dict(Channel = channel))
            self.analogOutput[channel] = EifAnalogOutput(channel, self, self._config, self.analog_allowedMin, self.analog_allowedMax)

    def serviceQueue(self):
        sampleList = []
        while True:
            try:
                sampleList.append(self.sampleBuffer.get(timeout=0.5))
            except Queue.Empty:
                print "Queue.Empty"
            curDasTime = getTimestamp()
            if sampleList and \
                ((len(sampleList) >= self.analog_buffer_size) or \
                (sampleList[0][0] < (curDasTime+self.analog_time_margin))):
                self._driver.sendDacSamples(sampleList)
                sampleList = []

    def writeSample(self, channel, voltage):
        self._driver.writeDacSample(channel, voltage)
        
    def measFilter( self, dataDict ):
        """Filter for data broadcasts"""
        tStart = time.clock()
        try:
            self._measData.ImportPickleDict( dataDict )
            # if __debug__: print("\nSource (%s), Data (%s) %r" % (self._measData.Source, self._measData.Data, self._measData.MeasGood))
            for channel in self.analog_outputs:
                if self.analogOutput[channel].mode == EIF_OUTPUT_MODE_TRACKING:
                    source,label = self.analogOutput[channel].source.split( SOURCE_DELIMITER )
                    if source == self._measData.Source and label in self._measData.Data:
                        data = float(self._measData.Data[label])
                        dasTime = unixTimeToTimestamp(self._measData.Time)
                        if (self.analogOutput[channel].invalidvalue != None) and (not self._measData.MeasGood):
                            if self.analog_allowedMin<=self.analogOutput[channel].invalidvalue<=self.analog_allowedMax:
                                (dasTime, channel, voltage) = self.analogOutput[channel].trackInvalidOutput(dasTime)
                        else:
                            (dasTime, channel, voltage) = self.analogOutput[channel].trackMeasOutput(dasTime, data)
                        self.sampleBuffer.put(((dasTime + 1000*self.analog_time_delay) , channel, voltage))
        except:
            msg = "measFilter: %s %s" % ( sys.exc_info()[0], sys.exc_info()[1])
            print msg
            Log(msg)
        duration = time.clock() - tStart
        self.tSum += duration
        self.tSumSq += duration**2
        self.tNum += 1
        if self.tNum % 200 == 0:
            tMean = self.tSum/self.tNum
            tMeanSq = self.tSumSq/self.tNum
            print "Mean measFilter time: %.3f, Std dev: %.3f, Number: %d" % (tMean,sqrt(tMeanSq-tMean**2),self.tNum)
            self.tSum = 0
            self.tSumSq = 0
            self.tNum = 0

    def run(self):
        self.RpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_EIF_HANDLER),
          ServerName = "ElectricalInterface", ServerDescription = "EifMgr",
          ServerVersion = __version__, threaded = True)
        self.registerRPCs( self )
        rpcThread = threading.Thread(target = self.RpcServer.serve_forever)
        rpcThread.setDaemon(True)
        rpcThread.start()
        self.serviceQueue()

    def registerRPCs(self, obj ):
        """ Register base class routines """
        for k in dir(obj):
            v = getattr(obj, k)
            if callable(v) and (not isclass(v)):
                if v.__name__.startswith("RPC_"):
                    self.RpcServer.register_function( v, name = k, NameSlice = 4 )

    def RPC_AO_SetOutputMode( self, channel, mode ):
        """Set output mode, 0=Manual, 1=Tracking"""
        if channel in self.analogOutput:
            return self.analogOutput[channel].setOutputMode( mode )
        else:
            return False

    def RPC_AO_SetTracking( self, channel):
        """Set output mode to be Tracking on a specified channel"""
        if channel in self.analogOutput:
            return self.analogOutput[channel].setOutputMode( 1 )
        else:
            return False
            
    def RPC_AO_SetSource( self, channel, sourceName ):
        """Set the source name of the variable to monitor"""
        if channel in self.analogOutput:
            return self.analogOutput[channel].setSource( sourceName )
        else:
            return False

    def RPC_AO_Configure( self, channel, calSlope, calOffset, minOutput, maxOutput, bootmode, bootvalue, invalidvalue ):
        """This routine configures the analog output."""
        if channel in self.analogOutput:
            return self.analogOutput[channel].configure( self._filename, calSlope, calOffset, minOutput, maxOutput, bootmode, bootvalue, invalidvalue )
        else:
            return False

    def RPC_AO_SetOutput( self, channel, outputLevel ):
        """Sets the analog output to the specified output level.
           Units are V for voltage outputs.
           If not already in Manual mode, this forces manual mode."""
        if channel in self.analogOutput:
            return self.analogOutput[channel].setOutput( outputLevel )
        else:
            return False

    def RPC_AO_SetMeasOutput( self, channel, measuredValue):
        """Sets the analog output to the output level appropriate for the specified value. 
           The value is determined using the calibration values currently associated with the output:
           Analog output value = (cal slope)*(measured value) + (Cal offset)
           If not already in Manual mode, this forces manual mode."""
        if channel in self.analogOutput:
            return self.analogOutput[channel].setMeasOutput( measuredValue )
        else:
            return False

    def RPC_AO_GetInfo( self, channel, getStr=True ):
        """ Retrieves the configuration information for the specified OutputName.
            The returned values are as follows:
              CurrentState; MeasSource; CalSlope; CalOffset; MinOutput; MaxOutput; bootmode; bootvalue; CurrentValue """
        if channel in self.analogOutput:
            return self.analogOutput[channel].getInfo(getStr)
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
    configFile = HandleCommandSwitches()
    Log("%s started." % APP_NAME, dict(ConfigFile = configFile), Level = 0)
    try:
        eif = EifMgr(configFile)
        eif.run()
        Log("Exiting program")
    except Exception, E:
        if __debug__: raise
        msg = "Exception trapped outside execution"
        print msg + ": %s %r" % (E, E)
        Log(msg, Level = 3, Verbose = "Exception = %s %r" % (E, E))
