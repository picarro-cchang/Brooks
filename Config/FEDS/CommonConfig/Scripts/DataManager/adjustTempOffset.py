#!/usr/bin/python
#
"""
Description: Adjusts the laser temperature offset value to compensate
             for laser aging.

Details:     This script is run from scripts such as analyze_CFKADS.py
             which use compile() and exec(). The latter is run in globals().
             The dictionaries (_REPORT_, _INSTR_, and _DATA_) and
             _FREQ_CONV_ object exist in the caller so they exist here. The
             _UTILS_ dictionary contains the worker function object
             doAdjustTempOffset().

Copyright (c) 2013 Picarro, Inc. All rights reserved.
"""

def adjustTempOffset():
    # call common module to do the adjustment and stash the results in _REPORT_
    # set printInfo=True for some debugging output in the DataManager console
    _UTILS_["doAdjustTempOffset"](report=_REPORT_, instr=_INSTR_, data=_DATA_, freqConv=_FREQ_CONV_, printInfo=False)

adjustTempOffset()
