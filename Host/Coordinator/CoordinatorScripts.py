#
# FILE:
#   CoordinatorScripts.py
#
# DESCRIPTION:
#   Support routines for isotopic water coordinator INI file
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   15-Sep-2008  sze  Incorporated into compiled code
#   12-Dec-2008  alex Added batch mode functionality
#   20-Sep-2010  sze  Add tag along data functions and add pCalOffset parameter
#                     to loadWarmBoxCal
#   18-Aug-2011  alex Added socket interface functions to add tagalong data
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#

# Routines to support state machine handler for autosampler

# Note that the module variables DRIVER, MEASSYS, SAMPLEMGR, SPECTCOLLECTOR, DATAMGR,
#   FREQCONV and LOGFUNC are set from outside

from time import sleep, mktime, localtime, strptime, strftime, time, clock, ctime
from datetime import datetime, timedelta, MINYEAR
from numpy import *
from configobj import ConfigObj
import traceback
import socket
import sys
import os
from os.path import abspath, exists, join, split
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot, dates
from matplotlib.ticker import MaxNLocator
import urllib2
from xml.dom import minidom
import ImageGrab
from shutil import move
from glob import glob
#import pytz

import Pyro.errors

from Host.Common.CubicSpline import CubicSpline
from Host.Common import CmdFIFO

#Set up a useful TimeStamp function...
if sys.platform == 'win32':
    TimeStamp = clock
else:
    TimeStamp = time
_valveSequenceLabels = {}

VALVE_CTRL_MODE_DICT = {0: "Disabled", 1: "Outlet Control", 2: "Inlet Control", 3: "Manual Control"}
ORIGIN = datetime(MINYEAR,1,1,0,0,0,0)
UNIXORIGIN = datetime(1970,1,1,0,0,0,0)

class MeasBufferStatus(object):

    def __init__(self):
        self.cols = None
        self.dataMgr = None
        self.bufferSize = None
        self.active = False
        self.nextDataBad = False
        
    def isActive(self):
        return self.active
        
    def setConfiguration(self, dataMgr, columns, bufferSize):
        self.dataMgr = dataMgr
        self.cols = columns
        self.bufferSize = bufferSize
        
    def configuration(self):
        return (self.dataMgr, self.cols, self.bufferSize)
        
    def setNextDataBad(self):
        self.nextDataBad = True
    
    def isNextDataBad(self):
        return self.nextDataBad
        
    def clearNextDataBad(self):
        self.nextDataBad = False
        pass
    
MEAS_BUFFER = MeasBufferStatus()
##############
# General file utilities
##############
def moveWildToDir(src,dest):
    srcFiles = glob(src)
    for f in srcFiles:
        move(abspath(f),join(dest,split(f)[1]))

##############
# General DRIVER functions
##############
def getAnalyzerId():
    try:
        instInfo = DRIVER.fetchLogicEEPROM()[0]
        analyzerId = instInfo["Analyzer"]+instInfo["AnalyzerNum"]
    except Exception, err:
        print err
        analyzerId = "UNKNOWN"
    return analyzerId

def getAnalyzerType():
    try:
        instInfo = DRIVER.fetchLogicEEPROM()[0]
        analyzerType = instInfo["Analyzer"]
    except Exception, err:
        print err
        analyzerType = "UNKNOWN"
    return analyzerType

def setFanState(fanState):
    DRIVER.setFanState(fanState)

##############
# Numerical calculations
##############
def cubicSpline(xList, yList, numPoints):
    cs = CubicSpline(array(xList), array(yList))
    newXList = arange(xList[0], xList[-1], (xList[-1]-xList[0])/numPoints)
    newYList = list(cs(newXList))
    return list(newXList), newYList

#############
# DAS Register
#############
def wrDasReg(regName, regValue):
    DRIVER.wrDasReg(regName, regValue)

def rdDasReg(regName):
    return DRIVER.rdDasReg(regName)

#############
# Config File accces
#############
def getConfig(fileName):
    return ConfigObj(fileName)

#############
# Warm Box Accessor
#############
def loadWarmBoxCal(fileName='',pCalOffset=None):
    FREQCONV.loadWarmBoxCal(fileName,pCalOffset)

#############
# Hot Box Accessor
#############
def loadHotBoxCal(fileName=''):
    FREQCONV.loadHotBoxCal(fileName)

#############
# UTC & Time
#############
def getUTCTime(option="float"):
    """Get UTC (GMT) time"""
    uctTimeTuple = datetime.timetuple(datetime.utcnow())
    if option.lower() == "tuple":
        return uctTimeTuple
    elif option.lower() == "float":
        return mktime(uctTimeTuple)
    elif option.lower() == "string":
        return ctime(mktime(uctTimeTuple))

def getSpecUTC(specTime = "00:00:00", option="float"):
    """Get the sepcified GMT time"""
    (hr, min, sec) = specTime.split(":")
    newTime = datetime.timetuple(datetime.utcnow().replace(hour=int(hr), minute=int(min), second = int(sec)))
    if option.lower() == "tuple":
        return newTime
    if option.lower() == "float":
        return mktime(newTime)
    elif option.lower() == "string":
        return ctime(mktime(newTime))

##############
# Plotting and Images
##############
def unixTimeArray2MatplotTimeArray(timeArray):
    dt = datetime.fromtimestamp(timeArray[0])
    mTime0 = dates.date2num(dt)
    mTimeArray = (timeArray-timeArray[0])/(3600.0*24.0) + mTime0
    formatter = dates.DateFormatter('%H:%M:%S\n%Y/%m/%d')
    return mTimeArray, formatter

def plotWithMatplotTime(plotObj, matplotTimeArray, dataArray, xLabel, yLabel, formatter, numLocator):
    plotObj.plot(matplotTimeArray, dataArray)
    plotObj.set_xlabel(xLabel)
    plotObj.set_ylabel(yLabel)
    plotObj.grid()
    plotObj.xaxis.set_major_formatter(formatter)
    plotObj.xaxis.set_major_locator(MaxNLocator(numLocator))

def grabScreenshot(filename):
    im = ImageGrab.grab()
    im.save(filename)

##########################
# Get barometric pressure with Yahoo weather
##########################
def getBarometricPressure(zipCode):
    url = 'http://xml.weather.yahoo.com/forecastrss?p=%s&u=f' % zipCode
    handler = urllib2.urlopen(url)
    dom = minidom.parse(handler)
    element = dom.getElementsByTagNameNS('http://xml.weather.yahoo.com/ns/rss/1.0', 'atmosphere')[0]
    handler.close()
    return 25.4*float(element.getAttribute('pressure'))

##########################
# Fitter functions
##########################
class FitterRPC(object):
    def __init__(self, rpcPort):
        self.fitter = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % rpcPort, ClientName = "Coordinator")

    def setH5Files(self, h5FileList):
        self.fitter.FITTER_makeHdf5RepositoryRpc(h5FileList)

    def fitSpectrum(self):
        self.fitter.FITTER_fitSpectrumRpc()
        sleep(2)
        self.fitter.FITTER_updateViewer(True)
        sleep(2)
        self.fitter.FITTER_setProcModeRpc(False)

    def maximizeViewer(self):
        self.fitter.FITTER_maximizeViewer(True)

    def restoreViewer(self):
        self.fitter.FITTER_maximizeViewer(False)

    def getProcessID(self):
        return self.fitter.CmdFIFO.GetProcessID()

    def stopServer(self):
        return self.fitter.CmdFIFO.StopServer()

####################
# External valve sequencer control
####################
def startExtValveSequencer():
    try:
        VALSEQ.startValveSeq()
        LOGFUNC("Started external valve sequencer\n")
    except Exception, err:
        LOGFUNC("External valve sequencer: %r\n" % err)

def stopExtValveSequencer():
    try:
        VALSEQ.stopValveSeq()
        LOGFUNC("Stopped external valve sequencer\n")
    except Exception, err:
        LOGFUNC("External valve sequencer: %r\n" % err)

def isExtValveSequencerOn():
    try:
        status = VALSEQ.getValveSeqStatus()
        return "ON" in status
    except Exception, err:
        LOGFUNC("External valve sequencer: %r\n" % err)
        return False

##########################
# Pulse analyzer functions
##########################
def pulseAnalyzerSet(source, concNameList, targetConc = None, thres1Pair = [0.0, 0.0],
                     thres2Pair = [0.0, 0.0], triggerType = "in", waitTime = 0.0,
                     validTimeAfterTrigger = 0.0, validTimeBeforeEnd = 0.0, timeout = 0.0,
                     bufSize = 500, numPointsToTrigger = 1, numPointsToRelease = 1, armCond = None):
    DATAMGR.PulseAnalyzer_Set(source, concNameList, targetConc, thres1Pair, thres2Pair,
                             triggerType, waitTime, validTimeAfterTrigger, validTimeBeforeEnd,
                             timeout, bufSize, numPointsToTrigger, numPointsToRelease, armCond)
    LOGFUNC("Pulse analyzer set\n")

def pulseAnalyzerStartRunning():
    DATAMGR.PulseAnalyzer_StartRunning()
    LOGFUNC("Pulse analyzer started\n")

def pulseAnalyzerStopRunning():
    DATAMGR.PulseAnalyzer_StopRunning()
    LOGFUNC("Pulse analyzer stopped\n")

def pulseAnalyzerStartAddingData():
    DATAMGR.PulseAnalyzer_StartAddingData()
    LOGFUNC("Started adding data to pulse analyzer\n")

def pulseAnalyzerStopAddingData():
    DATAMGR.PulseAnalyzer_StopAddingData()
    LOGFUNC("Stopped adding data to pulse analyzer\n")

def pulseAnalyzerGetDataReady():
    return DATAMGR.PulseAnalyzer_GetDataReady()

def pulseAnalyzerIsTriggeredStatus():
    return DATAMGR.PulseAnalyzer_IsTriggeredStatus()

def pulseAnalyzerGetOutput():
    return DATAMGR.PulseAnalyzer_GetOutput()

def pulseAnalyzerGetTimestamp():
    return DATAMGR.PulseAnalyzer_GetTimestamp()

def pulseAnalyzerReset():
    return DATAMGR.PulseAnalyzer_Reset()
    LOGFUNC("Pulse analyzer reset\n")

def pulseAnalyzerGetStatistics():
    return DATAMGR.PulseAnalyzer_GetStatistics()

def pulseAnalyzerGetPulseStartEndTime():
    return DATAMGR.PulseAnalyzer_GetPulseStartEndTime()

##########################
# Data manager functions
##########################
def setMeasBuffer(source, colList, bufSize):
    DATAMGR.MeasBuffer_Set(source, colList, bufSize)
    MEAS_BUFFER.active = True
    MEAS_BUFFER.setConfiguration(source, colList, bufSize)
    LOGFUNC("Meas buffer set\n")

def clearMeasBuffer():
    DATAMGR.MeasBuffer_Clear()
    LOGFUNC("Meas buffer cleared\n")

def measGetBuffer():
    return DATAMGR.MeasBuffer_Get()

def measGetBufferFirst():
    try:
        if not MEAS_BUFFER.isActive():
            DATAMGR.MeasBuffer_Set(*MEAS_BUFFER.configuration())
            DATAMGR.MeasBuffer_Clear()
            MEAS_BUFFER.active = True
   
        return DATAMGR.MeasBuffer_GetFirst()
    
    except CmdFIFO.ShutdownInProgress:
        MEAS_BUFFER.active = False
        MEAS_BUFFER.setNextDataBad()
        LOGFUNC("DataManager shutdown in progress\n")
        return None
    
    except Pyro.errors.ProtocolError:
        MEAS_BUFFER.active = False
        MEAS_BUFFER.setNextDataBad()
        LOGFUNC("DataManager not running\n")
        return None

def measIsDataBad():
    isBad = MEAS_BUFFER.isNextDataBad()
    MEAS_BUFFER.clearNextDataBad()
    return isBad
        
def enableCalScript():
    LOGFUNC("Calibration script from Data Manager is enabled\n")
    DATAMGR.Cal_Enable()

def disableCalScript():
    LOGFUNC("Calibration script from Data Manager is disabled\n")
    DATAMGR.Cal_Disable()

def getUserCalibrations():
    return DATAMGR.Cal_GetUserCalibrations()

def getInstrCalibrations():
    return DATAMGR.Cal_GetInstrCalibrations()

##########################
# Other Driver functions
##########################
def getDasTemperature():
    return DRIVER.rdDasReg("DAS_TEMPERATURE_REGISTER")

##########################
# Quick GUI functions
##########################
def setLineMarkerColor(color=None, colorTime=None):
    try:
        QUICKGUI.setLineMarkerColor(color, colorTime)
    except:
        pass

def getLineMarkerColor():
    try:
        return QUICKGUI.getLineMarkerColor()
    except:
        pass

##########################
# Data logger functions
##########################
def startDataLog(userLogName):
    try:
        DATALOGGER.DATALOGGER_startLogRpc(userLogName)
        LOGFUNC("Data log started\n")
    except:
        LOGFUNC("Failed to start data log\n")

def stopDataLog(userLogName):
    try:
        DATALOGGER.DATALOGGER_stopLogRpc(userLogName)
        LOGFUNC("Data log stopped\n")
    except:
        LOGFUNC("Failed to stop data log\n")

#########################
# Batch mode / rising loss trigger functions
#########################
def configBatchModeToDasReg(configDict):
    DRIVER.wrDasReg("VLVCNTRL_RISING_LOSS_THRESHOLD_REGISTER", float(configDict["risingLossThreshold"]))
    DRIVER.wrDasReg("VLVCNTRL_RISING_LOSS_RATE_THRESHOLD_REGISTER", float(configDict["risingLossRateThreshold"]))
    DRIVER.wrDasReg("VLVCNTRL_TRIGGERED_SOLENOID_STATE_REGISTER", int(configDict["triggeredSolenoidValveStates"]))
    DRIVER.wrDasReg("VLVCNTRL_TRIGGERED_SOLENOID_MASK_REGISTER", int(configDict["triggeredSolenoidValveMask"]))
    DRIVER.wrDasReg("VLVCNTRL_TRIGGERED_OUTLET_VALVE_VALUE_REGISTER", float(configDict["triggeredOutletValve"]))
    DRIVER.wrDasReg("VLVCNTRL_TRIGGERED_INLET_VALVE_VALUE_REGISTER", float(configDict["triggeredInletValve"]))

def getThresholdMode():
    return DRIVER.rdDasReg("VLVCNTRL_THRESHOLD_MODE_REGISTER")

def setThresholdMode(mode):
    """
    mode -- an integer in the range of [0,1,2]:
      0 -> Disabled
      1 -> Rising Loss
      2 -> Triggered
    """
    DRIVER.wrDasReg("VLVCNTRL_THRESHOLD_MODE_REGISTER", mode)

#####################
#   Solenoid valve control functions
#####################
def setValveMask(mask):
    """Set the valve mask to the specified value, where the lowest 6 bits are for the solenoid valves.
    mask = 0 -> all closed
           1 -> open valve 1
           2 -> open valve 2
           4 -> open valve 3
           ...
    """
    LOGFUNC("Set solenoid valve mask to %d\n" % mask)
    DRIVER.setValveMask(mask)

def getValveMask():
    """Read the valve mask, where the lowest 6 bits are for the solenoid valves.
    mask = 0 -> all closed
           1 -> open valve 1
           2 -> open valve 2
           4 -> open valve 3
           ...
    """
    return DRIVER.getValveMask()

#####################
#   Rotary valve control functions
#####################
def setRotValveMask(rotPos):
    """Set the MPV valve mask (position)
    """
    DRIVER.setMPVPosition(int(rotPos))

def getRotValveMask(rotPos):
    """Get the MPV valve mask (position)
    """
    DRIVER.getMPVPosition()

######################
# Inlet/outlet valve control functions
######################
def setInletValveMaxChange(value):
    """Set maximum inlet valve DAC change"""
    try:
        DRIVER.wrDasReg("VALVE_CNTRL_INLET_VALVE_MAX_CHANGE_REGISTER", value)
        LOGFUNC("Maximum inlet valve change: %.2f\n" % value)
    except:
        LOGFUNC("setInletValveMaxChange() failed!\n")

def setInletValveGains(g1, g2):
    try:
        DRIVER.wrDasReg("VALVE_CNTRL_INLET_VALVE_GAIN1_REGISTER", g1)
        DRIVER.wrDasReg("VALVE_CNTRL_INLET_VALVE_GAIN2_REGISTER", g2)
        LOGFUNC("Inlet valve gain1 = %.2f, gain2 = %.2f\n" % (g1, g2))
    except:
        LOGFUNC("setInletValveGains() failed!\n")


def setValveMinDac(valveSelect, value):
    valveSelect = valveSelect.lower()
    try:
        if valveSelect == "inlet":
            return DRIVER.wrDasReg("VALVE_CNTRL_INLET_VALVE_MIN_REGISTER", value)
        elif valveSelect == "outlet":
            return DRIVER.wrDasReg("VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER", value)
        else:
            raise Exception, "Choose either 'inlet' or 'outlet'!"
    except:
        LOGFUNC("setValveMinDac() failed!\n")

def setValveMaxDac(valveSelect, value):
    valveSelect = valveSelect.lower()
    try:
        if valveSelect == "inlet":
            return DRIVER.wrDasReg("VALVE_CNTRL_INLET_VALVE_MAX_REGISTER", value)
        elif valveSelect == "outlet":
            return DRIVER.wrDasReg("VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER", value)
        else:
            raise Exception, "Choose either 'inlet' or 'outlet'!"
    except:
        LOGFUNC("setValveMaxDac() failed!\n")

def getValveMinMaxDac(valveSelect):
    valveSelect = valveSelect.lower()
    try:
        if valveSelect == "inlet":
            min = DRIVER.rdDasReg("VALVE_CNTRL_INLET_VALVE_MIN_REGISTER")
            max = DRIVER.rdDasReg("VALVE_CNTRL_INLET_VALVE_MAX_REGISTER")
        elif valveSelect == "outlet":
            min = DRIVER.rdDasReg("VALVE_CNTRL_OUTLET_VALVE_MIN_REGISTER")
            max = DRIVER.rdDasReg("VALVE_CNTRL_OUTLET_VALVE_MAX_REGISTER")
        else:
            raise Exception, "Choose either 'inlet' or 'outlet'!"
        return {"min": min, "max": max}
    except:
        LOGFUNC("getValveMinMaxDac() failed!\n")

def startInletValveControl(pressureSetpoint=None, outletValveDac=None):
    result = DRIVER.startInletValveControl(pressureSetpoint, outletValveDac)
    LOGFUNC("Inlet valve control started, pressure setpoint = %.2f, outlet valve DAC = %.2f\n" %
            (result["cavityPressureSetpoint"], result["outletValve"]))

def startOutletValveControl(pressureSetpoint=None, inletValveDac=None):
    result = DRIVER.startOutletValveControl(pressureSetpoint, inletValveDac)
    LOGFUNC("Outlet valve control started, pressure setpoint = %.2f, inlet valve DAC = %.2f\n" %
            (result["cavityPressureSetpoint"], result["inletValve"]))

def setValveControlMode(mode):
    """
    mode -- an integer in the range of [0,1,2,3]:
      0 -> Disabled
      1 -> Outlet Control
      2 -> Inlet Control
      3 -> Manual Control
    """
    DRIVER.wrDasReg("VALVE_CNTRL_STATE_REGISTER", mode)
    LOGFUNC("Current valve control mode: %s\n" % VALVE_CTRL_MODE_DICT[mode])

def getValveDacValues():
    """Get Valve DAC value for both valves """
    inletDacValue = DRIVER.rdDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER")
    outletDacValue = DRIVER.rdDasReg("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER")
    return {"inletDacValue": inletDacValue, "outletDacValue": outletDacValue}

def setValveDacValue(valveSelect, dacValue1, dacValue2 = None):
    """Set Valve DAC value for inlet, outlet, or both valves
    valveSelect -- a string that indicates the target valve to be changed. Valid values are ["both", "inlet", and "outlet"].
    """
    valveSelect = valveSelect.lower()
    try:
        if valveSelect == "both":
            if dacValue2 == None:
                raise Exception, "Two valid valve DAC values are required!"
            DRIVER.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER", dacValue1)
            DRIVER.wrDasReg("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER", dacValue2)
            # LOGFUNC("New inlet valve DAC: %.2f; new outlet valve DAC: %.2f\n" % (dacValue1, dacValue2))
        elif valveSelect == "inlet":
            DRIVER.wrDasReg("VALVE_CNTRL_USER_INLET_VALVE_REGISTER", dacValue1)
            # LOGFUNC("New inlet valve DAC: %.2f\n" % dacValue1)
        elif valveSelect == "outlet":
            DRIVER.wrDasReg("VALVE_CNTRL_USER_OUTLET_VALVE_REGISTER", dacValue1)
            # LOGFUNC("New outlet valve DAC: %.2f\n" % dacValue1)
    except:
        LOGFUNC("setValveDacValues() failed!\n")

#####################
# Cavity pressure control functions
#####################
def getCavityPressure():
    """Read the current cavity pressure"""
    return DRIVER.rdDasReg("CAVITY_PRESSURE_REGISTER")

def getCavityPressureSetPoint():
    """Get cavity pressure set point in torr """
    return DRIVER.rdDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER")

def setCavityPressureSetPoint(setpoint):
    """Set cavity pressure set point in torr """
    try:
        DRIVER.wrDasReg("VALVE_CNTRL_CAVITY_PRESSURE_SETPOINT_REGISTER", setpoint)
        # LOGFUNC("New cavity pressure set point: %.2f torr\n" % setpoint)
    except:
        LOGFUNC("setCavityPressureSetPoint() failed!\n")

def getMaxCavityPressureRate():
    """Get maximum cavity pressure change rate in torr/s """
    return DRIVER.rdDasReg("VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER")

def setMaxCavityPressureRate(rate):
    """Set maximum cavity pressure change rate in torr/s """
    try:
        DRIVER.wrDasReg("VALVE_CNTRL_CAVITY_PRESSURE_MAX_RATE_REGISTER", rate)
        # LOGFUNC("Maximum cavity pressure change rate: %.2f torr/s\n" % rate)
    except:
        LOGFUNC("setMaxCavityPressureRate() failed!\n")

##############
# Stabilizing functions
##############
def waitPressureStabilize(setpoint, tolerance, timeout, checkInterval, lockCount=1):
    """ Wait for pressure to stabilize """
    inRange      = False
    index        = 0
    inRangeCount = 0
    isStable     = False
    while index < timeout:
        pressure = getCavityPressure()
        # LOGFUNC("Pressure delta from setpoint = %.2f\n" %  (pressure - setpoint))
        inRange  = (abs(pressure - setpoint)/setpoint <= tolerance)
        if inRange:
            inRangeCount+=1
        else:
            inRangeCount=0
        sleep(checkInterval)
        index += 1
        if inRangeCount >= lockCount:
            # LOGFUNC("Pressure locked at %.2f\n" % setpoint)
            isStable = True
            break
    return isStable

####################
# Measurement System functions
####################
def setMeasSysMode(mode, timeout=3):
    """
    mode -- a string representing the desired measurement mode
    """
    measSysStates = MEASSYS.GetStates()
    if measSysStates['State_MeasSystem'] == 'ERROR':
        MEASSYS.Error_Clear()

    MEASSYS.Disable()
    startTime = TimeStamp()
    measSysStates = MEASSYS.GetStates()
    while not (measSysStates['State_MeasSystem'] == 'READY' and measSysStates['State_SpectrumManager'] == 'READY'):
        if measSysStates['State_MeasSystem'] == 'ERROR':
            MEASSYS.Error_Clear()

        if TimeStamp() - startTime < timeout:
            sleep(0.1)
            measSysStates = MEASSYS.GetStates()
        else:
            LOGFUNC("MeasSystem wasn't disabled properly within timeout limit - setMeasSysMode() failed\n")
            MEASSYS.Enable()
            return
    MEASSYS.Mode_Set(mode)
    MEASSYS.Enable()

def getMeasSysMode():
    return MEASSYS.Mode_Get()

#################
# Sample Manager functions
#################
def skipPressureCheck():
    SAMPLEMGR.SkipPressureCheck()

def resumePressureCheck():
    SAMPLEMGR.ResumePressureCheck()

def setSampleMgrMode(mode):
    SAMPLEMGR._SetMode(mode)

#################
# Instrument Manager functions
#################
def enableInstMgrAutoRestartFlow():
    INSTMGR.INSTMGR_EnableAutoRestartFlow()

def disableInstMgrAutoRestartFlow():
    INSTMGR.INSTMGR_DisableAutoRestartFlow()

################
# Output format functions
################
def calcInjectDateTime(logDate,logTime,injTime):
    fmt = "%Y/%m/%d %H:%M:%S"
    fmtd = "%Y/%m/%d"
    fmtt = "%H:%M:%S"
    d1 = mktime(strptime(logDate+" "+logTime,fmt))
    t2 = '23:59:57'
    d2 = mktime(strptime(logDate+" "+injTime,fmt))
    if d1<d2:
        d2 = d2 - 24*3600
    return strftime(fmtd,localtime(d2)),strftime(fmtt,localtime(d2))

def formatOutput(results,config):
    i = 1
    out = []
    while True:
        try:
            c = config["column%d" % i]
            f = config["format%d" % i]
            out.append(("%s" % (f,)) % results[c])
            i += 1
        except:
            break
    return "".join(out)

#################
# Valve sequence functions
#################
def getValveStep():
    return DRIVER.rdDasReg("VALVE_CNTRL_SEQUENCE_STEP_REGISTER")

def atValveStep(step):
    global _valveSequenceLabels
    if isinstance(step,str):
        step = _valveSequenceLabels[step]
    return DRIVER.rdDasReg("VALVE_CNTRL_SEQUENCE_STEP_REGISTER") == step

def sendValveSequence(configDict):
    global _valveSequenceLabels
    _valveSequenceLabels = {"none":-1}
    good = True
    sequence = []
    step = 0
    try:
        for line in configDict["steps"].split("\n"):
            # Remove comments from the line
            line = line.split("#",1)[0].strip()
            if not line: continue
            # Look for a label
            if ":" in line:
                label = line.split(":",1)[0].strip()
                _valveSequenceLabels[label] = step
                line = line[line.find(":")+1:].strip()
            if not line: continue
            try:
                mask,value,dwell = [eval(x) for x in line.split(",")]
                step += 1
                if mask<0 or mask>0xFF:
                    good = False
                    LOGFUNC("Invalid valve sequence mask %s in %s\n" % (mask,line))
                if value<0 or value>0xFF:
                    good = False
                    LOGFUNC("Invalid valve sequence value %s in %s\n" % (value,line))
                if dwell<0 or dwell>0xFFFF:
                    good = False
                    LOGFUNC("Invalid valve sequence dwell %s in %s\n" % (dwell,line))
                sequence.append([mask,value,dwell])
            except:
                good = False
                LOGFUNC("Invalid valve definition command: %s" % line)
            if not good:
                break
    except:
        while good:
            optName = 'step%d' % step
            if optName not in configDict:
                break
            try:
                optValue = configDict[optName]
                mask = eval(optValue[0])
                value = eval(optValue[1])
                dwell = eval(optValue[2])
                # LOGFUNC("Step %d, mask 0x%x, value 0x%x, dwell %d\n" % (step,mask,value,dwell))
                step += 1
                if mask<0 or mask>0xFF:
                    good = False
                    LOGFUNC("Invalid valve sequence mask %s in %s\n" % (optValue[0],optName))
                if value<0 or value>0xFF:
                    good = False
                    LOGFUNC("Invalid valve sequence value %s in %s\n" % (optValue[1],optName))
                if dwell<0 or dwell>0xFFFF:
                    good = False
                    LOGFUNC("Invalid valve sequence dwell %s in %s\n" % (optValue[2],optName))
            except Exception,e:
                LOGFUNC("Error %s in valve sequence definition\n" % e)
                good = False
            sequence.append([eval(optValue[0]),eval(optValue[1]),eval(optValue[2])])
    if not good:
        raise ValueError("Cannot process and send valve sequence definition")
    else:
        print _valveSequenceLabels
        print sequence
        # LOGFUNC("Sending valve sequence definition to DAS\n")
        DRIVER.wrValveSequence(sequence)

def setValveStep(step):
    global _valveSequenceLabels
    if isinstance(step,str):
        step = _valveSequenceLabels[step]
    DRIVER.wrDasReg("VALVE_CNTRL_SEQUENCE_STEP_REGISTER",step)

def parseAutosamplerLog(logText):
    logString = logText.split("\n")
    logDate = logString[0].strip().split()[-2]
    logTime = logString[0].strip().split()[-1]
    injTime = "00:00:00"
    sampleNum = -1
    trayName = "Unknown"
    jobNum = -1
    methodName = "Unknown"

    sampleLineNum = -1
    try:
        while True:
            injLine = logString[sampleLineNum].strip().split()
            if len(injLine) == 4:
                if injLine[1] == "Sample" and injLine[3]=="Injected":
                    injTime = injLine[0]
                    sampleNum = int(injLine[2])
                    break
            sampleLineNum -= 1
        while True:
            trayLine = logString[sampleLineNum].strip().split()
            if trayLine and trayLine[0]=="Tray":
                trayName = trayLine[1][:-1]
                break
            sampleLineNum -= 1
        while True:
            jobLine = logString[sampleLineNum].strip().split()
            if len(jobLine) >= 7:
                if jobLine[2] == "Job" and jobLine[4] == "started:":
                    jobNum = int(jobLine[3])
                    if jobLine[5] == "Method":
                        methodName = jobLine[6]
                    break
            sampleLineNum -= 1
    except:
        pass
    return logDate, logTime, injTime, trayName, sampleNum, jobNum, methodName

#################
# Temp Cycle functions
#################
def setTempCycleRegisters(sweepMax, sweepMin, sweepIncr):
    origMax = None
    origMin = None
    origIncr = None
    origState = None
    try:
        origState = DRIVER.rdDasReg("CAVITY_TEMP_CNTRL_STATE_REGISTER")
        DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_STATE_REGISTER","TEMP_CNTRL_SweepingState")
    except:
        logFunc("Problem with setTempCycleRegisters for register: CAVITY_TEMP_CNTRL_STATE_REGISTER\n")

    try:
        origMax = DRIVER.rdDasReg("CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER")
        DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER",sweepMax)
    except:
        logFunc("Problem with setTempCycleRegisters for register: CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER\n")

    try:
        origMin = DRIVER.rdDasReg("CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER")
        DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER",sweepMin)
    except:
        logFunc("Problem with setTempCycleRegisters for register: CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER\n")

    try:
        origIncr = DRIVER.rdDasReg("CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER")
        DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER",sweepIncr)
    except:
        logFunc("Problem with setTempCycleRegisters for register: CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER\n")

    return origMax,origMin,origIncr,origState

def restoreTempCycleRegisters(sweepMax, sweepMin, sweepIncr, cntlState):
    try:
        if cntlState: DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_STATE_REGISTER",cntlState)
    except:
        logFunc("Problem with restoreTempCycleRegisters for register: CAVITY_TEMP_CNTRL_STATE_REGISTER\n")

    try:
        if sweepMax: DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER",sweepMax)
    except:
        logFunc("Problem with restoreTempCycleRegisters for register: CAVITY_TEMP_CNTRL_SWEEP_MAX_REGISTER\n")

    try:
        if sweepMin: DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER",sweepMin)
    except:
        logFunc("Problem with restoreTempCycleRegisters for register: CAVITY_TEMP_CNTRL_SWEEP_MIN_REGISTER\n")

    try:
        if sweepIncr: DRIVER.wrDasReg("CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER",sweepIncr)
    except:
        logFunc("Problem with restoreTempCycleRegisters for register: CAVITY_TEMP_CNTRL_SWEEP_INCR_REGISTER\n")

    return True

#################
# Tag-along data functions
#################
def setTagalongData(name,value):
    SPECTCOLLECTOR.setTagalongData(name, value)

def getTagalongData(name):
    return SPECTCOLLECTOR.getTagalongData(name)

def deleteTagalongData(name):
    SPECTCOLLECTOR.deleteTagalongData(name)

ANALYSIS_FNAME = "/PicarroSeq.txt"

def incrAnalysisNumber():
    try:
        fname = CONFIG["Files"]["sequence"]
    except:
        fname = ANALYSIS_FNAME
    try:
        fp = file(fname,"r")
        seq = int(fp.read())
        fp.close()
    except:
        seq = 0
    seq += 1
    fp = file(fname,"w")
    print >>fp, "%d" % seq
    fp.close()

def getAnalysisNumber():
    try:
        fname = CONFIG["Files"]["sequence"]
    except:
        fname = ANALYSIS_FNAME
    fp = file(fname,"r")
    seq = int(fp.read())
    fp.close()
    return seq

def getPrefix():
    try:
        prefix = CONFIG["Files"]["prefix"]
    except:
        prefix = "P"
    return prefix

#################
# Setting and getting pressure calibration constants
#################
def getCavityPressureCalibration():
    return (DRIVER.rdDasReg('CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER'),
            DRIVER.rdDasReg('CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER'))

def setCavityPressureCalibration(scale,offset):
    return (DRIVER.wrDasReg('CONVERSION_CAVITY_PRESSURE_SCALING_REGISTER',scale),
            DRIVER.wrDasReg('CONVERSION_CAVITY_PRESSURE_OFFSET_REGISTER',offset))

#################
# Loading and saving Master.ini file
#################
def loadMaster():
    DRIVER.loadIniFile()

def writeMaster(fileName=None):
    DRIVER.writeIniFile(fileName)

def dummyGetLog():
    return """   Print Date: 2008/08/13   10:04:35
   Site Name: CTC, System Name: PAL, System SNo: 142218

   2008/08/13  10:02:22 Job 01 started: Method 5ulMethd
                        Tray MT1-Frnt, Vial 1-3, Count = 1, Increment = 1
               10:02:43 Sample 1 Injected
               10:03:14 Sample 2 Injected
               10:03:46 Sample 3 Injected

   2008/08/13  10:03:56 Job 04 started: Method 5ulMethd
                        Tray MT1-Frnt, Vial 1-1, Count = 1, Increment = 1
               10:04:17 Sample 1 Injected
               10:05:20 Sample 2 Injected
|
"""

def dummyGetLog():
    return """   Print Date: 2008/08/13   10:04:35
   Site Name: CTC, System Name: PAL, System SNo: 142218

   2008/08/13  10:02:22 Job 01 started: Method 5ulMethd
                        Tray MT1-Frnt, Vial 1-3, Count = 1, Increment = 1
               10:02:43 Sample 1 Injected
               10:03:14 Sample 2 Injected
               10:03:46 Sample 3 Injected
|
"""

class SocketInterface(object):
    def __init__(self, host, port=51020):
        self.s = None
        self.host = host
        self.port = port

    def sendAndGet(self,str):
        # Send str and get data back. If a communications error
        #  occurs, wait 30s, then try again (in case GUI restarts)
        while True:
            try:
                self.connect()
                self.s.sendall(str + '\r')
                try:
                    data = self.s.recv(1024)
                except:
                    data = "UNKNOWN\n"
                break
            except Exception,e:
                LOGFUNC("Socket communication error: %s, retrying in 30s\n" % (e,))
                self.close()
                sleep(30)
        self.close()
        return data

    def connect(self):
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.connect((self.host,self.port))
        self.s.settimeout(1.0)

    def close(self):
        self.s.close()
        self.s = None

    def setTagalongData(self, label, value):
        return self.sendAndGet("_MEAS_SET_TAGALONG_DATA '%s' %f" % (label, value))

    def getTagalongData(self, label):
        return self.sendAndGet("_MEAS_GET_TAGALONG_DATA '%s'" % (label))

class Comms(object):
    def __init__(self,host,port):
        self.s = None
        self.host = host
        self.port = port
        self.cols = None

    def sendAndGet(self,str):
        # Send str and get data back. If a communications error
        #  occurs, wait 30s, then try again (in case GUI restarts)
        while True:
            try:
                self.connect()
                self.s.sendall(str + '\r')
                data = ""
                while True:
                    d = self.s.recv(1024)
                    if d:
                        data += d
                    else:
                        break
                break
            except Exception,e:
                LOGFUNC("Socket communication error: %s, retrying in 30s\n" % (e,))
                self.s.close()
                self.s = None
                sleep(30)
        self.s.close()
        self.s = None
        return data

    def connect(self):
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.connect((self.host,self.port))

    def getColumns(self):
        reply = self.sendAndGet("_PULSE_GETSTATUS")
        replyList = reply.split("\n")
        for r in replyList:
            key,value = r.split("=")
            if key.strip() == "COLUMNS":
                self.cols = value.split(";")
                self.cols = [c.strip() for c in self.cols][:-1]

    def clearPulseBuffer(self):
        reply = self.sendAndGet("_PULSE_CLEARBUFFER")

    def clearMeasBuffer(self):
        reply = self.sendAndGet("_MEAS_CLEARBUFFER")

    def getBufferFirst(self):
        reply = self.sendAndGet("_PULSE_GETBUFFERFIRST")
        dataCols = reply.split(";")[:-1]
        dataCols = [float(d) for d in dataCols]
        self.results = {}
        if sum([abs(d) for d in dataCols]) != 0:
            self.getColumns()
            for i,c in enumerate(self.cols):
                self.results[c] = dataCols[2*i+1]
            self.results["time"] = dataCols[0]

    def measGetBufferFirst(self, setFloat=False, instrType="H2O"):
        if instrType == "H2O":
            concKeys = ["DAYS_SINCE_JAN", "DAS_TEMP", "H2O", "D_1816", "D_DH", "SOLENOID_VALVES"]
        elif instrType == "iCO2":
            concKeys = ["12CO2", "13CO2", "Delta", "Ratio", "H2O"]
        else:
            concKeys = []
        numKeys = len(concKeys)
        reply = self.sendAndGet("_MEAS_GETBUFFERFIRST")
        dataCols = reply.split(";")[:-1]
        self.results = {}
        if len(dataCols) >= 2*numKeys:
            date = dataCols[0].split(".")[0]
            fmt1 = "%y/%m/%d %H:%M:%S"
            d1 = mktime(strptime(date,fmt1))
            fmt2 = "%Y/%m/%d %H:%M:%S"
            self.results["date"] = strftime(fmt2,localtime(d1))
            for idx in range(numKeys):
                if not setFloat:
                    self.results[concKeys[idx]]  = dataCols[2*idx+1]
                else:
                    try:
                        self.results[concKeys[idx]]  = float(dataCols[2*idx+1])
                    except:
                        self.results[concKeys[idx]]  = dataCols[2*idx+1]

class DummyAutosampler(object):
    def __init__(self,startVial=1,endVial=54,count=20,incr=1,jobNum=1,method="5ulMethd",tray="MT1-Frnt"):
        self.startVial = startVial
        self.endVial = endVial
        self.count = count
        self.incr = incr
        self.vial = self.startVial
        self.current = 0
        self.jobNum = jobNum
        self.method = method
        self.tray = tray
        self.done = False
        self.logLines = []
        nowStr = strftime("%Y/%m/%d  %H:%M:%S",localtime())
        self.logLines.append("   %s Job %02d started: Method %s\n                        Tray %s, Vial %d-%d, Count = %d, Increment = %d" \
        % (nowStr,jobNum,method,tray,startVial,endVial,count,incr))

    def getLog(self):
        nowStr = strftime("%Y/%m/%d   %H:%M:%S",localtime())
        header = "   Print Date: %s\n   Site Name: CTC, System Name: PAL, System SNo: 142218\n" % (nowStr,)
        if not self.done:
            self.current += 1
            nowStr = strftime("%H:%M:%S",localtime())
            self.logLines.append("               %s Sample %d Injected" % (nowStr,self.vial,))
            if self.current >= self.count:
                self.current = 0
                self.vial += self.incr
                self.done = self.vial > self.endVial
        #print header + "\n".join(self.logLines)
        return header + "\n".join(self.logLines)
    def open(self):
        pass
    def close(self):
        pass
    def flush(self):
        pass
    def assertStart(self):
        pass
    def deassertStart(self):
        pass
    def assertInject(self):
        pass
    def deassertInject(self):
        pass
    def getInjected(self):
        return True
