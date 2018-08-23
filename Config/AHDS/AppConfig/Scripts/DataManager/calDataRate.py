# Calculate reporting data rate
try:
    data_rate = 1.0/((_OLD_DATA_["h2o_shift"][-2].time-_OLD_DATA_["h2o_shift"][-12].time)/10)
    _REPORT_["data_rate"] = data_rate
except:
    pass
    
