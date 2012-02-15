rem This batch file should be in Windows StartUp for all users. It starts the AccessViaNet utility for 
rem communicating with the aircraft network

ping -n 46 127.0.0.1 >nul
cd C:\Picarro\G2000\AccessViaNet
AccessViaNet.exe -c AccessViaNet.ini
