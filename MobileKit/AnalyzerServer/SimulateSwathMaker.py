#!/usr/bin/python
#
"""
File Name: SimulateSwathMaker.py
Purpose: Calls the swath maker to calculate the field of view swath associated with a data collection
run with the Picarro Surveyor

File History:
    17-Apr-2012  sze  Initial version.
Copyright (c) 2012 Picarro, Inc. All rights reserved
"""
import os
import sys
import time
from SwathMaker import SwathMaker

if __name__ == "__main__":
    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]

    data_dir = 'C:/UserData/AnalyzerServer' # local Analyzer data location
    debug = False
    ulog = os.path.join(data_dir, '*DataLog_User_Minimal.dat')
    sm = SwathMaker()
    if len(sys.argv) < 2:
        sm.userlogfiles = ulog
    else:
        sm.file_path = sys.argv[1]
    if len(sys.argv) > 2:
        sm.stabClass = sys.argv[2]
    else:
        sm.stabClass = "*"
    
    sm.debug = debug
    sm.noWait = True
    start = time.time()
    sm.run()
    print "Time taken", time.time() - start