@echo off
REM copy the files I need to my test drive and my network folder

echo executing CopyTools.bat
set TEST_DRIVE=K:
set TEST_DIR="%TEST_DRIVE%\Win7UserMigrationTools"
set TEST_DIR_EXE="%TEST_DIR%\Win7UserMigrationExe"
set TEST_DIR_SRC="%TEST_DIR%\Win7UserMigrationSource"

:: Skipping the test drive for now since I'm not building on Win 7
goto network


if exist %TEST_DRIVE% goto check_test_dir
echo Test drive %TEST_DRIVE% not found, skipping copy to test drive!
echo.
pause
goto network

REM ***** vvv NOT USED vvv ****
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
copy Win7UserMigrate_p1.py %TEST_DIR_SRC%\
copy Win7UserMigrate_p2.py %TEST_DIR_SRC%\
copy Win7UserMigrationToolsDefs.py %TEST_DIR_SRC%\
copy Win7UserMigrationUtils.py %TEST_DIR_SRC%\
copy ..\..\Host\Common\CmdFIFO.py %TEST_DIR_SRC%\

rem copy RunTool.py %TEST_DIR_SRC%\
copy RunPart1ExeDebug.bat %TEST_DIR%\
copy RunPart2ExeDebug.bat %TEST_DIR%\


:test_exes
echo Copying executable files to %TEST_DIR_EXE%
robocopy dist %TEST_DIR_EXE% /S
REM ***** ^^^ NOT USED ^^^ ****

REM copy sources to the network (for testing builds from a VirtualBox WinXP build image)
:network

:: set NETWORK_DIR="S:\For TracyW\Projects\Win7\Win7UserMigrationTools"
:: set NETWORK_DIR_EXE="S:\For TracyW\Projects\Win7\Win7UserMigrationTools\Win7UserMigrationExe"
set NETWORK_DIR_SRC="S:\For TracyW\Projects\Win7\Win7UserMigrationTools\Win7UserMigrationSource"

if exist %NETWORK_DIR_SRC% goto copy_to_network

:copy_to_network
if exist %NETWORK_DIR_SRC% goto copy_to_network2
echo Creating network folder %NETWORK_DIR_SRC%
mkdir %NETWORK_DIR_SRC%

:copy_to_network2
echo Copying files to %NETWORK_DIR_SRC%

rem Sources

copy buildWin7UserMigrationTools.py %NETWORK_DIR_SRC%\
copy build_version.py %NETWORK_DIR_SRC%\
copy setupWin7UserMigrationTools.py %NETWORK_DIR_SRC%\
copy Win7UserMigrate_Part1.py %NETWORK_DIR_SRC%\
copy Win7UserMigrate_Part1.py %NETWORK_DIR_SRC%\
copy Win7UserMigrationToolsDefs.py %NETWORK_DIR_SRC%\
copy Win7UserMigrationUtils.py %NETWORK_DIR_SRC%\
copy ..\..\..\Host\Common\CmdFIFO.py %NETWORK_DIR_SRC%\

rem copy RunTool.py %NETWORK_DIR_SRC%\

:: copy RunPart1Exe.bat %NETWORK_DIR%\
:: copy RunPart2Exe.bat %NETWORK_DIR%\

:egress
echo.
echo Exiting...

pause