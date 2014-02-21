# Win7MigrationToolsDefs.py
#
# Definitions for Win7 migration.
#
# History:
# 2014-01-30:  tw  Initial version.

MIGRATION_TOOLS_VERSION = "1.0.0.6"
MIGRATION_TOOLS_LOGNAME = "MigrationTools"

MIGRATION_UNKNOWN_ANALYZER_TYPE = "Unknown"
MIGRATION_UNKNOWN_ANALYZER_NAME = "Unknown"
MIGRATION_UNKNOWN_CHASSIS_TYPE = "Unknown"


# This isn't working the way I want it to...
MIGRATION_DIALOG_CAPTION = "WinXP migration to Win7: Part %s"

MIGRATION_TOOLS_LOGFILENAME_BASE_1 = "MigrationPart1_%Y_%m_%d_%H_%M_%S"
MIGRATION_TOOLS_LOGFILENAME_BASE_2 = "MigrationPart2_%Y_%m_%d_%H_%M_%S"

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
#
# TODO: C:\Picarro\AnalyzerData is an empty folder on HB2272. Is it always empty?
#       Include it in the list below?
#
#       What about C:\Picarro\ChemCorrect? contains some empty subfolders on HB2272
#       C:\Picarro\arduino-0022? Contains apps, dlls, other misc files.
#       C:\Picarro\PostProcess\ChemCorrectExe folder contains exes, dlls, other misc.
#       C:\Picarro\Screenshots
DATA_FOLDERS_TO_BACKUP_LIST = ["C:/Picarro/g2000/Log/Archive",
                               "C:/UserData",
                               "C:/IsotopeData"]

"""
CONFIG_FOLDERS_TO_BACKUP_LIST = ["C:/Picarro/g2000/AppConfig",
                                 "C:/Picarro/g2000/InstrConfig",
                                 "C:/Picarro/g2000/CommonConfig",
                                 "C:/Picarro/g2000/HostExe",
                                 "C:/Picarro/g2000/AutosamplerExe"]
"""

# Just back up everything in Picarro\g2000
CONFIG_FOLDERS_TO_BACKUP_LIST = ["C:/Picarro/g2000"]


# Restore folder and file paths are relative to C: and the backup folder on the migration drive.
# List of specific folders to restore from after the Win7 software is installed
#
# TODO: Restore only specific autosampler files. Exes and Dlls are specific to WinXP.
CONFIG_FOLDERS_TO_RESTORE_LIST = ["C:/Picarro/g2000/InstrConfig"]

# List of specific files to restore.
#
# Note: It's a poor idea to update all Coordinator .ini files, PF made changes to them for 1.3.9,
#       and the dual Coordinator file was fixed for 1.4.1. These changes should be picked up.
#       So they aren't restored, Service/users can do this manually if required.
#
# TODO: Add specific Autosampler files from Picarro/g2000/AutosamplerExe.

CONFIG_FILES_TO_RESTORE_LIST = ["C:/Picarro/g2000/AppConfig/Config/Utilities/SupervisorLauncher.ini",
                                "C:/Picarro/g2000/AppConfig/Config/Utilities/CoordinatorLauncher.ini",
                                "C:/Picarro/g2000/AppConfig/Supervisor/StartupExeConfig.ini"
                                #"C:/Picarro/g2000/AppConfig/Supervisor/*.ini",
                                #"C:/Picarro/g2000/AppConfig/Coordinator/*.ini",
                               ]


# Destination folder (relative to drive root) on partition 2 where WinXP folders are backed up
BACKUP_XP_FOLDER_ROOT_NAME = "WinXPBackup"


# Destination folder (relative to drive root) on partition 2 where Win7 config folders are
# backed up (only on a virgin install). Useful for comparison for troubleshooting.
BACKUP_WIN7_CONFIG_FOLDER_ROOT_NAME = "Win7ConfigBackup"

CONFIG_WIN7_FOLDERS_TO_BACKUP_LIST = ["C:/Picarro/g2000/AppConfig",
                                      "C:/Picarro/g2000/InstrConfig",
                                      "C:/Picarro/g2000/CommonConfig"]

# Config filename, section and keys for stashing the analyzer type and volume name to use
MIGRATION_CONFIG_FILENAME = "Win7Config.ini"
MIGRATION_CONFIG_SECTION = "Win7Migration"
ANALYZER_TYPE = "AnalyzerType"
ANALYZER_NAME = "AnalyzerName"
VOLUME_NAME = "VolumeName"
COMPUTER_NAME = "ComputerName"
MY_COMPUTER_ICON_NAME = "MyComputerIconName"

# Folder name containing installers. Each installer is in a subdirectory
# named by analyzer type (e.g., CFADS, CFKADS, etc.) just like they are
# on the network staging and release areas.
INSTALLER_FOLDER_ROOT_NAME = "PicarroInstallers"
