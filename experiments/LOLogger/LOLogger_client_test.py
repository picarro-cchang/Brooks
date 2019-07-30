import random
import string
import time
import host.experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO
# import timeutils # fix when path fixed
import host.experiments.common.timeutils
from rpc_ports import rpc_ports
from LOLoggerClient import LOLoggerClient


# class LOLoggerClient():
#     """
#         A wrapper around CmdFIFO proxy for logger
#     """
#     def __init__(self, 
#                  logger_address="localhost", 
#                  port=rpc_ports["logger"], 
#                  ClientName="UnnamedClient",
#                  ip=""):
#         self.logger_address = logger_address
#         self.port = port
#         self.ip = ip
#         self.ClientName = ClientName
#         self.lologger = CmdFIFO.CmdFIFOServerProxy(f"http://{self.logger_address}:{self.port}", 
#                                                    ClientName = self.ClientName)


#     def Log(self, message, Level=0):
#         ClientTimestamp = str(timeutils.get_local_timestamp())
#         self.lologger.LogEvent(LogMessage=message,
#                                Level=Level,
#                                ClientName=self.ClientName,
#                                ip=self.ip,
#                                ClientTimestamp=ClientTimestamp)
    
#     def debug(self, message): self.Log( message, Level=10)
#     def info(self, message): self.Log( message, Level=20)
#     def warning(self, message): self.Log( message, Level=30)
#     def error(self, message): self.Log( message, Level=40)
#     def critical(self, message): self.Log( message, Level=50)




def randomString(stringLength=10):
    """Generate a random string of fixed length """
    if stringLength<0:
        stringLength = random.randint(5, 1000)
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

class LOLoggerTester:
    """
        DOCSTRING EHERE YOu
    """
    def __init__(self):
        self.counter = 0
        self.lologger = CmdFIFO.CmdFIFOServerProxy("http://10.100.3.28:%d" % 33050, ClientName = "LOLOGGER_CLIENTTEST")
        self.use_set_of_logs = True

    def generate_set_of_logs(self, size=100):
        self.set_of_logs = []
        for _ in range(size):
            self.set_of_logs.append(randomString(-1))

    def do_testing(self):
        self.lologger.LogEvent("12;DROP TABLE Events", Level=51, ClientName="LOLOGGER_CLIENTTEST", ip="localhost")

    def generate_minute_worth_of_logs(self,delay=1):
        for _ in range(60):
            if self.use_set_of_logs:
                message = self.set_of_logs[random.randint(0, len(self.set_of_logs)-1)]
            else:
                message = randomString(-1)
            message = f"{self.counter:0{10}}:::{message}"
            self.lologger.LogEvent(message, Level=random.randint(1,5), ClientName="logger_teste_pew_pew", ip="localhost")
            time.sleep(delay)
            self.counter +=1

    def generate_hour_worth_of_logs(self, delay=1, minutes=60):
        for i in range(minutes):
            self.generate_minute_worth_of_logs(delay)
            time.sleep(delay)
            print(f"{i} minutes passed")

    def generate_day_worth_of_logs(self, delay=1):
        for i in range(24):
            self.generate_hour_worth_of_logs(delay)
            time.sleep(delay)
            print(f"{i} hours passed")

    def generate_month_worth_of_logs(self, delay=1):
        for i in range(30):
            self.generate_day_worth_of_logs(delay)
            time.sleep(delay)
            print(f"{i} days passed")


    def generate_year_worth_of_logs(self, delay=1):
        for i in range(12):
            self.generate_month_worth_of_logs(delay)
            time.sleep(delay)
            print(f"{i} months passed")



# start_time = time.time()
# lologger_tester = LOLoggerTester()
# lologger_tester.generate_set_of_logs()
# try:
#     lologger_tester.generate_day_worth_of_logs(0.01)
# except Exception:
#     import traceback
#     print(traceback.format_exc())

# print(f"counter is {lologger_tester.counter}")

# # print(lologger_tester.counter)
# # lologger_tester.do_testing()
# print(f"done in {time.time() - start_time}")





l = LOLoggerClient(ClientName="TESTER")
l.debug("DEBUGGING")
l.info("INFORRMING")
l.warning("WARNING PEOPLE")
l.error("ERRORING")
l.critical("CRITICIZING")