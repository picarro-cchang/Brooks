import common.CmdFIFO as CmdFIFO
import common.timeutils as timeutils
from common.rpc_ports import rpc_ports

ATTEMPT_TO_RECONNECT_AFTER_N_LOGS = 5

class LOLoggerClient():
    """
        LOLogger client.
    """
    def __init__(self, client_name="UnnamedClient", logger_address="localhost", port=rpc_ports["logger"], ip="", verbose=False):
        self.logger_address = logger_address
        self.port = port
        self.client_name = client_name
        self.ip = ip
        self.verbose = verbose
        self.connected = False
        self.server_path = f"http://{self.logger_address}:{self.port}"
        self.reconnect_counter = 0
        self.local_logs = []

        if self.connect_to_lollogger(True):
            self.connected = True
        else:
            print(f"WARNING!!! Failed to connect to LOLogger RPC on {self.server_path}! Forcing local verbose")
            self.verbose = True

    def Log(self, message, level=0):
        ClientTimestamp = str(timeutils.get_local_timestamp())
        if self.verbose:
            print(message)
        if not self.connected:
            if self.reconnect_counter >= ATTEMPT_TO_RECONNECT_AFTER_N_LOGS:
                self.reconnect_counter = 0
                if self.connect_to_lollogger(True):
                    self.connected = True
            else:
                self.reconnect_counter += 1


        if self.connected:
            try:
                self.lologger.LogEvent(log_message=message,
                                       level=level,
                                       client_name=self.client_name,
                                       ip=self.ip,
                                       client_timestamp=ClientTimestamp)
            except Exception as e:
                print(f"{e}")
                print(
                    f"{ClientTimestamp}:WARNING!!! Failed to connect to LOLogger RPC on {self.server_path}! Forcing local verbose")
                self.verbose = True
                self.connected = False
        else:
            self.local_logs.append({"log_message":message,
                                       "level":level,
                                       "client_name":self.client_name,
                                       "ip":self.ip,
                                       "client_timestamp":ClientTimestamp})

    def connect_to_lollogger(self, verbose=False):
        try:
            self.lologger = CmdFIFO.CmdFIFOServerProxy(self.server_path, ClientName=self.client_name)
            self.lologger.CmdFIFO.PingFIFO()
            return True
        except Exception as e:
            if verbose:
                print(f"{e}")
            return False

    def debug(self, message):
        self.Log(message, level=10)

    def info(self, message):
        self.Log(message, level=20)

    def warning(self, message):
        self.Log(message, level=30)

    def error(self, message):
        self.Log(message, level=40)

    def critical(self, message):
        self.Log(message, level=50)
