
from Host.EventManager.EventInfo import EventInfo
from Host.Common import SharedTypes #to get the right TCP port to use
import time

DEFAULT_EVENT_CODE = 0

class EventLog(object):
    """Adds additional info required to record an occurrence of a single event.

    The actual event information is in the contained Event member (type EventInfo).

    Full events can be created on the fly by defining the event with all of the
    constructor args of this class (avoid using verbose if possible).

    To record an event of a pre-defined type (EventInfo instance), pass in the
    instance as the Description argument.

    Special EventLog properties over and above EventInfo are:

      Index     = The log entry # (starting at 1)
      Source    = Which application logged the event
      EventTime = The best guess at when the event occured. Options for this are
                  (in order of preference):
                      1. The client who requested the log sent a time
                      2. The time at which the RPC server dispatcher received
                         the log request
                      3. The LogTime (see below)
      LogTime   = The time at which the log entry is actually made.
      Data      = Data for the particular event occurrence.  eg: an event type
                  of 'Application started' might have data of 'CustomerGUI'. This
                  can be any data type, but a dict is recommended.

    There can be some lag between EventTime and LogTime (eg: if the logger is
    archiving, or if it is slow due to lower priority), and this is stored as
    the _LogLag attribute.

    NOTE: a nice thing is that no matter what the time stamps are, the rpc
    server implementation (and tcp queue) always ensures that events are
    serialized in order of receipt.

    The reason that EventLogger does not derive from EventInfo (which originally
    made sense) is to allow arbitrary pre-definition of event types.  Making
    EventInfo a member makse this easy.
    """

    InstanceCounter = 0 #for counting an index for all instances
    def __init__(self, Source,
                 Description = None,
                 Data = "",
                 Level = 1,
                 Code = DEFAULT_EVENT_CODE,
                 AccessLevel = SharedTypes.ACCESS_PICARRO_ONLY,
                 VerboseDescription = "",
                 EventTime = 0):
        EventLog.InstanceCounter += 1
        self.Index = self.InstanceCounter
        self.Data = Data
        self.Source = Source
        self.LogTime = time.time() #time at which the logger received the event
        #self.Time = SourceTime or time.time()
        self.EventTime = EventTime or self.LogTime #best guess at the event time
        self._LogLag = self.LogTime - self.EventTime

        if isinstance(Description, EventInfo):
            self.Event = Description
        else:
            #Should be a string, but if not we're going to interpret it as a string...
            self.Event = EventInfo(str(Description), Level = Level, Data = Data, Code = Code, AccessLevel = AccessLevel, VerboseDesc = VerboseDescription)

        assert isinstance(self.Event, EventInfo) #for Wing

    def __str__(self):
        timeStr = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.EventTime))
        ret = "%4s | %s | %-10s | %s" % (self.Index, timeStr, self.Source, self.Event)
        if self.Data:
            ret += ": %s" % (self.Data)
        return ret