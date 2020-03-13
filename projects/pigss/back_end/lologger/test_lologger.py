import os
import json
import json
import time
import queue
import random
import signal
import sqlite3
import lologger
import contextlib
from datetime import datetime
from ipaddress import IPv4Address

from common.rpc_ports import rpc_ports

import unittest
from unittest import TestCase
from unittest.mock import Mock, patch, MagicMock

class LOLoggerTest(TestCase):
 
    def setUp(self):

        self.lologger = None
        self.file_name = ""
        self.hostname = os.uname()[1]

        self.tmp_path = "/tmp/"
        self.should_be_filename = f"{self.hostname}__{lologger.get_current_year_month()}.db"
        self.should_be_path = os.path.join(self.tmp_path, self.should_be_filename)
        # self.json_filepath = None

        self.conn = None
        self.created_files = queue.Queue()

    def tearDown(self):
        if self.lologger is not None:
            self.lologger._signal_handler(signal.SIGINT, None)
            del self.lologger
        if os.path.exists(self.should_be_path):
            os.remove(self.should_be_path)

        while not self.created_files.empty():
            file_to_delete = self.created_files.get()
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)

    def create_default_lologger(self, *args, **kwargs):
        default_lologger_args = {"db_folder_path":self.tmp_path,
                                 "db_filename_prefix":"",
                                 "db_filename_hostname":True,
                                 "rpc_port":rpc_ports["logger"],
                                 "flushing_mode":"TIMED",
                                 "flushing_batch_size":10,
                                 "flushing_timeout":1,
                                 "move_to_new_file_every_month":True,
                                 "zip_old_file":True,
                                 "do_database_transition":True,
                                 "verbose":False,
                                 "redundant_json":False,
                                 "meta_table":False,
                                 "pkg_meta":None,
                                 "picarro_version":False,
                                 "purge_old_logs":None}
        for k in kwargs:
            if k in default_lologger_args:
                default_lologger_args[k] = kwargs[k]

        lologger_to_return = lologger.LOLogger(**default_lologger_args)
        time.sleep(0.001)
        return lologger_to_return

    def wait_until_flushed(self, flushing_timeout=0.1):
        while not self.lologger.queue.empty():
            time.sleep(0.01)
        time.sleep(flushing_timeout*2)



# ______________TESTS_____________________________

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_init(self, CmdFIFO):
        self.lologger = self.create_default_lologger()
        assert(os.path.exists(self.should_be_path))
        
    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_get_sqlite_path(self, CmdFIFO):
        self.lologger = self.create_default_lologger()

        self.assertEqual(self.should_be_path, self.lologger.get_sqlite_path())

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        self.lologger.LogEvent(test_string)
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT LogMessage FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertIn(test_string, result)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent_with_client_name(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        test_client_name = f"test_client_{random.random()}"
        self.lologger.LogEvent(test_string, client_name=test_client_name)
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT ClientName FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertIn(test_client_name, result)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent_with_bad_client_name(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        test_client_name = random.random()
        self.lologger.LogEvent(test_string, client_name=test_client_name)
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT ClientName FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertNotIn(test_client_name, result)


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent_with_ip(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        test_client_ip = str(IPv4Address(random.getrandbits(32)))
        self.lologger.LogEvent(test_string, ip=test_client_ip)
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT IP FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertIn(test_client_ip, result)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent_with_client_timestamp(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        test_timestamp = datetime.now().isoformat(' ')
        self.lologger.LogEvent(test_string, client_timestamp=test_timestamp)
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT ClientTimestamp FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertIn(test_timestamp, result)


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent_with_level(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        test_log_level = random.randrange(1, 51)
        self.lologger.LogEvent(test_string, level=test_log_level)
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT Level FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertIn(test_log_level, result)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent_with_string_level(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        levels = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}
        test_log_level = random.choice([k for k in levels])
        self.lologger.LogEvent(test_string, level=test_log_level)
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT Level FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertIn(levels[test_log_level], result)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_LogEvent_with_bad_level(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        test_string = f"test_event_number {random.random()}"
        self.lologger.LogEvent(test_string, level="BAD_LEVEL")
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT LogMessage FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]
                    self.assertNotIn(test_string, result)


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_flipVerbose(self, CmdFIFO):
        self.lologger = self.create_default_lologger(verbose=True)
        self.lologger.flip_verbose()
        self.assertEqual(self.lologger.verbose, False)
        self.assertEqual(self.lologger.get_verbose(), False)
        self.lologger.flip_verbose()
        self.assertEqual(self.lologger.verbose, True)
        self.assertEqual(self.lologger.get_verbose(), True)
        self.lologger.LogEvent("verbosity_test")

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_set_log_level(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        random_level_to_set = random.randrange(10,40)
        self.lologger.set_log_level(random_level_to_set)
        self.assertEqual(random_level_to_set, self.lologger.LogLevel)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_set_bad_log_level(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        random_level_to_set = random.randrange(60,100)

        with self.assertRaises(ValueError):
            self.lologger.set_log_level(random_level_to_set)


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_set_log_level_as_string(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        levels = {"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10}
        for level_name in levels:
            self.lologger.set_log_level(level_name)
            self.assertEqual(self.lologger.get_log_level(), levels[level_name])


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_get_log_level(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        random_level_to_set = random.randrange(1,50)
        self.lologger.set_log_level(random_level_to_set)
        self.assertEqual(random_level_to_set, self.lologger.get_log_level())


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_log_level_acceptance(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_timeout=0.01)
        random_level_to_set = random.randrange(10,40)
        self.lologger.set_log_level(random_level_to_set)

        # pass messages above and below current log level
        random_messages_below = []
        random_messages_above = []
        for i in range(5):
            # create logs below acceptable log level
            test_string = f"test_event_number {random.random()}"
            while test_string in random_messages_below + random_messages_above: # to prevent collisions
                test_string = f"test_event_number {random.random()}"
            random_messages_below.append(test_string)
            random_level_below = random.randrange(1, random_level_to_set-1)
            self.lologger.LogEvent(test_string, level=random_level_below)

            # create logs above acceptable log level
            test_string = f"test_event_number {random.random()}"
            while test_string in random_messages_below + random_messages_above: # to prevent collisions
                test_string = f"test_event_number {random.random()}"
            random_messages_above.append(test_string)
            random_level_above = random.randrange(random_level_to_set+1,50)
            self.lologger.LogEvent(test_string, level=random_level_above)
        self.wait_until_flushed()

        # test messages correctly saved
        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT LogMessage FROM Events ")
                    result = cursor.fetchall()
                    result = [r[0] for r in result ]

                    for message in random_messages_below:
                        self.assertNotIn(message, result)

                    for message in random_messages_above:
                        self.assertIn(message, result)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_get_metadata(self, CmdFIFO):
        packages = ["curl", "bash"]
        self.lologger = self.create_default_lologger(pkg_meta=packages)
        meta = self.lologger.get_metadata()
        meta_dict = {k[0]:k[1] for k in meta}
        must_have_fields = ["system_sysname", "system_nodename", "system_release", "system_version", "boot_time", "time_zone"]
        must_have_fields += [f"pkg_{p}" for p in packages]

        for must_have_field in must_have_fields:
            self.assertIn(must_have_field, meta_dict)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_reuse_db_file(self, CmdFIFO):
        # create lologger and make some logs
        self.lologger = self.create_default_lologger(flushing_timeout=0.01, verbose=False)
        for i in range(100):
            self.lologger.LogEvent(f"Message_{i}")
        self.wait_until_flushed()

        # delete lologger
        self.lologger._signal_handler(signal.SIGINT, None)
        del self.lologger

        # create another lologger and make more logs
        self.lologger = self.create_default_lologger(flushing_timeout=0.01, verbose=False)
        for i in range(100):
            self.lologger.LogEvent(f"Message_{i+100}")
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT * FROM Events")
                    result = cursor.fetchall()
                    self.assertTrue(len(result)>=200)


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_fill_the_queue(self, CmdFIFO):
        # create lologger and make some logs
        self.lologger = self.create_default_lologger(flushing_timeout=0.01, verbose=False)
        for i in range(10000):
            self.lologger.LogEvent(f"Message_{i}")
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    cursor.execute("SELECT LogMessage FROM Events")
                    result = cursor.fetchall()
                    self.assertTrue(len(result)>=10000)

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_json_file(self, CmdFIFO):
        # create lologger and make some logs
        self.lologger = self.create_default_lologger(flushing_timeout=0.01, verbose=False, redundant_json=True)
        for i in range(100):
            self.lologger.LogEvent(f"Message_{i}")
        self.wait_until_flushed()
        json_filepath = self.should_be_path.replace(".db" , ".json")
        self.created_files.put(json_filepath)
        with open(json_filepath) as json_file:
            json_messages = [json.loads(l)["LogMessage"] for l in json_file.readlines()]
            for i in range(100):
                self.assertIn(f"Message_{i}", json_messages)


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_purging_old_files(self, CmdFIFO):

        today = datetime.today()
        total_months_today = today.year*12 + today.month
        purge_older_than = 6
        files_that_should_be_deleted = []
        files_that_should_not_be_deleted = []
        # timetravel to create old log files
        for i in range(purge_older_than*3, 0,-1):
            year, month = months_to_year_months(total_months_today - i)
            new_get_current_year_month_return_value = f"{year}_{month:0{2}}"
            # print(new_get_current_year_month_return_value)
            new_get_current_year_month = MagicMock(return_value=new_get_current_year_month_return_value)

            with patch('lologger.get_current_year_month', new=new_get_current_year_month):
                self.lologger = self.create_default_lologger(redundant_json=True)
                self.should_be_filename = f"{self.hostname}__{new_get_current_year_month_return_value}.db"
                self.should_be_path = os.path.join(self.tmp_path, self.should_be_filename)
                self.created_files.put(self.should_be_path)
                self.created_files.put(self.should_be_path.replace(".db", ".json"))
                if i >= purge_older_than:
                    files_that_should_be_deleted.append(self.should_be_path)
                    files_that_should_be_deleted.append(self.should_be_path.replace(".db", ".json"))
                else:
                    files_that_should_not_be_deleted.append(self.should_be_path)
                    files_that_should_not_be_deleted.append(self.should_be_path.replace(".db", ".json"))
                # delete lologger
                self.lologger._signal_handler(signal.SIGINT, None)
                del self.lologger

            self.assertTrue(os.path.exists(self.should_be_path)) 


        # back to present - fail to purge old log files
        self.lologger = self.create_default_lologger(purge_old_logs="Bad input")
        self.should_be_filename = f"{self.hostname}__{lologger.get_current_year_month()}.db"
        self.should_be_path = os.path.join(self.tmp_path, self.should_be_filename)
        time.sleep(0.1)

        for file in files_that_should_be_deleted:
            self.assertTrue(os.path.exists(file))

        for file in files_that_should_not_be_deleted:
            self.assertTrue(os.path.exists(file))

        # back to present - purge old log files
        self.lologger = self.create_default_lologger(purge_old_logs=purge_older_than)
        self.should_be_filename = f"{self.hostname}__{lologger.get_current_year_month()}.db"
        self.should_be_path = os.path.join(self.tmp_path, self.should_be_filename)
        time.sleep(0.1)

        for file in files_that_should_be_deleted:
            self.assertFalse(os.path.exists(file))

        for file in files_that_should_not_be_deleted:
            self.assertTrue(os.path.exists(file))


    def test_cmd_args(self):
        args= ["","-v", "-j"]
        with patch('sys.argv', new=args):
            arguments = vars(lologger.parse_arguments())
        self.assertTrue(arguments["verbose"])
        self.assertTrue(arguments["json"])
        self.assertFalse(arguments["transition_to_new_database"])

    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_bad_flushing_mode(self, CmdFIFO):
        self.lologger = self.create_default_lologger(flushing_mode="BAD ONE")
        self.assertEqual(self.lologger.flushing_mode, lologger.TIMED)


    @patch('common.CmdFIFO.CmdFIFOServer')
    def test_meta_data_table(self, CmdFIFO):
        pkg_to_mess_with = "bash"
        self.lologger = self.create_default_lologger(flushing_timeout=0.01, meta_table=True, pkg_meta=[pkg_to_mess_with])
        self.lologger.LogEvent(f"Message")
        self.wait_until_flushed()

        # delete lologger
        self.lologger._signal_handler(signal.SIGINT, None)
        del self.lologger


        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    # check for metadata in file
                    cursor.execute("SELECT * FROM metadata")
                    result = cursor.fetchall()
                    meta_dict = {k[0]:k[1] for k in result}

                    # alter some metadata in file
                    pkg_name = f"pkg_{pkg_to_mess_with}"
                    pkg_version = meta_dict[pkg_name] 
                    cursor.execute("REPLACE INTO metadata VALUES (?, ?)", (pkg_name, pkg_version[::-1]))

                    # check that metadata been altered
                    cursor.execute("SELECT * FROM metadata")
                    result = cursor.fetchall()
                    meta_dict = {k[0]:k[1] for k in result}
                    self.assertEqual(meta_dict[pkg_name], pkg_version[::-1])

        # submit some message
        self.lologger = self.create_default_lologger(flushing_timeout=0.01, meta_table=True, pkg_meta=[pkg_to_mess_with])
        self.lologger.LogEvent(f"Second message")
        self.wait_until_flushed()

        with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes

                    # check for metadata again - it should be restored to initial
                    cursor.execute("SELECT * FROM metadata")
                    result = cursor.fetchall()
                    meta_dict = {k[0]:k[1] for k in result}
                    self.assertEqual(meta_dict[pkg_name], pkg_version)

#this test doesn't work as intended - fix
    # @patch('common.CmdFIFO.CmdFIFOServer')
    # def test_panic(self, CmdFIFO):
    #     # test raising an error while flushing the data
    #     # possible reasons - file is being blocked by other thread 
    #     pkg_to_mess_with = "bash"
    #     self.lologger = self.create_default_lologger(flushing_timeout=0.01, meta_table=True, pkg_meta=[pkg_to_mess_with])
    #     self.lologger.LogEvent(f"Message")
    #     self.wait_until_flushed()

    #     with contextlib.closing(sqlite3.connect(self.should_be_path)) as conn: # auto-closes
    #         with conn: # auto-commits
    #             with contextlib.closing(conn.cursor()) as cursor: # auto-closes

    #                 os.remove(self.should_be_path)
    #                 # submit some message - should not be able to submit
    #                 test_string = f"test_event_number {random.random()}"
    #                 self.lologger.LogEvent(test_string)
    #                 self.wait_until_flushed()

    #                 cursor.execute("SELECT LogMessage FROM Events ")
    #                 result = cursor.fetchall()
    #                 result = [r[0] for r in result ]
    #                 self.assertNotIn(test_string, result)


#this test is not finished
    # @patch('common.CmdFIFO.CmdFIFOServer')
    # def test_moving_to_new_month(self, CmdFIFO):

    #     new_check_if_need_to_switch_file = MagicMock(side_effect=[False, False, False, False, True])
    #     new_get_current_year_month
    #     with patch('lologger.LOLoggerThread.check_if_need_to_switch_file', new=new_check_if_need_to_switch_file):
    #         self.lologger = self.create_default_lologger(flushing_timeout=0.01)
    #         self.lologger.LogEvent(f"Message")
    #         self.wait_until_flushed()



def months_to_year_months(months):
    return int(months/12), months%12 


#160-162 hardware_failure
#292     dunno how to 
#317-318
#322
#344-345
#353
#362
#442-443
#456-457 flushing json fail panic
#512-519
#525-529
#580-587
#604