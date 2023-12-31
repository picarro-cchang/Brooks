from Host.QuickGui.QuickGui import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "QuickGui"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    """
    Import main from Driver. This ensures our processes launch with
    the same method regardless of called directly or via this pydCaller
    """
    main()
