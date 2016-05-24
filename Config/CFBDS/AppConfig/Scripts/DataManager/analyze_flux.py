##  20100628:  hoffnagle:  this script adds the quadratic water correction to the quantities reported in
##  flux mode.  The nomenclature is as follows:  h2o_reported is derived from the spectroscopic data without
##  correction for self broadening, h2o_conc is corrected for self-broadening (quadratic correction); co2_conc
##  and ch4_conc have no water correction;  co2_conc_dry and ch4_conc_dry have the quadratic correction for effect
##  of water concentration.  The water concentration used for the correction is the avrage of the two
##  measurements made before and after the CO2 or CH4 measurement.

co2_id = 1
ch4_id = 2
h2o_id = 3

if _DATA_["species"] == 1:
    try:
        co2_conc = _DATA_["co2_conc_precorr"] * (1-_DATA_["co2_corr_factor"])
        co2_conc_dry = _DATA_["co2_conc_dry_precorr"] * (1-_DATA_["co2_corr_factor"])
        _NEW_DATA_["co2_conc"] = co2_conc
        _NEW_DATA_["co2_conc_dry"] = co2_conc_dry
    except:
        pass
elif _OLD_DATA_["species"][-3].value == 1:
    try:
        _NEW_DATA_["co2_conc"] = _OLD_DATA_["co2_conc"][-1].value
        _NEW_DATA_["co2_conc_dry"] = _OLD_DATA_["co2_conc_dry"][-1].value
    except:
        pass
else:
    co2_id = 0

if _DATA_["species"] == 2:
    try:
        ch4_conc = _DATA_["ch4_conc_precorr"] * (1-_DATA_["ch4_corr_factor"])
        ch4_conc_dry = _DATA_["ch4_conc_dry_precorr"] * (1-_DATA_["ch4_corr_factor"])
        _NEW_DATA_["ch4_conc"] = ch4_conc
        _NEW_DATA_["ch4_conc_dry"] = ch4_conc_dry
    except:
        pass
elif _OLD_DATA_["species"][-3].value == 2:
    try:
        _NEW_DATA_["ch4_conc"] = _OLD_DATA_["ch4_conc"][-1].value
        _NEW_DATA_["ch4_conc_dry"] = _OLD_DATA_["ch4_conc_dry"][-1].value
    except:
        pass
else:
    ch4_id = 0

if _DATA_["species"] == 3:
    try:
        h2o_reported = _DATA_["h2o_reported_precorr"] * (1-_DATA_["h2o_corr_factor"])
        h2o_actual = _DATA_["h2o_actual"] * (1-_DATA_["h2o_corr_factor"])
        _NEW_DATA_["h2o_reported"] = h2o_reported
        _NEW_DATA_["h2o_conc"] = h2o_actual
    except:
        _NEW_DATA_["h2o_conc"] = 0.0
elif _OLD_DATA_["species"][-3].value == 3:
    try:
        _NEW_DATA_["h2o_reported"] = _OLD_DATA_["h2o_reported"][-1].value
        _NEW_DATA_["h2o_conc"] = _OLD_DATA_["h2o_conc"][-1].value
    except:
        _NEW_DATA_["h2o_conc"] = 0.0
else:
    h2o_id = 0

_NEW_DATA_["mode_id"] =  co2_id + ch4_id + h2o_id

try:
    _REPORT_["cavity_pressure"] = _OLD_DATA_["cavity_pressure"][-5].value
    _REPORT_["cavity_temperature"] = _OLD_DATA_["cavity_temperature"][-5].value
    _REPORT_["das_temp"] = _OLD_DATA_["das_temp"][-5].value
    _REPORT_["solenoid_valves"] = _OLD_DATA_["solenoid_valves"][-5].value
    _REPORT_["MPVPosition"] = _OLD_DATA_["MPVPosition"][-5].value
    _REPORT_["tuner"] = _OLD_DATA_["tuner"][-5].value
    _REPORT_["pzt"] = _OLD_DATA_["pzt"][-5].value
except:
    pass

for k in _NEW_DATA_:
    _REPORT_[k] = _NEW_DATA_[k]

for k in _DATA_:
    if k == "time_corr":
        _REPORT_["time"] = _DATA_["time_corr"]
    else:
        _REPORT_[k]=_DATA_[k]
