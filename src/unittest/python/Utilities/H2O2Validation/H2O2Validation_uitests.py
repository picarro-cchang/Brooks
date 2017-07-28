import os
import sys
import time
import shutil
import unittest
from mockito import patch, unstub
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication, QMessageBox
from Host.WebServer.SQLiteServer import SQLiteServer
from Host.WebServer.SQLiteServer import app as flask_app
from Host.Utilities.H2O2ValidationWizard.H2O2Validation import H2O2Validation, validation_steps
from Host.Utilities.BuildHelper.BuildHelper import isAnalyzerToBuild

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "H2O2Validation.ini")

app = QApplication(sys.argv)

#@unittest.skipUnless(isAnalyzerToBuild(["NDDS"]), "Analyzer type not match")
class TestH2O2Validation(unittest.TestCase):
    def setUp(self):
        self.wizard = H2O2Validation(CONFIG_FILE, simulation=True, no_login=False)
        self.message_box_content = {"title":"", "msg":"", "response":QMessageBox.Ok}
        patch(self.wizard.message_box, self.message_box)       

    def tearDown(self):
        self.wizard.close()
        self.wizard = None

    def message_box(self, icon, title, message, buttons=QMessageBox.Ok):
        self.message_box_content["title"] = title
        self.message_box_content["msg"] = message
        return self.message_box_content["response"]

    def bypass_login_screen(self):
        self.wizard.login_frame.hide()
        self.wizard.top_frame.show()
        self.wizard.wizard_frame.show()
        self.wizard.start_data_collection()
        
    def test_full_process(self):
        with flask_app.test_request_context():
            server = SQLiteServer(dummy=True)
            patch(self.wizard._send_request, server.get_request)
            # login
            self.wizard.input_user_name.setText("admin")
            self.wizard.input_password.setText("admin")
            QTest.mouseClick(self.wizard.button_user_login, Qt.LeftButton)
            self.assertTrue(self.wizard.current_user["username"] == "admin")
            self.assertTrue("Admin" in self.wizard.current_user["roles"])
            # validation
            next_button = self.wizard.button_next_step
            measurements = ["zero_air", "calibrant1", "calibrant2", "calibrant3"]
            nominal_concentraion = [0, 2, 10, 100]
            for step in range(4):
                stage = measurements[step]
                QTest.mouseClick(next_button, Qt.LeftButton)
                QTest.mouseClick(next_button, Qt.LeftButton)
                self.message_box_content["title"] = ""
                self.assertTrue(validation_steps[self.wizard.current_step] == stage)
                QTest.qWait(1500)   # data collection
                self.assertTrue(stage + "_ch4_mean" in self.wizard.validation_results)
                self.assertTrue(self.message_box_content["title"] == "Measurement Done")
            # create report
            QTest.mouseClick(next_button, Qt.LeftButton)
            # login again
            self.wizard.input_user_name.setText("tech")
            self.wizard.input_password.setText("tech")
            QTest.mouseClick(self.wizard.button_user_login, Qt.LeftButton)
            self.assertTrue(self.wizard.signature_user["username"] == "tech")
            self.assertTrue(self.message_box_content["title"] == "Validation Pass")
            # check report
            last_action = server.ds.action_model[-1].action
            self.assertTrue("Validation pass. Report created" in last_action)
            filename = last_action.split(":")[1]
            filename = os.path.join(self.wizard.curr_dir, filename.strip())
            self.assertTrue(os.path.exists(filename))
            data_file = os.path.join(os.path.split(filename)[0], "validation_data.csv")
            self.assertTrue(os.path.exists(data_file))
            shutil.rmtree(os.path.split(filename)[0]) 

        # clear mockito functions
        unstub()
    
    def test_low_cavity_pressure(self):
        # simulate the case that cylinder gets empty and cavity pressure drops
        self.wizard.simulation_dict["CavityPressure"] = "100-x"
        self.bypass_login_screen()
        next_button = self.wizard.button_next_step
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.qWait(1000)   # zero-air measurement
        self.assertTrue("Cavity pressure is out of range" in self.message_box_content["msg"])

    def test_select_wrong_cylinder(self):
        self.bypass_login_screen()
        for s in validation_steps:
            if validation_steps[s] == "calibrant1":
                self.wizard.current_step = s - 2
                break
        next_button = self.wizard.button_next_step
        QTest.mouseClick(next_button, Qt.LeftButton)
        # simulated concentration is 2; intentionally choose a different cylinder
        self.wizard.select_cylinder.setCurrentIndex(1)
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.qWait(1500)   # data collection
        self.assertTrue("Measurement result is too far away" in self.message_box_content["msg"])

if __name__ == '__main__':
    #unittest.main()
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)
