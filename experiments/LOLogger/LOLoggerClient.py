import host.experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO
import host.experiments.common.timeutils as timeutils # fix when path fixed
from host.experiments.common.rpc_ports import rpc_ports

class LOLoggerClient():
    """
        A wrapper around CmdFIFO proxy for logger
    """
    def __init__(self, 
                 client_name="UnnamedClient",
                 logger_address="localhost", 
                 port=rpc_ports["logger"], 
                 ip="",
                 verbose=False):
        self.logger_address = logger_address
        self.port = port
        self.client_name = client_name
        self.ip = ip
        self.verbose = verbose
        self.lologger = CmdFIFO.CmdFIFOServerProxy(f"http://{self.logger_address}:{self.port}", 
                                                   ClientName = self.client_name)


    def Log(self, message, level=0):
        ClientTimestamp = str(timeutils.get_local_timestamp())
        if self.verbose: print(message)
        self.lologger.LogEvent(log_message=message,
                               level=level,
                               client_name=self.client_name,
                               ip=self.ip,
                               client_timestamp=ClientTimestamp)
    
    def debug(self, message): self.Log(message, level=10)
    def info(self, message): self.Log(message, level=20)
    def warning(self, message): self.Log(message, level=30)
    def error(self, message): self.Log(message, level=40)
    def critical(self, message): self.Log(message, level=50)
