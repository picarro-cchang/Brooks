import os
import sys
from PeakAnalyzer import PeakAnalyzer

if __name__ == "__main__":
    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    
    data_dir = os.path.join(AppDir,'static/datalog') # local Analyzer data location
    debug = False
        
    ulog = os.path.join(data_dir, '*DataLog_User_Minimal.dat')
    pf = PeakAnalyzer()
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.run()
