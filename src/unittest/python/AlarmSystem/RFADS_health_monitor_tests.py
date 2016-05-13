import os
import unittest
from AlarmScriptTester import AlarmScriptTester
from Host.Common.CustomConfigObj import CustomConfigObj

ALARM_SCRIPT = os.path.abspath(r"./Config/RFADS/AppConfig/Scripts/AlarmSystem/alarm_RFADS.py")
ALARM_CONFIG = os.path.abspath(r"./Config/RFADS/AppConfig/Config/AlarmSystem/AlarmSystem.ini")

class TestHealthMonitor(unittest.TestCase):
    """unit test for alarm system script of health monitor"""
    def setUp(self):
        self.tester = AlarmScriptTester(ALARM_SCRIPT, ALARM_CONFIG)
        self.alarmConfig = CustomConfigObj(ALARM_CONFIG)

    def tearDown(self):
        self.tester = None
        self.alarmConfig = None

    def _get_analyzer_status(self, timestamp, reportDict):
        alarmDict = self.tester.runScript(timestamp, reportDict)
        return alarmDict["AnalyzerStatus"]

    def _get_peripheral_status(self, timestamp, reportDict):
        alarmDict = self.tester.runScript(timestamp, reportDict)
        return alarmDict["PeripheralStatus"]

    def _get_alarm_mask(self, alarmName):
        alarm = "ALARM_" + alarmName
        if alarm in self.alarmConfig:
            bit = int(self.alarmConfig[alarm]["bit"])
            return 1<<bit
        else:
            raise("Alarm not found: %s" % alarmName)

###################### flow rate #####################################################

    def test_zero_intake_flow_rate(self):
        for _ in range(10):
            status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "MOBILE_FLOW": 0.0, "interval": 10.0})
        self.assertTrue((status & self._get_alarm_mask("IntakeFlowRate")) > 0)

    def test_normal_intake_flow_rate(self):
        for _ in range(10):
            status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "MOBILE_FLOW": 4.0, "interval": 10.0})
        self.assertTrue((status & self._get_alarm_mask("IntakeFlowRate")) == 0)
        self.assertTrue((status & self._get_alarm_mask("IntakeFlowDisconnected")) == 0)

    def test_intake_flow_disconnected(self):
        status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "MOBILE_FLOW": -9999.0})
        self.assertTrue((status & self._get_alarm_mask("IntakeFlowDisconnected")) > 0)

###################### cavity ###############################################

    def test_large_cavity_baseline_loss(self):
        status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CFADS_base": 1e6})
        self.assertTrue((status & self._get_alarm_mask("CavityBaselineLoss")) > 0)
        self.assertTrue((status & self._get_alarm_mask("InvalidData")) == 0)

    def test_zero_cavity_baseline_loss(self):
        status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CFADS_base": 0})
        self.assertTrue((status & self._get_alarm_mask("CavityBaselineLoss")) == 0)

    def test_high_cavity_pressure(self):
        for _ in range(10):
            status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CavityPressure": 150.0, "interval": 10.0})
        self.assertTrue((status & self._get_alarm_mask("CavityPressure")) > 0)
        self.assertTrue((status & self._get_alarm_mask("InvalidData")) > 0)

    def test_high_cavity_temperature(self):
        for _ in range(10):
            status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CavityTemp": 50.0, "interval": 10.0})
        self.assertTrue((status & self._get_alarm_mask("CavityTemperature")) > 0)
        self.assertTrue((status & self._get_alarm_mask("InvalidData")) > 0)
        
###################### wlm ###############################################        
    
    def test_large_wlm_shift_and_adjust(self):
        status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "ch4_high_shift": 0.01, "ch4_high_adjust": -0.01})
        self.assertTrue((status & self._get_alarm_mask("WlmShift")) > 0)
        self.assertTrue((status & self._get_alarm_mask("WlmAdjust")) > 0)
        self.assertTrue((status & self._get_alarm_mask("WlmShiftAdjustCorrelation")) == 0)
        
    def test_uncorrelated_wlm_shift_and_adjust(self):
        status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "ch4_high_shift": 1e-3, "ch4_high_adjust": 0})
        self.assertTrue((status & self._get_alarm_mask("WlmShiftAdjustCorrelation")) > 0)
        self.assertTrue((status & self._get_alarm_mask("WlmShift")) == 0)
        self.assertTrue((status & self._get_alarm_mask("WlmAdjust")) == 0)

    def test_large_wlm_offset(self):
        for i in range(5):
            offset = i * 0.1
            status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "wlm8_offset": offset})
        self.assertTrue((status & self._get_alarm_mask("WlmTargetFreq")) > 0)

###################### measurement rate and results ############################################

    def test_slow_data_rate(self):
        for _ in range(10):
            status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CH4": 2.0, "interval": 10.0, "SpectrumID": 170})
        self.assertTrue((status & self._get_alarm_mask("MethaneInterval")) > 0)
        self.assertTrue((status & self._get_alarm_mask("InvalidData")) > 0)

    def test_slow_data_rate_at_high_ch4_concentration(self):
        for _ in range(10):
            status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CH4": 10.0, "interval": 10.0, "SpectrumID": 170})
        self.assertTrue((status & self._get_alarm_mask("MethaneInterval")) == 0)
        self.assertTrue((status & self._get_alarm_mask("InvalidData")) == 0)

    def test_negative_ch4_concentration(self):
        status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CH4": -1.0})
        self.assertTrue((status & self._get_alarm_mask("CH4Concentration")) > 0)
        self.assertTrue((status & self._get_alarm_mask("InvalidData")) > 0)

    def test_normal_ch4_concentration(self):
        status = self._get_analyzer_status(0, {"species": 170, "ValveMask": 0, "CH4": 2.0})
        self.assertTrue((status & self._get_alarm_mask("CH4Concentration")) == 0)
        self.assertTrue((status & self._get_alarm_mask("InvalidData")) == 0)
    
###################### GPS ############################################

    def test_normal_GPS_uncertainty(self):
        status = self._get_peripheral_status(0, {"species": 170, "ValveMask": 0, "GPS_UNC_LAT": 0.0, "GPS_UNC_LONG": 0.0})
        self.assertTrue((status & self._get_alarm_mask("ModerateGpsUncertainty")) == 0)
        self.assertTrue((status & self._get_alarm_mask("LargeGpsUncertainty")) == 0)

    def test_moderate_GPS_uncertainty(self):
        status = self._get_peripheral_status(0, {"species": 170, "ValveMask": 0, "GPS_UNC_LAT": 20.0, "GPS_UNC_LONG": 20.0})
        self.assertTrue((status & self._get_alarm_mask("ModerateGpsUncertainty")) > 0)
        self.assertTrue((status & self._get_alarm_mask("LargeGpsUncertainty")) == 0)

    def test_large_GPS_uncertainty(self):
        status = self._get_peripheral_status(0, {"species": 170, "ValveMask": 0, "GPS_UNC_LAT": 100.0, "GPS_UNC_LONG": 100.0})
        self.assertTrue((status & self._get_alarm_mask("ModerateGpsUncertainty")) > 0)
        self.assertTrue((status & self._get_alarm_mask("LargeGpsUncertainty")) > 0)

    def test_car_speed(self):
        # large car speed
        status = self._get_peripheral_status(0, {"species": 170, "ValveMask": 0, "CAR_VEL_N": 50.0, "CAR_VEL_E": 50.0})
        self.assertTrue((status & self._get_alarm_mask("LargeCarSpeed")) > 0)
        # normal car speed
        status = self._get_peripheral_status(0, {"species": 170, "ValveMask": 0, "CAR_VEL_N": 5.0, "CAR_VEL_E": 5.0})
        self.assertTrue((status & self._get_alarm_mask("LargeCarSpeed")) == 0)

###################### Anemometer ############################################