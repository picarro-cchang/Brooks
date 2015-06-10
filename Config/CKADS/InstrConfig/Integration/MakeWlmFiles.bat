..\..\HostExe\MakeWlmFile1.exe -c MakeWlmFileLaser1.ini -w 10
..\..\HostExe\MakeWlmFile1.exe -c MakeWlmFileLaser2.ini -w 0
..\..\HostExe\WriteLaserEeprom.exe -c WriteLaserEeprom1.ini
..\..\HostExe\WriteLaserEeprom.exe -c WriteLaserEeprom2.ini
..\..\HostExe\WriteWlmEeprom.exe   -c WriteWlmEeprom.ini
..\..\HostExe\DumpEeproms.exe

..\..\HostExe\MakeCalFromEeproms.exe -c MakeCalFromEeproms.ini
..\..\HostExe\CalibrateSystem.exe -c CalibrateSystemCO2.ini
..\..\HostExe\CalibrateSystem.exe -c CalibrateSystemCO.ini

..\..\HostExe\FindWlmOffset.exe -c FindWlmOffsetCO2.ini
..\..\HostExe\FindWlmOffset.exe -c FindWlmOffsetCO.ini
