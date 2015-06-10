#  Analysis script for isotopic water at 7200 wavenumbers and O17/O18 ratio at 7193 wavenumbers
#  2011 0804:  Added time averages to experimental analysis script and changed names to conform better to HBDS style
#  2011 0819:  Added methane reporting with averaging and changed reporting of concentrations to be more self-consistent
#  2011 1104:  Added WLM tracking for lines at 7193 wvn
#  2011 1128:  Added box averages for the O17/O18 peak height ratio
#  2011 1130:  Converted O17/O18 peak height ratio to delta-17 (assuming meteoric sample) and added O-17 excess calculation
#  2011 1202:  O-17 excess (reported as "Excess17') is expressed in permil
#  2011 1215:  Merge all spectra into single spectrum id = 123
#  2012 0928:  Added deuterium excess to private data log
#  2013 0130:  Add PZT adjust for lct mode
#  2013 0411:  Increase PZT adjust band to try to prevent FSR hopping
#  2013 0502:  Added methane post-correction for air
#  2013 0509:  Added averaging for deuterium excess.  Import exponent lambda from instrCal.ini
#  2014 0521:  Major change in PZT voltage control:  flag FSR adjustments and adjust all PZTs together
#  2014 0613:  Added test for log(negative number) when computing Excess17 (occurs when fitting noise)

import sys
import os
import inspect
from numpy import mean
from math import log
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
from Host.Common.InstMgrInc import INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, INSTMGR_STATUS_PRESSURE_LOCKED

here = os.path.split(os.path.abspath(inspect.getfile(inspect.currentframe())))[0]
if not here in sys.path: sys.path.append(here)

if os.path.isdir("../AppConfig/Scripts/DataManager"):
    # For .exe version
    pulseAnalyzerPath = "../AppConfig/Scripts/DataManager"
elif os.path.isdir("../../AppConfig/Scripts/DataManager"):
    # For .py version
    pulseAnalyzerPath = "../../AppConfig/Scripts/DataManager"

if pulseAnalyzerPath not in sys.path: sys.path.append(pulseAnalyzerPath)
import time
from PulseAnalyzer import PulseAnalyzer
REPORT_UPPER_LIMIT = 5000.0
REPORT_LOWER_LIMIT = -5000.0
R18_VSMOW = 0.0020052
RD_VSMOW = 0.00031153
R18_17_VSMOW = 5.2782

# Static variables for averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["wlm2_offset"] = 0.0
    _PERSISTENT_["wlm3_offset"] = 0.0
    _PERSISTENT_["wlm4_offset"] = 0.0
    _PERSISTENT_["wlm5_offset"] = 0.0
    _PERSISTENT_["pzt1_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1")
    _PERSISTENT_["pzt2_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER2")
    _PERSISTENT_["pzt3_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER3")
    _PERSISTENT_["pzt4_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER4")
    _PERSISTENT_["pzt5_offset"] = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER5")
    _PERSISTENT_["PZTshift"] = 0
    _PERSISTENT_["Dbuffer30"]  = []
    _PERSISTENT_["Dbuffer100"] = []
    _PERSISTENT_["Dbuffer120"] = []
    _PERSISTENT_["Dbuffer300"] = []
    _PERSISTENT_["O18buffer30"]  = []
    _PERSISTENT_["O18buffer100"]  = []
    _PERSISTENT_["O18buffer120"] = []
    _PERSISTENT_["O18buffer300"] = []
    _PERSISTENT_["CH4buffer30"]  = []
    _PERSISTENT_["CH4buffer120"] = []
    _PERSISTENT_["CH4buffer300"] = []
    _PERSISTENT_["O17buffer30"]  = []
    _PERSISTENT_["O17buffer100"]  = []
    _PERSISTENT_["O17buffer120"] = []
    _PERSISTENT_["O17buffer300"] = []
    _PERSISTENT_["O17ebuffer30"]  = []
    _PERSISTENT_["O17ebuffer100"]  = []
    _PERSISTENT_["O17ebuffer120"] = []
    _PERSISTENT_["O17ebuffer300"] = []
    _PERSISTENT_["Debuffer30"]  = []
    _PERSISTENT_["Debuffer100"] = []
    _PERSISTENT_["Debuffer120"] = []
    _PERSISTENT_["Debuffer300"] = []
    _PERSISTENT_["init"] = False

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

def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

# Define linear transformtions for post-processing
DELTA_17O = (_INSTR_["delta_17o_slope"],_INSTR_["delta_17o_intercept"])
DELTA_18O = (_INSTR_["delta_18o_slope"],_INSTR_["delta_18o_intercept"])
DELTA_D = (_INSTR_["delta_d_slope"],_INSTR_["delta_d_intercept"])
DELTA_1818 = (_INSTR_["delta_1818_slope"],_INSTR_["delta_1818_intercept"])
H2O = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])
CH4 = (_INSTR_["ch4_conc_slope"],_INSTR_["ch4_conc_intercept"])
LAMBDA = _INSTR_["exponent_for_17excess"]

if _DATA_["spectrum"] == 123:
    try:
        # Note: _OLD_DATA_[][-1] is the current data
        now = _OLD_DATA_["str2_offset"][-1].time

        h2o_conc = applyLinear(_DATA_["h2o_ppm"],H2O)
        ch4_conc = applyLinear(_DATA_["ch4_ppm"],CH4)
        SD_18_16 = applyLinear(protDivide(_DATA_["str11_offset"],_DATA_["str2_offset"]),DELTA_18O)
        SD_D_H =  applyLinear(protDivide(_DATA_["str3_offset"],_DATA_["str2_offset"]),DELTA_D)
        SD_17_16 =  applyLinear(protDivide(_DATA_["str13_offset"],_DATA_["str2_offset"]),DELTA_17O)
        if _DATA_["n2_flag"] == 0:
            SD_17_16 += 133.3*ch4_conc/h2o_conc
            SD_18_16 += 227.3*ch4_conc/h2o_conc
            SD_D_H -= 342.0*ch4_conc/h2o_conc
        _NEW_DATA_["SD_18_18"] = applyLinear(protDivide(_DATA_["str11_offset"],_DATA_["str1_offset"]),DELTA_1818)

        _NEW_DATA_["Delta_18_16"] = SD_18_16
        _NEW_DATA_["Delta_18_16_30s"] = boxAverage(_PERSISTENT_["O18buffer30"],SD_18_16,now,30)
        _NEW_DATA_["Delta_18_16_100s"] = boxAverage(_PERSISTENT_["O18buffer100"],SD_18_16,now,100)
        _NEW_DATA_["Delta_18_16_2min"] = boxAverage(_PERSISTENT_["O18buffer120"],SD_18_16,now,120)
        _NEW_DATA_["Delta_18_16_5min"] = boxAverage(_PERSISTENT_["O18buffer300"],SD_18_16,now,300)
        #ratioD = protDivide(h16od_conc,h16oh_conc)
        _NEW_DATA_["Delta_D_H"] = SD_D_H
        _NEW_DATA_["Delta_D_H_30s"] = boxAverage(_PERSISTENT_["Dbuffer30"],SD_D_H,now,30)
        _NEW_DATA_["Delta_D_H_100s"] = boxAverage(_PERSISTENT_["Dbuffer100"],SD_D_H,now,100)
        _NEW_DATA_["Delta_D_H_2min"] = boxAverage(_PERSISTENT_["Dbuffer120"],SD_D_H,now,120)
        _NEW_DATA_["Delta_D_H_5min"] = boxAverage(_PERSISTENT_["Dbuffer300"],SD_D_H,now,300)
        Dexcess = SD_D_H - 8*SD_18_16
        _NEW_DATA_["D_excess"] = Dexcess
        _NEW_DATA_["D_excess_30s"] = boxAverage(_PERSISTENT_["Debuffer30"],Dexcess,now,30)
        _NEW_DATA_["D_excess_100s"] = boxAverage(_PERSISTENT_["Debuffer100"],Dexcess,now,100)
        _NEW_DATA_["D_excess_2min"] = boxAverage(_PERSISTENT_["Debuffer120"],Dexcess,now,120)
        _NEW_DATA_["D_excess_5min"] = boxAverage(_PERSISTENT_["Debuffer300"],Dexcess,now,300)
        h2o_conc *= (1.0 + (1.0+0.001*SD_18_16)*R18_VSMOW + (1.0+0.001*SD_D_H)*RD_VSMOW)/0.996275
        _NEW_DATA_["H2O"] = h2o_conc
        _NEW_DATA_["CH4"] = ch4_conc
        _NEW_DATA_["CH4_30s"] = boxAverage(_PERSISTENT_["CH4buffer30"],ch4_conc,now,30)
        _NEW_DATA_["CH4_2min"] = boxAverage(_PERSISTENT_["CH4buffer120"],ch4_conc,now,120)
        _NEW_DATA_["CH4_5min"] = boxAverage(_PERSISTENT_["CH4buffer300"],ch4_conc,now,300)

        try:
            excess17 = 1000.0*(log(1.0+0.001*SD_17_16)-LAMBDA*log(1.0+0.001*SD_18_16))
        except:
            excess17 = SD_17_16 - LAMBDA*SD_18_16
        _NEW_DATA_["Delta_17_16"] = SD_17_16
        _NEW_DATA_["Delta_17_16_30s"] = boxAverage(_PERSISTENT_["O17buffer30"],SD_17_16,now,30)
        _NEW_DATA_["Delta_17_16_100s"] = boxAverage(_PERSISTENT_["O17buffer100"],SD_17_16,now,100)
        _NEW_DATA_["Delta_17_16_2min"] = boxAverage(_PERSISTENT_["O17buffer120"],SD_17_16,now,120)
        _NEW_DATA_["Delta_17_16_5min"] = boxAverage(_PERSISTENT_["O17buffer300"],SD_17_16,now,300)
        _NEW_DATA_["Excess_17"] = excess17
        _NEW_DATA_["Excess_17_30s"] = boxAverage(_PERSISTENT_["O17ebuffer30"],excess17,now,30)
        _NEW_DATA_["Excess_17_100s"] = boxAverage(_PERSISTENT_["O17ebuffer100"],excess17,now,100)
        _NEW_DATA_["Excess_17_2min"] = boxAverage(_PERSISTENT_["O17ebuffer120"],excess17,now,120)
        _NEW_DATA_["Excess_17_5min"] = boxAverage(_PERSISTENT_["O17ebuffer300"],excess17,now,300)

    except:
        pass

else:
    _NEW_DATA_["Delta_18_16"] = _OLD_DATA_["Delta_18_16"][-1].value
    _NEW_DATA_["Delta_18_16_30s"] = _OLD_DATA_["Delta_18_16_30s"][-1].value
    _NEW_DATA_["Delta_18_16_100s"] = _OLD_DATA_["Delta_18_16_100s"][-1].value
    _NEW_DATA_["Delta_18_16_2min"] = _OLD_DATA_["Delta_18_16_2min"][-1].value
    _NEW_DATA_["Delta_18_16_5min"] = _OLD_DATA_["Delta_18_16_5min"][-1].value
    _NEW_DATA_["Delta_D_H"] = _OLD_DATA_["Delta_D_H"][-1].value
    _NEW_DATA_["Delta_D_H_30s"] = _OLD_DATA_["Delta_D_H_30s"][-1].value
    _NEW_DATA_["Delta_D_H_100s"] = _OLD_DATA_["Delta_D_H_100s"][-1].value
    _NEW_DATA_["Delta_D_H_2min"] = _OLD_DATA_["Delta_D_H_2min"][-1].value
    _NEW_DATA_["Delta_D_H_5min"] = _OLD_DATA_["Delta_D_H_5min"][-1].value
    _NEW_DATA_["H2O"] = _OLD_DATA_["H2O"][-1].value
    _NEW_DATA_["CH4"] = _OLD_DATA_["CH4"][-1].value
    _NEW_DATA_["CH4_30s"] = _OLD_DATA_["CH4_30s"][-1].value
    _NEW_DATA_["CH4_2min"] = _OLD_DATA_["CH4_2min"][-1].value
    _NEW_DATA_["CH4_5min"] = _OLD_DATA_["CH4_5min"][-1].value
    _NEW_DATA_["Delta_17_16"] = _OLD_DATA_["Delta_17_16"][-1].value
    _NEW_DATA_["Delta_17_16_30s"] = _OLD_DATA_["Delta_17_16_30s"][-1].value
    _NEW_DATA_["Delta_17_16_100s"] = _OLD_DATA_["Delta_17_16_100s"][-1].value
    _NEW_DATA_["Delta_17_16_2min"] = _OLD_DATA_["Delta_17_16_2min"][-1].value
    _NEW_DATA_["Delta_17_16_5min"] = _OLD_DATA_["Delta_17_16_5min"][-1].value
    _NEW_DATA_["Excess_17"] = _OLD_DATA_["Excess_17"][-1].value
    _NEW_DATA_["Excess_17_30s"] = _OLD_DATA_["Excess_17_30s"][-1].value
    _NEW_DATA_["Excess_17_100s"] = _OLD_DATA_["Excess_17_100s"][-1].value
    _NEW_DATA_["Excess_17_2min"] = _OLD_DATA_["Excess_17_2min"][-1].value
    _NEW_DATA_["Excess_17_5min"] = _OLD_DATA_["Exdess_17_5min"][-1].value
    _NEW_DATA_["SD_18_18"] = _OLD_DATA_["SD_18_18"][-1].value

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    if k == "delta":
        _REPORT_[k] = clipReportData(_NEW_DATA_[k])
    else:
        _REPORT_[k] = _NEW_DATA_[k]

max_shift = 1.0e-5
H16OH_cm_adjust_gain = 0.1
H18OH_cm_adjust_gain = 0.1
H16OD_cm_adjust_gain = 0.1
O18a_cm_adjust_gain = 0.1
O17_cm_adjust_gain = 0.1
PZTgain = 0.05

# Check instrument status and do not do any updates if any parameters are unlocked

pressureLocked =    _INSTR_STATUS_ & INSTMGR_STATUS_PRESSURE_LOCKED
cavityTempLocked =  _INSTR_STATUS_ & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
warmboxTempLocked = _INSTR_STATUS_ & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
warmingUp =         _INSTR_STATUS_ & INSTMGR_STATUS_WARMING_UP
systemError =       _INSTR_STATUS_ & INSTMGR_STATUS_SYSTEM_ERROR
good = pressureLocked and cavityTempLocked and warmboxTempLocked and (not warmingUp) and (not systemError)
if abs(_DATA_["CavityPressure"]-50.0) > 0.5:
    good = False

if not good:
    print "Updating WLM offset not done because of bad instrument status"
else:
    if _DATA_["spectrum"] == 123:
        try:
            o18_adjust = _DATA_["O18a_adjust"]*O18a_cm_adjust_gain   # Update the offset for virtual laser 1
            o18_adjust = min(max_shift,max(-max_shift,o18_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(1) + o18_adjust
            _PERSISTENT_["wlm1_offset"] = newOffset0
            _NEW_DATA_["wlm1_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(1,float(newOffset0))
            #print "New O18 (virtual laser 1) offset: %.5f" % newOffset0
        except:
            pass
            print "No new O18 (virtual laser 1) offset"
        try:
            o17_adjust = _DATA_["O17_adjust"]*O17_cm_adjust_gain   # Update the offset for virtual laser 2
            o17_adjust = min(max_shift,max(-max_shift,o17_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(2) + o17_adjust
            _NEW_DATA_["wlm2_offset"] = newOffset0
            _PERSISTENT_["wlm2_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(2,float(newOffset0))
            #print "New O17 (virtual laser 2) offset: %.5f" % newOffset0
        except:
            pass
            print "No new O17 (virtual laser 2) offset"

        try:
            o16_adjust = _DATA_["h16oh_adjust"]*H16OH_cm_adjust_gain   # Update the offset for virtual laser 3
            o16_adjust = min(max_shift,max(-max_shift,o16_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(3) + o16_adjust
            _PERSISTENT_["wlm3_offset"] = newOffset0
            _NEW_DATA_["wlm3_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(3,float(newOffset0))
            #print "New O16 (virtual laser 3) offset: %.5f" % newOffset0
        except:
            pass
            print "No new O16 (virtual laser 3) offset"

        try:
            o18_adjust = _DATA_["h18oh_adjust"]*H18OH_cm_adjust_gain   # Update the offset for virtual laser 4
            o18_adjust = min(max_shift,max(-max_shift,o18_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(4) + o18_adjust
            _PERSISTENT_["wlm4_offset"] = newOffset0
            _NEW_DATA_["wlm4_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(4,float(newOffset0))
            #print "New O18 (virtual laser 4) offset: %.5f" % newOffset0
        except:
            pass
            print "No new O18 (virtual laser 4) offset"

        try:
            d_adjust = _DATA_["h16od_adjust"]*H16OD_cm_adjust_gain   # Update the offset for virtual laser 5
            d_adjust = min(max_shift,max(-max_shift,d_adjust))
            newOffset0 = _FREQ_CONV_.getWlmOffset(5) + d_adjust
            _PERSISTENT_["wlm5_offset"] = newOffset0
            _NEW_DATA_["wlm5_offset"] = newOffset0
            _FREQ_CONV_.setWlmOffset(5,float(newOffset0))
            #print "New D (virtual laser 5) offset: %.5f" % newOffset0
        except:
            pass
            print "No new D (virtual laser 5) offset"

#  PZT voltage control goes here.  First step is to apply the adjustments from spectroscopy

        FSR = _DATA_["pzt_per_fsr"]
        try:
            adjust = _DATA_["pzt1_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt1_offset"] + adjust
            _PERSISTENT_["pzt1_offset"] = newPZToffset
        except:
            pass

        try:
            adjust = _DATA_["pzt2_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt2_offset"] + adjust
            _PERSISTENT_["pzt2_offset"] = newPZToffset
        except:
            pass

        try:
            adjust = _DATA_["pzt3_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt3_offset"] + adjust
            _PERSISTENT_["pzt3_offset"] = newPZToffset
        except:
            pass

        try:
            adjust = _DATA_["pzt4_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt4_offset"] + adjust
            _PERSISTENT_["pzt4_offset"] = newPZToffset
        except:
            pass

        try:
            adjust = _DATA_["pzt5_adjust"]*PZTgain
            newPZToffset = _PERSISTENT_["pzt5_offset"] + adjust
            _PERSISTENT_["pzt5_offset"] = newPZToffset
        except:
            pass

#  Next force PZT voltages to lie within 1.1*FSR (approx. 22000 DN)

        PZT = [{'index':1,'value':_PERSISTENT_["pzt1_offset"]},{'index':2,'value':_PERSISTENT_["pzt2_offset"]},
               {'index':3,'value':_PERSISTENT_["pzt3_offset"]},{'index':4,'value':_PERSISTENT_["pzt4_offset"]},
               {'index':5,'value':_PERSISTENT_["pzt5_offset"]}]
        orderedPZT = sorted(PZT, key=lambda k: k['value'])
        while orderedPZT[4]['value']-orderedPZT[0]['value'] > 1.1*FSR:
            lowestPZT = orderedPZT[0]['index']
            highestPZT = orderedPZT[4]['index']
            if PZT[lowestPZT-1]['value'] < 65536 - 1.1*FSR:
                PZT[lowestPZT-1]['value'] += FSR
            else:
                PZT[highestPZT-1]['value'] -= FSR
            orderedPZT = sorted(PZT, key=lambda k: k['value'])

#  Check if PZTS are near limit and move all of them if they are

        if orderedPZT[0]['value'] < 32768 - 1.2*FSR:
            PZT[0]['value'] += FSR
            PZT[1]['value'] += FSR
            PZT[2]['value'] += FSR
            PZT[3]['value'] += FSR
            PZT[4]['value'] += FSR
            _PERSISTENT_["PZTshift"] += 1
        if orderedPZT[4]['value'] > 32768 + 1.2*FSR:
            PZT[0]['value'] -= FSR
            PZT[1]['value'] -= FSR
            PZT[2]['value'] -= FSR
            PZT[3]['value'] -= FSR
            PZT[4]['value'] -= FSR
            _PERSISTENT_["PZTshift"] += 1

#  Report adjusted PZT voltages and apply to analyzer

        _PERSISTENT_["pzt1_offset"] = PZT[0]['value']
        _NEW_DATA_["pzt1_offset"] = PZT[0]['value']
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1",PZT[0]['value'])
        _PERSISTENT_["pzt2_offset"] = PZT[1]['value']
        _NEW_DATA_["pzt2_offset"] = PZT[1]['value']
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER2",PZT[1]['value'])
        _PERSISTENT_["pzt3_offset"] = PZT[2]['value']
        _NEW_DATA_["pzt3_offset"] = PZT[2]['value']
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER3",PZT[2]['value'])
        _PERSISTENT_["pzt4_offset"] = PZT[3]['value']
        _NEW_DATA_["pzt4_offset"] = PZT[3]['value']
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER4",PZT[3]['value'])
        _PERSISTENT_["pzt5_offset"] = PZT[4]['value']
        _NEW_DATA_["pzt5_offset"] = PZT[4]['value']
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER5",PZT[4]['value'])

_REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
_REPORT_["wlm2_offset"] = _PERSISTENT_["wlm2_offset"]
_REPORT_["wlm3_offset"] = _PERSISTENT_["wlm3_offset"]
_REPORT_["wlm4_offset"] = _PERSISTENT_["wlm4_offset"]
_REPORT_["wlm5_offset"] = _PERSISTENT_["wlm5_offset"]
_REPORT_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
_REPORT_["pzt2_offset"] = _PERSISTENT_["pzt2_offset"]
_REPORT_["pzt3_offset"] = _PERSISTENT_["pzt3_offset"]
_REPORT_["pzt4_offset"] = _PERSISTENT_["pzt4_offset"]
_REPORT_["pzt5_offset"] = _PERSISTENT_["pzt5_offset"]
_REPORT_["PZTshift"] = _PERSISTENT_["PZTshift"]
