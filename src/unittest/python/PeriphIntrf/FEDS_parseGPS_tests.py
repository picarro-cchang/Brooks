import os
import unittest
from PeripheralScriptTester import PeripheralScriptTester

PARSEGPS_SCRIPT = os.path.abspath(r"./Config/FEDS/AppConfig/Scripts/PeriphIntrf/parseGPS.py")
PARSEGPS_CONFIG = os.path.abspath(r"./Config/FEDS/InstrConfig/Config/PeriphIntrf/RunSerial2Socket.ini")

class TestRegularGPS(unittest.TestCase):
    """unit test for alarm system script of health monitor"""
    def setUp(self):
        self.tester = PeripheralScriptTester(PARSEGPS_SCRIPT, PARSEGPS_CONFIG, 0)
    
    def tearDown(self):
        self.tester = None
    
###################### test cases #####################################################

    def test_regular_GPS(self):
        self.tester.dataLabels = ["GPS_ABS_LAT", "GPS_ABS_LONG", "GPS_FIT", "GPS_TIME"]
        gpsData = self.tester.runScript("$GPGGA,012345.67,12.345,N,123.456,W,1")
        self.assertTrue(gpsData[2] == 1)
        gpsData = self.tester.runScript("$GPGGA,012345.98,12.345,N,123.456,W,1")
        self.assertTrue(gpsData[2] == 1)
        
    def test_inertial_GPS(self):
        self.tester.dataLabels = ["GPS_ABS_LAT", "GPS_ABS_LONG", "GPS_UNC_LAT", "GPS_UNC_LONG", "GPS_FIT", "GPS_TIME"]
        gpsData = self.tester.runScript("$GPGGA,012345.67,12.345,N,123.456,W,1")
        self.assertTrue(len(gpsData) == 0)
        gpsData = self.tester.runScript("$GPGST,012345.67,,,,,1.0,2.0")
        self.assertTrue(gpsData[2:4] == [1.0, 2.0])
        
    def test_iGPS_not_initialized(self):
        self.tester.dataLabels = ["GPS_ABS_LAT", "GPS_ABS_LONG", "GPS_UNC_LAT", "GPS_UNC_LONG", "GPS_FIT", "GPS_TIME"]
        gpsData = self.tester.runScript("$GPGGA,012345.67,12.345,N,123.456,W,1")
        gpsData = self.tester.runScript("$GPGST,012345.67,,,,,,")
        self.assertTrue(gpsData[2:4] == [-1, -1])
        
    def test_iGPS_without_GPGST(self):
        self.tester.dataLabels = ["GPS_ABS_LAT", "GPS_ABS_LONG", "GPS_UNC_LAT", "GPS_UNC_LONG", "GPS_FIT", "GPS_TIME"]
        gpsData = self.tester.runScript("$GPGGA,012345.67,12.345,N,123.456,W,1")
        gpsData = self.tester.runScript("$GPGGA,012346.67,12.345,N,123.456,W,1")
        self.assertTrue(gpsData[2:5] == [-1, -1, 1])
        gpsData = self.tester.runScript("$GPGGA,012346.67,12.345,N,123.456,W,1")
        self.assertTrue(gpsData[2:5] == [-1, -1, 1])