# Utility to rebroadcast a data manager stream to InfluxDB

import queue as Queue
import sys
import time
from datetime import datetime, timedelta, tzinfo

from influxdb import InfluxDBClient

#from Host.autogen import interface
#from Host.Common import CmdFIFO, SharedTypes, StringPickler, timestamp
#from Host.Common.Listener import Listener
import CmdFIFO
import StringPickler
from Listener import Listener


ZERO = timedelta(0)
HOUR = timedelta(hours=1)


# A UTC class.
class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()


class InfluxDBWriter(object):
    def __init__(self, address, dbase_name, batch_size=50):
        self.client = InfluxDBClient(host=address)
        self.batch_size = batch_size
        self.dbase_name = dbase_name
        if dbase_name not in self.client.get_list_database():
            self.client.create_database(dbase_name)
        self.client.switch_database(dbase_name)

    def run(self, data_gen):
        data = []
        for datum in data_gen():
            if datum is not None:
                data.append(datum)
            if len(data) > self.batch_size or datum is None:
                if data:
                    while True:
                        try:
                            self.client.write_points(data, time_precision='ms', database=self.dbase_name)
                            break
                        except:
                            time.sleep(5.0)
                            #sys.stderr.write("x")
                            print('x', end='')
                    #sys.stderr.write(".")
                    print('.', end='')
                    data = []

ip = '10.100.3.53'
Driver = CmdFIFO.CmdFIFOServerProxy("http://%s:50010" % ip, ClientName="InfluxDBWriter")
try:
    curValDict = Driver.fetchLogicEEPROM()[0]
    print(curValDict)
#except Exception as err:
except Exception:
    import traceback
    print(traceback.format_exc)
    curValDict = {"Chassis": "NONE", "Analyzer": "NONE", "AnalyzerNum": "NONE"}
analyzer_name = curValDict["Analyzer"] + curValDict["AnalyzerNum"]
chassis = curValDict["Chassis"]

queue = Queue.Queue(200)
listener = Listener(
    host=ip,
    queue=queue,
    port=40060,
    elementType=StringPickler.ArbitraryObject,
    retry=True,
    name="Sensor stream listener")


def data_gen():
    # done = False
    tag_list = ['source', 'mode', 'ver', 'good']
    while True:
        try:
            obj = queue.get(timeout=5.0)
            data = {'measurement': 'crds', 'fields': {}, 'tags': {'analyzer': analyzer_name, 'chassis': chassis}}
            if 'time' in obj:
                data['time'] = datetime.fromtimestamp(obj['time'], tz=utc)
            for tag in tag_list:
                if tag in obj:
                    data['tags'][tag] = obj[tag]
            for field in obj['data']:
                data['fields'][field] = obj['data'][field]
            yield data
        except Queue.Empty:
            yield None
        except Exception:
            import traceback
            print(traceback.format_exc())
        
            #print('Unhandled exception: {}'.format(e))


if __name__ == "__main__":
    dmr = InfluxDBWriter("10.100.2.93", "test_data", batch_size=1)
    dmr.run(data_gen)
