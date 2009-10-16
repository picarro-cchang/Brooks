max_shift = 5.0e-4
try:
	ch4_shift = _OLD_DATA_["avg_ch4_shift"][-1].value
	ch4_shift = min(max_shift,max(-max_shift,ch4_shift))
	newOffset1 = _MEAS_SYS_.GetWlmOffset(1) + ch4_shift/250.0
	_NEW_DATA_["wlm2_offset"] = newOffset1
	_MEAS_SYS_.SetWlmOffset(1,float(newOffset1))
	print "new CH4 offset: %.5f" % newOffset1 
except:
	print "No CH4 offset update"	