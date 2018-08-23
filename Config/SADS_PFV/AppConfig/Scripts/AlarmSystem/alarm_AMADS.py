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

from Host.Common.CustomConfigObj import CustomConfigObj

# SpectrumIds used
TARGET_SPECIES = [150, 153]
# Buffer length
WlmTargetFreqHistoryBufferLen = 6000

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
       
def alarmTestBit(word, bit):
    mask = 1 << bit
    return word & mask

def GetBaselineCavityLoss():
    #fitterConfigFile = os.path.join(here,'..', '..', 'InstrConfig', 'Calibration', 'InstrCal', 'FitterConfig.ini')
    #fitterConfig = evalLeaves(CustomConfigObj(fitterConfigFile, list_values=False).copy())
    return 0 #fitterConfig['CFADS_baseline']
    
def getAlarmOrder(section):
    if "order" in _ALARM_PARAMS_[section]:
        return _ALARM_PARAMS_[section]["order"]
    else:
        return 0

class BasicAlarm(_ALARM_FUNCTIONS_.Alarm):
    def __init__(self, *a):
        _ALARM_FUNCTIONS_.Alarm.__init__(self, *a)
        self.variable = self.params["variable"].split(",")
        self.input = [0 for i in range(len(self.variable))]
    
class AlarmByBinaryExpAverage(BasicAlarm):
    def __init__(self, *a):
        BasicAlarm.__init__(self, *a)
        self.timeConstant = float(self.params["timeConstant"])
        self.average = 0.0
        
    def processAfterCheckValue(self, value, *a):
        interval = a[0]
        self.average = expAverage(self.average, int(value), interval, self.timeConstant)
        return (self.average >= 0.5)
        
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
        if analyzerStatus > 0:
            for b in p.AnalyzerStatusInvalidDataBits:
                if alarmTestBit(int(analyzerStatus), b): return 1
        else:
            return 0       
            
if _GLOBALS_["init"]:
    _GLOBALS_["init"] = False
    _GLOBALS_['alarms'] = OrderedDict()
    alarm_list = [[section, getAlarmOrder(section), _ALARM_PARAMS_[section]] for section in _ALARM_PARAMS_ if section.startswith("ALARM_")]
    alarm_list_sorted = sorted(alarm_list, key=lambda k: (k[1], k[2]['word'], k[2]['bit']))
    for section, order, a in alarm_list_sorted:
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
                if var.startswith("_"):
                    alarm.input[i] = eval(var)
                else:
                    if var in _REPORT_:
                        alarm.input[i] = _REPORT_[var]
                    else:
                        enableAlarm = False
                        break
            if enableAlarm:
                alarm.processAlarm(_ALARMS_, *alarm.input)
                
        _ALARM_REPORT_['AnalyzerStatus'] = _ALARMS_[0]
        _ALARM_REPORT_["cavityPressureOORAvg"] = _GLOBALS_["alarms"]["ALARM_CavityPressure"].average
        _ALARM_REPORT_["warmBoxTempOORAvg"] = _GLOBALS_["alarms"]["ALARM_WarmBoxTemperature"].average
        _ALARM_REPORT_["cavityTempOORAvg"] = _GLOBALS_["alarms"]["ALARM_CavityTemperature"].average