@echo off
:: Windows batch file for clearing the EventLogWatcher log and cache files from a cmd shortcut
:: and then make a single pass through the event logs to reset the log and cache files
call RunEventLogWatcher --once --resetLogs
if "%ERRORLEVEL%" == "0" echo EventLogWatcher log files successfully reset & goto egress
echo error executing RunEventLogWatcher --once --resetLogs
echo Exit Code = %ERRORLEVEL%

:egress
pause
