import getopt
import sys
from collections import deque
from Driver.DummyDriver import Driver
from Host.DataManager import ScriptRunner
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.DataManager.DataManager import MeasTuple

ANALYSIS_HISTORY_MAX_LENGTH = 10

class AlarmScriptTester(object):
    def __init__(self, alarmScriptFile, configPath):
        ScriptRunner.alarmGlobals = {}
        self.DriverProxy = Driver()
        self.ReportHistory = {}
        self.AnalysisHistory = ANALYSIS_HISTORY_MAX_LENGTH
        with file(alarmScriptFile, "r") as fh:
            sourceString = fh.read()
        if sys.platform == 'win32':
            sourceString = sourceString.replace("\r","")
        self.alarmScriptCodeObj = compile(sourceString, alarmScriptFile, "exec")
        self.alarmParamsDict = CustomConfigObj(configPath)
        self.maxNumAlarmWords = -1
        for section in self.alarmParamsDict:
            if "word" in self.alarmParamsDict[section]:
                self.maxNumAlarmWords = max(self.maxNumAlarmWords, int(self.alarmParamsDict[section]["word"]))
        self.maxNumAlarmWords += 1

    def runScript(self, SourceTime_s, reportDict):
        self._AddToHistory(self.ReportHistory, reportDict, SourceTime_s)
        return ScriptRunner.RunAlarmScript( ScriptCodeObj = self.alarmScriptCodeObj,
                                            SourceTime_s = SourceTime_s,
                                            AlarmParamsDict = self.alarmParamsDict,
                                            ReportDict = reportDict,
                                            ReportHistory = self.ReportHistory,
                                            SensorHistory = {},
                                            DriverRpcServer = self.DriverProxy,
                                            InstrumentStatus = 0,
                                            MeasSysRpcServer = None,
                                            FreqConvRpcServer = None,
                                            SpecCollRpcServer = None,
                                            PeriphIntrfFunc = None,
                                            PeriphIntrfCols = [],
                                            ExcLogFunc = sys.stdout.write,
                                            numAlarmWords = self.maxNumAlarmWords)

    def _AddToHistory(self, HistoryDict, DataDict, DataTime):
        for k in DataDict.keys():
            if not HistoryDict.has_key(k):
                #fifo'ing happening more than access, so a deque should be better than a list (I think)...
                HistoryDict[k] = deque()
            HistoryDict[k].append(MeasTuple((DataTime, DataDict[k])))
            #make sure the history is no larger than requested
            if len(HistoryDict[k]) > self.AnalysisHistory:
                HistoryDict[k].popleft()

HELP_STRING = \
"""\
AlarmSystemTester.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h              Print this help.
-s              Specify a AlarmSystem script.  
"""

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt
    alarmConfigFile = None
    shortOpts = 'hs:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    executeTest = False
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()
    else:
        if "--test" in options:
            executeTest = True

    #Start with option defaults...
    scriptFile = ""

    if "-s" in options:
        scriptFile = options["-s"]
        print "Script file specified at command line: %s" % scriptFile
    
    return (scriptFile)