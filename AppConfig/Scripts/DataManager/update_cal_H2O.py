max_shift = 5.0e-4
try:
	co2_shift = _OLD_DATA_["avg_co2_shift"][-1].value
	co2_shift = min(max_shift,max(-max_shift,co2_shift))
	newOffset0 = _MEAS_SYS_.GetWlmOffset(0) + co2_shift/25.0
	_NEW_DATA_["wlm1_offset"] = newOffset0
	_MEAS_SYS_.SetWlmOffset(0,float(newOffset0))
	print "new CO2 offset: %.5f" % newOffset0 
except:
	print "No CO2 offset update"

try:
	h2o_shift = _OLD_DATA_["avg_h2o_shift"][-1].value
	h2o_shift = min(max_shift,max(-max_shift,h2o_shift))
	newOffset1 = _MEAS_SYS_.GetWlmOffset(1) + h2o_shift/25.0
	_NEW_DATA_["wlm2_offset"] = newOffset1
	_MEAS_SYS_.SetWlmOffset(1,float(newOffset1))
	print "new h2o offset: %.5f" % newOffset1 
except:
	print "No h2o offset update"