PERIPH_DELAY = 1000
if _PERSISTENT_["init"]:
    _PERSISTENT_["init"] = False
    try:
        _DATA_LOGGER_.DATALOGGER_startLogRpc("DataLog_Sensor_Minimal")
    except Exception, err:
        print "_DATA_LOGGER_ Error: %r" % err
        
try :
    for sensorKey in _OLD_SENSOR_:
        _REPORT_[sensorKey] = _OLD_SENSOR_[sensorKey][-1][1]
except:
    print "Sensor data unavailable"

if _PERIPH_INTRF_:
    try:
        interpData = _PERIPH_INTRF_( _MEAS_TIMESTAMP_-PERIPH_DELAY, _PERIPH_INTRF_COLS_)
        #print interpData
        for i in range(len(_PERIPH_INTRF_COLS_)):
            if interpData[i]:
                _REPORT_[_PERIPH_INTRF_COLS_[i]] = interpData[i]
    except Exception, err:
        print "%r" % err