APP_NAME = "MeasSystem"

import sys
import traceback
from Host.MeasSystem.MeasSystem import main
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    try:
        #profile.run("main()","c:/temp/measSystemProfile")
        main()
    except:
        Log("Unhandled exception trapped by last chance handler",
            Data = dict(Note = "<See verbose for debug info>"),
            Level = 3,
            Verbose = traceback.format_exc())
    Log("Exiting program")
    sys.stdout.flush()
