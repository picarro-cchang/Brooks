rem This batch file should be in Windows StartUp for all users. It starts the GlobalHawk utility for 
rem communicating with the aircraft network

ping -n 46 127.0.0.1 >nul
cd C:\Picarro\G2000\Host\Utilities\GlobalHawkComms
C:\python25\python.exe GlobalHawk.py -c GlobalHawkATTREX.ini
