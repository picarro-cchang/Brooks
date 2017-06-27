import os
import time
import unittest
from TestUtils import TestAnalyzer
from Host.Utilities.BuildHelper.BuildHelper import isAnalyzerToBuild

@unittest.skipUnless(isAnalyzerToBuild(["NCDS"]), "Analyzer type not match")
class TestNCDSAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_agent = TestAnalyzer("NCDS", "supervisorSO_simulation.ini")
        cls.test_agent.start_analyzer()
        
    @classmethod
    def tearDownClass(cls):
        cls.test_agent.stop_analyzer()

    def test_0_warm_up_mode(self):
        self.test_agent.start_log_listener()
        start_time = time.time()
        while time.time() - start_time < 300:
            if self.test_agent.error_msg:
                print self.test_agent.error_msg
                self.assertTrue(self.test_agent.error_msg == None)
            elif self.test_agent.measurement:
                self.test_agent.log_listener.stop()
                break
            time.sleep(1)
        self.assertTrue(self.test_agent.measurement)

    def test_1_measurement_mode(self):
        time.sleep(10)  # skip some initial points
        self.test_agent.start_data_manager_listener("analyze_H2O2", ["H2O2", "CH4", "H2O"])
        time.sleep(60)  # collect data
        data_dict = dict(H2O2=[], CH4=[], H2O=[])
        while not self.test_agent.data_queue.empty():
            data = self.test_agent.data_queue.get(block=False)
            if data:
                for k in data_dict:
                    data_dict[k].append(data[k])
        self.test_agent.data_manager_listener.stop()
        h2o2_avg = sum(data_dict["H2O2"]) / len(data_dict["H2O2"])
        ch4_avg = sum(data_dict["CH4"]) / len(data_dict["CH4"])
        h2o_avg = sum(data_dict["H2O"]) / len(data_dict["H2O"])
        self.assertTrue(h2o2_avg > 180 and h2o2_avg < 230)
        self.assertTrue(ch4_avg > 1 and ch4_avg < 5)
        self.assertTrue(h2o_avg > 0 and h2o_avg < 3)

if __name__ == '__main__':
    unittest.main()