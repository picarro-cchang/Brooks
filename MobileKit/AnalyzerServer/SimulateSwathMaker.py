#!/usr/bin/python
#
"""
File Name: SimulateSwathMaker.py
Purpose: Calls the swath maker to calculate the field of view swathe associated with a data collection
run with the Picarro Surveyor

File History:
    17-Apr-2012  sze  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
import os
import sys
from SwathMaker import SwathMaker

if __name__ == "__main__":
    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    
    data_dir = 'C:/UserData/AnalyzerServer' # local Analyzer data location
    debug = False
        
    ulog = os.path.join(data_dir, '*DataLog_User_Minimal.dat')
    pf = SwathMaker()
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.noWait = True
    pf.run()
