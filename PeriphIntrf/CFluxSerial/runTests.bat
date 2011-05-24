gcc -DTEST AllTestsSerial2Socket.c Serial2Socket.c ini.c CuTest.c
if "%ERRORLEVEL%" == "1" exit /b /1
a.exe
