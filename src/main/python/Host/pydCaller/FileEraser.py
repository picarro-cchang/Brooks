import traceback
from Host.FileEraser.FileEraser import main

if __name__ == "__main__":
    try:
        main()
    except:
        tbMsg = traceback.format_exc()
        print "Unhandled exception trapped by last chance handler"
        print "%s" % (tbMsg, )
