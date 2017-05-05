setLag = 3.0
scriptTime = _MEAS_TIME_

def linInterp(p1,p2,t):
    dtime = p2.time - p1.time
    if dtime == 0:
        return 0.5*(p1.value + p2.value)
    else:
        return ((t-p1.time)*p2.value + (p2.time-t)*p1.value) / dtime

def resync(dataLabel):
    index = -1
    try:
        result = _OLD_DATA_[dataLabel][-1].value
    except:
        return
    try:
        while _OLD_DATA_[dataLabel][index].time > scriptTime - setLag: 
            index -= 1
        result = linInterp(_OLD_DATA_[dataLabel][index],_OLD_DATA_[dataLabel][index+1],scriptTime-setLag)
    except:
        pass
    _REPORT_[dataLabel] = result
    
resync("co2_conc")
resync("ch4_conc")
_REPORT_["time"] = _MEAS_TIME_
