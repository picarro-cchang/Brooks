import time
import sys
import argparse
from Host.Supervisor.SupervisorUtilities import RunningApps


# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--interval",
                    help="minutes to wait between test cycles",
                    required=True)
parser.add_argument("--type",
                    help="type of test to run (kill or restart)",
                    required=True)
args = parser.parse_args()

# Give feedback to user if necessary
if not args.interval:
    print("\n\nYou must specify an interval!\n\n")
    parser.print_help()
    sys.exit(1)
else:
    # argparser will return interval as a string, let's try to convert it
    # to an integer. If the input cannot be converted, we'll get a ValueError
    try:
        test_interval = int(args.interval)
    except ValueError:
        print("\n\nPlease pass a float or integer for the interval!\n\n")
        parser.print_help()
        sys.exit(1)
if not args.type:
    print("\n\nYou must specify a test type!\n\n")
    parser.print_help()
    sys.exit(1)
else:
    test_type = args.type.lower()
if test_type not in ["restart", "kill"]:
    print("\n\nYou must enter a valid test type! (kill or restart)")
    parser.print_help()
    sys.exit(1)


def kill_random_app():
    running_apps = RunningApps()
    random_app = running_apps.get_random_app()
    if "Supervisor" in random_app:
        print("Skipping so we don't kill Supervisor")
    else:
        running_apps.kill_app(random_app)


def restart_random_app_via_rpc():
    running_apps = RunningApps()
    random_app = running_apps.get_random_app()
    if "Supervisor" in random_app:
        print("Skipping so we don't kill Supervisor")
    else:
        print("Restarting %s via RPC call to supervisor" % random_app)
        running_apps.restart_via_rpc(random_app)


def run_test():
    while True:
        time.sleep((test_interval * 60))
        if "kill" in test_type:
            kill_random_app()
        else:
            restart_random_app_via_rpc()


def main():
    try:
        print("\n\nStarting up SupervisorTests\n\nType: %s\nInterval: %s minutes\n\n"
              % (test_type, test_interval))
        run_test()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
