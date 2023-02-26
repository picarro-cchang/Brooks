import time
from Host.autogen import interface
from Host.Common.SharedTypes import BROADCAST_PORT_RDRESULTS, BROADCAST_PORT_RD_RECALC, BROADCAST_PORT_RD_UNIFIED
from Host.Common.Listener import Listener
from Host.Common import StringPickler

def Log(msg):
    print(msg)

def myfilt(d):
    print(d.modeIndex)

def main():
    rdListener = Listener(queue=None,
                          port=BROADCAST_PORT_RDRESULTS,
                          streamFilter=myfilt,
                          elementType=interface.RingdownEntryType,
                          retry=True,
                          name="PZTCal",
                          logFunc=Log)
    time.sleep(10.0)

if __name__== "__main__":
    main()