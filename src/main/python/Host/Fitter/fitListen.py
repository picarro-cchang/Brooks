from Host.autogen import interface
from Host.Common import StringPickler, Listener
from Host.Common.SharedTypes import BROADCAST_PORT_FITTER_BASE
from Queue import Queue

if __name__ == "__main__":
    spectQueue = Queue(0)
    spectListener = Listener.Listener(spectQueue,
                                      int(raw_input('Fitter broadcast port? ')),
                                      StringPickler.ArbitraryObject,
                                      retry = True,
                                      name = "Fitter listener")
    while True:
        print spectQueue.get()