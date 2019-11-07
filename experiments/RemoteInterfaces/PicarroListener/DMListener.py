# Utility to rebroadcast a data manager stream to InfluxDB

import queue as Queue
import sys
import time
from datetime import datetime, timedelta, tzinfo

import CmdFIFO
import StringPickler
from Listener import Listener

queue = Queue.Queue(200)
ip = "192.168.56.103"

listener = Listener(host=ip,
                    queue=queue,
                    port=40060,
                    elementType=StringPickler.ArbitraryObject,
                    retry=True,
                    name="Sensor stream listener")

while True:
    try:
        obj = queue.get(timeout=5.0)
        print(obj)
    except Queue.Empty:
        continue
    except Exception:
        import traceback
        print(traceback.format_exc())
