# Utility to rebroadcast a data manager stream to InfluxDB

import sys
import time

from influxdb import InfluxDBClient


class InfluxDBWriter(object):
    def __init__(self, address, dbase_name, batch_size=50, write_interval=2):
        self.client = InfluxDBClient(host=address)
        self.batch_size = batch_size
        self.dbase_name = dbase_name
        self.write_interval = write_interval
        if dbase_name not in self.client.get_list_database():
            self.client.create_database(dbase_name)
        self.client.switch_database(dbase_name)
        self.last_write = time.time()

    def run(self, data_gen):
        data = []
        for datum in data_gen():
            if datum is not None:
                data.append(datum)
            if len(data) > self.batch_size or datum is None or time.time() - self.last_write > self.write_interval:
                if data:
                    while True:
                        try:
                            self.client.write_points(data, time_precision='ms', database=self.dbase_name)
                            self.last_write = time.time()
                            break
                        except:
                            time.sleep(5.0)
                            sys.stderr.write("x")
                    sys.stderr.write(".")
                    data = []
        sys.stderr.write('\n')
