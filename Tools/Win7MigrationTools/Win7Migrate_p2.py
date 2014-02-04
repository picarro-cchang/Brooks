# Win7Migrate_p2.py
#
# Part 2 of migration tools for WinXP to Win7
#
# Runs the installer (or at least suggests one?)
# Part 1 needs to save off the instrument type so this script
# can find the recommended installer.

import logging

import Win7MigrationToolsDefs as mdefs
import Win7MigrationUtils as mutils


def main():
    logger = logging.getLogger(mdefs.MIGRATION_TOOLS_LOGNAME)
    logger.warning("Migration part 2 (install) needs to be implemented!")

    # ==== Validation =====
    # software should not be running

    # look for installed software (there shouldn't be any)

    # should be running Win7 and Python 2.7

    # find the backup partition

    # ==== Install Software ====

    # run the installer (use saved instrument type to determine which one)

    # if install completed successfully, could run Win7Migrate_p3.py (restore)



if __name__ == "__main__":
    main()