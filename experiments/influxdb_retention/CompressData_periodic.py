import math
import time
from influxdb import InfluxDBClient
from experiments.LOLogger.LOLoggerClient import LOLoggerClient

# https://influxdb-python.readthedocs.io/en/latest/api-documentation.html#influxdb.InfluxDBClient.close


def generate_duration_ms(duration):
    ms_map = {"s":1000,
              "m":1000*60,
              "h":1000*60*60,
              "d":1000*60*60*24}
    return int(duration[:-1]) * ms_map[duration[-1]]

class DB_DECIMATOR(object):
    def __init__(self,
                 host,
                 port,
                 db_name,
                 logger=None,
                 master_measurement="crds",
                 time_sleep=5):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.master_measurement = master_measurement
        self.time_sleep = time_sleep
        self.client = InfluxDBClient(host=self.host, port=self.port)

        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(client_name=self.__class__.__name__, verbose=True)

        self.durations = ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "24h"]
        self.durations_ms = [generate_duration_ms(d) for d in self.durations]
        self.durations_map = [list(a) for a in zip(self.durations[:-1], self.durations[1:], self.durations_ms[1:])]


    def run(self):
        # check if db exists
        if self.db_name not in [result["name"] for result in self.client.get_list_database()]:
            self.logger.error(f"Database {self.db_name} not found, exiting")
            raise ValueError(f"Database {self.db_name} not found, exiting")
        self.client.switch_database(self.db_name)

        while True:
            dest_duration_ms = self.durations_ms[0]
            start_time_ms, stop_time_ms, last_recorded_timestamp = self.get_start_stop_last(self.master_measurement, dest_duration_ms)

            if stop_time_ms > start_time_ms:
                # time to decimate has come

                # first, decimate raw data
                self.logger.debug(f'Decimating to: {dest_duration_ms} ms, from {start_time_ms} ms to {stop_time_ms} ms')
                self.compress_raw_data(start_time_ms, stop_time_ms) # we can do it for all fields at once this way

                # then, in a loop, decimate all smaller resolutions if needed
                for src_duration, dest_duration, dest_duration_ms in self.durations_map:
                    src_meas = f"{self.master_measurement}_{src_duration}" 
                    dest_meas = f"{self.master_measurement}_{dest_duration}"

                    start_time_ms, stop_time_ms, last_recorded_timestamp = self.get_start_stop_last(src_meas, dest_duration_ms)

                    if last_recorded_timestamp is None or stop_time_ms <= start_time_ms:
                        break
                    self.logger.debug(f'Decimating to: {dest_duration_ms} ms, from {start_time_ms} ms to {stop_time_ms} ms')
                    for field_key, field_type in self.get_field_keys(self.master_measurement):  #here we need to do it for each field
                        if field_type in ['float', 'integer']:
                            err, comp_time = self.compress_measurement(src_meas= src_meas,
                                                                       dest_meas= dest_meas,
                                                                       field_key= field_key,
                                                                       duration= dest_duration,
                                                                       start_time_ms= start_time_ms,
                                                                       stop_time_ms=stop_time_ms)

                    self.record_decimation_timestamp(timestamp=stop_time_ms, src_meas=src_meas)
            time.sleep(self.time_sleep)

    def get_start_stop_last(self, src_measurement, dest_duration_ms):
        last_recorded_timestamp = self.get_last_recorded_timestamp(src_measurement)
        start_time_ms = self.get_last_decimation_timestamp(src_measurement)
        stop_time_ms = int(dest_duration_ms * math.floor(last_recorded_timestamp / dest_duration_ms))
        return start_time_ms, stop_time_ms, last_recorded_timestamp

    def compress_raw_data(self, start_time_ms, stop_time_ms):
        query = f"""SELECT   Min(*), 
                             Max(*), 
                             Mean(*), 
                             Count(*) 
                    INTO     crds_15s 
                    FROM     crds 
                    WHERE    time>={start_time_ms}ms 
                    AND      time<{stop_time_ms}ms
                    GROUP BY time(15s), *"""
        rs = self.client.query(query)
        self.record_decimation_timestamp(timestamp=stop_time_ms, src_meas="crds")

    def get_last_recorded_timestamp(self, measurement):
        # i feel like this should be just a query grabbing time, not entire point, TODO
        query = f"""SELECT   (*) 
                    FROM     {measurement} 
                    ORDER BY time DESC limit 1"""
        rs = self.client.query(query, epoch='ms')
        for key, gen in rs.items():
            for row in gen:
                return (row["time"])

    def get_field_keys(self, measurement):
        query = f"""SHOW FIELD KEYS FROM {measurement}"""
        rs = self.client.query(query)
        return [(row["fieldKey"], row["fieldType"]) for key, row_gen in rs.items() for row in row_gen]

    def get_last_decimation_timestamp(self, measurement):
        query = f"""SELECT last_decimation 
                    FROM   crds_workspace 
                    WHERE  meas_name = '{measurement}' 
                    ORDER  BY time DESC 
                    LIMIT  5 """
        rs = self.client.query(query)
        last_decimations = [row["last_decimation"] for key, row_gen in rs.items() for row in row_gen]
        return last_decimations[0] if last_decimations else 0

    def record_decimation_timestamp(self, timestamp, src_meas):
        self.client.write_points([{
                    "measurement": "crds_workspace",
                    "fields": {
                        "last_decimation": int(timestamp)
                    },
                    "tags": {
                        "meas_name": src_meas
                    }
                }])

    def compress_measurement(self, 
                             src_meas, 
                             dest_meas, 
                             field_key, 
                             duration, 
                             start_time_ms, 
                             stop_time_ms):
        start = time.time()
        # calculate total sum of each measurement of the small time period
        subquery3 = f"""SELECT   ("mean_{field_key}"*"count_{field_key}") AS tot, 
                                 "count_{field_key}"                      AS count, 
                                 "max_{field_key}"                        AS max, 
                                 "min_{field_key}"                        AS min 
                        FROM     {src_meas} 
                        WHERE    time>={start_time_ms}ms 
                        AND      time<{stop_time_ms}ms 
                        GROUP BY *"""
        # group total sums by time and calculate total sum of the big time period
        subquery2 = f"""SELECT   Sum(tot)   AS sum_tot, 
                                 Sum(count) AS sum_count, 
                                 Max(max)   AS max, 
                                 Min(min)   AS min 
                        FROM     ({subquery3}) 
                        GROUP BY time({duration}), *"""
        # calculate mean of the big time period and put it in bigger period table
        subquery1 =f"""SELECT   sum_tot/sum_count AS "mean_{field_key}", 
                                sum_count         AS "count_{field_key}", 
                                min               AS "min_{field_key}", 
                                max               AS "max_{field_key}" 
                        INTO      {dest_meas} 
                        FROM     ({subquery2}) 
                        GROUP BY *"""
        rs = self.client.query(subquery1)
        return rs.error, time.time() - start



if __name__ == "__main__":
    db_decimator = DB_DECIMATOR(host="localhost",port="8086",db_name="pigss_sim_data")
    db_decimator.run()

#todo
#   cli
#   head/tail? is it even a problem?
#   test on real data when there will be one
#   time_since_valve_change
#   sql injection prevention and other bulletproof
#   change logs to more human readable
#   dockstrings

# questions:
# rpc server here? i think yes since in the beginning of the rack lifespan those settings will be twicked a lot, and then never used for decade or so
# retention policies? do manual delete or set influx policies? if second, who is responcible?
# store settings in a file or rely on zookeeper to pass it everytime
# a request to see data on edge of available resolition?
# measure performance, memory leaks and such

