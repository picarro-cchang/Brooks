import sys
import os
if os.path.isdir("../AppConfig/Scripts/DataManager"):
    # For .exe version
    alarmEmailPath = "../AppConfig/Scripts/DataManager"
elif os.path.isdir("../../AppConfig/Scripts/DataManager"):
    # For .py version
    alarmEmailPath = "../../AppConfig/Scripts/DataManager"

if alarmEmailPath not in sys.path: sys.path.append(alarmEmailPath)

import time
#setLag = 3.0
setLag = 4
# Specify number of initial filter outputs to ignore. Must be less than length of history kept, since this is used to determine
#  when enough data have been processed
ignoreInitial = 20
scriptTime = _MEAS_TIME_

# Butterworth filter
#filter_B = [0.0004166,  0.0016664,  0.0024996,  0.0016664,  0.0004166]
#filter_A = [1.       , -3.18063855,  3.86119435, -2.11215536,  0.43826514]
# Bessel filter with cutoff at Wn=0.2
filter_B = [ 0.00428742,  0.01714968,  0.02572452,  0.01714968,  0.00428742]
filter_A = [ 1.        , -2.21797364,  1.97707284, -0.82511242,  0.13461194]

from AlarmEmail import AlarmEmail
ae=AlarmEmail(["alee@picarro.com","stan@picarro.com"])
MAX_RESYNC_MISSING = 100
MAX_EMAIL_ALARMS = 10

if _PERSISTENT_["init"]:
    timeStamp = time.ctime()
    try:
        ae.sendMsg("New Resync Script Started", timeStamp) 
    except:
        pass
    _PERSISTENT_["status"]["resyncMissingCount"] = 0
    _PERSISTENT_["status"]["emailCount"] = 0
    _PERSISTENT_["init"] = False
    
def linInterp(p1,p2,t):
    dtime = p2.time - p1.time
    if dtime == 0:
        return 0.5*(p1.value + p2.value)
    else:
        return ((t-p1.time)*p2.value + (p2.time-t)*p1.value) / dtime

def resyncAndFilter(dataLabel):
    """ Performs resynchronizarion and filtering, returning True if all operations succeeded """
    syncDataLabel = dataLabel + "_sync"
    filtDataLabel = dataLabel + "_filt"
    syncStatus = False
    status = False
    index = -1
    try:
        result = _OLD_DATA_[dataLabel][-1].value
    except:
        return status
    try:
        while _OLD_DATA_[dataLabel][index].time > scriptTime - setLag: 
            index -= 1
            
        if index == -1:
            _PERSISTENT_["status"]["resyncMissingCount"] += 1
        else:
            _PERSISTENT_["status"]["resyncMissingCount"] = 0
        print "resyncMissingCount = ", _PERSISTENT_["status"]["resyncMissingCount"]    
        if _PERSISTENT_["status"]["resyncMissingCount"] == MAX_RESYNC_MISSING:
            _PERSISTENT_["status"]["resyncMissingCount"] = 0
            if _PERSISTENT_["status"]["emailCount"] <= MAX_EMAIL_ALARMS:
                try:
                    ae.sendMsg("Resync Data Missing Alarm", "Alarm %d: resync index has been -1 for %d consecutive times" % (_PERSISTENT_["status"]["emailCount"], MAX_RESYNC_MISSING)) 
                except:
                    pass
                _PERSISTENT_["status"]["emailCount"] += 1            

        print "index = %d, time since last fit = %f" % (index,scriptTime-_OLD_DATA_[dataLabel][-1].time)
        if index < -1:
            result = linInterp(_OLD_DATA_[dataLabel][index],_OLD_DATA_[dataLabel][index+1],scriptTime-setLag)
            syncStatus = True
    except:
        pass
    _NEW_DATA_[syncDataLabel] = result
    try:
        output = filter_B[0]*result
        for i in range(1,len(filter_B)):
            output += filter_B[i]*_OLD_DATA_[syncDataLabel][-i].value
        for i in range(1,len(filter_A)):
            output -= filter_A[i]*_OLD_DATA_[filtDataLabel][-i].value
        output /= filter_A[0]
        if len(_OLD_DATA_[filtDataLabel])>ignoreInitial and syncStatus: 
            status = True
    except:
        output = result
    _NEW_DATA_[filtDataLabel] = output    
    return status
    
allGood = True
allGood = allGood and resyncAndFilter("co2_conc")
allGood = allGood and resyncAndFilter("ch4_conc")

if allGood:
    t = time.gmtime(scriptTime-setLag)
    t1 = float("%04d%02d%02d" % t[0:3])
    t2 = "%02d%02d%02d.%03.0f" % (t[3],t[4],t[5],1000*(scriptTime-int(scriptTime)),)
    _REPORT_["time"] = scriptTime-setLag
    _REPORT_["ymd"] = t1
    _REPORT_["hms"] = t2
    for k in _NEW_DATA_:
        _REPORT_[k] = _NEW_DATA_[k]
