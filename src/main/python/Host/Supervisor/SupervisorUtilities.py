import os
import fnmatch
import random
import commands
from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.EventManagerProxy import EventManagerProxy_Init, Log


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


class RunningApps:
    def __init__(self):
        """
        This class is reserved for application specific utilities, such as
        getting process IDs (PIDs), killing applications, restarting applications via RPC
        calls to the Supervisor, checking whether applications are running, etc.
        """
        self.pid_file_path = "/run/user/" + str(os.getuid()) + "/picarro/"
        self.app_list = []
        self.file_type = "*.pid"

    def get_pid(self, app_name):
        """
        This method will return the process ID (PID) of an application if
        launched using the Host.Common.SingleInstance class (all applications
        should be using this class).

        When an application is launched with the SingleInstance class,
        it creates a .pid file that is located in the /run/user/1000/picarro
        directory.

        The method will open the applicable .pid file, read the contents
        and return the PID as an integer.

        :param app_name: Name of application you would like to get the PID for
        :return: The PID as an integer
        """
        full_path = self.pid_file_path + app_name + ".pid"
        if os.path.exists(self.pid_file_path) and os.path.exists(full_path):
            with open(full_path) as pid_file:
                pid = pid_file.read().strip()
            return int(pid)

    def get_list(self):
        """
        This method will loop through the /run/user/1000/picarro directory,
        search for any files that end in .pid, then append them to a list
        and return it.

        No arguments are necessary.

        :return: List of all processes with a .pid file
        """
        if os.path.exists(self.pid_file_path):
            files_in_dir = os.listdir(self.pid_file_path)
            for pid_file in files_in_dir:
                if fnmatch.fnmatch(pid_file, self.file_type):
                    running_app = pid_file.split('.')[0]
                    self.app_list.append(running_app)
        return self.app_list

    def get_random_app(self):
        """
        This method will get a list of all running apps by calling the
        get_list method. It will then select a random element from the list
        and return the name of the app.

        :return: Random running app
        """
        app_list = self.get_list()
        this_app = app_list[random.randrange(0, (len(app_list) - 1))]
        return this_app

    @staticmethod
    def restart_via_rpc(app_name):
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
            to supervisor via an RPC call
        """
        # Set up and EventManagerProxy
        EventManagerProxy_Init(app_name)
        # Request a restart from Supervisor via RPC call
        restart = RequestRestart(app_name)
        if restart.requestRestart(app_name) is True:
            Log("Restart request to supervisor sent", Level=0)
        else:
            Log("Restart request to supervisor not sent", Level=2)

    def kill_app(self, app_name):
        """
        This method will send a SIGTERM signal from the OS to the app
        requested via the app_name argument, thereby killing it and giving
        it the opportunity to exit cleanly.

        :param app_name: Name of the app you would like to kill (SIGTERM)
        :return: Nothing is returned in this method
        """
        pid = self.get_pid(app_name)
        print("\nSending SIGTERM to: %s \nPID: %s\n" % (app_name, pid))
        os.kill(pid, 15)

    def is_running(self, app_name):
        """
        This method will get the process ID (PID) by calling the get_pid
        method. Once it has the PID, it will cross-reference it with the OS
        process table to check whether it actually is running or not. If it is
        running, it will return True; otherwise False.

        :param app_name: Name of the app (is it running?)
        :return: Boolean
        """
        pid = self.get_pid(app_name)
        pid_running = commands.getoutput("ls /proc | grep %s" % pid)
        pid_state = commands.getoutput("cat /proc/%s/status | grep State:" % pid)
        if pid_running and ("Z" or "zombie") not in pid_state:
            return True
        else:
            return False


if __name__ == "__main__":
    """
    while True:
        fifo = SupervisorFIFO()
        process_launched = fifo.read_from_fifo()
        print process_launched
        if "BackupSupervisor" in process_launched or len(process_launched) == 0:
            break
    """
    running_apps = RunningApps()
    # random_app = running_apps.get_random_app()
    # print("\nApp: %s" % random_app)
    # random_app_pid = running_apps.get_pid(random_app)
    # print("PID: %s" % random_app_pid)
    # print("Restarting", random_app)
    app = "Driver"
    # running_apps.get_pid(app)
    status = running_apps.is_running(app)
    print(status)
    running_apps.restart_via_rpc(app)
    # running_apps.kill_app(app)
    # print("Running: %s\n" % status)
