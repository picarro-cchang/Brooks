from Host.CommandInterface.CommandInterface import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "CommandInterface"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    main()
