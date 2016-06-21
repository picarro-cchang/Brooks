"""
Instruction:
1)  Do not use _REPORT_ and other global variables in alarm classes and related functions. 
    Instead pass desired variables from main script into class methods.
2)  Alarms will be sorted by their attributes "order" (default to 0 if not specified), "word" and "bit", 
    and those with lower values will be processed first.
"""

import inspect
import time
import os
import sys
here = os.path.split(os.path.abspath(inspect.getfile(inspect.currentframe())))[0]
if here not in sys.path:
    sys.path.append(here)
import numpy as np
from collections import deque, OrderedDict

from Host import PeriphIntrf
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.EventManagerProxy import Log

# SpectrumIds used
TARGET_SPECIES = [170]
# Buffer length
WindSpeedHistoryBufferLen = 100
WlmTargetFreqHistoryBufferLen = 6000
# Valve masks
VALVE_MASK_ACTIVE = 0x10
VALVE_MASK_CHECK_ALARM = 0x03

# From fitterThread.py -- should be integrated into DM to use the "flat" .ini structure of FitterConfig.ini
def evalLeaves(d):
    for k in d:
        if isinstance(d[k],dict):
            evalLeaves(d[k])
        else:
            try:
                d[k] = eval(d[k])
            except:
                pass
    return d

def expAverage(xavg,x,dt,tau):
    if xavg is None:
        xavg = x
    else:
        xavg = (1.0-np.exp(-dt/tau))*x + np.exp(-dt/tau)*xavg
    return xavg
    
def totalSpeed(vx, vy):
    if (not np.isnan(vx)) and (not np.isnan(vy)):
        return np.sqrt(vx*vx + vy*vy)
    else:
        return 0.0
        
def alarmTestBit(word, bit):
    mask = 1 << bit
    return word & mask

def GetBaselineCavityLoss():
    fitterConfigFile = os.path.join(here, '..', '..', '..', 'InstrConfig', 'Calibration', 'InstrCal', 'FitterConfig.ini')
    fitterConfig = evalLeaves(CustomConfigObj(fitterConfigFile, list_values=False).copy())
    return fitterConfig['CFADS_Baseline_level']

def getAlarmOrder(section):
    if "order" in _ALARM_PARAMS_[section]:
        return _ALARM_PARAMS_[section]["order"]
    else:
        return 0

class BasicAlarm(_ALARM_FUNCTIONS_.Alarm):
    def __init__(self, *a):
        _ALARM_FUNCTIONS_.Alarm.__init__(self, *a)
        self.variable = self.params["variable"].split(",")
        self.input = np.zeros(len(self.variable))
    
class AlarmOfInterval(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.timeConstant = float(self.params["timeConstant"])
        self.maximum  = float(self.params["maximum"])
        self.normalInterval = float(self.params["normal"])
        self.average = 0.0
        self.badInterval = False
        
    def processData(self, dt, CH4):
        self.badInterval = (dt == 0.0)
        if CH4 > p.MethaneConcThreshold:
            dt = self.normalInterval
        average = expAverage(self.average, dt, dt, self.timeConstant)
        self.average = min(average, self.maximum)
    
    def processBeforeCheckValue(self, value, *a):
        spectrumId, CH4 = a
        if spectrumId == p.EthaneSpectrumId:
            self.processData(value, CH4)
        else:
            return None
        return self.average
        
    def processAfterCheckValue(self, value, *a):
        return None if value is None else (value or self.badInterval)
        
class AlarmByBinaryExpAverage(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.timeConstant = float(self.params["timeConstant"])
        self.average = 0.0
        
    def processAfterCheckValue(self, value, *a):
        interval = a[0]
        self.average = expAverage(self.average, int(value), interval, self.timeConstant)
        return (self.average >= 0.5)
        
class AlarmOfCaptureMode(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.timeConstant = float(self.params["timeConstant"])
        self.average = 0.0
        
    def processAfterCheckValue(self, value, *a):
        interval = a[0]
        g = _GLOBALS_['alarms']["General"]
        if g.alarmActive and g.alarmActiveState:
            self.average = expAverage(self.average, int(value), interval, self.timeConstant)
        return (self.average >= 0.5)
        
class AlarmOfCarSpeed(BasicAlarm):
    def processBeforeCheckValue(self, value, *a):
        return totalSpeed(value, a[0])
        
class AlarmOfWindSpeed(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.history = deque(maxlen=WindSpeedHistoryBufferLen)
        
    def processBeforeCheckValue(self, value, *a):
        windSpeed = totalSpeed(value, a[0])
        self.history.append(windSpeed)
        windSpeedHistoryStd = np.std(self.history, ddof=1)
        windSpeedHistoryAvg = np.mean(self.history)
        return abs(windSpeed - windSpeedHistoryAvg) > (3.5 * windSpeedHistoryStd)

class AlarmOfCavityBaselineLoss(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.baselineCavityLoss = GetBaselineCavityLoss()
        
    def processBeforeCheckValue(self, value, *a):
        return value > p.CavityBaselineLossScaleFactor * self.baselineCavityLoss
        
class AlarmOfWlm(BasicAlarm):
    def processBeforeCheckValue(self, value, *a):
        return np.absolute(value)
        
class AlarmOfWlmShiftAdjustCorrelation(BasicAlarm):
    def processBeforeCheckValue(self, value, *a):
        return [np.absolute(value), np.absolute(a[0])]
       
class AlarmOfWlmTargetFreq(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.wlmOffsetBuffer = deque(maxlen=WlmTargetFreqHistoryBufferLen)
        
    def processBeforeCheckValue(self, value, *a):
        self.wlmOffsetBuffer.append(value)
        wlm6OffsetMean = np.mean(self.wlmOffsetBuffer)
        wlm6OffsetMax = max(self.wlmOffsetBuffer)
        wlm6OffsetMin = min(self.wlmOffsetBuffer)
        if wlm6OffsetMean != 0.0:
            return (wlm6OffsetMax - wlm6OffsetMin) / wlm6OffsetMean

class AlarmOfInvalidData(BasicAlarm):
    def processBeforeCheckValue(self, value, *a):
        analyzerStatus = value
        peripheralStatus = a[0]
        if analyzerStatus > 0:
            for b in p.AnalyzerStatusInvalidDataBits:
                if alarmTestBit(int(analyzerStatus), b): return 1
        if peripheralStatus > 0:
            for b in p.PeripheralStatusInvalidDataBits:
                if alarmTestBit(int(peripheralStatus), b): return 1
        else:
            return 0
            
class AlarmOfPeripheralStatus(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.lastUpdated = -1
        
    def processBeforeCheckValue(self, value, *a):
        current_time = time.time()
        interval = (current_time - self.lastUpdated) if self.lastUpdated > 0 else 0
        self.lastUpdated = current_time
        return interval
        
class AlarmOfGpsUpdated(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.oldGpsTime = -1
        
    def processBeforeCheckValue(self, value, *a):
        gpsNotUpdated = (value == self.oldGpsTime)
        self.oldGpsTime = value
        return gpsNotUpdated
        
class AlarmOfIGpsError(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        try:
            self.iGPS_installed = _DRIVER_.fetchHardwareCapabilities()["iGPS"]
        except:
            self.iGPS_installed = False
    
    def processAfterCheckValue(self, value, *a):
        # value = True if GPS_FIT > 2
        return value and (not self.iGPS_installed)
            
class AlarmGeneral:
    """
    This class does not set any alarm bit, but deals with some general stuffs 
    necessary for processing other alarms or just for checking data
    """
    def __init__(self):
        self.variable = ['peak_detector_state', 'ValveMask']
        self.peakDetectState = deque(maxlen=50)
        self.input = np.zeros(len(self.variable))
        
    def processAlarm(self, alarm, *values):
        peakDetectState, valveMask = values
        self.peakDetectState.append(peakDetectState)
        self.alarmActive = (int(valveMask) & VALVE_MASK_CHECK_ALARM) == 0
        self.alarmActiveState = np.sum( np.abs( np.diff(self.peakDetectState) ) ) < 1       
                    
class AlarmOfWindCheck:
    def __init__(self):
        self.variable = ['PERIPHERAL_STATUS', 'CAR_SPEED', 'GPS_FIT']
        self.input = np.zeros(len(self.variable))
        self.inactiveForWind = False
        
    def processAlarm(self, alarm, *values):
        peripheralStatus, carSpeed, gpsFit = values
        # Wind anomaly handling
        if (int(peripheralStatus) & PeriphIntrf.PeripheralStatus.PeripheralStatus.WIND_ANOMALY) > 0:
            if not np.isnan(carSpeed) and gpsFit >= 1:
                Log("Wind NaN due to anomaly")
                self.inactiveForWind = True
            else:
                Log("Wind NaN due to GPS")
        else:
            if self.inactiveForWind:
                Log("Survey status back to active after wind anomaly")
                self.inactiveForWind = False

if _GLOBALS_["init"]:
    _GLOBALS_["init"] = False
    _GLOBALS_['alarms'] = OrderedDict({"General" : AlarmGeneral(), "WindCheck" : AlarmOfWindCheck()})
    alarm_list = [[section, getAlarmOrder(section), _ALARM_PARAMS_[section]] for section in _ALARM_PARAMS_ if section.startswith("ALARM_")]
    alarm_list_sorted = sorted(alarm_list, key=lambda k: (k[1], k[2]['word'], k[2]['bit']))
    for section, order, a in alarm_list_sorted:
        if "class" in a:
            _GLOBALS_["alarms"][section] = eval(a["class"])(_ALARM_PARAMS_, section)
        else:
            _GLOBALS_["alarms"][section] = BasicAlarm(_ALARM_PARAMS_, section)

p = _ALARM_FUNCTIONS_.loadAlarmParams(_ALARM_PARAMS_, "Params")
if 'PERIPHERAL_STATUS' in _REPORT_:
    _ALARMS_[1] = _ALARMS_[1] | int(_REPORT_['PERIPHERAL_STATUS'])

if "species" in _REPORT_:
    if _REPORT_["species"] in TARGET_SPECIES: 
        for alarmName in _GLOBALS_["alarms"]:
            enableAlarm = True
            alarm = _GLOBALS_["alarms"][alarmName]
            for i, var in enumerate(alarm.variable):
                var = var.strip()
                if var.isdigit():
                    alarm.input[i] = _ALARMS_[int(var)]
                else:
                    if var in _REPORT_:
                        alarm.input[i] = _REPORT_[var]
                    else:
                        enableAlarm = False
                        break
            if enableAlarm:
                alarm.processAlarm(_ALARMS_, *alarm.input)
                
        _ALARM_REPORT_["SystemStatus"] = _ALARMS_[2]
        _ALARM_REPORT_["PeripheralStatus"] = _ALARMS_[1]
        _ALARM_REPORT_['AnalyzerStatus'] = _ALARMS_[0]
        _ALARM_REPORT_["cavityPressureOORAvg"] = _GLOBALS_["alarms"]["ALARM_CavityPressure"].average
        _ALARM_REPORT_["warmBoxTempOORAvg"] = _GLOBALS_["alarms"]["ALARM_WarmBoxTemperature"].average
        _ALARM_REPORT_["cavityTempOORAvg"] = _GLOBALS_["alarms"]["ALARM_CavityTemperature"].average
        _ALARM_REPORT_["module2FlowOORAvg"] = _GLOBALS_["alarms"]["ALARM_IntakeFlowRate"].average
        _ALARM_REPORT_["methaneInterval"] = _GLOBALS_["alarms"]["ALARM_MethaneInterval"].average