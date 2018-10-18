from Host.DataManager.DataManager import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "DataManager"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()