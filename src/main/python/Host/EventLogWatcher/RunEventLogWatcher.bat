@echo off
:: Windows batch file for executing EventLogWatcher from a cmd shortcut
set EVENT_LOG_WATCHER=C:\Picarro\G2000\HostExe\EventLogWatcher.exe
set EVENT_LOG_WATCHER_JSON=C:\Picarro\Utilities\EventLogWatcher\EventLogWatcher.json

if exist %EVENT_LOG_WATCHER% goto check_json

:: dist folder for internal testing
set EVENT_LOG_WATCHER_DEV=..\dist\EventLogWatcher.exe
if not exist %EVENT_LOG_WATCHER_DEV% goto outdir_not_found
set EVENT_LOG_WATCHER=%EVENT_LOG_WATCHER_DEV%
goto check_json

:outdir_not_found
echo Can't find EventLogMgr app '%EVENT_LOG_WATCHER%', exiting.
goto egress

:check_json
if exist %EVENT_LOG_WATCHER_JSON% goto run_app
echo Can't find config file '%EVENT_LOG_WATCHER_JSON%', exiting.
goto egress

:run_app
::echo Command line = %EVENT_LOG_WATCHER% %1 %2 %3 %4 %5 %6 %7 %8
%EVENT_LOG_WATCHER% %1 %2 %3 %4 %5 %6 %7 %8

:egress
