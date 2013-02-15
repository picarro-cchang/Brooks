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
        for name, filt, filtVal in self.crossList:
            if (filt is None) or (data[filt] == filtVal):
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


crossList = \
[
 ("co2_conc", "species", 1),
 ("ch4_conc", "species", 2),
 ("h2o_conc", "species", 3),
]

if _PERSISTENT_["init"]:
    _GLOBALS_["xProcessor"] = CrosstalkProcessor(crossList,"FORWARD1")
    _PERSISTENT_["init"] = False

###############
# Apply instrument calibration 
###############
def applyLinear(value,xform):
    return xform[0]*value + xform[1]
        
CO2 = (_INSTR_["co2_conc_slope"],_INSTR_["co2_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])

try:
    if _DATA_["SpectrumID"] == 12:
        co2_conc = applyLinear(0.5*(_DATA_["galpeak14_final"]+_OLD_DATA_["galpeak14_final"][-3].value),CO2)
        _NEW_DATA_["co2_conc"] = co2_conc
    else:
        _NEW_DATA_["co2_conc"] = _OLD_DATA_["co2_conc"][-1].value
except:
    _NEW_DATA_["co2_conc"] = 0.0
    
try:
    ch4_conc = applyLinear(_DATA_["ch4_conc_ppmv_final"],CH4)
    _NEW_DATA_["ch4_conc"] = ch4_conc
    #try:
    #    h2o_precorr = applyLinear(_OLD_DATA_["h2o_conc_precal"][-1].value,H2O)
    #    ch4_conc_dry = ch4_conc/(1.0+h2o_precorr*(_INSTR_["ch4_watercorrection_linear"]+h2o_precorr*_INSTR_["ch4_watercorrection_quadratic"]))
    #    _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry
    #except:
    #    _NEW_DATA_["ch4_conc_dry"] = 0.0
except:
    _NEW_DATA_["ch4_conc"] = 0.0
    #_NEW_DATA_["ch4_conc_dry"] = 0.0
    
try:
    h2o_reported = applyLinear(_DATA_["h2o_conc_precal"],H2O)
    h2o_precorr = 0.5*(h2o_reported+_OLD_DATA_["h2o_reported"][-4].value)  # average of current and last uncorrected h2o measurements
    
    try:
        ch4_conc_dry = _OLD_DATA_["ch4_conc"][-2].value/(1.0+h2o_precorr*(_INSTR_["ch4_watercorrection_linear"]+h2o_precorr*_INSTR_["ch4_watercorrection_quadratic"]))
        _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry
        co2_conc_dry = _OLD_DATA_["co2_conc"][-1].value/(1.0+h2o_precorr*(_INSTR_["co2_watercorrection_linear"]+h2o_precorr*_INSTR_["co2_watercorrection_quadratic"]))
        _NEW_DATA_["co2_conc_dry"] = co2_conc_dry
    except:
        _NEW_DATA_["ch4_conc_dry"] = 0.0
        _NEW_DATA_["co2_conc_dry"] = 0.0
    
    try:
        h2o_actual = _INSTR_["h2o_selfbroadening_linear"]*(h2o_reported+_INSTR_["h2o_selfbroadening_quadratic"]*h2o_reported**2)
        _NEW_DATA_["h2o_reported"] = h2o_reported
        _NEW_DATA_["h2o_conc"] = h2o_actual
    except:
        _NEW_DATA_["h2o_reported"] = h2o_reported
        _NEW_DATA_["h2o_conc"] = h2o_reported
except:
    _NEW_DATA_["h2o_conc"] = 0.0
    _NEW_DATA_["h2o_reported"] = 0.0


xp = _GLOBALS_["xProcessor"]
xp.process(_MEAS_TIMESTAMP_, _DATA_, _NEW_DATA_, _ANALYZE_)
for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]
for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]

