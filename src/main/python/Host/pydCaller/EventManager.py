from Host.EventManager.EventManager import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "EventManager"
EventManagerProxy_Init(APP_NAME)


if __name__ == "__main__":
    main()
