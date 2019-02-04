from Host.FileEraser.FileEraserSimplified import main
from Host.Common.EventManagerProxy import EventManagerProxy_Init

APP_NAME = "FileEraserSimplified"
EventManagerProxy_Init(APP_NAME)

if __name__ == "__main__":
    """
    Import main from APP_NAME. This ensures our processes launch with
    the same method regardless of called directly or via this pydCaller
    """
    main()
