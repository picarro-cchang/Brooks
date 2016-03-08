APP_NAME = "AlarmSystemLegacyStub"

import sys
import traceback
from Host.AlarmSystem.AlarmSystem import main
from Host.Common.EventManagerProxy import Log, LogExc, EventManagerProxy_Init

EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    try:
        main()
    except:
        tbMsg = traceback.format_exc()
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = tbMsg)
    Log("Exiting program")
    sys.stdout.flush()