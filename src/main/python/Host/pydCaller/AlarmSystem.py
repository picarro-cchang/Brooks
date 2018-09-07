from Host.AlarmSystem.AlarmSystem import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "AlarmSystem"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()