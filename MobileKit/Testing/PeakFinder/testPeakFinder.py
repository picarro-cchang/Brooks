# 1. Start peak finder
# 2. Playback data file with different delay patterns
# 3. Create new data file to flush old peaks file
# 4. Compare outputs
import math
import os
import subprocess
import sys
import time
import random
import unittest

class TestPeakFinder(unittest.TestCase):
    def setUp(self):
        pfName = "c:/Picarro/G2000/MobileKit/AnalyzerServer/SimulatePeakFinder.py"
        self.dataFile = "CFADS2274-20120817-012321Z-DataLog_User_Minimal.dat"
        self.peaksFile = "CFADS2274-20120817-012321Z-DataLog_User_Minimal_OK.peaks"
        self.proc = subprocess.Popen(["python",pfName])
        self.tidyUpDir("c:/UserData/AnalyzerServer","ZZZZ2274")
        self.success = False
        
    def checkEqual(self,f1,f2):
        fp1 = file(f1,"rb")
        fp2 = file(f2,"rb")
        try:
            return fp1.read() == fp2.read()
        finally:
            fp1.close()
            fp2.close()
            
    def testErraticWrite(self):
        niter = 3
        for i in range(niter):
            if i>0: 
                assert(self.checkEqual(self.peaksFile,lastFile+".peaks"))
            liveFile = "c:/UserData/AnalyzerServer/ZZZZ2274-20120817-%06dZ-DataLog_User_Minimal" % i
            op = file(liveFile + ".dat","wb",0)  # Non buffered
            ip = file(self.dataFile,"rb")
            # Copy the input file to the output
            totBytes = 0
            while True:
                bytes = int(math.ceil(random.expovariate(0.001)))
                delay = random.expovariate(100.0)
                x = ip.read(bytes)
                op.write(x)
                totBytes += len(x)
                sys.stdout.write(".")
                if len(x) != bytes: break
                time.sleep(delay)
            print "\nPass %d"  % i
            time.sleep(10)  # Allow processing to complete
            if i>0:
                os.remove(lastFile + ".dat")
                os.remove(lastFile + ".peaks")
            lastFile = liveFile
            op.close()
            ip.close()
        assert(self.checkEqual(self.peaksFile,lastFile+".peaks"))
        self.success = True
        
    def tearDown(self):
        self.proc.terminate()
        print "Killed peak finder"
        if self.success:
            time.sleep(5.0)
            self.tidyUpDir("c:/UserData/AnalyzerServer","ZZZZ2274")
    
    def tidyUpDir(self,path,prefix):
        for dpath,dnames,fnames in os.walk(path):
            for fn in fnames:
                if fn.startswith(prefix):
                    os.remove(os.path.join(dpath, fn))
        
if __name__ == "__main__":
    unittest.main()
    