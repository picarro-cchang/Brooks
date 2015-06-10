scanningMode = _ARGS_[0]

# Calculate reporting data rate
try:
    if scanningMode in ["CO2_CH4", "CO2_H2O"]:
        data_rate = 1.0/((_OLD_DATA_["co2_shift"][-2].time-_OLD_DATA_["co2_shift"][-12].time)/10)/2
    elif scanningMode == "H2O_CH4":
        data_rate = 1/((_OLD_DATA_["ch4_shift"][-2].time-_OLD_DATA_["ch4_shift"][-12].time)/10)/2
    else:
        data_rate = 0.0
    _REPORT_["data_rate"] = data_rate
except:
    pass

