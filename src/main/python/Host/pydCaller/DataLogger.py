from Host.DataLogger.DataLogger import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "DataLogger"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()
