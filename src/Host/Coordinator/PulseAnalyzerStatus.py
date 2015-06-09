# PulseAnalyzerStatus.py

#from Host.Common import CmdFIFO


class PulseAnalyzerStatus(object):
    def __init__(self, logFunc=None):
        self.source = None
        self.concNameList = None
        self.args = None
        self.kwargs = None
        self.active = False
        self.nextDataBad = False

        if logFunc is not None:
            self.logFunc = logFunc
        else:
            self.logFunc = self.localLog

    def isActive(self):
        return self.active

    def setActive(self, active):
        self.active = active

    def setConfiguration(self, source, concNameList, *args, **kwargs):
        self.source = source
        self.concNameList = concNameList
        self.args = args
        self.kwargs = kwargs

        # Make sure proper defaults used if not passed in the configuration
        defaults = { "targetConc": None,
                     "thres1Pair": [0.0, 0.0],
                     "thres2Pair": [0.0, 0.0],
                     "triggerType": "in",
                     "waitTime": 0.0,
                     "validTimeAfterTrigger": 0.0,
                     "validTimeBeforeEnd": 0.0,
                     "timeout": 0.0,
                     "bufSize": 500,
                     "numPointsToTrigger": 1,
                     "numPointsToRelease": 1,
                     "armCond": None
                   }

        for key in defaults:
            if key not in self.kwargs:
                self.kwargs[key] = defaults[key]
                #self.logFunc("%s not set, setting to default '%s'\n" % (key, str(defaults[key])))
            else:
                #self.logFunc("using input arg '%s' = '%s'\n" % (key, str(self.kwargs[key])))
                pass

    def printConfiguration(self):
        self.logFunc("------------------\n")
        self.logFunc("printConfiguration:\n")
        self.logFunc("  source= %s\n" % self.source)
        self.logFunc("  concNameList=%s\n" %str(self.concNameList))
        self.logFunc("  args=%r\n\n" % self.args)
        self.logFunc("  kwargs=%s\n" % str(self.kwargs))
        self.logFunc("------------------\n")

    def configuration(self):
        return (self.source, self.concNameList, self.args, self.kwargs)

    def setNextDataBad(self):
        self.nextDataBad = True

    def isNextDataBad(self):
        return self.nextDataBad

    def clearNextDataBad(self):
        self.nextDataBad = False
        pass

    def localLog(self, *args, **kwargs):
        # logging function called if no logger passed
        pass