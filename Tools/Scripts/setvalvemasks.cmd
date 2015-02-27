@echo on
::
:: A hack to set valve mask values to desired values. Need this since
:: the installer won't change InstrConfig files and we need to ensure
:: valve mask values are reset new values
::
:: Relies on having sed (through Git) on the installer. Leaves behind a
:: snapshot of Master.ini in case something goes wrong
::

set SED=c:\program files (x86)\Git\bin\sed.exe
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set mytime=%%a%%b)

set MASTER_INI=c:\picarro\g2000\InstrConfig\Calibration\InstrCal\Master.ini
set TMP_FILE=c:\picarro\g2000\InstrConfig\Calibration\InstrCal\Master.ini.tmp

:: Need sed for this to work
if not exist "%SED%" (
   echo "%SED%" is missing
   exit /b 1	       
)

:: Master.ini should exist
if not exist %MASTER_INI% (
   echo "%MASTER_INI%" is missing
   exit /b 2
)

del %TMP_FILE% 2> nul

:: Look for keys of interest and replace the whole line with the new value
"%SED%" -e 's/^PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER.*/PEAK_DETECT_CNTRL_INACTIVE_VALVE_MASK_AND_VALUE_REGISTER = 54016/;s/^PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER.*/PEAK_DETECT_CNTRL_PRIMING_VALVE_MASK_AND_VALUE_REGISTER = 55044/;s/^PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER.*/PEAK_DETECT_CNTRL_PURGING_VALVE_MASK_AND_VALUE_REGISTER = 55040/;s/^PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER.*/PEAK_DETECT_CNTRL_INJECTION_PENDING_VALVE_MASK_AND_VALUE_REGISTER = 54016/' < %MASTER_INI% > %TMP_FILE%

:: Master.ini should exist
if not exist %MASTER_INI% (
   echo "FATAL: %MASTER_INI% is missing after substitution"
   exit /b 3	       
)

copy %MASTER_INI% %MASTER_INI%.%mydate%_%mytime% > nul
del %MASTER_INI%
ren %TMP_FILE% Master.ini
