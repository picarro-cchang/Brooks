xp = _GLOBALS_["xProcessor"]
xh = xp.xHistory

xs = xh.popleft()
for i,(c,f,v) in enumerate(xp.crossList):
    _REPORT_[c + '_xsync'] = xs.valueArray[xs.indexByName[c]]
_REPORT_["timestamp"] = int(xs.timestamp)

"""
# The following two loops forward all other variables as well
for d in xs.data:
    if d == "timestamp": continue
    _REPORT_[d] = xs.data[d]
for d in xs.new_data:
    if d == "timestamp": continue
    _REPORT_[d] = xs.new_data[d]
"""

if xh and xh[0].ready:
    _ANALYZE_[xp.forward_id] = {"new_timestamp":xh[0].timestamp}
