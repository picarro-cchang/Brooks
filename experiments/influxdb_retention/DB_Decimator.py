"""
    This file contains necessary classes and functions for Database decimation service.
    There is multiple ways to start the service:
        1. Run this file without any arguments
        2. Run this file with some arguments of the provided command line arguments
        3. Create DB_decimation from as a Thread:
            3.1 With default settings:
                > db_decimator = DBDecimatorFactory().create_default_DBDecimator()
                > db_decimator.start()
            3.2 With settings:
                > DBDecimatorFactory().create_DBDecimator_with_settings(db_decimator_settings)
                > db_decimator.start()
"""

import datetime
import math
import sys
import threading
import time
from functools import cmp_to_key

from influxdb import InfluxDBClient

import experiments.influxdb_retention.duration_tools as dt
import host.experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO
from experiments.influxdb_retention.RT_policy_manager import RT_policy_manager
from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from host.experiments.common.rpc_ports import rpc_ports

influx_comparison_operators = ["=", "<>", "!=", ">", ">=", "<", "<="]
default_durations = ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "1d"]

default_settings = {
    "db_host_address": "localhost",
    "db_port": 8086,
    "db_name": "pigss_data",
    "rpc_server_port": rpc_ports["db_decimator"],
    "rpc_server_name": "DB Decimator",
    "rpc_server_description": "DB Decimator",
    "durations": default_durations,
    "logger": "DB_Decimator",
    "verbose": True,
    "master_measurement": "crds",
    "time_sleep": 5,
    "raw_filter_conditions": None,
    "start": False,
    "retention_policies": {
        "autogen": "260w",
        "crds_15s": "520w",
        "crds_1m": "780w",
        "crds_5m": "1040w",
        "crds_15m": "1300w",
        "crds_1h": "1560w",
        "crds_4h": "1820w",
        "crds_12h": "2080w",
        "crds_1d": "2340w"
    }
}


class DBDecimatorFactory(object):
    """
        A class to create DBDecimator with a provided dictionary of settings
    """
    def create_default_DBDecimator(self):
        """Create DBDecimator with default settings"""
        return self.create_DBDecimator_with_settings(default_settings)

    def create_DBDecimator_with_settings(self, settings):
        """Create DBDecimator with provided settings"""
        # if passed settings missed some fields - fill it with default ones
        raw_settings = default_settings.copy()
        for key in raw_settings:
            if key in settings:
                raw_settings[key] = settings[key]

        try:
            db_decimator = DBDecimator(**settings)
        except Exception as e:
            print(e)
            return False
        return db_decimator


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
                 db_host_address="localhost",
                 db_port=8086,
                 db_name="pigss_data",
                 rpc_server_port=rpc_ports["db_decimator"],
                 rpc_server_name="DB Decimator",
                 rpc_server_description="DB Decimator",
                 durations=None,
                 logger=None,
                 verbose=True,
                 master_measurement="crds",
                 time_sleep=5,
                 raw_filter_conditions=None,
                 retention_policies=None,
                 start=True):
        # DB params
        self.db_host_address = db_host_address
        self.db_port = db_port
        self.db_name = db_name
        self.master_measurement = master_measurement

        # logger params
        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger, verbose=verbose)
        elif isinstance(logger, LOLoggerClient):
            self.logger = logger
        else:
            self.logger = LOLoggerClient(client_name=self.__class__.__name__, verbose=verbose)

        # check if database can be reached
        self.main_client = InfluxDBClient(host=self.db_host_address, port=self.db_port)
        if not check_if_db_exists(self.db_name, self.main_client):
            raise ValueError(f"Database {self.db_name} not found")
        self.main_client.switch_database(self.db_name)

        # compare passed retention policies to existed and fix existed if needed
        self.rt_policy_manager = RT_policy_manager(client=self.main_client, logger=self.logger)

        ### DELETE THIS SHIT
        # self.rt_policy_manager.delete_all_retention_policies()

        if retention_policies is not None:
            self.rt_policy_manager.compare_and_fix(retention_policies)

        # how often loop will check for new decimation need
        if not (isinstance(time_sleep, int) or isinstance(time_sleep, float)) or time_sleep < 0:
            raise ValueError(f"time_sleep must be an int or float >=0, getting {self.db_name}")
        self.time_sleep = time_sleep

        # RPC server params
        self.rpc_server_port = rpc_server_port
        self.rpc_server_name = rpc_server_name
        self.rpc_server_description = rpc_server_description

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
            for condition in raw_filter_conditions:
                if not check_for_valid_raw_filter_condition(condition):
                    raise ValueError(f"Bad raw filter condition '{condition}'\n" /
                                     "Conditions should be a tupple of a form (field, *one of the " /
                                     "influx comparison operators*, value)" / "for example ('valve_stable_time', '>', 30)")
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

        self.auto_start = start

        if self.auto_start:
            self.start()

    def get_settings(self):
        settings = {
            "db_host_address": self.db_host_address,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "rpc_server_port": self.rpc_server_port,
            "rpc_server_name": self.rpc_server_name,
            "rpc_server_description": self.rpc_server_description,
            "durations": self.durations,
            "logger": self.logger.client_name,
            "master_measurement": self.master_measurement,
            "time_sleep": self.time_sleep,
            "raw_filter_conditions": self.get_raw_data_filter(),
            "start": self.auto_start,
            "retention_policies": self.rt_policy_manager.get_retention_policies_as_dict()
        }
        return settings

    def set_settings(self, key, value):
        #should try to apply new value to a setting and return boolean
        settings_whitelist = ["retention_policies", "raw_filter_conditions"]
        if not isinstance(key, list):
            key = [key]
        if key[0] not in ["retention_policies", "raw_filter_conditions"]:
            self.logger.error(f"Only settings in {settings_whitelist} allowed to "\
                                f"change, tried to change {key[0]}")
            return False

        try:
            if key[0] == "raw_filter_conditions":
                self.remove_all_raw_data_filters()
                return self.add_raw_data_filters(value)
            if key[0] == "retention_policies":
                return self.rt_policy_manager.create_retention_policy(key[1], value)
        except Exception as e:  #todo specify error
            self.logger.error(e)
            return False
        return False

    def start(self):
        """A method to start the loop and the thread loop. """
        self.start_decimator_loop_thread()
        self.rpc_serve_forever()

    def generate_durations_meta(self):
        """Some routines around durations list"""
        self.durations = sort_durations(self.durations)
        self.durations_ms = [dt.generate_duration_in_seconds(d, ms=True) for d in self.durations]
        self.durations_map = [list(a) for a in zip(self.durations[:-1], self.durations[1:], self.durations_ms[1:])]

    def rpc_serve_forever(self):
        """
            Start RPC server and serve it forever.
            this is a blocking method - call once you are done setting tags
        """
        self.logger.info(f"Starting RPC server to serve forever on port {self.rpc_server_port}")
        self.server.serve_forever()

    def start_decimator_loop_thread(self):
        """
            Method to start thread that will be compressing data
        """
        if not self.thread_created:
            self.DBDecimatorThread = DBDecimatorThread(
                parent=self,
                db_name=self.db_name,
                db_host_address=self.db_host_address,
                db_port=self.db_port,
                master_measurement=self.master_measurement,
                rt_policy_manager=self.rt_policy_manager,
                # durations=self.durations,
                time_sleep=self.time_sleep,
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

        # not something we need at least in Rev 1
        # self.server.register_function(self.get_durations)
        # self.server.register_function(self.remove_durations)
        # self.server.register_function(self.remove_all_durations)
        # self.server.register_function(self.add_durations)

        # self.server.register_function(self.get_raw_data_filter)
        # self.server.register_function(self.remove_all_raw_data_filters)
        # self.server.register_function(self.add_raw_data_filter)
        # self.server.register_function(self.add_raw_data_filters)

        # self.server.register_function(self.get_retention_policies)
        # self.server.register_function(self.alter_retention_policy)
        # self.server.register_function(self.alter_shard_group_retention_policy)

        self.server.register_function(self.get_settings)
        self.server.register_function(self.set_settings)

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
                if dt.check_for_valid_literal_duration(duration):
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
        if not check_for_valid_raw_filter_condition(condition):
            raise TypeError(f"Bad raw filter condition '{condition}'\n" /
                            "Conditions should be a tupple of a form (field, *one of the " /
                            "influx comparison operators*, value)" / "for example ('valve_stable_time', '>', 30)")

        with self.compression_in_progress_lock:
            self.raw_filter_conditions.append(condition)
        self.logger.info(f"Raw data condition {condition} was added")
        return True

    def add_raw_data_filters(self, conditions):
        """Same as for add_raw_data_filter, but accepts a list of tuples"""
        if not isinstance(conditions, list):
            conditions = [conditions]
        for condition in conditions:
            self.add_raw_data_filter(condition)
        return True


class DBDecimatorThread(threading.Thread):
    def __init__(
            self,
            parent,
            db_name,
            db_host_address,
            db_port,
            master_measurement,
            rt_policy_manager,
            # durations,
            logger=None,
            time_sleep=5):
        threading.Thread.__init__(self, name="DBDecimatorThread")
        self.parent = parent
        self.db_name = db_name
        self.db_host_address = db_host_address
        self.db_port = db_port
        self.master_measurement = master_measurement
        self.rt_policy_manager = rt_policy_manager
        self.time_sleep = time_sleep

        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(client_name="DBDecimatorLoopThread")

        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

        self.client = self.parent.main_client

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

    def to_rp(self, measurement):
        """
            Convert measurement name to include retention policie if needed.
            Convention is that retention policy must have same name as the measurement it belongs to.
            Respectively, each retention policy can have only one measurement in it.
        """
        if measurement == self.master_measurement:
            return measurement
        if "." in measurement:
            # check if valid
            dot = measurement.index(".")
            if not measurement[:dot] == measurement[dot + 1:]:
                # if '.' is part of the measurement, it means that the part before it - a retentiona policy name
                # current convention is that retention policy should have same name as measurement in it
                # only one measurement allowed per retention policy
                raise ValueError(f"Measurement '{measurement}' has '.' in it, but naming convention is bad")
            return measurement
        else:
            return f"{measurement}.{measurement}"

    def get_last_recorded_timestamp(self, measurement):
        # Method to grab last compression time for the passed measurement
        measurement = self.to_rp(measurement)
        query = f"""SELECT   (*) 
                    FROM     {measurement} 
                    ORDER BY time DESC limit 1"""
        rs = self.client.query(query, epoch='ms')
        for key, gen in rs.items():
            for row in gen:
                # return (row["time"])
                return row["time"] if row["time"] else 0
        return 0

    def get_field_keys(self, measurement):
        # get all the field keys for a given measurement
        measurement = self.to_rp(measurement)

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
            "measurement": f"{self.master_measurement}_workspace",
            "fields": {
                "last_decimation": int(timestamp)
            },
            "tags": {
                "meas_name": src_meas
            }
        }])

    def compress_measurement(self, src_meas, dest_meas, field_key, duration, start_time_ms, stop_time_ms):
        self.rt_policy_manager.make_sure_policy_exists(dest_meas)

        src_meas = self.to_rp(src_meas)
        dest_meas = self.to_rp(dest_meas)
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
        subquery1 = f"""SELECT   sum_tot/sum_count AS "mean_{field_key}", 
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

        self.rt_policy_manager.make_sure_policy_exists(dest_meas)

        src_meas = self.to_rp(src_meas)
        dest_meas = self.to_rp(dest_meas)
        conditions_str = ""
        if len(self.parent.raw_filter_conditions) > 0:
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

    def delete_last_decimation_timestamps(self):
        measurement = f"{self.master_measurement}_workspace"
        query = f"drop {measurement}"

    def run(self):
        # start the loop
        while True:

            if self._stop_event.is_set():
                # if IDriver is set to be closed
                break

            if not self._pause_event.is_set():
                with self.parent.compression_in_progress_lock:
                    dest_duration_ms = self.parent.durations_ms[0]
                    start_time_ms, stop_time_ms, last_recorded_timestamp = self.get_start_stop_last(
                        self.master_measurement, dest_duration_ms)

                    if stop_time_ms > start_time_ms:
                        # time to decimate has come

                        # first, decimate raw data
                        self.logger.debug(ghrdm(dest_duration_ms, start_time_ms, stop_time_ms))
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

                            start_time_ms, stop_time_ms, last_recorded_timestamp = self.get_start_stop_last(
                                src_meas, dest_duration_ms)

                            if last_recorded_timestamp is None or stop_time_ms <= start_time_ms:
                                break
                            self.logger.debug(ghrdm(dest_duration_ms, start_time_ms, stop_time_ms))
                            for field_key, field_type in self.get_field_keys(
                                    self.master_measurement):  #here we need to do it for each field
                                if field_type in ['float', 'integer']:
                                    err, comp_time = self.compress_measurement(src_meas=src_meas,
                                                                               dest_meas=dest_meas,
                                                                               field_key=field_key,
                                                                               duration=dest_duration,
                                                                               start_time_ms=start_time_ms,
                                                                               stop_time_ms=stop_time_ms)

                            self.record_decimation_timestamp(timestamp=stop_time_ms, src_meas=src_meas)
            time.sleep(self.time_sleep)
        self.clien.close()
        self.logger.info("DBDecimator loop has ended")


def ghrdm(dest_duration_ms, start_time_ms, stop_time_ms):  # generate_human_readable_decimation_message
    dest_duration_ms = dt.generate_duration_literal(int(dest_duration_ms / 1000))
    start_time_ms /= 1000
    stop_time_ms /= 1000
    start_time_ms = datetime.datetime.fromtimestamp(start_time_ms).strftime('%Y-%m-%d %H:%M:%S')
    stop_time_ms = datetime.datetime.fromtimestamp(stop_time_ms).strftime('%Y-%m-%d %H:%M:%S')
    return f'Decimating to: {dest_duration_ms} , from {start_time_ms} to {stop_time_ms}'


def check_for_valid_raw_filter_condition(condition):
    """
        Should be 
    """
    if not isinstance(condition[0], str):
        return False
    if condition[1] not in influx_comparison_operators:
        return False
    if not (isinstance(condition[2], int) or isinstance(condition[2], float)
            or isinstance(condition[2], str) and condition[2].isdigit()):
        return False
    return True


def sort_durations(durations):
    """Given list of durations in a string form - sort it"""
    durations_in_seconds = [dt.generate_duration_in_seconds(a, ms=False) for a in durations]
    durations_in_seconds.sort()
    durations = [dt.generate_duration_literal(a) for a in durations_in_seconds]
    return durations


def check_if_db_exists(db_name, client):
    return db_name in [result["name"] for result in client.get_list_database()]


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
    parser.add_argument('-n', '--db_name', help='Database name', default="pigss_data")

    # parser.add_argument('-v', '--verbose', help='Verbose', default=False, action="store_true")

    args = parser.parse_args()
    return args


def main():
    if len(sys.argv) == 1:
        db_decimator = DBDecimatorFactory().create_default_DBDecimator()
        db_decimator.start()
    else:
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


if __name__ == "__main__":
    main()

#todo
#   test on real data when there will be one
#   conditions - done, need test
#   sql injection prevention and other bulletproof
#   define default retention policies
