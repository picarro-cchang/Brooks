#  Bare-bones analysis script to operate the CFADS analyzer in laser current tuning mode
#  2013 0620:  Add water vapor to CO2 and incorporate structure of other lct analyses
#  2013 0711:  Add CH4 with w/d correction
#  2014 0325:  Increase max_adjust for WLM offset from 2e-5 to 5e-5 to try to improve tracking when warm box temp is badly off
#  2018 0927:  First cut at an analysis script specifically for a CFADS "spectroscopic manometer"
#  2019 0304:  Adapted
#  2019 0415:  Reporting modified for 45 C G2000 (CO2 from XII.27, 1 Oct 2018, water from 2013 dilution)
#  2019 0423:  New variant to measure the 6547.69 wvn line of 1% CO2 in nitrogen
#  2019 0501:  Plan ahead for line width measurement of the oxygen line at 7823 wvn in dry air

import inspect
import os
import sys


def applyLinear(value, xform):
    return xform[0] * value + xform[1]


if _PERSISTENT_["init"]:
    _PERSISTENT_["wlm1_offset"] = 0.0
    _PERSISTENT_["pzt1_offset"] = 32768
    _PERSISTENT_["init"] = False

max_adjust = 1e-4
WLMgain = 0.2
PZTgain = 0.1

if _DATA_["species"] == 62:
    try:
        _NEW_DATA_["O2"] = _DATA_["o2_pct"]
        _NEW_DATA_["H2O"] = _DATA_["h2o_ppm"]

        adjust = _DATA_["o2_adjust"] * WLMgain
        adjust = min(max_adjust, max(-max_adjust, adjust))
        newOffset = _FREQ_CONV_.getWlmOffset(1) + adjust
        _PERSISTENT_["wlm1_offset"] = newOffset
        _FREQ_CONV_.setWlmOffset(1, float(newOffset))

        adjust = _DATA_["pzt1_adjust"] * PZTgain
        newPZToffset = _DRIVER_.rdDasReg("PZT_OFFSET_VIRTUAL_LASER1") + adjust
        while newPZToffset > 45768:
            newPZToffset -= _DATA_["pzt_per_fsr"]
        while newPZToffset < 19768:
            newPZToffset += _DATA_["pzt_per_fsr"]
        _PERSISTENT_["pzt1_offset"] = newPZToffset
        _DRIVER_.wrDasReg("PZT_OFFSET_VIRTUAL_LASER1", newPZToffset)
    except:
        pass

for k in _DATA_.keys():
    _REPORT_[k] = _DATA_[k]

for k in _NEW_DATA_.keys():
    _REPORT_[k] = _NEW_DATA_[k]

_REPORT_["wlm1_offset"] = _PERSISTENT_["wlm1_offset"]
_REPORT_["pzt1_offset"] = _PERSISTENT_["pzt1_offset"]
