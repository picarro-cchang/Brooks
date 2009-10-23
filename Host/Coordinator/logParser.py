import unittest

autosamplerLog1 = """   Print Date: 2008/08/13   10:04:35
   Site Name: CTC, System Name: PAL, System SNo: 142218

   2008/08/13  10:02:22 Job 01 started: Method 5ulMethd
                        Tray MT1-Frnt, Vial 1-3, Count = 1, Increment = 1
               10:02:43 Sample 1 Injected
               10:03:14 Sample 2 Injected
               10:03:46 Sample 3 Injected

   2008/08/13  10:03:56 Job 04 started: Method 5ulMethd
                        Tray MT1-Frnt, Vial 1-1, Count = 1, Increment = 1
               10:04:17 Sample 1 Injected
|
"""
autosamplerLog2 = """   Print Date: 2008/08/13   10:04:35
   Site Name: CTC, System Name: PAL, System SNo: 142218

   2008/08/13  10:02:22 Job 01 started: Method 5ulMethd
                        Tray MT1-Frnt, Vial 1-3, Count = 1, Increment = 1
               10:02:43 Sample 1 Injected
               10:03:14 Sample 2 Injected
               10:03:46 Sample 3 Injected
|
"""

def parseAutosamplerLog(logText):
    logString = logText.split("\n")
    logDate = logString[0].strip().split()[-2]
    logTime = logString[0].strip().split()[-1]
    injTime = "00:00:00"
    sampleNum = -1
    trayName = "Unknown"
    jobNum = -1
    methodName = "Unknown"
    
    sampleLineNum = -1
    try:
        while True:
            injLine = logString[sampleLineNum].strip().split()
            if len(injLine) == 4:
                if injLine[1] == "Sample" and injLine[3]=="Injected":
                    injTime = injLine[0]
                    sampleNum = int(injLine[2])
                    break
            sampleLineNum -= 1
        while True:
            trayLine = logString[sampleLineNum].strip().split()
            if trayLine and trayLine[0]=="Tray":
                trayName = trayLine[1]
                break
            sampleLineNum -= 1
        while True:
            jobLine = logString[sampleLineNum].strip().split()
            if len(jobLine) >= 7:
                if jobLine[2] == "Job" and jobLine[4] == "started:":
                    jobNum = int(jobLine[3])
                    if jobLine[5] == "Method":
                        methodName = jobLine[6]
                    break
            sampleLineNum -= 1
    except:
        pass            
    return logDate, logTime, injTime, sampleNum, jobNum, methodName


class TestLogParser(unittest.TestCase):
    def testBasic1(self):
        logDate,logTime,injTime,sampleNum,jobNum,methodName = parseAutosamplerLog(autosamplerLog1)
        self.assertEqual(logDate,"2008/08/13")
        self.assertEqual(logTime,"10:04:35")
        self.assertEqual(injTime,"10:04:17")
        self.assertEqual(sampleNum,1)
        self.assertEqual(jobNum,4)
        self.assertEqual(methodName,"5ulMethd")
    def testBasic2(self):
        logDate,logTime,injTime,sampleNum,jobNum,methodName = parseAutosamplerLog(autosamplerLog2)
        self.assertEqual(logDate,"2008/08/13")
        self.assertEqual(logTime,"10:04:35")
        self.assertEqual(injTime,"10:03:46")
        self.assertEqual(sampleNum,3)
        self.assertEqual(jobNum,1)
        self.assertEqual(methodName,"5ulMethd")
        
if __name__ == "__main__":
    unittest.main()
            
