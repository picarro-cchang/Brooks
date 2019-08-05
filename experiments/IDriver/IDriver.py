import time
import json
import threading
import queue as Queue
import experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO
import experiments.common.timeutils as timeutils

from datetime import datetime, timedelta, tzinfo
from experiments.IDriver import StringPickler
from experiments.IDriver.Listener import Listener
from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from experiments.IDriver.DBWriter.InfluxDBWriter import InfluxDBWriter

ZERO = timedelta(0)
HOUR = timedelta(hours=1)

# database flushing modes:
BATCHING = "BATCHING"
TIMED = "TIMED"
DEFAULT_FLUSHING_BATCH_SIZE = 10
DEFAULT_FLUSHING_TIMEOUT = 1

# default list of tags that will be taken from each measurement point from an instrument
DEFAULT_DYNAMIC_DATABASE_TAGS = ['source', 'mode', 'ver', 'good']

DEFAULT_RPC_TUNNEL_CONFIG_FILE = "rpc_tunnel_configs.json"
DEFAULT_DATABASE_NAME = "pigss_data"


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


class PicarroAnalyzerDriver:
    """
        class represents IDriver for Picarro Analyser instrument,
        it pipelines measurement point from instrument to the database and
        is responsible for passing to the instrument commands from upper layer
    """

    def __init__(self,
                 instrument_ip_address,
                 database_writer,
                 rpc_server_port,
                 rpc_server_name="",
                 rpc_server_description="IDriver for Picarro Instrument",
                 app_name="IDriver",
                 rpc_tunnel_config=None,
                 database_tags=None,
                 dynamic_database_tags=None,
                 start_now=False,
                 flushing_mode=BATCHING,
                 flushing_batch_size=DEFAULT_FLUSHING_BATCH_SIZE,
                 flushing_timeout=DEFAULT_FLUSHING_TIMEOUT,
                 logger=None):
        self.APP_NAME = app_name
        self.instrument_ip_address = instrument_ip_address
        self.database_writer = database_writer
        self.rpc_server_name = rpc_server_name
        self.rpc_server_port = rpc_server_port
        self.rpc_tunnel_config = rpc_tunnel_config
        self.rpc_server_description = rpc_server_description
        self.database_tags = {}
        self.database_tags_lock = threading.Lock()
        self.dynamic_database_tags = dynamic_database_tags if dynamic_database_tags is not None else []
        self.dynamic_database_tags_lock = threading.Lock()
        self.stopwatch_database_tags = {}
        self.stopwatch_database_tags_lock = threading.Lock()
        self.flushing_mode = flushing_mode
        self.flushing_batch_size = flushing_batch_size
        self.flushing_timeout = flushing_timeout

        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(client_name=self.rpc_server_name)

        if database_tags is not None:
            for database_tag in database_tags:
                self.database_tags[database_tag] = database_tags[database_tag]
        else:
            self.database_tags = {}

        self.thread_created = False

        # create CmdFIFO server
        if self.rpc_tunnel_config is None:
            # if tunnel settings not supplied - it is a regular CmdFIFO server
            # import CmdFIFO as CmdFIFO
            self.server = CmdFIFO.CmdFIFOServer(
                ("", self.rpc_server_port),
                ServerName=self.rpc_server_name,
                ServerDescription=self.rpc_server_description,
                threaded=True)
        else:
            # if tunnel settings supplied - create CmdFIFO tunnel
            # server and register functions from configs
            # import CmdFIFO_tunnel as CmdFIFO
            self.server = CmdFIFO.CmdFIFOServerTunnel(
                ("", self.rpc_server_port),
                ServerName=self.rpc_server_name,
                ServerDescription=self.rpc_server_description,
                threaded=True)
            # if self.rpc_tunnel_config is not None:
            self.proxys = CmdFIFO.register_proxy_rpcs_from_configs(
                rpc_tunnel_configs=self.rpc_tunnel_config,
                RpcTunnelServer=self.server,
                master_ip=self.instrument_ip_address)

        # start instrument listener for data points
        self.__create_listener(self.instrument_ip_address)

        # add commands methods and rpc them
        self.register_idriver_rpc_functions()

        # start thread that writes datapoints to database
        if start_now:
            self.start_idriver_loop_thread()
            self.rpc_serve_forever()

    def rpc_serve_forever(self):
        """
            Start RPC server and serve it forever.
            this is a blocking method - call once you are done setting tags
        """
        self.logger.info(f"Starting RPC server to serve forever")
        self.server.serve_forever()

    def start_idriver_loop_thread(self):
        """
        Method to start thread that reporting data to database
        """
        if not self.thread_created:
            self.IDriverThread = IDriverThread(
                self,
                flushing_mode=self.flushing_mode,
                flushing_batch_size=self.flushing_batch_size,
                flushing_timeout=self.flushing_timeout)
            self.thread_created = True
            self.logger.info("IDriver loop has started")
        else:
            self.IDriverThread.unpause()

    def pause_idriver_loop_thread(self):
        """
        Method use to pause reporting data to database if caller wants too
        """

        if not self.thread_created:
            self.logger.error("can't stop thread, it doesn't exist yet")
            return
        self.IDriverThread.pause()
        self.logger.info("IDriver loop is paused")

    def stop_idriver_loop_thread(self):
        """
        Method use to cleaning close all connections and close HW if requires
        """
        self.logger.info("Driver instance closed")
        self.IDriverThread.stop()
        self.thread_created = False

    def remove_tags(self, tags):
        """
            remove given tags from the self.database_tags, so it won't be passed to database anymore
            :param tags: a string, a list of strings, or a dictionary
        """
        if isinstance(tags, str):
            tags = [tags]
        if isinstance(tags, dict):
            tags = [k for k in tags]
        with self.database_tags_lock:
            for tag in tags:
                self.database_tags.pop(tag, None)
        self.logger.info(f"Static tags {tags} have been removed")

    def remove_all_tags(self):
        """
            removes all tags, will be writing to database without any tags
        """
        with self.database_tags_lock:
            self.database_tags = {}
        self.logger.info(f"All static tags have been removed")

    def get_tags(self):
        """
            return a dictionary of current tags
        """
        with self.database_tags_lock:
            database_tags_return = self.database_tags.copy()
        return database_tags_return

    def add_tags(self, tags):
        """
            add given tags to the self.database_tags, so it will
            be passed to database with each measurment
            :param tags: a dictionary
        """
        if not isinstance(tags, dict):
            raise ValueError("tags must be dictionary")

        with self.database_tags_lock:
            for tag in tags:
                self.database_tags[tag] = tags[tag]
        self.logger.info(f"Static tags {tags} have been added")

    def adjust_tags(self,
                    remove_tags=None,
                    add_tags=None,
                    remove_all_tags=False):
        """
            adjust tags by passing tags to be added, removed or
            removed all to the corresponging arguments
        """
        if remove_tags is not None:
            self.remove_tags(remove_tags)
        if add_tags is not None:
            self.add_tags(add_tags)
        if remove_all_tags:
            self.remove_all_tags()

    def remove_dynamic_tags(self, tags):
        """
            remove given dynamic tags from the self.database_tags, so
            it won't be passed to database anymore
            :param tags: a string or a list of strings
        """
        if isinstance(tags, str):
            tags = [tags]
        with self.dynamic_database_tags_lock:
            for tag in tags:
                if tag in self.dynamic_database_tags:
                    self.dynamic_database_tags.remove(tag)
        self.logger.info(f"Dynamic tags {tags} have been removed")

    def remove_all_dynamic_tags(self):
        """
            removes all tags, will be writing to database without any tags
        """
        with self.dynamic_database_tags_lock:
            self.dynamic_database_tags = []
        self.logger.info(f"All Dynamic tags have been removed")

    def get_dynamic_tags(self):
        """
            return a dictionary of current dynamic tags
        """
        with self.dynamic_database_tags_lock:
            dynamic_database_tags_return = self.dynamic_database_tags.copy()
        return dynamic_database_tags_return

    def add_dynamic_tags(self, tags):
        """
            add given dynamic tags to the self.database_tags, so
            it will be passed to database with each measurement
            and value taken from each measurement
            :param tags: a string or an array of strings
        """
        if isinstance(tags, str):
            tags = [tags]

        with self.dynamic_database_tags_lock:
            for tag in tags:
                self.dynamic_database_tags.append(tag)
        self.logger.info(f"Dynamic tags {tags} have been added")

    def adjust_dynamic_tags(self,
                            remove_tags=None,
                            add_tags=None,
                            remove_all_tags=False):
        """
            adjust tags by passing tags to be added, removed or
            removed all to the corresponging arguments
        """
        if remove_tags is not None:
            self.remove_dynamic_tags(remove_tags)
        if add_tags is not None:
            self.add_dynamic_tags(add_tags)
        if remove_all_tags:
            self.remove_all_dynamic_tags()

    def add_stopwatch_tag(self, tag_name, timestamp_of_event=None):
        """
            eVENT, lol, you got it? bcz it will mostly be used for 
            changing VENTs. this will add a stopwatch tag - this tag's
            value will be calculated time since some event. name of 
            the event is passed as tag_name. if time_stamp_of_event
            is passed - it will be used for calculation
        """
        if timestamp_of_event is None:
            timestamp_of_event = timeutils.get_epoch_timestamp()
        with self.stopwatch_database_tags_lock:
            self.stopwatch_database_tags[tag_name] = timestamp_of_event

    def remove_stopwatch_tag(self, tag_name):
        """Remove a stopwatch tag."""
        with self.stopwatch_database_tags_lock:
            if tag_name in self.stopwatch_database_tags:
                self.stopwatch_database_tags.remove(tag_name)

    def remove_all_stopwatch_tags(self):
        """Remove all stopwatch tags."""
        with self.stopwatch_database_tags_lock:
            self.stopwatch_database_tags = {}

    def get_stopwatch_tags(self):
        """Get stopwatch tags, pretty self explanatory."""
        with self.stopwatch_database_tags_lock:
            stopwatch_db_tags_return = self.stopwatch_database_tags.copy()
        return stopwatch_db_tags_return


    def __create_listener(self, ip):
        """
            create an instrument listener by given IP address
        """
        self.queue = Queue.Queue(200)
        self.listener = Listener(host=ip,
                                 queue=self.queue,
                                 port=40060,
                                 elementType=StringPickler.ArbitraryObject,
                                 retry=True,
                                 name="Sensor stream listener")
        return self.queue

    def register_idriver_rpc_functions(self):
        """
            register all public methods to the rpc server
        """
        # IDriver measurement collection and database flushing loop control
        self.server.register_function(self.start_idriver_loop_thread,
                                      name="IDRIVER_start")
        self.server.register_function(self.pause_idriver_loop_thread,
                                      name="IDRIVER_stop")
        self.server.register_function(self.stop_idriver_loop_thread,
                                      name="IDRIVER_close_driver")

        # Static tags controls - value predifined
        self.server.register_function(self.remove_tags,
                                      name="IDRIVER_remove_tags")
        self.server.register_function(self.remove_all_tags,
                                      name="IDRIVER_remove_all_tags")
        self.server.register_function(self.get_tags, name="IDRIVER_get_tags")
        self.server.register_function(self.add_tags, name="IDRIVER_add_tags")
        self.server.register_function(self.adjust_tags,
                                      name="IDRIVER_adjust_tags")

        # Dynamic tags controls - value taken from each measurement
        self.server.register_function(self.remove_dynamic_tags,
                                      name="IDRIVER_remove_dynamic_tags")
        self.server.register_function(self.remove_all_dynamic_tags,
                                      name="IDRIVER_remove_all_dynamic_tags")
        self.server.register_function(self.get_dynamic_tags,
                                      name="IDRIVER_get_dynamic_tags")
        self.server.register_function(self.add_dynamic_tags,
                                      name="IDRIVER_add_dynamic_tags")
        self.server.register_function(self.adjust_dynamic_tags,
                                      name="IDRIVER_adjust_dynamic_tags")

        # Stopwatch tags controls - value is a time calculated as 
        # difference between measurement time and event time
        self.server.register_function(self.remove_stopwatch_tag,
                                      name="IDRIVER_remove_stopwatch_tag")
        self.server.register_function(self.remove_all_stopwatch_tags,
                                      name="IDRIVER_remove_all_stopwatch_tags")
        self.server.register_function(self.get_stopwatch_tags,
                                      name="IDRIVER_get_stopwatch_tags")
        self.server.register_function(self.add_stopwatch_tag,
                                      name="IDRIVER_add_stopwatch_tag")



class IDriverThread(threading.Thread):
    """
        A thread which is meant to collect measurement points from
        an instrument and when unpaused - write it to database
    """

    def __init__(self,
                 parent_idriver,
                 flushing_mode=BATCHING,
                 flushing_batch_size=10,
                 flushing_timeout=1,
                 logger=None):
        threading.Thread.__init__(self, name="IDriverThread")
        self.parent_idriver = parent_idriver
        self.queue = parent_idriver.queue
        self.database_writer = parent_idriver.database_writer
        if flushing_mode in [BATCHING, TIMED]:
            self.flushing_mode = flushing_mode
        else:
            self.logger.error(
                "unsopperted flushing_mode supplied, setting to be BATCHING")
            self.flushing_mode = BATCHING
        self.flushing_batch_size = flushing_batch_size
        self.flushing_timeout = flushing_timeout

        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        if isinstance(logger, LOLoggerClient):
            self.logger = logger
        if logger is None:
            self.logger = LOLoggerClient(
                client_name=f"{self.parent_idriver.rpc_server_name}_subthread")

        # self starting thread
        self.setDaemon(True)
        self.start()

    def pause(self):
        self._pause_event.set()

    def unpause(self):
        self._pause_event.clear()

    def stop(self):
        self._stop_event.set()

    def equip_data_object_with_defined_tags(self, data):
        with self.parent_idriver.database_tags_lock:
            for tag in self.parent_idriver.database_tags:
                data["tags"][tag] = self.parent_idriver.database_tags[tag]
        return data

    def equip_data_object_with_dynamic_tags(self, data, obj):
        with self.parent_idriver.dynamic_database_tags_lock:
            for tag in self.parent_idriver.dynamic_database_tags:
                if tag in obj:
                    data['tags'][tag] = obj[tag]
        return data

    def equip_data_object_with_stopwatch_tags(self, data, obj):
        with self.parent_idriver.stopwatch_database_tags_lock:
            for tag in self.parent_idriver.stopwatch_database_tags:
                time_passed = obj['time'] - self.parent_idriver.stopwatch_database_tags[tag]
                data['tags'][tag] = time_passed
        return data

    def generate_data_for_database(self, queue):
        """

        """
        while True:
            try:
                obj = queue.get(timeout=5.0)

                if 'time' in obj:
                    data['time'] = datetime.fromtimestamp(obj['time'], tz=utc)
                    # print(obj['time'])
                else:
                    self.logger.error("Measurment with no 'time' value passed, gonna ignore it")
                    continue

                data = {
                    'measurement': 'crds',
                    'fields': {},
                    'tags': {}
                }

                # equip measurement with tags
                data = self.equip_data_object_with_defined_tags(data)
                data = self.equip_data_object_with_dynamic_tags(data, obj)
                data = self.equip_data_object_with_stopwatch_tags(data, obj)

                # equip measurement with fields
                for field in obj['data']:
                    data['fields'][field] = obj['data'][field]
                yield data
            except Queue.Empty:
                yield None
            except Exception:
                import traceback
                self.logger.error(traceback.format_exc())

    def run(self):
        """
            runs the main loop of this thread:
                - generate data from listener,
                - equip it with tags,
                - store it in temporary list
                - flush it to database according to flushing mode
        """
        data_to_flush = []
        time_since_last_flush = time.time()
        gonna_flush_now = False
        loop_just_was_just_running = False
        # print(f"flushing is timeout? - {self.flushing_mode == TIMED}")

        for datum in self.generate_data_for_database(self.queue):
            # print("woop")
            if self._stop_event.is_set():
                # if IDriver is set to be closed
                break
            if not self._pause_event.is_set():
                # if IDriver is not set to be paused - store generated data in temp list
                if datum is not None:
                    data_to_flush.append(datum)
                    # print(len(data_to_flush))
                    # print('.', end='')

                # check if it is time to flush to database
                # print(f"time since last flush - {time_since_last_flush}")
                if ((self.flushing_mode == BATCHING
                     and len(data_to_flush) > self.flushing_batch_size) or
                    (self.flushing_mode == TIMED and time_since_last_flush +
                     self.flushing_timeout <= time.time()) or datum is None):
                    gonna_flush_now = True

                loop_just_was_just_running = True
            else:
                if loop_just_was_just_running:
                    # loop has paused, but we need to flush what is currently in the temporary list
                    gonna_flush_now = True
                    loop_just_was_just_running = False

            if gonna_flush_now:
                # print("gonna_flush_now")
                # flushing
                if data_to_flush:
                    while True:
                        try:
                            self.database_writer.write_data(data_to_flush)
                            # print("flushed to db")
                            break
                        except:
                            self.logger.debug(
                                "flushing to db failed, try again in 5 seconds"
                            )
                            time.sleep(5.0)
                            # print('x', end='')

                    # print('.', end='')
                    data_to_flush = []
                time_since_last_flush = time.time()
                gonna_flush_now = False

            else:
                time.sleep(0.1)


def parse_arguments():
    """
        parse command line arguments
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("instrument_ip_address",
                        help="ip address of the Picarro instrument")
    parser.add_argument("rpc_server_port",
                        help="port for an rpc server to accept client")
    parser.add_argument("-n", "--name", help="name for an rpc server")
    parser.add_argument("-dbn",
                        "--database_name",
                        help="name of the influxdb database",
                        default=None)
    parser.add_argument("-dbi",
                        "--database_ip",
                        help="ip address of the influxdb database",
                        default=None)
    parser.add_argument("-dbp",
                        "--database_port",
                        help="port of the influxdb database",
                        default=None)
    parser.add_argument("-t",
                        "--tunnel_configs",
                        help="path to the rpc tunnel configuration file",
                        default=DEFAULT_RPC_TUNNEL_CONFIG_FILE)
    parser.add_argument(
        "-f",
        "--flushing_mode",
        help="""flushing mode - data will be flushed to database
                                                        either after time period, or after some buffer is
                                                        full""",
        choices=["TIMED", "BATCHING"],
        default="TIMED")
    parser.add_argument("-ddt",
                        "--dynamic_database_tags",
                        help="""database tags that will have a dynamic
                                                                   value taken from each measurement""",
                        nargs="*",
                        default=DEFAULT_DYNAMIC_DATABASE_TAGS)
    parser.add_argument("-adt",
                        "--add_default_tags",
                        help="add default static tags for testing",
                        action="store_true")

    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()

    if args.name:
        rpc_server_name = args.name
    else:
        rpc_server_name = "IDRIVER_{}".format(args.instrument_ip_address)

    log = LOLoggerClient(client_name=f"{rpc_server_name}__main__",
                         verbose=True)

    db_writer = InfluxDBWriter(db_name=args.database_name,
                               address=args.database_ip,
                               db_port=args.database_port)
    log.info("Connected to Database '{}' on {}:{}".format(
        db_writer.get_db_name(), db_writer.get_db_address(),
        db_writer.get_db_port()))

    with open(args.tunnel_configs, "r") as f:
        rpc_tunnel_config = json.loads(f.read())
    log.info(f"RPC Tunnel settings loaded from {args.tunnel_configs}")

    ipdriver = PicarroAnalyzerDriver(
        instrument_ip_address=args.instrument_ip_address,
        database_writer=db_writer,
        rpc_server_port=int(args.rpc_server_port),
        rpc_server_name=rpc_server_name,
        database_tags=None,
        start_now=False,
        rpc_tunnel_config=rpc_tunnel_config,
        flushing_mode=args.flushing_mode,
        dynamic_database_tags=args.dynamic_database_tags)

    log.info(
        f"Picarro Instrument Driver for {args.instrument_ip_address} created.")
    log.info(
        f"RPC server will be available at {args.rpc_server_port} in a sec.")

    if args.add_default_tags:
        tags = {'analyzer': "AMADS2002", 'chassis': "2633"}
        ipdriver.add_tags(tags)
        log.info(f"Static tags added: {tags}")

    log.info(f"Dynamic tags added: {args.dynamic_database_tags}")

    ipdriver.start_idriver_loop_thread()
    log.info("Quering from Instrument and flushing to Database has started")
    try:
        ipdriver.rpc_serve_forever()
    except KeyboardInterrupt:
        log.info(
            "RPC server has ended it's lifecycle after brutal KeyboardInterrupt, good job."
        )

    log.info("RPC server has ended")


if __name__ == "__main__":
    main()
