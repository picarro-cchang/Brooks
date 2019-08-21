import math
import time
import threading
import datetime
from influxdb import InfluxDBClient
from functools import cmp_to_key
from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from host.experiments.common.rpc_ports import rpc_ports
import host.experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO


# https://influxdb-python.readthedocs.io/en/latest/api-documentation.html#influxdb.InfluxDBClient.close



influx_comparison_operators = ["=","<>","!=",">",">=","<","<="]

default_durations = ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "24h"]
ms_map = {"s":1,
          "m":1*60,
          "h":1*60*60,
          "d":1*60*60*24}

def ghrdm(dest_duration_ms, start_time_ms, stop_time_ms): #generate_human_readable_decimation_message
    dest_duration_ms=generate_duration_timecode(int(dest_duration_ms/1000))
    start_time_ms/=1000
    stop_time_ms/=1000
    start_time_ms = datetime.datetime.fromtimestamp(start_time_ms).strftime('%Y-%m-%d %H:%M:%S')
    stop_time_ms = datetime.datetime.fromtimestamp(stop_time_ms).strftime('%Y-%m-%d %H:%M:%S')
    return f'Decimating to: {dest_duration_ms} sec, from {start_time_ms} ms to {stop_time_ms} ms'

def generate_duration_time(duration, ms=True):
    """Given duration time in form like '15s', '30m' or '16h', translate it to seconds or ms"""
    duration = int(duration[:-1]) * ms_map[duration[-1]]
    if ms:
        duration*=1000
    return duration

def generate_duration_timecode(duration):
    """Given duration as int of seconds, translate to a '15s', '30m' or '16h' form"""
    smallest_num = duration
    smallest_key = "s"
    for key in ms_map:
        if duration % ms_map[key] == 0:
            if smallest_num > duration/ms_map[key]:
                smallest_num = duration/ms_map[key]
                smallest_key = key
    return f"{int(smallest_num)}{smallest_key}"

def check_for_valid_duration(duration):
    """Check if passed argument is a valid duration of a form '15s', '30m' or '16h'"""
    return duration[:-1].isdigit() and duration[-1] in ms_map

def sort_durations(durations):
    """Given list of durations in a string form - sort it"""
    durations_in_seconds = [generate_duration_time(a, ms=False) for a in durations]
    durations_in_seconds.sort()
    durations = [generate_duration_timecode(a) for a in durations_in_seconds]
    return durations


class DBDecimator(object):
    """ 
        A Database Decimator class, like Heinrich Decimator (c.1544 – 1615), a German Protestant theologian,
        astronomer and linguist.
        It's purpose is to compress raw data from influxDB into data points with lower resolution, like
        instead of having data points for each second - data point for each 15 seconds, 1,5 or 15 minutes, etc.
        mulitple data resolutions allows more flixible data retention policies, for example: 
           delete raw data after 5 years, 
           delete 15s resolution data after 10 years, 
           delete 1m resolution data after 15 years, etc.
    """
    def __init__(self,
                 db_host_address,
                 db_port,
                 db_name,
                 rpc_server_port,
                 rpc_server_name="",
                 rpc_server_description="DB Decimator",
                 durations=None,
                 logger=None,
                 master_measurement="crds",
                 time_sleep=5,
                 raw_filter_conditions=None,
                 start=True):
        # DB params
        self.db_host_address = db_host_address
        self.db_port = db_port
        self.db_name = db_name
        self.master_measurement = master_measurement

        # how often loop will check for new decimation need
        self.time_sleep = time_sleep

        # RPC server params
        self.rpc_server_port = rpc_server_port
        self.rpc_server_name = rpc_server_name
        self.rpc_server_description = rpc_server_description

        # logger params
        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(client_name=self.__class__.__name__, verbose=True)

        # durations params
        if durations is None:
            self.durations = default_durations
        else:
            self.durations = durations
        self.generate_durations_meta()

        # raw filter params
        if raw_filter_conditions is None:
            self.raw_filter_conditions = []
        else:
            self.raw_filter_conditions = raw_filter_conditions

        # concurency stuff
        self.compression_in_progress_lock = threading.Lock()
        self.thread_created = False

        # RPC server
        self.server = CmdFIFO.CmdFIFOServer(("", self.rpc_server_port),
                                                ServerName=self.rpc_server_name,
                                                ServerDescription=self.rpc_server_description,
                                                threaded=True)
        self.register_rpc_functions()


        if start:
            self.start()

    def save_settings_to_file(self, filename):
        pass

    def load_settings_from_file(self, filename):
        pass

    def start(self):
        """A method to start the loop and the thread loop. """
        self.start_decimator_loop_thread()
        self.rpc_serve_forever()

    def generate_durations_meta(self):
        """Some routines around durations list"""
        self.durations = sort_durations(self.durations)
        self.durations_ms = [generate_duration_time(d) for d in self.durations]
        self.durations_map = [list(a) for a in zip(self.durations[:-1], self.durations[1:], self.durations_ms[1:])]

    def rpc_serve_forever(self):
        """
            Start RPC server and serve it forever.
            this is a blocking method - call once you are done setting tags
        """
        self.logger.info(f"Starting RPC server to serve forever")
        self.server.serve_forever()

    def start_decimator_loop_thread(self):
        """
            Method to start thread that will be compressing data
        """
        if not self.thread_created:
            self.DBDecimatorThread = DBDecimatorThread(parent=self,
                                                       db_name=self.db_name,
                                                       db_host_address=self.db_host_address,
                                                       db_port=self.db_port,
                                                       master_measurement=self.master_measurement,
                                                       # durations=self.durations,
                                                       time_sleep = self.time_sleep,
                                                       logger=self.logger)
            self.thread_created = True
            self.logger.info("DBDecimatorThread loop has started")
        else:
            self.DBDecimatorThread.unpause()

    def pause_decimator_loop_thread(self):
        """ Method use to pause compressing data loop. """

        if not self.thread_created:
            self.logger.error("can't stop thread, it doesn't exist yet")
            return
        if not self.DBDecimatorThread.is_paused():
            self.DBDecimatorThread.pause()
            self.logger.info("DBDecimatorThread loop is paused")
        else:
            self.DBDecimatorThread.unpause()
            self.logger.info("DBDecimatorThread loop is unpaused")

    def stop_decimator_loop_thread(self):
        """
        DEFINE AND TEST THIS!!!!
        """
        self.logger.info("Decimator instance closed")
        self.DBDecimatorThread.stop()
        self.thread_created = False

    def register_rpc_functions(self):
        """Register defined rpc functions"""
        self.server.register_function(self.start_decimator_loop_thread)
        self.server.register_function(self.pause_decimator_loop_thread)
        self.server.register_function(self.stop_decimator_loop_thread)

        self.server.register_function(self.get_durations)
        self.server.register_function(self.remove_durations)
        self.server.register_function(self.remove_all_durations)
        self.server.register_function(self.add_durations)

        self.server.register_function(self.get_raw_data_filter)
        self.server.register_function(self.remove_all_raw_data_filters)
        self.server.register_function(self.add_raw_data_filter)
        self.server.register_function(self.add_raw_data_filters)

    def check_for_valid_duration(self, duration):
        """Check if passed string is a valid duration"""
        return duration[:-1].isdigit() and duration[-1] in ms_map

    def get_durations(self):
        """Get list of current durations"""
        with self.compression_in_progress_lock:
            durations_return = self.durations.copy()
        return durations_return
        
    def remove_durations(self, durations):
        """
            Remove duration or durations from current decimation process.
            This will just stop generating those resolutions, already generated data will remain untouched.
        """
        if isinstance(durations, str):
            durations = [durations]
        removed_duraions = []
        with self.compression_in_progress_lock:
            for duration in durations:
                if duration in self.durations:
                    self.durations.remove(duration)
                    removed_duraions.append(duration)
            self.generate_durations_meta()
        self.logger.info(f"Durations {removed_duraions} has been removed")
        with self.compression_in_progress_lock:
            self.logger.info(f"New durations are {self.durations}")

    def remove_all_durations(self):
        """
            Remove all durations from current decimation process.
            This will just stop generating those resolutions, already generated data will remain untouched.
        """
        with self.compression_in_progress_lock:
            self.durations = []
            self.generate_durations_meta()
        self.logger.info(f"All durations for data compressing has been removed")

    def add_durations(self, durations):
        """
            Remove all durations from current decimation process.
            This will just stop generating those resolutions, already generated data will remain untouched.
        """
        if isinstance(durations, str):
            durations = [durations]
        added_durations = []
        with self.compression_in_progress_lock:
            for duration in durations:
                if check_for_valid_duration(duration):
                    self.durations.append(duration)
                    added_durations.append(duration)
            self.generate_durations_meta()
        self.logger.info(f"Durations {added_durations} has been added")
        with self.compression_in_progress_lock:
            self.logger.info(f"New durations are {self.durations}")
        

    def get_raw_data_filter(self):
        """Return current filters, which are being applied to a raw data during decimation."""
        with self.compression_in_progress_lock:
            raw_filter_conditions = self.raw_filter_conditions.copy()
        return raw_filter_conditions


    def remove_all_raw_data_filters(self):
        """Remove all current filters, which are being applied to a raw data during decimation."""
        with self.compression_in_progress_lock:
            self.raw_filter_conditions = []
        self.logger.info("All raw data condition were removed")

    def add_raw_data_filter(self, condition):
        """
           Conditions should be a tupple of a form (field, *one of the influx comparison operators*, value)
           for example ("valve_stable_time", ">", 30).
           this method doesn't check for valid field name, potential sql injection here TODO
        """
        if (not isinstance(condition[0], str) or 
            condition[1] not in influx_comparison_operators or 
            not isinstance(condition[2], int)):
            self.logger.error(f"Bad condition format: {condition}")
            return False

        with self.compression_in_progress_lock:
            self.raw_filter_conditions.append(condition)
        self.logger.info(f"Raw data condition {condition} was added")
        return True

    def add_raw_data_filters(self, conditions):
        """Same as for add_raw_data_filter, but accepts a list of tuples"""
        for condition in conditions:
           self.add_raw_data_filter(condition) 



class DBDecimatorThread(threading.Thread):
    def __init__(self,
                 parent,
                 db_name,
                 db_host_address,
                 db_port,
                 master_measurement,
                 # durations,
                 logger=None,
                 time_sleep=5):
        threading.Thread.__init__(self, name="DBDecimatorThread")
        self.parent = parent
        self.db_name = db_name
        self.db_host_address = db_host_address
        self.db_port = db_port
        self.master_measurement = master_measurement
        self.time_sleep = time_sleep

        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(client_name="DBDecimatorLoopThread")

        self._pause_event = threading.Event()
        self._stop_event = threading.Event()


        # self starting thread
        self.setDaemon(True)
        self.start()

    def pause(self):
        self._pause_event.set()

    def unpause(self):
        self._pause_event.clear()

    def is_paused(self):
        return self._pause_event.is_set()

    def stop(self):
        self._stop_event.set()


    def get_last_recorded_timestamp(self, measurement):
        # Method to grab last compression time for the passed measurement
        query = f"""SELECT   (*) 
                    FROM     {measurement} 
                    ORDER BY time DESC limit 1"""
        rs = self.client.query(query, epoch='ms')
        for key, gen in rs.items():
            for row in gen:
                return (row["time"])

    def get_field_keys(self, measurement):
        # get all the field keys for a given measurement
        query = f"""SHOW FIELD KEYS FROM {measurement}"""
        rs = self.client.query(query)
        return [(row["fieldKey"], row["fieldType"]) for key, row_gen in rs.items() for row in row_gen]


    def get_last_decimation_timestamp(self, measurement):
        """get the time of the last decimation"""
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

    def compress_raw_data(self, start_time_ms, stop_time_ms, src_meas, dest_meas, sort_time):
        # compress original data, collect Min, Max, Mean and Count from it and 
        # store it in the smallest requested resolution 
        conditions_str = ""
        if len(self.parent.raw_filter_conditions)>0:
            for condition in self.parent.raw_filter_conditions:
                conditions_str = f"{conditions_str} AND {condition[0]}{condition[1]}{condition[2]}"
        query = f"""SELECT   Min(*), 
                             Max(*), 
                             Mean(*), 
                             Count(*) 
                    INTO     {dest_meas} 
                    FROM     {src_meas}
                    WHERE    time>={start_time_ms}ms 
                    AND      time<{stop_time_ms}ms
                    {conditions_str}
                    GROUP BY time({sort_time}), *"""
        rs = self.client.query(query)
        self.record_decimation_timestamp(timestamp=stop_time_ms, src_meas="crds")

    def get_start_stop_last(self, src_measurement, dest_duration_ms):
        # a helper for run function
        last_recorded_timestamp = self.get_last_recorded_timestamp(src_measurement)
        start_time_ms = self.get_last_decimation_timestamp(src_measurement)
        stop_time_ms = int(dest_duration_ms * math.floor(last_recorded_timestamp / dest_duration_ms))
        return start_time_ms, stop_time_ms, last_recorded_timestamp



    def run(self):
        # create db client
        self.client = InfluxDBClient(host=self.db_host_address, port=self.db_port)

        # check if db exists
        if self.db_name not in [result["name"] for result in self.client.get_list_database()]:
            self.logger.error(f"Database {self.db_name} not found, exiting")
            raise ValueError(f"Database {self.db_name} not found, exiting")
        self.client.switch_database(self.db_name)

        # start the loop
        while True:

            if self._stop_event.is_set():
                # if IDriver is set to be closed
                break

            if not self._pause_event.is_set():
                with self.parent.compression_in_progress_lock:
                    dest_duration_ms = self.parent.durations_ms[0]
                    start_time_ms, stop_time_ms, last_recorded_timestamp = self.get_start_stop_last(self.master_measurement, dest_duration_ms)

                    if stop_time_ms > start_time_ms:
                        # time to decimate has come

                        # first, decimate raw data
                        self.logger.debug(ghrdm(dest_duration_ms,start_time_ms,stop_time_ms))
                         # we can do it for all fields at once this way
                        dest_meas = f"{self.master_measurement}_{self.parent.durations[0]}"

                        self.compress_raw_data(start_time_ms=start_time_ms,
                                               stop_time_ms=stop_time_ms,
                                               src_meas=self.master_measurement,
                                               dest_meas=dest_meas,
                                               sort_time=self.parent.durations[0])

                        # then, in a loop, decimate all smaller resolutions if needed
                        for src_duration, dest_duration, dest_duration_ms in self.parent.durations_map:
                            src_meas = f"{self.master_measurement}_{src_duration}" 
                            dest_meas = f"{self.master_measurement}_{dest_duration}"

                            start_time_ms, stop_time_ms, last_recorded_timestamp = self.get_start_stop_last(src_meas, dest_duration_ms)

                            if last_recorded_timestamp is None or stop_time_ms <= start_time_ms:
                                break
                            self.logger.debug(ghrdm(dest_duration_ms,start_time_ms,stop_time_ms))
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
        self.clien.close()
        self.logger.info("DBDecimator loop has ended")


def parse_arguments():
    """
        parse command line arguments
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rpc_port', help='Decimator RPC Port', default=rpc_ports["db_decimator"])
    parser.add_argument('-a', '--address', help='InfluxDB address', default="localhost")
    parser.add_argument('-p', '--port', help='InfluxDB port', default=8086)
    parser.add_argument('-m', '--measurement', help='Name of the measurement to be decimated', default="crds")
    parser.add_argument('-n', '--db_name', help='Database name', default="pigss_sim_data")
    
    parser.add_argument('-v', '--verbose', help='Verbose', default=False, action="store_true")

    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()

    log = LOLoggerClient(client_name="DBDecimator", verbose=True)

    log.info(f"DBDecimator is about to start.")
    log.info(f"RPC server will be available at {args.rpc_port} in a sec.")

    db_decimator = DBDecimator(db_host_address=args.address,
                               db_port=args.port,
                               db_name=args.db_name,
                               rpc_server_port=args.rpc_port,
                               rpc_server_name="",
                               rpc_server_description="DB Decimator",
                               logger=log,
                               start=True)



# def test_shit():
#     # duration = ["15s", "1h", "5m", "155s", "10h", "4h", "12h", "24h"]
#     duration = default_durations
#     duration.append("10s")
#     print(duration)
#     ms_durations = [generate_duration_time(a, ms=False) for a in duration]
#     # print(ms_durations)
#     ms_durations.sort()
#     # print(ms_durations)
#     durations = [generate_duration_timecode(a) for a in ms_durations]
#         # duration.sort(key=cmp_to_key(compare_durations), reverse=True)
#     # duration = sorted(duration,key=cmp_to_key(compare_durations))
#     print(durations)

if __name__ == "__main__":
    main()
    # test_shit()



#todo
#   test on real data when there will be one
#   conditions - done, need test
#   sql injection prevention and other bulletproof
#   dockstrings
# measure performance, memory leaks and such
# start/stop with/without settings file

# questions:
# retention policies? do manual delete or set influx policies? if second, who is responcible?

# low priority: a request to see data on edge of available resolition?

