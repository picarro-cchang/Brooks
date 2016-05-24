from Host.autogen import interface
from Host.Common import StringPickler, Listener
from Host.Common.SharedTypes import BROADCAST_PORT_SPECTRUM_COLLECTOR
from Queue import Queue

if __name__ == "__main__":
    spectQueue = Queue(0)
    spectListener = Listener.Listener(spectQueue,
                                      BROADCAST_PORT_SPECTRUM_COLLECTOR,
                                      StringPickler.ArbitraryObject,
                                      retry = True,
                                      name = "Fitter listener")
    while True:
        print spectQueue.get()