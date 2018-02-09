"""
EventStore
EventStore is a class to collect event log messages broadcasted by the EventManager.
EventStore should be instantiated by each process that wants to monitor events logs.

Call getQueuedEvents() periodically to load the queue with event messages.
Call getEvent() to get individual messages. You have to track indicies to get
unique messages in the correct order.
"""
import sys
import Queue
import collections
from Host.Common import TextListener
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
from Host.Common.SharedTypes import BROADCAST_PORT_EVENTLOG

# Name of file importing this module.
APP_NAME = sys.argv[0]
EventManagerProxy_Init(APP_NAME,DontCareConnection = True)

class EventStore(object):
    def __init__(self,config):
        self.config = config
        self.loadConfig()
        self.queue = Queue.Queue()
        self.listener = TextListener.TextListener(self.queue,
                                                  BROADCAST_PORT_EVENTLOG,
                                                  retry = True,
                                                  name = "QuickGUI event log listener", logFunc = Log)
        self.eventDeque = collections.deque()
        self.firstEvent = 0

    def loadConfig(self):
        self.maxEvents = self.config.getint('EventManagerStream','Lines')

    def getQueuedEvents(self):
        n = self.maxEvents
        while True:
            try:
                line = self.queue.get_nowait()
                index,time,source,level,code,desc = [s.strip() for s in line.split("|",6)]
                date,time = [s.strip() for s in time.split()]
                eventTuple = (int(index),date,time,source,float(level[1:]),int(code[1:]),desc)
                # Level 1.5 = info only; message shows on both GUI and EventLog
                if eventTuple[4] >= 1.5:
                    self.eventDeque.append(eventTuple)
                while len(self.eventDeque) > n:
                    self.eventDeque.popleft()
                    self.firstEvent += 1
            except Queue.Empty:
                return

    def getFirstEventIndex(self):
        return self.firstEvent

    def getMaxEvents(self):
        return self.maxEvents

    def getEventCount(self):
        return len(self.eventDeque)

    def getEvent(self,item):
        if item<self.firstEvent:
            return None
        else:
            return self.eventDeque[item-self.firstEvent]