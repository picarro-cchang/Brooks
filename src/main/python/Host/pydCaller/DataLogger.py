APP_NAME = "DataLogger"
import time
import sys
import traceback
from Host.DataLogger.DataLogger import main
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    DEBUG = __debug__
    try:
        # workaround for exception: AttributeError: _strptime_time
        # time.strptime() is not thread-safe
        # details: http://code-trick.com/python-bug-attribute-error-_strptime/
        time.strptime(time.ctime())
        main()
    except:
        tbMsg = traceback.format_exc()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
    Log("Exiting program")
    sys.stdout.flush()