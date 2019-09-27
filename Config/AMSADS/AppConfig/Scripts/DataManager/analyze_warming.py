try :
    for sensorKey in _OLD_SENSOR_:
        _REPORT_[sensorKey] = _OLD_SENSOR_[sensorKey][-1][1]
except:
    print "Sensor data unavailable"
