MakeWlmFile1.py -c C:\Work\G2000\InstrConfig\Integration\MakeWlmFileLaser1.ini -w 10
MakeWlmFile1.py -c C:\Work\G2000\InstrConfig\Integration\MakeWlmFileLaser2.ini -w 0
WriteLaserEeprom.py -c C:\Work\G2000\InstrConfig\Integration\WriteLaserEeprom1.ini
WriteLaserEeprom.py -c C:\Work\G2000\InstrConfig\Integration\WriteLaserEeprom2.ini
WriteWlmEeprom.py   -c C:\Work\G2000\InstrConfig\Integration\WriteWlmEeprom.ini
MakeCalFromEeproms.py -c C:\Work\G2000\InstrConfig\Integration\MakeCalFromEeproms.ini