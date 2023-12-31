import os
import time
import json
import queue
import signal
import sqlite3
import threading
from datetime import datetime

import common.CmdFIFO as CmdFIFO
import common.timeutils as timeutils
from common.rpc_ports import rpc_ports
from common.meta_data_collector import get_metadata_ready_for_db
"""
    LOLogger: a logging service with RPC server capabilities. At current implementation it
    accepts logs using RPC function LogEvent() with multiple optional arguments. It is
    encoraged that function caller would supply as many of those arguments as possible.
    Passed log messages would be passed to an SQLite database. Each month SQLite dile will
    be changed to prevent creating huge log files and add convinience for when costumer has
    to give us logs files for some bugs.

    RACE CONDITION:
    Service contains 3 threads: main, CMDFIFOserver and looping thread. Loop thread is daemonic,
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
db_fields = [("ClientTimestamp", str), ("ClientName", str), ("EpochTime", int), ("LogMessage", str), ("Level", int), ("IP", str)]

python_to_sqlite_types_cast_map = {"<class 'str'>": "text", "<class 'int'>": "int"}

# database flushing stuff:
FLUSHING_MODES = ["BATCHING", "TIMED"]
BATCHING = FLUSHING_MODES[0]
TIMED = FLUSHING_MODES[1]
DEFAULT_FLUSHING_BATCH_SIZE = 10
DEFAULT_FLUSHING_BATCHING_TIMEOUT = 60
DEFAULT_FLUSHING_TIMEOUT = 1

LOG_LEVELS_RANGE = range(0, 51)
LOG_LEVELS = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10, "NOTSET": 0}

MOVE_TO_NEW_FILE_EVERY_MONTH = True

DEFAULT_DB_PATH = "."  # TODO

FILE_TRACKING_DB_FILENAME = "lologger_file_tracking.db"

def get_current_year_month():
    today = datetime.today()
    return f"{today.year}_{today.month:0{2}}"

def approximate_end_of_the_month():
    # this function will calculate approximate end of the month
    # it is not neccessary for this method to return exact epoch time of the end of the month
    # rather to make sure it is close enough and be above the actual end of the month.
    # calculating the actual end of the month in the local time zone in epoch time would be too
    # complicated, since we can't guarantee that we can always know current time zone and UTC offset
    # and without further ado:
    today = datetime.today()
    current_year = today.year
    current_month = today.month

    if current_month==12:
        next_month = 1
        next_year = current_year + 1
    else:
        next_month = current_month + 1
        next_year = current_year
    return today.replace(year=next_year,
                         month=next_month,
                         day=2,
                         hour=0,
                         minute=0,
                         second=0,
                         microsecond=0).timestamp()

class LOLogger(object):
    def __init__(self,
                 db_folder_path,
                 db_filename_prefix,
                 rpc_port,
                 db_filename_hostname=None,
                 rpc_server_name="LOLogger",
                 rpc_server_description="Universal log collector, flushes to sqlite",
                 flushing_mode=TIMED,
                 flushing_batch_size=10,
                 flushing_timeout=1,
                 move_to_new_file_every_month=MOVE_TO_NEW_FILE_EVERY_MONTH,
                 verbose=True,
                 log_level=1,
                 redundant_json=False,
                 meta_table=False,
                 pkg_meta=None,
                 picarro_version=False,
                 purge_old_logs=None,
                 file_tracking=True):
        self.db_folder_path = db_folder_path
        self.db_filename_prefix = db_filename_prefix
        self.db_filename_hostname = db_filename_hostname
        self.rpc_port = int(rpc_port)
        self.rpc_server_name = rpc_server_name
        self.rpc_server_description = rpc_server_description

        if flushing_mode in FLUSHING_MODES:
            self.flushing_mode = flushing_mode
        else:
            print("unsupported flushing_mode supplied, setting to be TIMED")
            self.flushing_mode = TIMED
        self.flushing_batch_size = flushing_batch_size
        self.flushing_timeout = flushing_timeout

        self.move_to_new_file_every_month = move_to_new_file_every_month

        self.queue = queue.Queue(maxsize=2048)
        self.verbose = verbose
        self.LogLevel = log_level
        self.logs_passed_to_queue = 0
        self.redundant_json = redundant_json
        self.file_tracking = file_tracking

        self.meta_table = meta_table
        self.pkg_meta = pkg_meta
        self.picarro_version = picarro_version
        self.purge_old_logs = purge_old_logs

        self.server = CmdFIFO.CmdFIFOServer(("", self.rpc_port),
                                            ServerName=self.rpc_server_name,
                                            ServerDescription=self.rpc_server_description,
                                            threaded=True)

        self.lologger_thread = LOLoggerThread(db_folder_path=self.db_folder_path,
                                              db_filename_prefix=self.db_filename_prefix,
                                              db_filename_hostname=self.db_filename_hostname,
                                              queue=self.queue,
                                              parent=self,
                                              flushing_mode=self.flushing_mode,
                                              flushing_batch_size=self.flushing_batch_size,
                                              flushing_timeout=self.flushing_timeout,
                                              move_to_new_file_every_month=self.move_to_new_file_every_month,
                                              redundant_json=self.redundant_json,
                                              meta_table=self.meta_table,
                                              pkg_meta=self.pkg_meta,
                                              picarro_version=self.picarro_version,
                                              purge_old_logs=self.purge_old_logs,
                                              file_tracking=self.file_tracking)

        self.register_rpc_functions()

        signal.signal(signal.SIGINT, self._signal_handler)

        self.server.serve_forever()

    def LogEvent(self, log_message, client_name="AnonymService", ip="localhost", client_timestamp=None, level=30):
        if level in LOG_LEVELS_RANGE:
            passed_level = level
        elif level in LOG_LEVELS:
            passed_level = LOG_LEVELS[level]
        else:
            return
        if passed_level >= self.LogLevel:
            if client_timestamp is None:
                client_timestamp = str(timeutils.get_local_timestamp())
            EpochTime = int(1000 * timeutils.get_epoch_timestamp())

            values = [client_timestamp, client_name, EpochTime, log_message, passed_level, ip]
            try:
                self.queue.put_nowait(values)
            except queue.Full:
                temp_queue = queue.Queue(maxsize=2 * self.queue.qsize())
                while not self.queue.empty():
                    temp_queue.put(self.queue.get())
                self.queue = temp_queue
                self.lologger_thread.queue = self.queue
                self.queue.put_nowait(values)
            except MemoryError:
                # TO DO
                print("IF THIS HAS REACHED, WE MIGHT NEED NEW STRATEGY")

            self.logs_passed_to_queue += 1
            if self.verbose:
                print(f"{client_timestamp}:::{client_name} :: L-{passed_level} :: -  {log_message}")

    def register_rpc_functions(self):
        self.server.register_function(self.LogEvent)
        self.server.register_function(self.flip_verbose)
        self.server.register_function(self.get_verbose)
        self.server.register_function(self.set_log_level)
        self.server.register_function(self.get_log_level)
        self.server.register_function(self.get_sqlite_path)
        self.server.register_function(self.get_metadata)


    def flip_verbose(self):
        """Switch verbose value to opposite from current."""
        self.verbose = not self.verbose
        return True

    def get_verbose(self):
        """Return current verbose value."""
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
            message = f"""Level passed: {Level}; Should be between {LOG_LEVELS_RANGE[0]}:{LOG_LEVELS_RANGE[-1]}"""
            self.LogEvent(message, client_name="LOLogger", level=40)
            raise ValueError(message)
        return True

    def get_log_level(self):
        """Get current log level."""
        return self.LogLevel

    def get_sqlite_path(self):
        """Get path of the curretn sqlite DB file"""
        return self.lologger_thread.db_path

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

    def get_metadata(self):
        """
            This function will return current system's metadata, 
            as well as flush this metadata to Events table
        """
        metadata = self.lologger_thread.collect_metadata()
        self.LogEvent(json.dumps(metadata), client_name="LOLogger", level=10)
        return metadata

class LOLoggerThread(threading.Thread):
    """
        Thread that will be dealing with sqlite database.
    """

    def __init__(self,
                 db_folder_path,
                 db_filename_prefix,
                 db_filename_hostname,
                 queue,
                 parent,
                 flushing_mode=TIMED,
                 flushing_batch_size=10,
                 flushing_timeout=1,
                 move_to_new_file_every_month=MOVE_TO_NEW_FILE_EVERY_MONTH,
                 redundant_json=False,
                 meta_table=False,
                 pkg_meta=None,
                 picarro_version=False,
                 purge_old_logs=None,
                 file_tracking=True):
        threading.Thread.__init__(self, name="LOLoggerThread")
        self.db_folder_path = db_folder_path
        self.db_filename_prefix = db_filename_prefix
        self.db_filename_hostname = db_filename_hostname
        self.db_path = self._create_database_file_path()
        self.queue = queue
        self.parent = parent
        self.move_to_new_file_every_month = move_to_new_file_every_month
        self.redundant_json = redundant_json
        self.file_tracking = file_tracking
        if self.file_tracking and self.move_to_new_file_every_month:
            self.file_tracking_db_path = self._create_database_file_path(True)

        self.current_year_month = get_current_year_month()

        self.flushing_mode = flushing_mode
        self.flushing_batch_size = flushing_batch_size
        self.flushing_timeout = flushing_timeout

        self._sigint_event = threading.Event()

        self.start_time = time.time()
        self.meta_table = meta_table
        self.pkg_meta = pkg_meta
        self.picarro_version = picarro_version
        self.purge_old_logs = purge_old_logs

        self.data_to_flush = []

        self.setDaemon(True)
        self.start()

    def get_rowid_from_db_connection(self, connection):
        """Get last ROWID from connected database"""
        last_row_id = connection.execute(f"select max(rowid) from {db_table_name}").fetchone()[0]
        if last_row_id is None:
            return 0
        else:
            return last_row_id

    def _create_database_file_path(self, file_tracking_db=False):
        """Create a filename for the new sqlite file."""
        if file_tracking_db:
            db_filename = f"{self.db_filename_prefix}_{FILE_TRACKING_DB_FILENAME}"
        else:
            db_filename = f"{self.db_filename_prefix}_{get_current_year_month()}.db"
        self.full_prefix = f"{self.db_filename_prefix}_"
        if self.db_filename_hostname is not None:
            self.full_prefix = f"{os.uname()[1]}_{self.full_prefix}"
            db_filename = f"{os.uname()[1]}_{db_filename}"
        return os.path.join(self.db_folder_path, db_filename)

    def _create_new_database_table(self):
        """Create table."""
        query_arguments = ",".join(["{} {}".format(t[0], python_to_sqlite_types_cast_map[str(t[1])]) for t in db_fields])
        query = f"CREATE TABLE {db_table_name} ({query_arguments})"
        self.connection.execute(query)
        if self.meta_table:
            query = f"CREATE TABLE metadata (field text PRIMARY KEY, value text)"
            self.connection.execute(query)

    def _check_tupple_types(self, t):
        """Check if a content of the passed tupple corresponds to the db fields types."""
        if len(t) != len(db_fields):
            raise ValueError(f"Tupple value is {len(t)}, should be {len(db_fields)}")
            return False
        for obj in zip(t, db_fields):
            if not isinstance(obj[0], obj[1][1]):
                raise ValueError(f"Tuple element {obj[0]} is type of {type(obj[0])}, should be {obj[1][1]}")
                return False
        return True

    def get_connection(self, db_path):
        """Get connection to a database and redundunt json file if needed."""
        if os.path.exists(db_path):
            self.connection = sqlite3.connect(db_path)
            self.rowid = self.get_rowid_from_db_connection(self.connection)
        else:
            self.connection = sqlite3.connect(db_path)
            self._create_new_database_table()
            self.rowid = 0
        if self.file_tracking and self.move_to_new_file_every_month:
            self.add_entry_to_file_tracking(db_path)
        if self.redundant_json:
            db_extension = os.path.splitext(db_path)[1]
            json_file_path = db_path.replace(db_extension, ".json")
            self.json_file = open(json_file_path, "a")
        if self.purge_old_logs is not None:
            self.get_purging_old_logs_done()


    def add_entry_to_file_tracking(self, db_path):
        # create connection to file_tracking_db
        if os.path.exists(self.file_tracking_db_path):
            self.file_tracking_db_connection = sqlite3.connect(self.file_tracking_db_path)
        else:
            self.file_tracking_db_connection = sqlite3.connect(self.file_tracking_db_path)
            query = '''CREATE TABLE db_entry (filepath TEXT NOT NULL PRIMARY KEY,
                         start_date INTEGER NOT NULL, end_date INTEGER NOT NULL)'''
            self.file_tracking_db_connection.execute(query)
        cursor = self.file_tracking_db_connection.cursor()

        # check if db_path present in the file_tracking_db
        cursor.execute("SELECT * FROM db_entry WHERE filepath=?", (db_path,))
        if len(cursor.fetchall()) == 0:
            # if not - make an entry with current time as start_date and approximate date for end_date
            start_date = int(datetime.now().timestamp())
            approximate_upper_bound_end = int(approximate_end_of_the_month())

            # insert to file_tracking_db
            cursor.execute(''' INSERT INTO db_entry(filepath,start_date,end_date)
              VALUES(?,?,?) ''', (db_path,start_date ,approximate_upper_bound_end))
            self.file_tracking_db_connection.commit()

        # close connection to file_tracking_db
        cursor.close()
        self.file_tracking_db_connection.close()

    def end_file_tracking(self, db_path):
        # function that should be called in the end of the month if file tracking is enabled.
        # it will replace the value "end_date" in the file_tracking_db for the passed db_path argument.
        # previous value is an earlier made approximation, to be reaplaced with an exact
        # epochtime of the last log message before moving to new months file
        self.file_tracking_db_connection = sqlite3.connect(self.file_tracking_db_path)
        cursor = self.file_tracking_db_connection.cursor()
        cursor.execute("SELECT * FROM db_entry WHERE filepath=?", (db_path,))
        entry = cursor.fetchall()[0]
        start_date = entry[1] # needs to be preserved while replacing end_date
        end_date = int(datetime.now().timestamp())
        replacing_query = "REPLACE INTO db_entry (filepath, start_date, end_date) values (?, ?, ?);"
        cursor.execute(replacing_query, (db_path, start_date, end_date, ))
        self.file_tracking_db_connection.commit()
        time.sleep(1)

        # check with db that all went well
        cursor.execute("SELECT * FROM db_entry WHERE filepath=?", (db_path,))
        entry = cursor.fetchall()[0]
        fetched_end_date = entry[2]
        if end_date != fetched_end_date:
            self.flush_internal_log_messages(f"Failed to update end_date for {db_path} in the file_tracking_db", level=40)

    def check_if_need_to_switch_file(self):
        """Check if year or month has changed."""
        if self.current_year_month != get_current_year_month():
            self.current_year_month = get_current_year_month()
            return True
        return False

    def _sigint_handler(self):
        """
            This function is called by main thread when SIGINT recieved,
            once event is set - main loop will be wrapping up
        """
        self._sigint_event.set()

    def exit_sequence(self):
        """Close connection to db and json file if needed"""
        self.flush_internal_log_messages("Last message before closing connection")
        self.connection.close()
        if self.redundant_json:
            self.json_file.close()

    def collect_metadata(self):
        """
            Prepare metadata for database
        """
        meta_dict = get_metadata_ready_for_db(self.pkg_meta, self.picarro_version)
        meta_dict.append(("lologger_start_time", self.start_time))
        return meta_dict

    def flush_metadata_as_event(self):
        self.flush_internal_log_messages("Current metadata:")
        metadata = self.collect_metadata()
        self.flush_internal_log_messages(json.dumps(metadata))
        return metadata

    def get_purging_old_logs_done(self):
        """
            Delete old logs files if they are older than self.duration
        """
        if not isinstance(self.purge_old_logs, int) and not self.purge_old_logs.isdigit():
            return False
        # get list of files
        filelist = [f for f in os.listdir(self.db_folder_path) if os.path.isfile(os.path.join(self.db_folder_path, f))]

        today = datetime.today()
        current_month_count = today.year * 12 + today.month

        for filename in filelist:
            # check if actual log file
            if filename.startswith(self.full_prefix) and filename.endswith(".db"):
                # check if old enough
                year, month = [k for k in filename[len(self.full_prefix):-3].split("_") if k]
                if current_month_count - (int(year) * 12 + int(month)) >= int(self.purge_old_logs):
                    # the file appeared to be older than purge period - gonna be deleted
                    db_filepath = os.path.join(self.db_folder_path, filename)
                    self.flush_internal_log_messages(f"Deleting file: {db_filepath}", level=20)
                    os.remove(db_filepath)
                    json_filepath = db_filepath.replace(".db", ".json")
                    if os.path.exists(json_filepath):
                        self.flush_internal_log_messages(f"Deleting file: {json_filepath}", level=20)
                        os.remove(json_filepath)

        return True


    def flush_internal_log_messages(self, message, level=10):
        client_timestamp = str(timeutils.get_local_timestamp())
        epoch_time = int(1000 * timeutils.get_epoch_timestamp())
        data_to_flush = [client_timestamp, "LOLogger", epoch_time, message, level, "localhost"]

        if self.parent.verbose:
            print(f"{client_timestamp}:::LOLogger :: L-{level} :: -  {message}")

        self.flush_log(data_to_flush, executemany=False)

    def flush_log(self, data_to_flush, executemany=True):
        placeholders = f'({",".join("?"*len(db_fields))})'
        if not executemany:
            data_to_flush = [data_to_flush]
        try:
            self.connection.executemany(f"INSERT INTO {db_table_name} VALUES {placeholders}", data_to_flush)
            self.connection.commit()

            if self.meta_table:
                # insert metadata here
                self.connection.executemany(f"REPLACE INTO metadata VALUES (?, ?)", self.collect_metadata())
                self.connection.commit()

            if self.redundant_json:
                string_to_flush = ""
                for data in data_to_flush:
                    obj_for_json = {col_name[0]: value for col_name, value in zip(db_fields, data)}
                    obj_for_json["rowid"] = self.rowid
                    self.rowid += 1
                    string_row = json.dumps(obj_for_json)
                    string_to_flush = f"{string_to_flush}{string_row}\n"
                try:
                    self.json_file.write(string_to_flush)
                    self.json_file.flush()
                except ValueError as e:
                    self.flush_internal_log_messages(f"""ValueError while tried to write to json file: {e}\n
                                                         Going to stop writing logs to json file""", level=40)
        except sqlite3.OperationalError as e:
            raise e
        except Exception as e:
                # absolute panic mode! logs can't be flushed
                # i don't know what possibly can lead to this place and 
                # i honesty don't know what cource of action i should implement here.
                import traceback
                print(traceback.format_exc())



    def run(self):
        """Get tuples from queue and flush it to database."""
        self.get_connection(self.db_path)

        if self.purge_old_logs is not None:
            self.get_purging_old_logs_done()

        time_since_last_flush = time.time()
        gonna_flush_now = False
        flushed_counter = 0

        self.flush_internal_log_messages("Starting lologger")

        if self.meta_table:
            self.flush_metadata_as_event()

        while True:
            try:
                if not self.queue.empty():
                    obj = self.queue.get(timeout=5.0)
                    if self._check_tupple_types(obj):
                        self.data_to_flush.append(obj)

                # if batch reached size
                if ((self.flushing_mode == BATCHING and len(self.data_to_flush) > self.flushing_batch_size) or
                        # if batch been waiting for too long
                    (self.flushing_mode == BATCHING and time_since_last_flush + DEFAULT_FLUSHING_BATCHING_TIMEOUT <= time.time()) or
                        # if it is time bit.ly/30RJTbw
                    (self.flushing_mode == TIMED and abs(time.time() - time_since_last_flush) >= self.flushing_timeout )):
                    gonna_flush_now = True

                if gonna_flush_now and len(self.data_to_flush) > 0:

                    self.flush_log(self.data_to_flush)

                    gonna_flush_now = False
                    flushed_counter += len(self.data_to_flush)
                    self.data_to_flush = []
                    time_since_last_flush = time.time()

                if self.queue.empty():
                    if len(self.data_to_flush) == 0:
                        # if we have no logs waiting anywhere - we can check if need move to a new file
                        if self.move_to_new_file_every_month and self.check_if_need_to_switch_file():
                            if self.redundant_json:
                                self.json_file.close()
                            if self.file_tracking:
                                self.end_file_tracking(self.db_path)
                            self.db_path = self._create_database_file_path()
                            self.get_connection(self.db_path)

                        if self._sigint_event.is_set():
                            break
                    time.sleep(0.005)
            except sqlite3.OperationalError:
                import traceback
                if not os.path.exists(self.db_path):
                    self.get_connection(self.db_path)
                    self.flush_internal_log_messages(traceback.format_exc(), level=30)
                    self.flush_internal_log_messages("Creating new db file", level=30)

            except Exception:
                import traceback
                self.flush_internal_log_messages(traceback.format_exc(), level=40)
        self.exit_sequence()


def parse_arguments():
    """
        parse command line arguments
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rpc_port', help='Piglet RPC Port', default=rpc_ports["logger"])
    parser.add_argument('-l', '--log_level', help='LogLevel: all the logs below that level will be ignored', default=1)
    parser.add_argument('-p', '--db_path', help='Path to where sqlite files with logs will be stored', default=os.getcwd())
    parser.add_argument('-pr', '--db_filename_prefix', help='SQLite filename will be started with that prefix', default="")
    parser.add_argument('-prh',
                        '--db_filename_prefix_hostname',
                        help='SQLite filename will be started with that hostname',
                        default=None,
                        action="store_true")
    parser.add_argument('-m', '--move_to_new_file_every_month', help='Every month it will create new db file',
                        default=True)  # this is kinda wrong
    parser.add_argument('-v', '--verbose', help='Print all recieved logs', default=False, action="store_true")
    parser.add_argument('-j', '--json', help='Write redundunt logs to json file', default=False, action="store_true")
    parser.add_argument('-meta', '--meta_table', help='Create a table with metadata', default=False, action="store_true")
    parser.add_argument('-pkg', '--pkg_meta', nargs='+', help='Add versions of the passed packages to the metadata table')
    parser.add_argument('-pv',
                        '--picarro_version',
                        help='Store version of Picarro OS in metadata',
                        default=False,
                        action="store_true")
    parser.add_argument('-pol', '--purge_old_logs', help='Will delete log files older than provided number of months', default=None)
    parser.add_argument('-fl', '--file_tracking', help='Will create a separate db file to track created log files', default=True)

    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    print(f"LOLogger is about to start.")
    print(f"RPC server will be available at {args.rpc_port} in a sec.")

    if not os.path.isabs(args.db_path):
        args.db_path = os.path.abspath(args.db_path)

    lologger = LOLogger(
        db_folder_path=args.db_path,  # noqa
        db_filename_prefix=args.db_filename_prefix,
        db_filename_hostname=args.db_filename_prefix_hostname,
        rpc_port=args.rpc_port,
        move_to_new_file_every_month=args.move_to_new_file_every_month,
        verbose=args.verbose,
        log_level=args.log_level,
        redundant_json=args.json,
        meta_table=args.meta_table,
        pkg_meta=args.pkg_meta,
        picarro_version=args.picarro_version,
        purge_old_logs=args.purge_old_logs,
        file_tracking=args.file_tracking)

if __name__ == "__main__":
    main()
