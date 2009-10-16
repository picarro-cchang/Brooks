try:
    Laser2Temp = _OLD_SENSOR_["Laser2Temp"][-1][1]
    #Tcav  = _OLD_SENSOR_["CavityTemp"][-1][1]
    #Pcav  = _OLD_SENSOR_["CavityPressure"][-1][1]
    Tdas  = _OLD_SENSOR_["DasTemp"][-1][1]
    _REPORT_["Laser2Temp"] = Laser2Temp
    #_REPORT_["CavityTemp"] = Tcav
    #_REPORT_["CavityPressure"] = Pcav
    _REPORT_["DasTemp"] = Tdas
except:
    print "Sensor data unavailable"
