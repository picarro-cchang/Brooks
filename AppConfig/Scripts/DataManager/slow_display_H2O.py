try:
	_REPORT_["co2_conc_slow"] = _OLD_DATA_["co2_conc"][-1].value
	_REPORT_["h2o_conc_slow"] = _OLD_DATA_["h2o_conc"][-1].value
except:
	pass