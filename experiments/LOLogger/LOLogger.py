import os
import time
import queue
import signal
import sqlite3
import inspect
import threading
from datetime import datetime

import host.experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO
import host.experiments.common.timeutils as timeutils
from host.experiments.common.rpc_ports import rpc_ports
# import CmdFIFO as CmdFIFO # path for pk debugging
# import timeutils as timeutils # path for pk debugging
# from rpc_ports import rpc_ports # path for pk debugging
"""
    LOLogger: a logging service with RPC server capabilities. At current implementation it 
    accepts logs using RPC function LogEvent() with multiple optional arguments. It is
    encoraged that function caller would supply as many of those arguments as possible.
    Passed log messages would be passed to an SQLite database. Each month SQLite dile will 
    be changed to prevent creating huge log files and add convinience for when costumer has 
    to give us logs files for some bugs.

    RACE CONDITION:
    Service contains 3 threads: main, CMDFIFOserver and loop thread. Loop thread is daemonic,
    CMDFifo - no. CMDFifo accepts RPC requests and passes data to the queuq, Loop thread reads
    from queue and flushes data to db.When SIGINT recieved, main thread is meant to kill 
    CMDFifo and then wait for Loop thread to dieSince it might still have some data to flush
    to DB before dying.Problem is that CMDFifo thread is not properly dying and keeps 
    supplying data to queue even after Loop thread is dead,Therefore it creates a 0.2 second
    window, during which CMDFifo still accepts logs, but thos logs will be lost. Assuming use
    case when LOLogger would be the last service to recieve a SIGINT during a Shutdown sequance
    - no logs are expected during that 0.2 second and explained race condition should not be an 
    issue.
"""

# DB table scheme stuff
db_table_name = "Events"
db_fields = [("ClientTimestamp", str), ("ClientName", str), ("EpochTime", str),
             ("LogMessage", str), ("Level", int), ("IP", str)]

python_to_sqlite_types_cast_map = {
    "<class 'str'>": "text",
    "<class 'int'>": "int"
}

# database flushing stuff:
FLUSHING_MODES = ["BATCHING", "TIMED"]
BATCHING = FLUSHING_MODES[0]
TIMED = FLUSHING_MODES[1]
DEFAULT_FLUSHING_BATCH_SIZE = 10
DEFAULT_FLUSHING_BATCHING_TIMEOUT = 60
DEFAULT_FLUSHING_TIMEOUT = 1

LOG_LEVELS_RANGE = range(0, 51)
LOG_LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0
}

MOVE_TO_NEW_FILE_EVERY_MONTH = True
ZIP_OLD_FILE = False  # not emplemented yet, might be not nessecarry
DO_DATABASE_TRANSITION = False  # not emplemented yet, might be not nessecarry

DEFAULT_DB_PATH = "."  # TODO


def get_current_year_month():
    today = datetime.today()
    return f"{today.year}_{today.month:0{2}}"


class LOLogger(object):
    def __init__(
            self,
            db_folder_path,
            db_filename_prefix,
            rpc_port,
            rpc_server_name="LOLogger",
            rpc_server_description="Universal log collector, flushes to sqlite",
            flushing_mode=TIMED,
            flushing_batch_size=10,
            flushing_timeout=1,
            move_to_new_file_every_month=MOVE_TO_NEW_FILE_EVERY_MONTH,
            zip_old_file=ZIP_OLD_FILE,
            do_database_transition=DO_DATABASE_TRANSITION,
            verbose=True):
        self.db_folder_path = db_folder_path
        self.db_filename_prefix = db_filename_prefix
        self.rpc_port = rpc_port
        self.rpc_server_name = rpc_server_name
        self.rpc_server_description = rpc_server_description

        self.flushing_mode = flushing_mode
        self.flushing_batch_size = flushing_batch_size
        self.flushing_timeout = flushing_timeout

        self.move_to_new_file_every_month = move_to_new_file_every_month
        self.zip_old_file = zip_old_file
        self.do_database_transition = do_database_transition

        self.queue = queue.Queue(200)
        self.verbose = verbose
        self.LogLevel = 1
        self.logs_passed_to_queue = 0

        self.server = CmdFIFO.CmdFIFOServer(
            ("", self.rpc_port),
            ServerName=self.rpc_server_name,
            ServerDescription=self.rpc_server_description,
            threaded=True)

        self.lologger_thread = LOLoggerThread(
            db_folder_path=self.db_folder_path,
            db_filename_prefix=self.db_filename_prefix,
            queue=self.queue,
            parent=self,
            flushing_mode=self.flushing_mode,
            flushing_batch_size=self.flushing_batch_size,
            flushing_timeout=self.flushing_timeout,
            move_to_new_file_every_month=self.move_to_new_file_every_month,
            zip_old_file=self.zip_old_file,
            do_database_transition=self.do_database_transition)
        self.register_rpc_functions()

        signal.signal(signal.SIGINT, self._signal_handler)

        self.server.serve_forever()

    def LogEvent(self,
                 log_message,
                 client_name="AnonymService",
                 ip="localhost",
                 client_timestamp=None,
                 level=30):
        if level in LOG_LEVELS_RANGE:
            passed_level = level
        elif level in LOG_LEVELS:
            passed_level = LOG_LEVELS[level]
        if passed_level >= self.LogLevel:
            if client_timestamp is None:
                client_timestamp = str(timeutils.get_local_timestamp())
            EpochTime = str(timeutils.get_epoch_timestamp())

            values = [
                client_timestamp, client_name, EpochTime, log_message, level,
                ip
            ]
            self.queue.put_nowait(values)
            self.logs_passed_to_queue += 1
            if self.verbose:
                print(f"{client_timestamp}:::{client_name}  -  {log_message}")

    def register_rpc_functions(self):
        self.server.register_function(self.LogEvent)
        self.server.register_function(self.flip_verbose)
        self.server.register_function(self.get_verbose)
        self.server.register_function(self.set_log_level)
        self.server.register_function(self.get_log_level)

    def flip_verbose(self):
        """
            Switch verbose value to opposite from current
        """
        self.verbose = not self.verbose
        return True

    def get_verbose(self):
        """
            Return current verbose value
        """
        return self.verbose

    def set_log_level(self, Level):
        """
            Set log level for the server, so all the log 
            messages below that level will be ignorred
        """
        if Level in LOG_LEVELS_RANGE:
            self.LogLevel = Level
        elif Level in LOG_LEVELS:
            self.LogLevel = LOG_LEVELS[Level]
        else:
            raise ValueError(f"Level passed: {Level}; " \
                              f"should be between {LOG_LEVELS_RANGE[0]}:{LOG_LEVELS_RANGE[-1]} " \
                              f"or one of {list(LOG_LEVELS.keys())}")
        return True

    def get_log_level(self):
        """
            Get current log level
        """
        return self.LogLevel

    def _signal_handler(self, sig, frame):
        """
            This function will be called when SIGINT recieved.
            It should first stop the RPC server, then notify 
            the looping thread and wait until it will complete
            itss shutdown sequance and die gracefully.
        """
        self.server.stop_server()
        self.lologger_thread._sigint_handler()
        self.lologger_thread.join()


class LOLoggerThread(threading.Thread):
    """
        Thread that will be dealing with sqlite database.
    """

    def __init__(
            self,
            db_folder_path,
            db_filename_prefix,
            queue,
            parent,
            flushing_mode=TIMED,
            flushing_batch_size=10,
            flushing_timeout=1,
            move_to_new_file_every_month=MOVE_TO_NEW_FILE_EVERY_MONTH,
            zip_old_file=ZIP_OLD_FILE,
            do_database_transition=DO_DATABASE_TRANSITION,
    ):
        threading.Thread.__init__(self, name="LOLoggerThread")
        self.db_folder_path = db_folder_path
        self.db_filename_prefix = db_filename_prefix
        self.db_path = self._create_database_file_path(self.db_folder_path,
                                                       self.db_filename_prefix)
        self.queue = queue
        self.parent = parent
        self.move_to_new_file_every_month = move_to_new_file_every_month
        self.zip_old_file = zip_old_file
        self.do_database_transition = do_database_transition

        self.current_year_month = get_current_year_month()

        if flushing_mode in FLUSHING_MODES:
            self.flushing_mode = flushing_mode
        else:
            print("unsopperted flushing_mode supplied, setting to be TIMED")
            self.flushing_mode = TIMED
        self.flushing_batch_size = flushing_batch_size
        self.flushing_timeout = flushing_timeout

        self._sigint_event = threading.Event()

        self.setDaemon(True)
        self.start()

    def _create_database_file_path(self, db_folder_path, db_filename_prefix):
        """Create a filename for the new sqlite file."""
        db_filename = f"{db_filename_prefix}_{get_current_year_month()}.db"
        return os.path.join(db_folder_path, db_filename)

    def _create_new_databade_table(self):
        """Create table."""
        query_arguments = ",".join([
            "{} {}".format(t[0], python_to_sqlite_types_cast_map[str(t[1])])
            for t in db_fields
        ])
        query = f"CREATE TABLE {db_table_name} ({query_arguments})"
        self.connection.execute(query)

    def _check_tupple_types(self, t):
        """Check if a content of the passed tupple corresponds to the db fields types."""
        if len(t) != len(db_fields):
            raise ValueError(
                f"Tupple value is {len(t)}, should be {len(db_fields)}")
            return False
        for obj in zip(t, db_fields):
            if not isinstance(obj[0], obj[1][1]):
                raise ValueError(
                    f"Tupple element {obj[0]} is type of {type(obj[0])}, should be {obj[1][1]}"
                )
                return False
        return True

    def get_connection(self, db_path):
        """Get connection to a database."""
        if os.path.exists(db_path):
            self.connection = sqlite3.connect(db_path)
        else:
            self.connection = sqlite3.connect(db_path)
            self._create_new_databade_table()

    def check_if_need_to_switch_file(self):
        """Check if year or month has changed."""
        if self.current_year_month != get_current_year_month():
            self.current_year_month = get_current_year_month()
            return True
        return False

    def archive_old_file(self, filepath):
        """
            TODO, spawn a subprocess to zip filepath and then delete original, 
            obv make sure it's safe and we are not loosing anything
        """
        pass

    def transition_to_new_database(self, old_db_path):
        """
            TODO some magic bullshit so frontend would not notice transition,
            Gerald suggested to clone 100 last logs from old to new
            i think we can use a secondary query for it
            or even main, just shovel those logs there to wait for new DB creation
        """
        pass

    def _sigint_handler(self):
        """
            This function is called by main thread when SIGINT recieved,
            once event is set - main loop will be wrapping up
        """
        self._sigint_event.set()

    def run(self):
        """Get tuples from queue and flush it to database."""
        self.get_connection(self.db_path)
        data_to_flush = []
        time_since_last_flush = time.time()
        gonna_flush_now = False
        flushed_counter = 0

        while True:
            try:
                if not self.queue.empty():
                    obj = self.queue.get(timeout=5.0)
                    if self._check_tupple_types(obj):
                        data_to_flush.append(obj)

                    # if batch reached size
                if ((self.flushing_mode == BATCHING
                     and len(data_to_flush) > self.flushing_batch_size) or
                        # if batch been waiting for too long
                    (self.flushing_mode == BATCHING and time_since_last_flush +
                     DEFAULT_FLUSHING_BATCHING_TIMEOUT <= time.time()) or
                        # if it is time bit.ly/30RJTbw
                    (self.flushing_mode == TIMED and time_since_last_flush +
                     self.flushing_timeout <= time.time())):
                    gonna_flush_now = True

                if gonna_flush_now:
                    placeholders = f'({",".join("?"*len(db_fields))})'
                    self.connection.executemany(
                        f"INSERT INTO {db_table_name} VALUES {placeholders}",
                        data_to_flush)
                    self.connection.commit()
                    gonna_flush_now = False
                    flushed_counter += len(data_to_flush)
                    data_to_flush = []
                    time_since_last_flush = time.time()

                if self.queue.empty():
                    if len(data_to_flush) == 0:
                        # if we have no logs waiting anywhere - we can check if need move to a new file
                        if self.move_to_new_file_every_month and self.check_if_need_to_switch_file(
                        ):
                            if self.zip_old_file:
                                self.archive_old_file(self.db_path)
                            if self.do_database_transition:
                                self.transition_to_new_database(self.db_path)
                            self.db_path = self._create_database_file_path(
                                self.db_folder_path, self.db_filename_prefix)
                            self.get_connection(self.db_path)

                        if self._sigint_event.is_set():
                            break
                    time.sleep(0.005)
            except sqlite3.OperationalError:
                import traceback
                print(traceback.format_exc())
                if not os.path.exists(self.db_path):
                    print(
                        "Seems like the database file has been deleted, don't worry, gonna create new one"
                    )
                    self.get_connection(self.db_path)

            except Exception:
                import traceback
                print(traceback.format_exc())
                print(data_to_flush)
                time.sleep(0.5)


def parse_arguments():
    """
        parse command line arguments
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-r',
                        '--rpc_port',
                        help='Piglet RPC Port',
                        default=rpc_ports["logger"])
    parser.add_argument('-l', '--log_level', help='LogLevel', default=20)
    parser.add_argument(
        '-p',
        '--db_path',
        help='Path to where sqlite files with logs will be stored',
        default=".")
    parser.add_argument(
        '-pr',
        '--db_filename_prefix',
        help='SQLite filename will be started with that prefix',
        default="")
    parser.add_argument('-m',
                        '--move_to_new_file_every_month',
                        help='Every month it will create new db file',
                        default=True)  # this is kinda wrong
    parser.add_argument(
        '-z',
        '--zip_old_file',
        help=
        'Archive old log files to preserve disk space, not implemented yet',
        default=False,
        action="store_true")
    parser.add_argument(
        '-t',
        '--transition_to_new_database',
        help='Do a smooth DB file transition, not implemented yet',
        default=False,
        action="store_true")
    parser.add_argument('-v',
                        '--verbose',
                        help='Print all recieved logs',
                        default=False,
                        action="store_true")

    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    print(f"LOLogger is about to start.")
    print(f"RPC server will be available at {args.rpc_port} in a sec.")
    lologger = LOLogger(
        db_folder_path=args.db_path,
        db_filename_prefix=args.db_filename_prefix,
        rpc_port=args.rpc_port,
        move_to_new_file_every_month=args.move_to_new_file_every_month,
        zip_old_file=args.zip_old_file,
        do_database_transition=args.transition_to_new_database,
        verbose=args.verbose)


# def test_shit():
#     # query_arguments = ",".join(" {} {}".format(t[0], python_to_sqlite_types_cast_map[str(t[1])]) for t in db_fields)
#     # query = f"CREATE TABLE Events ({query_arguments})"
#     # print(query)
#     l = LOLogger(db_folder_path=".", db_filename_prefix="DB_SERIAL", rpc_port=33050)
#     l.server.serve_forever()
#     # l.server.Launch()
#     # while True:
#     #     time.sleep(1)

#     print(f"logs_passed_to_queue main: {l.logs_passed_to_queue}")

#     # conn = sqlite3.connect('test.db')
#     # # Insert a row of data

#     # conn.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")

#     # # Save (commit) the changes
#     # conn.commit()

#     # # We can also close the connection if we are done with it.
#     # # Just be sure any changes have been committed or they will be lost.
#     # conn.close()

if __name__ == "__main__":
    # test_shit()
    # print("done")
    main()
