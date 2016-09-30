import inspect
import os
import sys
import time
# Need to find path to the translation table
here = os.path.split(os.path.abspath(inspect.getfile( inspect.currentframe())))[0]
if here not in sys.path: sys.path.append(here)
from translate import newname

SYNC_LIST = ["NH3", "NH3_2min", "NH3_30s", "NH3_5min", "H2O"]
SENSOR_LIST = ["species", "solenoid_valves", "DasTemp", "CavityPressure",
               "MPVPosition", "OutletValve", "CavityTemp", "WarmBoxTemp", "EtalonTemp"]
setLag = 10.0
# Specify number of initial filter outputs to ignore. Must be less than length of history kept, since this is used to determine
#  when enough data have been processed
ignoreInitial = 5
scriptTime = _MEAS_TIME_

# Butterworth filter
#filter_B = [0.0004166,  0.0016664,  0.0024996,  0.0016664,  0.0004166]
#filter_A = [1.       , -3.18063855,  3.86119435, -2.11215536,  0.43826514]
# Bessel filter with cutoff at Wn=0.2
filter_B = [ 0.00428742,  0.01714968,  0.02572452,  0.01714968,  0.00428742]
filter_A = [ 1.        , -2.21797364,  1.97707284, -0.82511242,  0.13461194]

def applyLinear(value,xform):
    return xform[0]*value + xform[1]

def linInterp(p1,p2,t):
    dtime = p2.time - p1.time
    if dtime == 0:
        return 0.5*(p1.value + p2.value)
    else:
        return ((t-p1.time)*p2.value + (p2.time-t)*p1.value) / dtime

def resync(dataLabel):
    """ Performs resynchronizarion and filtering, returning True if all operations succeeded """
    global index
    syncDataLabel = dataLabel + "_sync"
    syncStatus = False
    status = False
    index = -1
    try:
        result = _OLD_DATA_[dataLabel][-1].value
    except Exception, err:
        print err
        return status
    try:
        while _OLD_DATA_[dataLabel][index].time > scriptTime - setLag:
            index -= 1
        #print "index = %d, time since last fit = %f" % (index,scriptTime-_OLD_DATA_[dataLabel][-1].time)
        if index < -1:
            result = linInterp(_OLD_DATA_[dataLabel][index],_OLD_DATA_[dataLabel][index+1],scriptTime-setLag)
            syncStatus = True
    except:
        pass
    if dataLabel in newname:
        callabel = newname[dataLabel]
    else:
        callabel = dataLabel
    result = applyLinear(result,_USER_CAL_[callabel])
    _NEW_DATA_[syncDataLabel] = result
    try:
        if len(_OLD_DATA_[syncDataLabel])>ignoreInitial and syncStatus:
            status = True
    except:
        pass

    return status

allGood = True
for conc in SYNC_LIST:
    allGood = allGood and resync(conc)

if allGood:
    t = time.gmtime(scriptTime-setLag)
    t1 = float("%04d%02d%02d" % t[0:3])
    t2 = "%02d%02d%02d.%03.0f" % (t[3],t[4],t[5],1000*(scriptTime-int(scriptTime)),)
    #print t2
    _REPORT_["time"] = scriptTime-setLag
    _REPORT_["ymd"] = t1
    _REPORT_["hms"] = t2
    for k in _NEW_DATA_:
        if k in newname:
            _REPORT_[newname[k]] = _NEW_DATA_[k]
        else:
            _REPORT_[k] = _NEW_DATA_[k]
    for key in SENSOR_LIST:
        _REPORT_[key] = _OLD_DATA_[key][index].value
