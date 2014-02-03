# Win7MigrationToolsDefs.py
#
# Definitions for Win7 migration.
#
# History:
# 2014-01-30:  tw  Initial version.

MIGRATION_TOOLS_VERSION = "1.0.0"
MIGRATION_TOOLS_LOGNAME = "MigrationTools"

# This isn't working the way I want it to...
MIGRATION_DIALOG_CAPTION = "WinXP migration to Win7: Part %s"

MIGRATION_TOOLS_LOGFILENAME_BASE = "MigrationPart1_%Y_%m_%d_%H_%M_%S"

PARTITION_2_VOLUME_NAME = "MIGRATE"

# Partition 1 folder where the migration tools are installed
MIGRATION_TOOLS_FOLDER_NAME = "Win7MigrationTools"




# TODO: Find out where the autosampler code lives, do we want to back it up too?
#       What about autosampler config files, where do they live? (not part of installs)
#       Should the log folder be here?

# List of folders to be backed up
"""
FOLDERS_TO_BACKUP_LIST = [ "C:/Picarro/g2000/AppConfig",
                           "C:/Picarro/g2000/InstrConfig",
                           "C:/Picarro/g2000/CommonConfig",
                           "C:/Picarro/g2000/Log",  # include this folder?
                           "C:/UserData",
                           "C:/IsotopeData"
                         ]
"""


# for testing
FOLDERS_TO_BACKUP_LIST = ["C:/UserData",
                          "C:/Picarro/g2000/CommonConfig"]


# Destination folder (relative to drive root) on partition 2 where above folders are backed up
BACKUP_FOLDER_ROOT_NAME = "WinXPBackup"

