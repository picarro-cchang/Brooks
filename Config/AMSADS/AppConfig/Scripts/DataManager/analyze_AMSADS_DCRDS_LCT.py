#  Analysis script for MADS HF analyzer started by Hoffnagle
#  2016 0629:  merged with AEDS script to create AMADS
#  2016 0711:  variant for LCT operation
#  2016 0901:  added filter for pressure lock to prevent spikes from perturbing PZT
#  2016 0920: EWMA - Exponential Weighted Moving Average; requested by Raymond
#  2017 0111:  changed PZT gain factor from 0.05 to 0.2 (hoffnagle)
#  2017 0412:  Added post-fit corrections for water cross-talk to HF; no need for HF cross-talk to water (jah)
#              Change HF reporting to come from peak77 WITHOUT baseline averaging (jah)
#              Correction coefficient comes from stored config for MADS2060 aka Golden 
#  2018 0710:  Added cross-talk corrections from acetylene and propyne to post-fit reported concentrations
#              for heavily contaminated FOUP application
#  2018 0719:  Changed source of NH3 for user from "dry" (essentially AEDS without hydrocarbons) to "nh3_cal_HCcorrected" from PF
#  2018 0730:  Changed reporting of CO2 and H2O to be corrected for hydrocarbons
#  2018 0913:  changed nh3_HC_corrected to include dry parameters using derived PF_peak15
#              included h2o calibration on PF data for H2O with HC
#              added in -0.294 offset derived from change to DCRDS release on 3 analyzers (2075,2081,2080)
#  2019 0509:  merge AMADS with SADS_DCRDS

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
from DynamicNoiseFilter import variableExpAverage,negative_number_filter 
# for the simulation of noise
# Static variables used for wlm offsets, bookending and averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["pzt1_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1")
    _PERSISTENT_["pzt2_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER2")
    _PERSISTENT_["bufferHF30"]  = []
    #_PERSISTENT_["bufferHF30_NZ"]  = []
    _PERSISTENT_["bufferHF120"] = []
    _PERSISTENT_["bufferHF300"] = []
    #_PERSISTENT_["bufferNH330_NZ"]  = []
    _PERSISTENT_["bufferNH330"]  = []
    _PERSISTENT_["bufferNH3120"] = []
    _PERSISTENT_["bufferNH3300"] = []
    
    _PERSISTENT_["bufferExpAvg_HF"] = []
    _PERSISTENT_["bufferExpAvg_NH3"] = []

    _PERSISTENT_["bufferZZ_HF"] = []
    _PERSISTENT_["bufferZZ_NH3"] = []
    
    _PERSISTENT_["previousNoise_HF"]=0.0
    _PERSISTENT_["previousNoise_NH3"]=0.0
    _PERSISTENT_["previousS_HF"]=0.0
    _PERSISTENT_["previousS_NH3"]=0.0
    _PERSISTENT_["tau_HF"]=0.0
    _PERSISTENT_["tau_NH3"]=0.0
    _PERSISTENT_["HF_filter"]=0.0
    _PERSISTENT_["NH3_filter"]=0.0

    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["pzt3_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER3")
    _PERSISTENT_["bufferHCl30"]  = []
    _PERSISTENT_["bufferHCl30_H2O"]  = []
    _PERSISTENT_["bufferHCl120"] = []
    _PERSISTENT_["bufferHCl300"] = []
#    _PERSISTENT_["ignoreHCl_count"] = 5
    _PERSISTENT_["bufferExpAvg_HCl"] = []
    _PERSISTENT_["bufferZZ_HCl"] = []
    _PERSISTENT_["previousNoise_HCl"]=0.0
    _PERSISTENT_["previousS_HCl"]=0.0
    _PERSISTENT_["tau_HCl"]=0.0
    _PERSISTENT_["HCl_filter"]=0.0
    
    _PERSISTENT_["Pressure_save"]= 140.0    
    _PERSISTENT_["ignore_count"] = 17
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

# Define linear transformtions for post-processing
HCl_CONC = (_INSTR_["concentration_hcl_slope"],_INSTR_["concentration_hcl_intercept"])
H2O_a_CONC = (_INSTR_["concentration_h2o_a_slope"],_INSTR_["concentration_h2o_a_intercept"])
CH4_CONC = (_INSTR_["concentration_ch4_slope"],_INSTR_["concentration_ch4_intercept"])
# Import empirical cross-talk parameters
C2H4_to_HCl = _INSTR_["c2h4_to_hcl"]
###################################################################################################

# Import water selfbroadening, cross-talk and cross-broadening parameters
Hlin = _INSTR_["water_linear"]
Hquad = _INSTR_["water_quadratic"]
H1 = _INSTR_["water_crosstalk_linear"]
A1H1 = _INSTR_["water_crossbroadening_linear"]
A1H2 = _INSTR_["water_crossbroadening_quadratic"]

H1onHF = _INSTR_["water_to_hf"]

# Import hydrocarbon cross-talk parameters
C2H2toNH3 = _INSTR_["c2h2_to_nh3"]
C3H4toNH3 = _INSTR_["c3h4_to_nh3"]
C2H2toCO2 = _INSTR_["c2h2_to_co2"]
C3H4toCO2 = _INSTR_["c3h4_to_co2"]
C2H2toH2O = _INSTR_["c2h2_to_h2o"]
C3H4toH2O = _INSTR_["c3h4_to_h2o"]

#offset that change to DCRDS and HC fit induced
NH3_update_offset = -0.294

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if abs(_DATA_["CavityPressure"]-140.0) > 0.1:
    good = False

try:
    # This if condition is False if the NH3 fit hasn't yet be run for the first time
    if "nh3_conc_ave" in _DATA_:
        temp = applyLinear(_DATA_["nh3_conc_ave"],NH3_CONC)
        _NEW_DATA_["NH3_uncorrected"] = temp
        h2o_actual = Hlin*_DATA_["peak15"] + Hquad*_DATA_["peak15"]**2
        str15 = 1.1794*_DATA_["peak15"] + 0.001042*_DATA_["peak15"]**2
        corrected = (temp + H1*_DATA_["peak15"])/(1.0 + A1H1*str15 + A1H2*str15**2)
        dry = corrected/(1.0-0.01*h2o_actual)
        now = _OLD_DATA_["NH3_uncorrected"][-2].time
        #add spikes

        #if ((now-_PERSISTENT_["TimeS"])> 200*(1.0+random.random())) and (_DATA_["species"]==4):
        #    dry = dry + 10*random.random()
        #    _PERSISTENT_["TimeS"] = now

        _NEW_DATA_["NH3_broadeningCorrected"] = corrected
        _NEW_DATA_["NH3_dry"] = dry
        _NEW_DATA_["NH3_raw"] = dry

    	PF_nh3_corrected = _DATA_["PF_nh3_conc_ave"] + C2H2toNH3*_DATA_["PF_c2h2_conc"] + C3H4toNH3*_DATA_["PF_c3h4_conc"]
    	nh3_cal_HCcorrected_wet = applyLinear(PF_nh3_corrected,NH3_CONC)
    	#added dry HCcorrected section, and replaced so nh3_cal_HCcorrected is dry
    	#previous reporting is now known as "_wet"
    	h2o_HCcorrected = _DATA_["PF_a_h2o_conc"] + C2H2toH2O*_DATA_["PF_c2h2_conc"] + C3H4toH2O*_DATA_["PF_c3h4_conc"]
    	pf_peak15 = h2o_HCcorrected/0.02
    	_NEW_DATA_["NH3_HCcorrected_wet"] = nh3_cal_HCcorrected_wet
    	pf_h2o_actual = Hlin*pf_peak15 + Hquad*pf_peak15**2
    	pf_str15 = 1.1794*pf_peak15 + 0.001042*pf_peak15**2
    	pf_corrected = (nh3_cal_HCcorrected_wet + H1*pf_peak15)/(1.0 + A1H1*pf_str15 + A1H2*pf_str15**2)
    	nh3_cal_HCcorrected = pf_corrected/(1.0-0.01*h2o_actual) + NH3_update_offset
    	_NEW_DATA_["NH3_HCcorrected"] = nh3_cal_HCcorrected
    	_NEW_DATA_["H2O"] = applyLinear(pf_h2o_actual,H2O_CONC)
    
    	if((_DATA_["species"]==4) and (abs(_DATA_["CavityPressure"]-_PERSISTENT_["Pressure_save"]) < 2.0)):
        	_PERSISTENT_["NH3_filter"] = nh3_cal_HCcorrected  #  "nh3_cal_HCcorrected" replaced "dry" on 19 July 2018 (5 places)
        	_PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousNoise_NH3"],_PERSISTENT_["tau_NH3"] = variableExpAverage(_PERSISTENT_["bufferZZ_NH3"],_PERSISTENT_["bufferExpAvg_NH3"],nh3_cal_HCcorrected,now,1100,1,_PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousNoise_NH3"])
    	_PERSISTENT_["Pressure_save"]=_DATA_["CavityPressure"]
    	_NEW_DATA_["NH3_sigma"]=_PERSISTENT_["previousNoise_NH3"]*1.5*sqrt(2)
    	_NEW_DATA_["NH3_ExpAvg"]=_PERSISTENT_["previousS_NH3"]
    	_NEW_DATA_["NH3_tau"]=_PERSISTENT_["tau_NH3"]
    	_NEW_DATA_["NH3_filter"] = _PERSISTENT_["NH3_filter"]
    	_NEW_DATA_["NH3raw-NH3expavg"] = _NEW_DATA_["NH3_filter"] - _NEW_DATA_["NH3_ExpAvg"]
    	_NEW_DATA_["NH3_ExpAvg_NZ"] = negative_number_filter("NH3",_NEW_DATA_["NH3_ExpAvg"])
    	_NEW_DATA_["NH3"] =_NEW_DATA_["NH3_ExpAvg_NZ"]
    	#print "final=",_NEW_DATA_["NH3_ExpAvg"],_PERSISTENT_["bootstrapcounter_NH3"],_PERSISTENT_["previousS_NH3"],_PERSISTENT_["previousY_NH3"]
    	NH330s= boxAverage(_PERSISTENT_["bufferNH330"],nh3_cal_HCcorrected,now,30)
    	_NEW_DATA_["NH3_30s"] = NH330s
    	_NEW_DATA_["NH3_2min"] = boxAverage(_PERSISTENT_["bufferNH3120"],nh3_cal_HCcorrected,now,120)
    	_NEW_DATA_["NH3_5min"] = boxAverage(_PERSISTENT_["bufferNH3300"],nh3_cal_HCcorrected,now,300)
   
except Exception as e:
    _NEW_DATA_["NH3"] = 0
    pass

try:
    h2o_actual = Hlin*_DATA_["peak15"] + Hquad*_DATA_["peak15"]**2
    temp = applyLinear(h2o_actual,H2O_CONC)
    _NEW_DATA_["H2O_uncorrected"] = temp
except:
    pass

try:
    temp = applyLinear(_DATA_["co2_conc"],CO2_CONC)
    _NEW_DATA_["CO2_uncorrected"] = temp
    _NEW_DATA_["CO2_HCcorrected"] = _DATA_["PF_a_co2_conc"] + C2H2toCO2*_DATA_["PF_c2h2_conc"] + C3H4toCO2*_DATA_["PF_c3h4_conc"]
    _NEW_DATA_["CO2"] = applyLinear(_NEW_DATA_["CO2_HCcorrected"],CO2_CONC)
except:
    pass

try:
    # Fix I2-1083
    # This if condition is False if the HF fit hasn't yet be run for the first time.
    # This will happen as the AMADS scheme fits NH3, H2O, CO2 first, reports the available data (without HF),
    # fits HF, then reports available data now with all gases including HF.
    #
    if "peak_82" in _DATA_:
        temp = applyLinear(_DATA_["hf_ppbv"],HF_CONC) + H1onHF*_DATA_["peak_82"]
        _NEW_DATA_["HF_raw"] = temp
        if "HF_raw" in _OLD_DATA_ and len(_OLD_DATA_["HF_raw"]) > 1:
            now = _OLD_DATA_["HF_raw"][-2].time
            HF30s = boxAverage(_PERSISTENT_["bufferHF30"],temp,now,30)
            _NEW_DATA_["HF_30sec"] = HF30s
            _NEW_DATA_["HF_2min"] = boxAverage(_PERSISTENT_["bufferHF120"],temp,now,120)
            _NEW_DATA_["HF_5min"] = boxAverage(_PERSISTENT_["bufferHF300"],temp,now,300)
            if ((_DATA_["species"]==60)and (abs(_DATA_["CavityPressure"]-140.0) < 2.0)):
                _PERSISTENT_["HF_filter"] = temp
                _PERSISTENT_["previousS_HF"],_PERSISTENT_["previousNoise_HF"], _PERSISTENT_["tau_HF"] = variableExpAverage(_PERSISTENT_["bufferZZ_HF"],_PERSISTENT_["bufferExpAvg_HF"],temp,now,1100,0,_PERSISTENT_["previousS_HF"],_PERSISTENT_["previousNoise_HF"])
            _NEW_DATA_["HF_sigma"]=_PERSISTENT_["previousNoise_HF"]*1.5*sqrt(2)
            _NEW_DATA_["HF_ExpAvg"]=_PERSISTENT_["previousS_HF"]
            _NEW_DATA_["HF_tau"]=_PERSISTENT_["tau_HF"]
            _NEW_DATA_["HF_filter"] = _PERSISTENT_["HF_filter"]
            _NEW_DATA_["HFraw-HFexpavg"] = _NEW_DATA_["HF_filter"] - _PERSISTENT_["previousS_HF"]
            _NEW_DATA_["HF_ExpAvg_NZ"] = negative_number_filter("HF",_NEW_DATA_["HF_ExpAvg"])
            _NEW_DATA_["HF"] =_NEW_DATA_["HF_ExpAvg_NZ"]

except Exception, e:
    _NEW_DATA_["HF"]=temp
    print "Exception: %s, %r" % (e,e)
    pass

try:
    _NEW_DATA_["O2"] = applyLinear(_DATA_["o2_conc"],O2_CONC)
except:
    pass

#  Analysis script for HCl 

try:
    if "hcl_conc" in _DATA_:   
        temp = applyLinear(_DATA_["hcl_conc"]+ C2H4_to_HCl*_DATA_["c2h4_conc"],HCl_CONC) 
        _NEW_DATA_["HCl_raw"] = temp
        now = _OLD_DATA_["HCl_raw"][-2].time
        _NEW_DATA_["HCl_30sec"] = boxAverage(_PERSISTENT_["bufferHCl30"],temp,now,30)
        _NEW_DATA_["HCl_2min"] = boxAverage(_PERSISTENT_["bufferHCl120"],temp,now,120)
        _NEW_DATA_["HCl_5min"] = boxAverage(_PERSISTENT_["bufferHCl300"],temp,now,300)
	    # remove the species filt#er (_DATA_["species"]==63) and
        if((abs(_DATA_["CavityPressure"]-_PERSISTENT_["Pressure_save"]) < 2.0)):
            _PERSISTENT_["HCl_filter"] = temp 
            _PERSISTENT_["previousS_HCl"],_PERSISTENT_["previousNoise_HCl"],_PERSISTENT_["tau_HCl"] = variableExpAverage(_PERSISTENT_["bufferZZ_HCl"],_PERSISTENT_["bufferExpAvg_HCl"],temp,now,1100,2,_PERSISTENT_["previousS_HCl"],_PERSISTENT_["previousNoise_HCl"])
        _PERSISTENT_["Pressure_save"] = _DATA_["CavityPressure"]
        _NEW_DATA_["HCl_sigma"]=_PERSISTENT_["previousNoise_HCl"]*1.5*sqrt(2)
        _NEW_DATA_["HCl_ExpAvg"]=_PERSISTENT_["previousS_HCl"]
        _NEW_DATA_["HCl_tau"]=_PERSISTENT_["tau_HCl"]
        _NEW_DATA_["HCl_P_filter"] = _PERSISTENT_["HCl_filter"]
        _NEW_DATA_["HClraw-HClexpavg"] = _NEW_DATA_["HCl_P_filter"] - _NEW_DATA_["HCl_ExpAvg"]
        _NEW_DATA_["HCl_ExpAvg_NZ"] = negative_number_filter("HCl",_NEW_DATA_["HCl_ExpAvg"])
        _NEW_DATA_["HCl"] = _NEW_DATA_["HCl_ExpAvg_NZ"]

except Exception, e:
   _NEW_DATA_["HCl"]=temp
   #_NEW_DATA_["HCl_raw"]
   print "Exception: %s, %r" % (e,e)
   pass
    
try:
    if "hcl_conc" in _DATA_:
        _NEW_DATA_["H2O_a"] = applyLinear(_DATA_["h2o_a_conc_raw"],H2O_a_CONC)
        now = _OLD_DATA_["H2O_a"][-2].time
        _NEW_DATA_["H2O_a_30sec"] = boxAverage(_PERSISTENT_["bufferHCl30_H2O"],_NEW_DATA_["H2O_a"],now,30)
except Exception, e:
   print "Exception: %s, %r" % (e,e)
   pass   

try:
   if "hcl_conc" in _DATA_:
        _NEW_DATA_["CH4"] = applyLinear(_DATA_["ch4_conc_raw"],CH4_CONC)
except:
   pass
         
    
max_adjust = 5.0e-5
PZTgain = 0.2
hcl_gain = 0.1

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
    
    if _DATA_["species"] == 63: # Update the offset for virtual laser 3
        try:
            hcl_adjust = _DATA_["hcl_adjust"]*hcl_gain
            hcl_adjust = min(max_adjust,max(-max_adjust,hcl_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + hcl_adjust
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset3))
            # print "New HCl (virtual laser 1) offset: %.5f" % newOffset0 
        except:
            pass
            # print "No new HCl (virtual laser 1) offset"

#  PZT voltage control goes here.
        try:
            adjust = _DATA_["pzt3_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt3_offset"] + adjust
            _PERSISTENT_["pzt3_offset"] = newPZToffset
        except:
            pass
        if _PERSISTENT_["pzt3_offset"] < 32768 - 1.2*FSR:
            _PERSISTENT_["pzt3_offset"] += FSR
        if _PERSISTENT_["pzt3_offset"] > 32768 + 1.2*FSR:
            _PERSISTENT_["pzt3_offset"] -= FSR                    
        _NEW_DATA_["pzt3_offset"] = _PERSISTENT_["pzt3_offset"]
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER3",_PERSISTENT_["pzt3_offset"])
            
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
        _REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
        _REPORT_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
        _REPORT_["pzt2_offset"] = _PERSISTENT_["pzt2_offset"]
        _REPORT_["pzt3_offset"] = _PERSISTENT_["pzt3_offset"]
