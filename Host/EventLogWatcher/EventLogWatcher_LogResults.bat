@echo off
:: Windows batch file for executing EventLogWatcher from a cmd shortcut
:: and display the results log in notepad++ (or notepad if not found)

set EVENT_LOG_WATCHER_OUTDIR=C:\Picarro\Utilities\EventLogWatcher
set EVENT_LOG_WATCHER_JSON=%EVENT_LOG_WATCHER_OUTDIR%\EventLogWatcher.json
set EVENT_LOG_WATCHER_LOG=%EVENT_LOG_WATCHER_OUTDIR%\EventLogWatcher_results.log

:: Remove existing log and pick up any new results since the last time cached
if exist %EVENT_LOG_WATCHER_LOG% del /F %EVENT_LOG_WATCHER_LOG%
call RunEventLogWatcher --once
if "%ERRORLEVEL%" == "0" goto step2
echo error executing RunEventLogWatcher --once
echo Exit Code = %ERRORLEVEL%
pause
goto egress

:step2
:: Output results to a log file
call RunEventLogWatcher --dumpAll --summary --summaryDetails -c %EVENT_LOG_WATCHER_JSON% > %EVENT_LOG_WATCHER_LOG%
if "%ERRORLEVEL%" == "0" goto step3
echo error executing RunEventLogWatcher --dumpAll --summary --summaryDetails -c %EVENT_LOG_WATCHER_JSON% > %EVENT_LOG_WATCHER_LOG%
echo Exit Code = %ERRORLEVEL%
pause
goto egress

:step3
set VIEWER_APP_WIN7="C:\Program Files (x86)\Notepad++\notepad++.exe"

if exist %EVENT_LOG_WATCHER_LOG% goto show_log
echo Event log watcher failed, exiting.
goto egress

:show_log
:: Look for notepad++ first
if not exist %VIEWER_APP_WIN7% set VIEWER_APP_WIN7=notepad
call %VIEWER_APP_WIN7% %EVENT_LOG_WATCHER_LOG%
if "%ERRORLEVEL%" == "0" goto egress
echo error executing %VIEWER_APP_WIN7% %EVENT_LOG_WATCHER_LOG%
echo Exit Code = %ERRORLEVEL%
pause

:egress