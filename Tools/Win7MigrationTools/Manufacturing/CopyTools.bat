@echo off
REM copy the files I need to my test drive and my network folder

echo executing CopyTools.bat
set TEST_DRIVE=K:
set TEST_DIR="%TEST_DRIVE%\Win7MigrationTools"
set TEST_DIR_EXE="%TEST_DIR%\Win7MigrationExe"
set TEST_DIR_SRC="%TEST_DIR%\Win7MigrationSource"


if exist %TEST_DRIVE% goto check_test_dir
echo Test drive %TEST_DRIVE% not found, skipping copy to test drive!
echo.
pause
goto network

:check_test_dir
if exist %TEST_DIR_EXE% goto check_test_dir2
echo Creating test drive folder %TEST_DIR_EXE%
mkdir %TEST_DIR_EXE%

:check_test_dir2
if exist %TEST_DIR_SRC% goto copy_to_drive
echo Creating test drive folder %TEST_DIR_SRC%
mkdir %TEST_DIR_SRC%

:copy_to_drive
echo Copying source files to %TEST_DIR_SRC%
copy Win7Migrate_p1.py %TEST_DIR_SRC%\
copy Win7Migrate_p2.py %TEST_DIR_SRC%\
copy Win7MigrationToolsDefs.py %TEST_DIR_SRC%\
copy Win7MigrationUtils.py %TEST_DIR_SRC%\
copy ..\..\Host\Common\CmdFIFO.py %TEST_DIR_SRC%\

rem copy RunTool.py %TEST_DIR_SRC%\
copy RunPart1ExeDebug.bat %TEST_DIR%\
copy RunPart2ExeDebug.bat %TEST_DIR%\


:test_exes
echo Copying executable files to %TEST_DIR_EXE%
robocopy dist %TEST_DIR_EXE% /S

REM copy them to the network
:network

:: set NETWORK_DIR="S:\For TracyW\Projects\Win7\Win7MigrationTools"
:: set NETWORK_DIR_EXE="S:\For TracyW\Projects\Win7\Win7MigrationTools\Win7MigrationExe"
:: set NETWORK_DIR_SRC="S:\For TracyW\Projects\Win7\Win7MigrationTools\Win7MigrationSource"

:: just copy exes to the staging area and quit
set NETWORK_DIR_EXE="S:\CRDS\CRD Engineering\Software\G2000\Installer_Staging\MigrationTools_win7"
goto network_exes

if exist %NETWORK_DIR% goto check_net_exe
echo Network folder %NETWORK_DIR% does not exist, skipping copy to network!
echo.
pause
goto egress

:check_net_exe
if exist %NETWORK_DIR_EXE% goto copy_to_network
echo Creating network folder %NETWORK_DIR_EXE%
mkdir %NETWORK_DIR_EXE%

:copy_to_network
if exist %NETWORK_DIR_SRC% goto copy_to_network2
echo Creating network folder %NETWORK_DIR_SRC%
mkdir %NETWORK_DIR_SRC%

:copy_to_network2
echo Copying files to %NETWORK_DIR_SRC% and %NETWORK_DIR_EXE%

rem Uncomment the following to skip copying sources
rem goto network_exes

rem Sources
copy Win7Migrate_Part1.py %NETWORK_DIR_SRC%\
copy Win7Migrate_Part1.py %NETWORK_DIR_SRC%\
copy Win7MigrationToolsDefs.py %NETWORK_DIR_SRC%\
copy Win7MigrationUtils.py %NETWORK_DIR_SRC%\
copy ..\..\Host\Common\CmdFIFO.py %NETWORK_DIR_SRC%\

rem copy RunTool.py %NETWORK_DIR_SRC%\

:network_exes
:: remove the dir if it exists
if exist %NETWORK_DIR_EXE% rm -r %NETWORK_DIR_EXE%
mkdir %NETWORK_DIR_EXE%
echo robocopy dist %NETWORK_DIR_EXE% /S
robocopy dist %NETWORK_DIR_EXE% /S

:: copy RunPart1Exe.bat %NETWORK_DIR%\
:: copy RunPart2Exe.bat %NETWORK_DIR%\

:egress
echo.
echo Exiting...

pause