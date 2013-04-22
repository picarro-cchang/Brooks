import os
import sys
from PeakFinder1 import PeakFinder

if __name__ == "__main__":
    AppPath = sys.argv[0]
    AppDir = os.path.split(AppPath)[0]
    
    data_dir = 'C:/UserData/AnalyzerServer' # local Analyzer data location
    debug = False
        
    ulog = os.path.join(data_dir, '*DataLog_User_Minimal.dat')
    pf = PeakFinder()
    if len(sys.argv) < 2:
        pf.userlogfiles = ulog
    else:
        pf.file_path = sys.argv[1]
    pf.debug = debug
    pf.run()
