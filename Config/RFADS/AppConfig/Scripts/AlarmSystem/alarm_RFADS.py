import inspect
import os
import sys
here = os.path.split(os.path.abspath(inspect.getfile(inspect.currentframe())))[0]
if here not in sys.path:
    sys.path.append(here)
import numpy as np
from collections import deque

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
    return _ALARMS_[word] | mask

def GetBaselineCavityLoss():
    fitterConfigFile = os.path.join(here, '..', '..', '..', 'InstrConfig', 'Calibration', 'InstrCal', 'FitterConfig.ini')
    fitterConfig = evalLeaves(CustomConfigObj(fitterConfigFile, list_values=False).copy())
    return fitterConfig['CFADS_Baseline_level']

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
        if ("FastMethaneInterval" in self.alarmName) and (spectrumId == p.FastMethaneSpectrumId):
            self.processData(value, CH4)
        elif "IsotopicMethaneInterval" in self.alarmName and (spectrumId in p.IsotopicModeSpectrumIds):
            if spectrumId == p.IsotopicMethaneSpectrumId:
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
        return windSpeed > (2.6 * windSpeedHistoryStd)

class AlarmOfCavityBaselineLoss(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.baselineCavityLoss = GetBaselineCavityLoss()
        
    def processBeforeCheckValue(self, value, *a):
        return value > p.CavityBaselineLossScaleFactor * self.baselineCavityLoss
        
class AlarmOfSamplingInterval(BasicAlarm):
    def processAfterCheckValue(self, value, *a):
        g = _GLOBALS_['alarms']["General"]
        return value and (not g.alarmActive) and g.alarmActiveState 
        
class AlarmOfWlm(BasicAlarm):
    def processBeforeCheckValue(self, value, *a):
        return np.absolute(value)
        
class AlarmOfWlmShiftAdjustCorrelation(BasicAlarm):
    def processBeforeCheckValue(self, value, *a):
        return [np.absolute(value), np.absolute(a[0])]
        
class AlarmOfInetialGPS(BasicAlarm):
    def processBeforeCheckValue(self, value, *a):
        return [value, a[0]]
        
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
        if _ALARMS_[0] > 0:
            return sum([int(alarmTestBit(0, b)) for b in p.InvalidDataBit])
        else:
            return 0
            
class AlarmGeneral:
    """
    This class does not set any alarm bit, but deals with some general stuffs 
    necessary for processing other alarms or just for checking data
    """
    def __init__(self):
        self.peakDetectState = deque(maxlen=50)
        self.variable = []
        self.input = []
        self.inactiveForWind = False
        
    def processAlarm(self, alarm):
        peakDetectState = _DRIVER_.rdDasReg('PEAK_DETECT_CNTRL_STATE_REGISTER') #integer value, see interface.py
        self.peakDetectState.append(peakDetectState)
        self.alarmActive = (int(_REPORT_['ValveMask']) & VALVE_MASK_CHECK_ALARM) == 0
        self.alarmActiveState = np.sum( np.abs( np.diff(self.peakDetectState) ) ) < 1
        # Wind anomaly handling
        validWindCheck = True
        windFields = ['PERIPHERAL_STATUS', 'CAR_SPEED', 'GPS_FIT']
        for f in windFields:
            validWindCheck &= (f in _REPORT_)
        if validWindCheck:
            if (int(_REPORT_['PERIPHERAL_STATUS']) & PeriphIntrf.PeripheralStatus.PeripheralStatus.WIND_ANOMALY) > 0:
                if not np.isnan(_REPORT_['CAR_SPEED']) and _REPORT_['GPS_FIT'] >= 1:
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
    _GLOBALS_['alarms'] = {"General" : AlarmGeneral()}
    for section in _ALARM_PARAMS_:
        if section.startswith("ALARM_"):
            a = _ALARM_PARAMS_[section]
            if "class" in a:
                _GLOBALS_["alarms"][section] = eval(a["class"])(_ALARM_PARAMS_, section)
            else:
                _GLOBALS_["alarms"][section] = BasicAlarm(_ALARM_PARAMS_, section)

p = _ALARM_FUNCTIONS_.loadAlarmParams(_ALARM_PARAMS_, "Params")

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
        _ALARM_REPORT_["fastMethaneInterval"] = _GLOBALS_["alarms"]["ALARM_FastMethaneInterval"].average
        _ALARM_REPORT_["isotopicMethaneInterval"] = _GLOBALS_["alarms"]["ALARM_IsotopicMethaneInterval"].average