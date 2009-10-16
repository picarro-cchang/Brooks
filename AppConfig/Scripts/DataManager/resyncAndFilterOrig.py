setLag = 3.0
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
    status = False
    index = -1
    try:
        result = _OLD_DATA_[dataLabel][-1].value
    except:
        return status
    try:
        while _OLD_DATA_[dataLabel][index].time > scriptTime - setLag: 
            index -= 1
        result = linInterp(_OLD_DATA_[dataLabel][index],_OLD_DATA_[dataLabel][index+1],scriptTime-setLag)
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
        if len(_OLD_DATA_[filtDataLabel])>ignoreInitial: status = True
    except:
        output = result
    _NEW_DATA_[filtDataLabel] = output    
    return status
    
allGood = True
allGood = allGood and resyncAndFilter("co2_conc")
allGood = allGood and resyncAndFilter("ch4_adjconc")

if allGood:
    _REPORT_["time"] = scriptTime
    for k in _NEW_DATA_:
        _REPORT_[k] = _NEW_DATA_[k]
