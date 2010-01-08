max_shift = 2.0e-4
try:
	co2_shift = _OLD_DATA_["avg_co2_shift"][-1].value/5.0
	co2_shift = min(max_shift,max(-max_shift,co2_shift))
	newOffset0 = _FREQ_CONV_.getWlmOffset(1) + co2_shift
	_NEW_DATA_["wlm1_offset"] = newOffset0
	_FREQ_CONV_.setWlmOffset(1,float(newOffset0))
	print "new CO2 offset: %.5f" % newOffset0 
except:
	print "No CO2 offset update"

try:
	ch4_shift = _OLD_DATA_["avg_ch4_shift"][-1].value/5.0
	ch4_shift = min(max_shift,max(-max_shift,ch4_shift))
	newOffset1 = _FREQ_CONV_.getWlmOffset(2) + ch4_shift
	_NEW_DATA_["wlm2_offset"] = newOffset1
	_FREQ_CONV_.setWlmOffset(2,float(newOffset1))
	print "new CH4 offset: %.5f" % newOffset1 
except:
	print "No CH4 offset update"	