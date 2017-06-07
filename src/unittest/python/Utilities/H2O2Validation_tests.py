import os
import sys
import time
import unittest
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication
from Host.Utilities.H2O2ValidationWizard.H2O2Validation import H2O2Validation
from Host.Utilities.BuildHelper.BuildHelper import isAnalyzerToBuild

CONFIG_FILE = os.path.abspath(r"./src/main/python/Host/Utilities/H2O2ValidationWizard/H2O2Validation.ini")

app = QApplication(sys.argv)

@unittest.skipUnless(isAnalyzerToBuild(["NCDS"]), "Analyzer type not match")
class TestH2O2Validation(unittest.TestCase):
    def setUp(self):
        self.wizard = H2O2Validation(CONFIG_FILE, True, False)
        # speed up the process to save time in testing
        self.wizard.update_period = 0.1
        self.wizard.wait_time_before_collection = 0.3
        self.wizard.data_collection_time = 2
        # bypass the login screen
        self.wizard.login_frame.hide()
        self.wizard.top_frame.show()
        self.wizard.wizard_frame.show()        

    def tearDown(self):
        self.wizard = None

    def test_low_cavity_pressure(self):
        self.wizard.simulation_dict["CavityPressure"] = "100-x"
        self.wizard.start_data_collection()
        next_button = self.wizard.button_next_step
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.qWait(2000)
        self.assertTrue("Cavity pressure is out of range" in self.wizard.info)

if __name__ == '__main__':
    unittest.main()