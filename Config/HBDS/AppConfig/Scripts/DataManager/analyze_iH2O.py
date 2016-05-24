from numpy import mean, polyfit, polyval
import time

# Static variables for averaging

if _PERSISTENT_["init"]:
    _PERSISTENT_["Dbuffer30"]  = []
    _PERSISTENT_["Dbuffer120"] = []
    _PERSISTENT_["Dbuffer300"] = []
    _PERSISTENT_["O18buffer30"]  = []
    _PERSISTENT_["O18buffer120"] = []
    _PERSISTENT_["O18buffer300"] = []
    _PERSISTENT_["init"] = False

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

def protDivide(num,den):
    if den != 0:
        return num/den
    return 0

def boxAverage(buffer,x,t,tau):
    buffer.append((x,t))
    while t-buffer[0][1] > tau:
        buffer.pop(0)
    return mean([d for (d,t) in buffer])

H2O_CONC = (_INSTR_["h2o_conc_slope"],_INSTR_["h2o_conc_intercept"])

DELTA_1816 = (_INSTR_["delta_1816_slope"],_INSTR_["delta_1816_intercept"])

DELTA_DH = (_INSTR_["delta_dh_slope"],_INSTR_["delta_dh_intercept"])

try:
    # in "%"
    #_REPORT_["H2O"] = 1.0e-4 * applyLinear(_DATA_["h2o_spline_max"],H2O_GAL)
    # in "ppm"
    _REPORT_["H2O"] = applyLinear(_DATA_["h2o_ppmv"],H2O_CONC)
except:
    pass

try:
    temp = protDivide(_DATA_["galpeak77"],_DATA_["h2o_spline_max"])
    delta_18_16 = applyLinear(temp,DELTA_1816)
    now = _OLD_DATA_["galpeak77"][-1].time
    _REPORT_["Delta_18_16"] = delta_18_16
    _REPORT_["Delta_18_16_30s"] = boxAverage(_PERSISTENT_["O18buffer30"],delta_18_16,now,30)
    _REPORT_["Delta_18_16_2min"] = boxAverage(_PERSISTENT_["O18buffer120"],delta_18_16,now,120)
    _REPORT_["Delta_18_16_5min"] = boxAverage(_PERSISTENT_["O18buffer300"],delta_18_16,now,300)
except:
    pass

try:
    temp = protDivide(_DATA_["galpeak82"],_DATA_["h2o_spline_max"])
    delta_D_H = applyLinear(temp,DELTA_DH)
    now = _OLD_DATA_["galpeak82"][-1].time
    _REPORT_["Delta_D_H"] = delta_D_H
    _REPORT_["Delta_D_H_30s"] = boxAverage(_PERSISTENT_["Dbuffer30"],delta_D_H,now,30)
    _REPORT_["Delta_D_H_2min"] = boxAverage(_PERSISTENT_["Dbuffer120"],delta_D_H,now,120)
    _REPORT_["Delta_D_H_5min"] = boxAverage(_PERSISTENT_["Dbuffer300"],delta_D_H,now,300)
except:
    pass

try:
    _REPORT_["wlm1_offset"] = _OLD_DATA_["wlm1_offset"][-1].value
except:
    pass

t = time.gmtime(_MEAS_TIME_)
t1 = float("%04d%02d%02d" % t[0:3])
t2 = "%02d%02d%02d.%03.0f" % (t[3],t[4],t[5],1000*(_MEAS_TIME_-int(_MEAS_TIME_)),)
#print t2
_REPORT_["time"] = _MEAS_TIME_
_REPORT_["ymd"] = t1
_REPORT_["hms"] = t2

for k in _DATA_.keys():
    if not k.startswith("cal_"):
        _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]
