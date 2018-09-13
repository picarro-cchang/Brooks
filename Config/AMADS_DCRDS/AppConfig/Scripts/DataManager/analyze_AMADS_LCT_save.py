#  Analysis script for MADS HF analyzer started by Hoffnagle
#  2016 0629:  merged with AEDS script to create AMADS
#  2016 0711:  variant for LCT operation
#  2016 0901:  added filter for pressure lock to prevent spikes from perturbing PZT
#  2016 0920: EWMA - Exponential Weighted Moving Average; requested by Raymond
import os
import sys
import inspect
from math import exp
from numpy import mean, sqrt
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED
# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname
from DynamicNoiseFilter import variableExpAverage 
# Static variables used for wlm offsets, bookending and averaging
sigma = 0.10

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["pzt1_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1")
    _PERSISTENT_["pzt2_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER2")
    _PERSISTENT_["bufferHF30"]  = []
    _PERSISTENT_["bufferHF30_NZ"]  = []
    _PERSISTENT_["bufferHF120"] = []
    _PERSISTENT_["bufferHF300"] = []
    _PERSISTENT_["bufferNH330_NZ"]  = []
    _PERSISTENT_["bufferNH330"]  = []
    _PERSISTENT_["bufferNH3120"] = []
    _PERSISTENT_["bufferNH3300"] = []
    
    _PERSISTENT_["bufferExpAvg_HF"] = []
    _PERSISTENT_["bufferExpAvg_NH3"] = []
  
    _PERSISTENT_["previousNoise_HF"]=0.0
    _PERSISTENT_["previousNoise_NH3"]=0.0
    _PERSISTENT_["previousS_HF"]=0.0
    _PERSISTENT_["previousS_NH3"]=0.0
    _PERSISTENT_["tau_HF"]=0.0
    _PERSISTENT_["tau_NH3"]=0.0
    
    _PERSISTENT_["ignore_count"] = 5
    _PERSISTENT_["init"] = False

# REPORT_UPPER_LIMIT = 5000.0
# REPORT_LOWER_LIMIT = -5000.0

TARGET_SPECIES = [2, 4, 60, 61]

# def clipReportData(value):
    # if value > REPORT_UPPER_LIMIT:
        # return REPORT_UPPER_LIMIT
    # elif  value < REPORT_LOWER_LIMIT:
        # return REPORT_LOWER_LIMIT
    # else:
        # return value
    
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

# Define linear transformations for post-processing
HF_CONC = (_INSTR_["concentration_hf_slope"],_INSTR_["concentration_hf_intercept"])
H2O_CONC_60 = (_INSTR_["concentration_h2o_60_slope"],_INSTR_["concentration_h2o_60_intercept"])
O2_CONC = (_INSTR_["concentration_o2_slope"],_INSTR_["concentration_o2_intercept"])
NH3_CONC = (_INSTR_["concentration_nh3_slope"],_INSTR_["concentration_nh3_intercept"])
CO2_CONC = (_INSTR_["concentration_co2_slope"],_INSTR_["concentration_co2_intercept"])
H2O_CONC = (_INSTR_["concentration_h2o_slope"],_INSTR_["concentration_h2o_intercept"])

# Import water selfbroadening, cross-talk and cross-broadening parameters
Hlin = _INSTR_["water_linear"]
Hquad = _INSTR_["water_quadratic"]
H1 = _INSTR_["water_crosstalk_linear"]
A1H1 = _INSTR_["water_crossbroadening_linear"]
A1H2 = _INSTR_["water_crossbroadening_quadratic"]

    
try:
    temp = applyLinear(_DATA_["nh3_conc_ave"],NH3_CONC)
    _NEW_DATA_["NH3_uncorrected"] = temp
    now = _OLD_DATA_["NH3_uncorrected"][-2].time
    h2o_actual = Hlin*_DATA_["peak15"] + Hquad*_DATA_["peak15"]**2
    str15 = 1.1794*_DATA_["peak15"] + 0.001042*_DATA_["peak15"]**2
    corrected = (temp + H1*_DATA_["peak15"])/(1.0 + A1H1*str15 + A1H2*str15**2)
    dry = corrected/(1.0-0.01*h2o_actual)
    _NEW_DATA_["NH3_broadeningCorrected"] = corrected
    _NEW_DATA_["NH3_dry"] = dry
    _NEW_DATA_["NH3"] = dry
    #print dry
    if _DATA_["species"] ==4:
        _PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousNoise_NH3"],_PERSISTENT_["tau_NH3"] = variableExpAverage(_PERSISTENT_["bufferExpAvg_NH3"],dry,now,1100,1,_PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousNoise_NH3"])
    _NEW_DATA_["NH3_sigma"]=_PERSISTENT_["previousNoise_NH3"]*1.25*sqrt(2)
    _NEW_DATA_["NH3_ExpAvg"]=_PERSISTENT_["previousS_NH3"]
    _NEW_DATA_["NH3_tau"]=_PERSISTENT_["tau_NH3"]
    #print "final=",_NEW_DATA_["NH3_ExpAvg"],_PERSISTENT_["bootstrapcounter_NH3"],_PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousY_NH3"]
    NH330s= boxAverage(_PERSISTENT_["bufferNH330"],dry,now,30)
    _NEW_DATA_["NH3_30s"] = NH330s
    _NEW_DATA_["NH3_2min"] = boxAverage(_PERSISTENT_["bufferNH3120"],dry,now,120)
    _NEW_DATA_["NH3_5min"] = boxAverage(_PERSISTENT_["bufferNH3300"],dry,now,300)
    if(dry <= 0.0):
            dry = dry + abs(NH330s) + sigma	
    _NEW_DATA_["NH3_30s_NZ"] = boxAverage(_PERSISTENT_["bufferNH330_NZ"],dry,now,30)
except:
    pass

try:
    h2o_actual = Hlin*_DATA_["peak15"] + Hquad*_DATA_["peak15"]**2
    temp = applyLinear(h2o_actual,H2O_CONC)
    _NEW_DATA_["H2O"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["co2_conc"],CO2_CONC)
    _NEW_DATA_["CO2"] = temp
except:
    pass

try:   
    
    temp = applyLinear(_DATA_["hf_ppbv_ave"],HF_CONC)
    _NEW_DATA_["HF"] = temp
    now = _OLD_DATA_["HF"][-2].time
    HF30s = boxAverage(_PERSISTENT_["bufferHF30"],temp,now,30)
    _NEW_DATA_["HF_30sec"] = HF30s
    _NEW_DATA_["HF_2min"] = boxAverage(_PERSISTENT_["bufferHF120"],temp,now,120)
    _NEW_DATA_["HF_5min"] = boxAverage(_PERSISTENT_["bufferHF300"],temp,now,300)
    if _DATA_["species"]==60:
        _PERSISTENT_["previousS_HF"],_PERSISTENT_["previousNoise_HF"], _PERSISTENT_["tau_HF"] = variableExpAverage(_PERSISTENT_["bufferExpAvg_HF"],temp,now,1100,0,_PERSISTENT_["previousS_HF"],_PERSISTENT_["previousNoise_HF"])
    _NEW_DATA_["HF_sigma"]=_PERSISTENT_["previousNoise_HF"]*1.25*sqrt(2)
    _NEW_DATA_["HF_ExpAvg"]=_PERSISTENT_["previousS_HF"]
    _NEW_DATA_["HF_tau"]=_PERSISTENT_["tau_HF"]
    #_NEW_DATA_["HF_ExpAvg"] = temp 
    ##variableExpAverage(_PERSISTENT_["bufferExp_HF"],temp,now,12)
    #print _NEW_DATA_["HF_ExpAvg"]
    if(temp <= 0.0):
            temp = temp + abs(HF30s) + sigma/4.0	
    _NEW_DATA_["HF_30sec_NZ"] = boxAverage(_PERSISTENT_["bufferHF30_NZ"],temp,now,30)   
except Exception, e:
    print "Exception: %s, %r" % (e,e)
    pass

try:
    _NEW_DATA_["O2"] = applyLinear(_DATA_["o2_conc"],O2_CONC)
except:
    pass
 
max_adjust = 5.0e-5
PZTgain = 0.05

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if abs(_DATA_["CavityPressure"]-140.0) > 0.1:
    good = False
if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    FSR = _DATA_["pzt_per_fsr"]
    if _DATA_["species"] == 2: # Update the offset for virtual laser 2
        try:
            nh3_adjust = _DATA_["cm_adjust"]
            nh3_adjust = min(max_adjust,max(-max_adjust,nh3_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + nh3_adjust
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            # print "New NH3 (virtual laser 2) offset: %.5f" % newOffset0
        except:
            pass
            # print "No new NH3 (virtual laser 2) offset"
            
#  PZT voltage control goes here.  For the time being I am not locking the pzt offsets
            
        try:
            adjust = _DATA_["pzt2_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt2_offset"] + adjust
            _PERSISTENT_["pzt2_offset"] = newPZToffset
        except:
            pass
        if _PERSISTENT_["pzt2_offset"] < 32768 - 1.2*FSR:
            _PERSISTENT_["pzt2_offset"] += FSR
        if _PERSISTENT_["pzt2_offset"] > 32768 + 1.2*FSR:
            _PERSISTENT_["pzt2_offset"] -= FSR                    
        _NEW_DATA_["pzt2_offset"] = _PERSISTENT_["pzt2_offset"]
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER2",_PERSISTENT_["pzt2_offset"])

    if _DATA_["species"] == 61: # Update the offset for virtual laser 1
        try:
            o2_adjust = _DATA_["adjust_81"]
            o2_adjust = min(max_adjust,max(-max_adjust,o2_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + o2_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            # print "New O2 (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            # print "No new O2 (virtual laser 1) offset"
            
#  PZT voltage control goes here.  For the time being I am not locking the pzt offsets
            
        try:
            adjust = _DATA_["pzt1_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt1_offset"] + adjust
            _PERSISTENT_["pzt1_offset"] = newPZToffset
        except:
            pass
        if _PERSISTENT_["pzt1_offset"] < 32768 - 1.2*FSR:
            _PERSISTENT_["pzt1_offset"] += FSR
        if _PERSISTENT_["pzt1_offset"] > 32768 + 1.2*FSR:
            _PERSISTENT_["pzt1_offset"] -= FSR                    
        _NEW_DATA_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",_PERSISTENT_["pzt1_offset"])
            
if _PERSISTENT_["ignore_count"] > 0:
    _PERSISTENT_["ignore_count"] = _PERSISTENT_["ignore_count"] - 1
else:
    if _DATA_["species"] in TARGET_SPECIES:
        for k in _DATA_.keys():
            if k in newname:
                _REPORT_[newname[k]] = _DATA_[k]
            else:
                _REPORT_[k] = _DATA_[k]

        for k in _NEW_DATA_.keys():
            if k in newname:
                _REPORT_[newname[k]] = _NEW_DATA_[k]
            else:
                _REPORT_[k] = _NEW_DATA_[k]

        _REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
        _REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
        _REPORT_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
        _REPORT_["pzt2_offset"] = _PERSISTENT_["pzt2_offset"]