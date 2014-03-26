:: CopySource.bat
::
:: Copies migration tools source to my network folder

set NETWORK_DIR_SRC="S:\For TracyW\Projects\Win7\Win7UserMigrationTools\Win7UserMigrationSource"

if exist %NETWORK_DIR_SRC% goto copy_to_network
echo Creating network folder %NETWORK_DIR_SRC%
mkdir %NETWORK_DIR_SRC%

:copy_to_network
echo Copying files to %NETWORK_DIR_SRC%

:: Sources

copy buildWin7UserMigrationTools.py %NETWORK_DIR_SRC%\
copy build_version.py %NETWORK_DIR_SRC%\
copy setupWin7UserMigrationTools.py %NETWORK_DIR_SRC%\
copy Win7UserMigrate_Part1.py %NETWORK_DIR_SRC%\
copy Win7UserMigrate_Part1.py %NETWORK_DIR_SRC%\
copy Win7UserMigrationToolsDefs.py %NETWORK_DIR_SRC%\
copy Win7UserMigrationUtils.py %NETWORK_DIR_SRC%\
copy ..\..\..\Host\Common\CmdFIFO.py %NETWORK_DIR_SRC%\
copy ..\..\..\Host\Common\SharedTypes.py %NETWORK_DIR_SRC%\