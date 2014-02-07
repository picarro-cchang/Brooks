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

# Lists of folders to be backed up.
#
# TODO: Include the entire C:/Picarro/g2000/Log folder below for folders to back up?
#       Or just the archive (C:/Picarro/g2000/Log/Archive)
#
# Data folders are not backed up if the --backupConfigsOnly option is used
DATA_FOLDERS_TO_BACKUP_LIST = ["C:/Picarro/g2000/Log/Archive",
                               "C:/UserData",
                               "C:/IsotopeData"]

CONFIG_FOLDERS_TO_BACKUP_LIST = ["C:/Picarro/g2000/AppConfig",
                                 "C:/Picarro/g2000/InstrConfig",
                                 "C:/Picarro/g2000/CommonConfig",
                                 "C:/Picarro/g2000/AutosamplerExe"]


# List of folders to restore after the Win7 software is installed
CONFIG_FOLDERS_TO_RESTORE_LIST = ["C:/Picarro/g2000/InstrConfig",
                                  "C:/Picarro/g2000/AutosamplerExe"]

# List of files to restore
# TODO: Bad idea to update all Coordinator .ini files, PF made changes to them that
#       should be used. Also the dual Coordinator file was fixed by me.
CONFIG_FILES_TO_RESTORE_LIST = ["C:/Picarro/g2000/AppConfig/Config/Utilities/SupervisorLauncher.ini",
                                "C:/Picarro/g2000/AppConfig/Config/Utilities/CoordinatorLauncher.ini",
                                #"C:/Picarro/g2000/AppConfig/Supervisor/*.ini",
                                #"C:/Picarro/g2000/AppConfig/Coordinator/*.ini",
                               ]



# Destination folder (relative to drive root) on partition 2 where above folders are backed up
BACKUP_FOLDER_ROOT_NAME = "WinXPBackup"

# Config filename, section and keys for stashing the analyzer type and volume name to use
CONFIG_FILENAME = "Win7Config.ini"
CONFIG_SECTION = "Win7Migration"
ANALYZER_TYPE = "AnalyzerType"
ANALYZER_NAME = "AnalyzerName"
VOLUME_NAME = "VolumeName"
COMPUTER_NAME = "ComputerName"
MY_COMPUTER_ICON_NAME = "MyComputerIconName"


