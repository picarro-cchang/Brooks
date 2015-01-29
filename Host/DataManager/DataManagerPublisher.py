"""
Copyright 2014, Picarro Inc.
"""

import calendar
import time

import zmq
import json

import Queue
from Host.Common import Listener
from Host.Common import SharedTypes
from Host.Common import StringPickler
from Host.Common import AppStatus
from Host.Common import EventManagerProxy as EventManager

EventManager.EventManagerProxy_Init('DataManagerPublisher')

class DataManagerPublisher(object):

    def __init__(self):
        self.context = zmq.Context()

        self.broadcastSocket = self.context.socket(zmq.PUB)
        self.broadcastSocket.bind("tcp://127.0.0.1:%d" % SharedTypes.TCP_PORT_DATAMANAGER_ZMQ_PUB)

        self.queue = Queue.Queue()
        self.listener = Listener.Listener(self.queue, SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                          StringPickler.ArbitraryObject,
                                          streamFilter=self.jsonifyMeasurements, retry=True)
        #self.instrumentStatusListener = Listener.Listener(self.queue, SharedTypes.STATUS_PORT_INST_MANAGER,
        #                                                  AppStatus.STREAM_Status,
        #                                                  streamFilter=self.jsonifyStatus, retry=True)

    def run(self):
        try:
            while True:
                msgs = self.queue.get()
                for m in msgs:
                    #print m
                    self.broadcastSocket.send_string("%s" % m)

        finally:
            self.broadcastSocket.close()
            self.context.term()
            self.listener.stop()

    def jsonifyMeasurements(self, entry):
        source = entry['source']
        if source == 'Sensors' or source == 'analyze_FBDS':
            if 'species' in entry['data'] and (entry['data']['species'] == 0.0 or entry['data']['species'] == "0.0"):
                print "Rejected species 0"
                return None
            return [{'type': 'measurement'}, {'mode': entry['mode']}, json.dumps(entry['data'])]
        elif source == 'parseGPS' or source == 'parseGillAnemometer':
            entry['data']['EPOCH_TIME'] = entry['time']
            return [{'type': 'gps' if source == 'parseGPS' else 'anemometer' }, json.dumps(entry['data'])]
        else:
            #print "Skip %s" % entry['source']
            return None

    def jsonifyStatus(self, entry):
        # Status messages do not contain timestamps!
        epochTime = calendar.timegm(time.gmtime())

        if self.lastInstrumentStatus == entry.status:
            return None

        result = json.dumps({'type': 'inst_status', 'data': {'timestamp': epochTime, 'status': entry.status}})
        print result
        self.lastInstrumentStatus = entry.status
        return result

if __name__ == "__main__":
    pub = DataManagerPublisher()
    pub.run()
