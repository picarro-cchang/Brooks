gcc -o Serial2Socket -O3 Serial2Socket.c ini.c -lws2_32
if "%ERRORLEVEL%" == "1" exit /b /1
Serial2Socket.exe
