from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
import os


class SupervisorFIFO:
    def __init__(self):
        self.fifo_path = '/tmp/SupervisorFIFO'
        try:
            if not os.path.exists(self.fifo_path):
                os.mkfifo(self.fifo_path, 0644)
        except OSError:
            raise OSError

    def write_to_fifo(self, supervisor_input):
        with open(self.fifo_path, 'w+') as pipe:
            pipe.write(supervisor_input)

    def read_from_fifo(self):
        with open(self.fifo_path, 'r') as pipe:
            output = pipe.readline().rstrip()
        return output


def restart_app_via_rpc(app_name):
    # Set up and EventManagerProxy
    EventManagerProxy_Init(app_name)
    # Request a restart from Supervisor via RPC call
    restart = RequestRestart(app_name)
    if restart.requestRestart(app_name) is True:
        Log("Restart request to supervisor sent", Level=0)
    else:
        Log("Restart request to supervisor not sent", Level=2)


if __name__ == "__main__":
    # restart_app_via_rpc(app_name="SpectrumCollector")
    while True:
        process = SupervisorFIFO()
        print process.read_from_fifo()
