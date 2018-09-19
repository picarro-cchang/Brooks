from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log
import os


class SupervisorFIFO:
    def __init__(self):
        """
        This class will allow supervisor to stream the name
        of the app to the fifo file located in /tmp/SupervisorFIFO
        Its intention is to allow external apps, such as QuickGui or
        any other future GUI utilities to read the stream and update
        the status of the applications as they are being launched.

        No arguments. We want this to be written to the /tmp directory
        as the OS will clear the directory on every boot.

        The 0644 permissions allow for File only Read/Write to the
        User (picarro) and Read only privileges to Group and Other
        """
        self.fifo_path = '/tmp/SupervisorFIFO'
        try:
            if not os.path.exists(self.fifo_path):
                os.mkfifo(self.fifo_path, 0644)
        except OSError:
            raise OSError

    def write_to_fifo(self, supervisor_input):
        """
        This function will allow any input to be written into
        the /tmp/SupervisorFIFO file

        :param supervisor_input: Name of the application to be written
        to the fifo file

        :return: Nothing is returned
        """
        with open(self.fifo_path, 'w+') as fifo_file:
            fifo_file.write(supervisor_input)

    def read_from_fifo(self):
        """
        This function will read any input written into the
        fifo file

        We will close the fifo once BackupSupervisor has been launched
        as it will always be the last app to launch as dictated by
        the applicable supervisor.ini file

        :return: Contents of the fifo file

        Example usage in external app:

                from Host.Supervisor.SupervisorUtilities import SupervisorFIFO

                while True:
                    fifo = SupervisorFIFO()
                    process_launched = fifo.read_from_fifo()
                    print process_launched
                    if "BackupSupervisor" in process_launched or len(process_launched) == 0:
                        break

        """
        with open(self.fifo_path, 'r') as fifo_file:
            output = fifo_file.readline().rstrip()
        return output


def restart_app_via_rpc(app_name):
    """
    This function will set up its own EventManagerProxy and
    send a signal to supervisor requesting a restart. It will
    "pretend" to be any app you like as determined by the
    app_name argument. The intention is to use this for a utility
    that will periodically request a restart from supervisor so we
    can test both supervisor and individual apps for their recovery
    behavior, stress-testing, etc.

    :param app_name: The name of the app you would like to restart.
        Some examples are: "Driver", "SpectrumCollector", "QuickGui", etc.
        The name of the app can typically be found at the header of
        the individual app's source under the APP_NAME variable.

    :return: Nothing is returned from this method. A request is sent
        to supervisor via an RPC call.
    """
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
        fifo = SupervisorFIFO()
        process_launched = fifo.read_from_fifo()
        print process_launched
        if "BackupSupervisor" in process_launched or len(process_launched) == 0:
            break
