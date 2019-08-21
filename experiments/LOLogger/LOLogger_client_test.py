import random
import string
import time
import host.experiments.common.timeutils
import host.experiments.testing.cmd_fifo.CmdFIFO as CmdFIFO
# import timeutils # path for pk debugging
# import CmdFIFO as CmdFIFO # path for pk debugging
# from rpc_ports import rpc_ports # path for pk debugging
from LOLoggerClient import LOLoggerClient


def randomString(stringLength=10):
    """Generate a random string of fixed length """
    if stringLength < 0:
        stringLength = random.randint(5, 1000)
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


class LOLoggerTester:
    """
        DOCSTRING EHERE YOu
    """

    def __init__(self):
        self.counter = 0
        self.lologger = CmdFIFO.CmdFIFOServerProxy("http://10.100.3.28:%d" % 33050, ClientName="LOLOGGER_CLIENTTEST")
        self.use_set_of_logs = True

    def generate_set_of_logs(self, size=100):
        self.set_of_logs = []
        for _ in range(size):
            self.set_of_logs.append(randomString(-1))

    def do_testing(self):
        self.lologger.LogEvent("12;DROP TABLE Events", Level=51, ClientName="LOLOGGER_CLIENTTEST", ip="localhost")

    def generate_minute_worth_of_logs(self, delay=1):
        for _ in range(60):
            if self.use_set_of_logs:
                message = self.set_of_logs[random.randint(0, len(self.set_of_logs) - 1)]
            else:
                message = randomString(-1)
            message = f"{self.counter:0{10}}:::{message}"
            self.lologger.LogEvent(message, Level=random.randint(1, 5), ClientName="logger_teste_pew_pew", ip="localhost")
            time.sleep(delay)
            self.counter += 1

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

l = LOLoggerClient(client_name="TESTER")
# l.debug("DEBUGGING")
# l.info("INFORRMING")
# l.warning("WARNING PEOPLE")
# l.error("ERRORING")
# l.critical("CRITICIZING")

for i in range(5):
    l.debug(f"Testing deleting db while writing there_{i}")
    time.sleep(0.01)
