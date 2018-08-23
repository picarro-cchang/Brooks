APP_NAME = "DataManager"

import sys
import traceback
from Host.DataManager.DataManager import main
from Host.Common.EventManagerProxy import *
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    try:
        main()
    except:
        LogExc("Unhandled exception trapped by last chance handler")
    Log("Exiting program")
    sys.stdout.flush()