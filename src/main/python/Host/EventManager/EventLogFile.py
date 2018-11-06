

import time
import os
from Host.EventManager.EventLog import EventLog

LOGFILE_PREFIX = "EventLog_"
LOGFILE_EXTENSION = "txt"

class EventLogFile(object):
    """Class to manage writing (and reading) of event logs to disk."""
    #TODO: Implement reading
    FORMAT_VERSION = 1

    def __init__(self, LogDir, TimeStandard="gmt"):
        self.NumWrittenEvents = 0
        self.LogDir = LogDir
        self.LogPath = ""
        self.TimeStandard = TimeStandard
        if self.TimeStandard.lower() == "local":
            self.maketimetuple = time.localtime
        else:
            self.maketimetuple = time.gmtime

    def _CreateNewLogFilePath(self):
        """Creates a new log file named with the current time stamp and with a version header."""
        if self.TimeStandard.lower() == "local":
            timeStr = time.strftime("%Y_%m_%d_%H_%M_%S",self.maketimetuple())
        else:
            timeStr = time.strftime("%Y_%m_%d_%H_%M_%SZ",self.maketimetuple())

        fname = "%s%s.%s" % (LOGFILE_PREFIX,
                             timeStr,
                             LOGFILE_EXTENSION)
        self.LogPath = os.path.join(self.LogDir, fname)
        fp = file(self.LogPath, "w")
        fp.write("v%s\n" % self.FORMAT_VERSION)
        fp.close()

    def WriteEvent(self, AnEventLog):
        """Writes a string representation of the provided event log to disk."""
        assert isinstance(AnEventLog, EventLog)
        el = AnEventLog #character saver
        timeStr = time.strftime("%Y-%m-%d %H:%M:%S",self.maketimetuple(el.EventTime))
        summaryLine = "%s\t%s\t%s\tL%s\tC%s\t%s" % (el.Index,
                                                    timeStr,
                                                    el.Source,
                                                    el.Event.Level,
                                                    el.Event.Code,
                                                    el.Event.Description)
        if el.Data:
            summaryLine += " : %s" % (el.Data,)

        if not self.LogPath:
            self._CreateNewLogFilePath()
        fp = file(self.LogPath, "a")
        fp.write("%s\n" % summaryLine)
        if el.Event.VerboseDescription:
            verboseList = el.Event.VerboseDescription.splitlines()
            #print "verboseList = %r" % verboseList
            fp.write("~~ VERBOSE ~~ (%s)\n" % len(verboseList))
            for line in verboseList:
                fp.write("%s\n" % line) #Doing this rather than writelines and keepends to ensure terminating \n
            fp.write("~~ END VERBOSE ~~\n")
        fp.close()
        self.NumWrittenEvents += 1