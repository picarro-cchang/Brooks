
from Host.Common import SharedTypes #to get the right TCP port to use
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_LOGGER, ACCESS_PICARRO_ONLY
from Host.EventManager.EventLog import EventLog

import traceback
import sys
import os
import time
import threading
import signal

# Get the EventManagerProxy min_ms_interval value from an environmental
# variable. If it doesn't exist, fall-back to a safe default.
try:
    min_ms_interval = os.environ['EVENT_MANAGER_PROXY_MIN_MS_INTERVAL']
except KeyError:
    min_ms_interval = 10


class EventManagerProxyWithBuffer:

    def __init__(self, application_name,
                           dont_care_connection = True,
                           print_everything = False,
                           min_ms_interval = min_ms_interval,
                           buffer_size = 10,
                           buffer_periodical_flush_timing_ms=10.0):

        # clean exit event
        import atexit
        atexit.register(self._exit)

        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

        self.event_log_list = []
        self.print_everything = print_everything
        self.buffer_size = buffer_size
        self.application_name = application_name
        self.buffer_lock = threading.RLock()
        self.buffer_periodical_flush_timing = (buffer_periodical_flush_timing_ms/1000.0)
        self.__event_manager_proxy = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_LOGGER,
                                                              application_name,
                                                              IsDontCareConnection=dont_care_connection,
                                                              min_ms_interval=min_ms_interval)
        self.timer_thread = threading.Thread(target=self._timer_log)
        self.timer_thread.daemon = True
        self.thread_running = True
        self.timer_thread.start()

    def _timer_log(self):
        """
        thread will loop until exited. Main purpose of this thread is
        for user given interval flush log messages
        :return:
        """
        while self.thread_running:
            time.sleep(self.buffer_periodical_flush_timing)
            self._buffer_lock_acquire()
            try:
                if len(self.event_log_list) > 0:
                    self._flush_log()
            finally:
                self._buffer_lock_release()

    def _buffer_lock_acquire(self):
        """Acquire lock on buffer (only if periodical flush is set)."""
        if self.buffer_lock:
            self.buffer_lock.acquire()

    def _buffer_lock_release(self):
        """Release lock on buffer (only if periodical flush is set)."""
        if self.buffer_lock:
            self.buffer_lock.release()

    def _create_event_log(self, Desc, Data="", Level=1, Code=-1, AccessLevel=SharedTypes.ACCESS_PICARRO_ONLY, Verbose="",
                        SourceTime=0, SourceNameOverride=None):
        # And the time that the dispatcher received the log (there may be some lag we
        # don't want if the log queue gets jammed while archiving or something)...
        #  - only do it this way if not provided by the caller...
        sourceTime = SourceTime or time.time()
        # print "s=", sourceTime
        thisEvent = EventLog(self.application_name,
                             Description=Desc,
                             Data=Data,
                             Level=Level,
                             Code=Code,
                             AccessLevel=AccessLevel,
                             VerboseDescription=Verbose,
                             EventTime=sourceTime
                             )
        return thisEvent

    def Log(self, Desc, Data=None, Level=1, Code=-1, AccessLevel=ACCESS_PICARRO_ONLY, Verbose="", SourceTime=0,
            LogInBuffer=False):
        """Short global log function that sends a log to the EventManager."""
        if __debug__:
            if self.print_everything or Level >= 2:
                print "*** LOGEVENT (%d) = %s; Data = %r" % (Level, Desc, Data)
                if Verbose:
                    print "+++ VERBOSE DATA FOLLOWS +++\n%s" % Verbose
        this_event = self._create_event_log(Desc, Data=Data, Level=Level, Code=Code, \
                                         AccessLevel=AccessLevel, Verbose=Verbose, SourceTime=SourceTime)
        self._buffer_lock_acquire()
        try:
            self.event_log_list.append(this_event)
            if len(self.event_log_list) >= self.buffer_size:
                self._flush_log()
        finally:
            self._buffer_lock_release()


    def LogExc(self, Msg="Exception occurred", Data={}, Level=2, Code=-1, AccessLevel=ACCESS_PICARRO_ONLY, SourceTime=0,
               LogInBuffer=False):
        """Sends a log of the current exception to the EventManager.

        Data must be a dictionary - exception info will be added to it.

        An advanced traceback is included as the verbose data.

        """
        excType, excValue, excTB = sys.exc_info()
        logDict = Data
        logDict.update(dict(Type=excType.__name__, Value=str(excValue), Note="<See verbose for debug info>"))
        # verbose = BetterTraceback.get_advanced_traceback(1)
        verbose = traceback.format_exc()
        self.Log(Msg, logDict, Level, Code, AccessLevel, verbose, SourceTime)

    def _exit(self):
        """Clean quit logging. Flush buffer. Stop the periodical thread if needed."""
        if self.thread_running:
            self.thread_running = False
        self._flush_log()

    def _flush_log(self):
        self._buffer_lock_acquire()
        try:
            self.__event_manager_proxy.LogEvents(self.event_log_list)
            self._empty_buffer()
        finally:
            self._buffer_lock_release()

    def _empty_buffer(self):
        """Empty the buffer list."""
        self._buffer_lock_acquire()
        try:
            del self.event_log_list
            self.event_log_list = []
        finally:
            self._buffer_lock_release()