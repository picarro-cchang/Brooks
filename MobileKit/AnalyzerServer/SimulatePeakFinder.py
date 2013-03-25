import os
import sys
from PeakFinder import PeakFinder

if __name__ == "__main__":
    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    
    data_dir = 'C:/UserData/AnalyzerServer' # local Analyzer data location
    debug = True
        
    ulog = os.path.join(data_dir, '*DataLog_User_Minimal.dat')
    pf = PeakFinder()
    pf.userlogfiles = ulog
    pf.debug = debug
    pf.run()
