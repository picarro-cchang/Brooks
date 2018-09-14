from Host.InstMgr.InstMgr import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "InstMgr"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()