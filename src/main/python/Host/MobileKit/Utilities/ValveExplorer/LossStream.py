"""
Copyright 2012, Picarro Inc.

Wrapper around the relevant measurement stream for the Valve Explorer:
ProcessedLoss1.
"""

from __future__ import with_statement

import pprint
import threading

#pylint: disable=W0401,W0614
from Host.autogen.interface import *
#pylint: enable=W0401,W0614
from Host.Common import SharedTypes
from Host.Common import Listener


class LossStream(object):
    """
    Provide a stream of ProcessedLoss1 values.
    """

    def __init__(self, filterCb=None):
        """
        filterCb is called any time a filtered data point appears
        unless filterCb is None. filterCb should take three arguments:
        stream type, timestamp in milliseconds and ProcessedLoss1
        value.
        """
        self.filterCb = filterCb

        # The listener filter callback, which is running on a
        # different thread, needs to check the stream status, which
        # itself is toggled from a different thread.
        self.lock = threading.Lock()
        self.isActive = False

        self.listener = Listener.Listener(
            queue=None,
            port=SharedTypes.BROADCAST_PORT_SENSORSTREAM,
            elementType=SensorEntryType,
            streamFilter=self._streamFilter)

    def _streamFilter(self, data):
        """
        Invoke the callback whenever we find a ProcessedLoss1 value.
        """

        with self.lock:
            isActive = self.isActive

        if isActive and data.streamNum == STREAM_ProcessedLoss1:
            if self.filterCb is not None:
                self.filterCb(STREAM_ProcessedLoss1, data.timestamp,
                              data.value)

    def start(self):
        with self.lock:
            self.isActive = True

    def stop(self):
        with self.lock:
            self.isActive = False