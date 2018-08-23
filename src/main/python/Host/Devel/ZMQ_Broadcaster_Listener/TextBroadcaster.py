# TextBroadcaster.py

from Broadcaster import Broadcaster

if __name__ == "__main__":
    from datetime import datetime
    from time import sleep
        
    def myLog(msg):
        print msg
    b = Broadcaster(8881,logFunc=myLog,sendHwm=10)
    while True:
        b.send("%s\n" % datetime.now().strftime("%A, %d %B %Y %H:%M:%S.%f"))
        sleep(0.1)
