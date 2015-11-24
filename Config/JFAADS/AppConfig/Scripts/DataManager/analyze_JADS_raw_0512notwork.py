#  Data analysis script for the experimental instrument operating at 7193 wavenumbers
#  2011 0920 - adapted from CFF analysis script

from math import exp
from numpy import mean
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

#
# Following code is to synchronize a set of variables and to do linear interpolation
#  of all the variables in the set so they are evaluated on a common time grid
#
from collections import deque
import numpy as np

class CrosstalkProcessor(object):
    def __init__(self,crossList,forward_id):
        self.crossList = crossList
        self.forward_id = forward_id
        self.xHistory = deque()
        self.xMostRecent = {}
        self.indexByName = {}
        for i,(c,f,v) in enumerate(crossList):
            self.indexByName[c] = i

    def process(self, meas_timestamp, data, new_data, analyze):
        xh = self.xHistory
        xc = self.xMostRecent
        for name, filt, filtVals in self.crossList:
            if (filt is None) or (data[filt] in filtVals):
                value = data[name] if (name in data) else new_data[name]
                xc[name] = (meas_timestamp, value)
                for x in xh:
                    x.update(xc, name)
                if xh:
                    if meas_timestamp < xh[-1].timestamp:
                        raise ValueError("Timestamps out of order in Data Manager")
                    elif meas_timestamp > xh[-1].timestamp:
                        xh.append(XSync(xc, name, self.indexByName, data.copy(), new_data.copy()))
                else:
                    xh.append(XSync(xc, name, self.indexByName, data.copy(), new_data.copy()))
        if xh and xh[0].ready:
            analyze[self.forward_id] = {"new_timestamp":xh[0].timestamp}

class XSync(object):
    TIMEOUT = 10.0
    def __init__(self, current, name, indexByName, data, new_data, ignore=None):
        #
        # Create an object representing a request to compute some values with crosstalk removed. This is done for
        #  a particular timestamp, at which time the measured values of all the quantities are required.
        # The values of the variables which are actually measured at this timestamp are called the targetValues
        # All other variables required to do the crosstalk removal are calculated using linear interpolation from
        #  measurements made around the specified timestamp (bookending).
        # 
        self.timestamp, value = current[name]
        nVar = len(indexByName)
        self.indexByName = indexByName
        self.valueArray = np.zeros(nVar,dtype=float)
        self.valueTimestamps = nVar * [None]            # Timestamps at which each value is known
        self.targetValues = np.zeros(nVar,dtype=bool)   # Which values are to have crosstalk removed
        self.valueOk = np.zeros(nVar,dtype=bool)        # Which values are available
        self.valueNeeded = np.ones(nVar,dtype=bool)     # Which values are needed for crosstalk correction
        if ignore:
            for i in ignore: self.valueNeeded[indexByName[i]] = False

        self.targetValues[indexByName[name]] = True
        # We initialize the arrays of values and timestamps from the current array, which contains the most recent
        #  values of all the variables
        for n in current:
            i = indexByName[n]
            self.valueTimestamps[i], self.valueArray[i] = current[n]
            self.valueOk[i] = (self.valueTimestamps[i] == self.timestamp)

        self.ready = self.valueOk[self.valueNeeded].all()
        self.data = data
        self.new_data = new_data
        
    def update(self, current, name, ignore=None):
        i = self.indexByName[name]
        timestamp, value = current[name]
        if timestamp == self.timestamp: # This indicates that another variable has been measured at this time. Add it to targetValues.
            self.targetValues[i] = True
            valueNeeded = np.ones(self.valueArray.shape,dtype=bool)
            if ignore:
                for i in ignore: valueNeeded[self.indexByName[i]] = False
            self.valueNeeded = self.valueNeeded & valueNeeded
        # Update the value and timestamp unless the value is already OK
        if not self.valueOk[i]:
            if self.valueTimestamps[i] is None:
                self.valueTimestamps[i] = timestamp
                self.valueArray[i] = value
                if timestamp >= self.timestamp:
                    self.valueOk[i] = True
            else:   # We need to do linear interpolation
                if timestamp < self.timestamp:
                    raise ValueError("Incorrect timestamp while interpolating value")
                alpha = float(self.timestamp - self.valueTimestamps[i])/(timestamp - self.valueTimestamps[i])
                self.valueArray[i] = (1.0-alpha)*self.valueArray[i] + alpha*value
                self.valueTimestamps[i] = self.timestamp
                self.valueOk[i] = True
        self.ready = self.valueOk[self.valueNeeded].all() or timestamp-self.timestamp > 1000*self.TIMEOUT

# Cross-talk variable list 
crossList = \
[
 ("peak_1a", "species", [45,47]),
 #("peak_2", "species", [47]),
 ("peak_41", "species", [46]),
 ("peak15", "species", [2]),
 ("ch4_splinemax", "species", [25]),
 ("nh3_conc_ave", "species", [2]),
]

# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm5_offset"] = 0.0
    _PERSISTENT_["wlm7_offset"] = 0.0
    _PERSISTENT_["wlm8_offset"] = 0.0
    _PERSISTENT_["average30"]  = []
    _PERSISTENT_["average120"] = []
    _PERSISTENT_["average300"] = []
    _PERSISTENT_["init"] = False
    _PERSISTENT_["plot"] = False
    
    # Set up the resynchronizer
    _GLOBALS_["xProcessor"] = CrosstalkProcessor(crossList,"FORWARD1")
        
    
REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [2, 3, 4, 25, 45, 46, 47]

def clipReportData(value):
    if value > REPORT_UPPER_LIMIT:
        return REPORT_UPPER_LIMIT
    elif  value < REPORT_LOWER_LIMIT:
        return REPORT_LOWER_LIMIT
    else:
        return value
        
def applyLinear(value,xform):
    return xform[0]*value + xform[1]
    
def apply2Linear(value,xform1,xform2):
    return applyLinear(applyLinear(value,xform1),xform2)

def protDivide(num,den):
    if den != 0:
        return num/den
    return 0
    
def expAverage(xavg,x,dt,tau):
    if xavg is None:
        xavg = x
    else:
        xavg = (1.0-exp(-dt/tau))*x + exp(-dt/tau)*xavg
    return xavg

def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

# # Define linear transformtions for post-processing
# CH4 = (_INSTR_["concentration_ch4_slope"],_INSTR_["concentration_ch4_intercept"])
# CO2 = (_INSTR_["concentration_co2_slope"],_INSTR_["concentration_co2_intercept"])
# H2O = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])
# N2O = (_INSTR_["concentration_n2o_slope"],_INSTR_["concentration_n2o_intercept"])
# NH3 = (_INSTR_["concentration_nh3_slope"],_INSTR_["concentration_nh3_intercept"])

# try:
    # NUM_BLOCKING_DATA = _INSTR_["num_blocking_data"]
# except:
    # NUM_BLOCKING_DATA = 3

# if _DATA_["species"] in TARGET_SPECIES:
    # try:
        # n2o = applyLinear(_DATA_["n2o_conc"],N2O)
        # now = _OLD_DATA_["peak_1a"][-1].time
        # _NEW_DATA_["N2O_raw"] = n2o
        # _NEW_DATA_["CH4"] = applyLinear(_DATA_["ch4_conc_ppmv_final"],CH4)
        # _NEW_DATA_["CO2"] = applyLinear(_DATA_["co2_conc"],CO2)
        # _NEW_DATA_["NH3"] = applyLinear(_DATA_["nh3_conc_ave"],NH3)
        # _NEW_DATA_["H2O"] = applyLinear(_DATA_["h2o_conc"],H2O)
        # _NEW_DATA_["N2O_30s"] = boxAverage(_PERSISTENT_["average30"],n2o,now,30)
        # _NEW_DATA_["N2O_2min"] = boxAverage(_PERSISTENT_["average120"],n2o,now,120)
        # _NEW_DATA_["N2O_5min"] = boxAverage(_PERSISTENT_["average300"],n2o,now,300)
    # except:
        # pass
                                                
    try:    
        if _PERIPH_INTRF_:
            try:
                interpData = _PERIPH_INTRF_( _DATA_["timestamp"], _PERIPH_INTRF_COLS_)
                for i in range(len(_PERIPH_INTRF_COLS_)):
                    if interpData[i]:
                        _NEW_DATA_[_PERIPH_INTRF_COLS_[i]] = interpData[i]
            except Exception, err:
                print "%r" % err
    except:
        pass
            
    for k in _DATA_.keys():
        _REPORT_[k] = _DATA_[k]
    
    for k in _NEW_DATA_.keys():
        if k.startswith("Delta"):
            _REPORT_[k] = clipReportData(_NEW_DATA_[k])
        else:    
            _REPORT_[k] = _NEW_DATA_[k]
        
#max_adjust = 1.0e-4
max_adjust = 5.0e-5
n2o_gain = 0.2
co2_gain = 0.2
damp = 0.2

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    if _DATA_["species"] == 47: # Update the offset for virtual laser 1
        try:
            n2o_adjust = n2o_gain*_DATA_["adjust_n2o"]
            n2o_adjust = min(max_adjust,max(-max_adjust,damp*n2o_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + n2o_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            #print "New N2O (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new N2O (virtual laser 1) offset"
    if _DATA_["species"] in [2,3]: # Update the offset for virtual laser 5
        try:
            h2o_adjust = _DATA_["h2o_adjust"]
            h2o_adjust = min(max_adjust,max(-max_adjust,h2o_adjust))           
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + h2o_adjust
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
            #print "New H2O (virtual laser 5) offset: %.5f" % newOffset5 
        except:
            pass
            #print "No new H2O (virtual laser 5) offset"
    if _DATA_["species"] == 25: # Update the offset for virtual laser 7
        try:
            ch4_adjust = n2o_gain*_DATA_["ch4_adjust"]
            #ch4_adjust = min(max_adjust,max(-max_adjust,damp*ch4_adjust))
            ch4_adjust = min(max_adjust,max(-max_adjust,ch4_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(7) + ch4_adjust
            _PERSISTENT_["wlm7_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(7,float(newOffset0))
            #print "New CH4 (virtual laser 7) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new CH4 (virtual laser 7) offset"
    if _DATA_["species"] == 46: # Update the offset for virtual laser 8
        try:
            co2_adjust = co2_gain*_DATA_["adjust_41"]
            co2_adjust = min(max_adjust,max(-max_adjust,co2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(8) + co2_adjust
            _PERSISTENT_["wlm8_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(8,float(newOffset0))
            #print "New CO2 (virtual laser 8) offset: %.5f" % newOffset0 
        except:
            pass
            #print "No new CO2 (virtual laser 8) offset"

_REPORT_["wlm1_offset"] = _NEW_DATA_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
_REPORT_["wlm5_offset"] = _NEW_DATA_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]
_REPORT_["wlm7_offset"] = _NEW_DATA_["wlm7_offset"] = _PERSISTENT_["wlm7_offset"]
_REPORT_["wlm8_offset"] = _NEW_DATA_["wlm8_offset"] = _PERSISTENT_["wlm8_offset"]
        
xp = _GLOBALS_["xProcessor"]
xp.process(_MEAS_TIMESTAMP_, _DATA_, _NEW_DATA_, _ANALYZE_)
