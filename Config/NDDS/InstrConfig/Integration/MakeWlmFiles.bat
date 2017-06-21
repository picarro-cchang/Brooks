..\..\SrcCode\Utilities\MakeWlmFile1.py -c MakeWlmFileLaser1.ini -w 10
..\..\SrcCode\Utilities\WriteLaserEeprom.py -c WriteLaserEeprom1.ini
..\..\SrcCode\Utilities\WriteWlmEeprom.py   -c WriteWlmEeprom.ini
..\..\SrcCode\Utilities\DumpEeproms.py

..\..\SrcCode\Utilities\MakeCalFromEeproms.py -c MakeCalFromEeproms.ini
..\..\SrcCode\Utilities\CalibrateSystem.py -c CalibrateSystemiH2O.ini

..\..\SrcCode\Utilities\FindWlmOffset.py -c FindWlmOffsetCO2.ini
..\..\SrcCode\Utilities\FindWlmOffset.py -c FindWlmOffsetCH4.ini
