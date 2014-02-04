# Win7Migrate_p3.py
#
# Part 3 of migration tools for WinXP to Win7.
# This restores the various config files from the backup.

import logging

import Win7MigrationToolsDefs as mdefs
import Win7MigrationUtils as mutils


def main():
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.warning("Migration part 3 (restore) is not fully implemented!")

    # ==== Validation =====
    # software should not be running (prompt to shut it down if it is)

    # make sure there is installed software

    # should be running Win7

    # find the backup partition

    # back up the installed config files somewhere first?

    # ==== Restore ====
    # restore config files

    # restore user data (ask what to restore? newer files since a specific date?)

    # restore autosampler (exe and configs)

    # fix up config files that have known issues
    # HIDS needs a manual upgrade to InstrConfig\Calibration\InstrCal\FitterConfig.ini:
    #   http://redmine.blueleaf.com/projects/software/wiki/140-22InternalChangelog

    # ==== Start the instrument ====
    # start up the instrument? reboot so it is started? or give instructions?


if __name__ == "__main__":
    main()
